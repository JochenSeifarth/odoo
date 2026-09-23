from odoo import _
from odoo.exceptions import UserError
from odoo.fields import Command
from odoo.http import request, route

from odoo.addons.website_sale.controllers.payment import (
    PaymentPortal as WebsiteSalePaymentPortal,
)


class PaymentPortal(WebsiteSalePaymentPortal):

    @route(
        "/shop/payment/transaction/<int:order_id>",
        type="jsonrpc",
        auth="public",
        website=True,
    )
    def shop_payment_transaction(self, order_id, access_token, **kwargs):

        order_sudo = self._document_check_access(
            "sale.order",
            order_id,
            access_token,
        )

        order_sudo._check_cart_is_ready_to_be_paid()
        self._validate_transaction_kwargs(kwargs)

        kwargs.update({
            "partner_id": order_sudo.partner_invoice_id.id,
            "currency_id": order_sudo.currency_id.id,
            "sale_order_id": order_id,
        })

        if not kwargs.get("amount"):
            kwargs["amount"] = (
                order_sudo._get_prepayment_required_amount()
                if order_sudo._has_prepayment()
                else order_sudo.amount_total
            )

        if order_sudo.currency_id.compare_amounts(
            order_sudo.amount_paid,
            order_sudo.amount_total,
        ) == 0:
            raise UserError(
                _("The cart has already been paid. Please refresh the page."),
            )

        delay_token_charge = kwargs.get("flow") == "token"

        if delay_token_charge:
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

        if delay_token_charge:
            tx_sudo._charge_with_token()

        return tx_sudo._get_processing_values()
