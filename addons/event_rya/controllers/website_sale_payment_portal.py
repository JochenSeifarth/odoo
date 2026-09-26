from psycopg2.errors import LockNotAvailable

from odoo import _
from odoo.exceptions import AccessError, MissingError, UserError, ValidationError
from odoo.fields import Command
from odoo.http import request, route
from odoo.tools import SQL

from odoo.addons.sale.controllers import portal as sale_portal
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


class PaymentPortal(
    website_sale_payment.PaymentPortal,
    sale_portal.PaymentPortal,
):

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
        """Create a website payment transaction."""
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
            "sale_order_id": order_id,
        })

        if order_sudo._has_event_ticket_lines():
            kwargs["amount"] = order_sudo._get_rya_payment_amount()
        elif not kwargs.get("amount"):
            kwargs["amount"] = order_sudo.amount_total

        if kwargs["amount"] <= 0:
            raise ValidationError(
                _("There is no payment currently due for this order."),
            )

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

        if kwargs.get("flow") == "token":
            request.update_context(delay_token_charge=True)

        tx_sudo = self._create_transaction(
            custom_create_values={
                "sale_order_ids": [Command.set([order_id])],
            },
            **kwargs,
        )

        request.session["__website_sale_last_tx_id"] = tx_sudo.id

        self._validate_transaction_for_order(
            tx_sudo,
            order_sudo,
        )

        if kwargs.get("flow") == "token":
            tx_sudo._charge_with_token()

        return tx_sudo._get_processing_values()
