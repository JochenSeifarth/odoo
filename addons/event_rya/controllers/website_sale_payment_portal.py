from psycopg2.errors import LockNotAvailable

from odoo import _
from odoo.exceptions import AccessError, MissingError, UserError, ValidationError
from odoo.fields import Command
from odoo.http import request, route
from odoo.tools import SQL

from odoo.addons.website_sale.controllers import payment


class PaymentPortal(payment.PaymentPortal):

    @route(
        "/shop/payment/transaction/<int:order_id>",
        type="jsonrpc",
        auth="public",
        website=True,
    )
    def shop_payment_transaction(self, order_id, access_token, **kwargs):
        """Create a website payment transaction.

        Event orders use the currently due payment-term amount.
        """
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
            kwargs["amount"] = order_sudo._get_rya_due_payment_amount()
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
