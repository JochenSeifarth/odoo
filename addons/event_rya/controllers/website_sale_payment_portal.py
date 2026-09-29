from psycopg2.errors import LockNotAvailable

from odoo import _
from odoo.exceptions import AccessError, MissingError, UserError, ValidationError
from odoo.fields import Command
from odoo.http import request, route
from odoo.tools import SQL

from odoo.addons.website_sale.controllers import payment as website_sale_payment
from odoo.addons.website_sale.controllers import sale as website_sale_sale


class CustomerPortal(website_sale_sale.CustomerPortal):

    def _get_payment_values(
        self,
        order_sudo,
        website_id=None,
        **kwargs,
    ):
        if order_sudo._has_event_ticket_lines():
            kwargs["payment_amount"] = order_sudo._get_rya_payment_amount()
            if order_sudo.state == "sale":
                kwargs["is_down_payment"] = False

        return super()._get_payment_values(
            order_sudo,
            website_id=website_id,
            **kwargs,
        )


class PaymentPortal(website_sale_payment.PaymentPortal):
    """Payment routes of the shop and of the My Account, for the event orders.

    `website_sale.PaymentPortal` is the only class extended here. It is worth
    knowing that the override of `_create_transaction` below serves the My
    Account route `/my/orders/<id>/transaction` as well: `odoo.http` rebuilds
    one controller per hierarchy, and every payment portal built on
    `payment.PaymentPortal` ends up in that single class, whichever of them an
    addon extends. This is intended, an event order pays the part of its term
    that is due wherever the payment is started, and the portal form is filled
    with that amount by `CustomerPortal._get_payment_values`.
    """

    def _create_transaction(
        self,
        provider_id,
        payment_method_id,
        token_id,
        amount,
        currency_id,
        partner_id,
        flow,
        tokenization_requested,
        landing_route,
        reference_prefix=None,
        is_validation=False,
        custom_create_values=None,
        **kwargs,
    ):
        """Create a draft transaction, the amount of an event order is ours.

        The browser only sends the order to pay, the part of the payment term
        that is due is computed on the server. An event order that has nothing
        due anymore is refused, paying it would create a transaction of zero.
        """
        sale_order_id = kwargs.get("sale_order_id")

        if sale_order_id and not is_validation:
            order = request.env["sale.order"].sudo().browse(sale_order_id)

            if order.exists() and order._has_event_ticket_lines():
                amount = order._get_rya_payment_amount()

                if amount <= 0:
                    raise ValidationError(
                        _("There is no payment currently due for this order."),
                    )

        return super()._create_transaction(
            provider_id,
            payment_method_id,
            token_id,
            amount,
            currency_id,
            partner_id,
            flow,
            tokenization_requested,
            landing_route,
            reference_prefix=reference_prefix,
            is_validation=is_validation,
            custom_create_values=custom_create_values,
            **kwargs,
        )

    @route(
        "/shop/payment/transaction/<int:order_id>",
        type="jsonrpc",
        auth="public",
        website=True,
    )
    def shop_payment_transaction(self, order_id, access_token, **kwargs):
        """Create a website payment transaction.

        Mirror of `website_sale.PaymentPortal.shop_payment_transaction`. The
        standard implementation requires the amount sent by the browser to
        equal the order total, which cannot hold for an event order paying only
        the part of its payment term that is due. That amount is computed on
        the server instead, and the check that the amount matches the total is
        left to the standard orders. Keep in sync with the standard method when
        overriding it upstream.
        """
        # Check the order id and the access token
        # Then lock it during the transaction to prevent concurrent payments
        try:
            order_sudo = self._document_check_access(
                "sale.order",
                order_id,
                access_token,
            )
            request.env.cr.execute(
                SQL(
                    "SELECT 1 FROM sale_order "
                    "WHERE id = %s FOR NO KEY UPDATE NOWAIT",
                    order_id,
                ),
            )
        except MissingError:
            raise
        except AccessError as e:
            raise ValidationError(
                _("The access token is invalid."),
            ) from e
        except LockNotAvailable:
            raise UserError(
                _("Payment is already being processed."),
            )

        if order_sudo.state == "cancel":
            raise ValidationError(
                _("The order has been cancelled."),
            )

        order_sudo._check_cart_is_ready_to_be_paid()

        self._validate_transaction_kwargs(kwargs)

        kwargs.update({
            "partner_id": order_sudo.partner_invoice_id.id,
            "currency_id": order_sudo.currency_id.id,
            # Include the SO to allow Subscriptions to tokenize the tx
            "sale_order_id": order_id,
        })

        if order_sudo._has_event_ticket_lines():
            # An event order pays the part of its term that is due, the amount
            # sent by the browser is ignored. A transaction without an amount to
            # pay is refused by `_create_transaction`.
            kwargs["amount"] = order_sudo._get_rya_payment_amount()
        elif not kwargs.get("amount"):
            kwargs["amount"] = order_sudo.amount_total

        compare_amounts = order_sudo.currency_id.compare_amounts

        if not order_sudo._has_event_ticket_lines():
            if compare_amounts(
                kwargs["amount"],
                order_sudo.amount_total,
            ):
                raise ValidationError(
                    _("The cart has been updated. Please refresh the page."),
                )

        if compare_amounts(
            order_sudo.amount_paid,
            order_sudo.amount_total,
        ) == 0:
            raise UserError(
                _("The cart has already been paid. Please refresh the page."),
            )

        if delay_token_charge := kwargs.get("flow") == "token":
            # wait until after tx validation
            request.update_context(delay_token_charge=True)

        tx_sudo = self._create_transaction(
            custom_create_values={
                "sale_order_ids": [Command.set([order_id])],
            },
            **kwargs,
        )

        # Store the new transaction into the transaction list and if there's an
        # old one, we remove it until the day the ecommerce supports multiple
        # orders at the same time.
        request.session["__website_sale_last_tx_id"] = tx_sudo.id

        self._validate_transaction_for_order(
            tx_sudo,
            order_sudo,
        )

        if delay_token_charge:
            tx_sudo._charge_with_token()

        return tx_sudo._get_processing_values()
