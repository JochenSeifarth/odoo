from odoo import Command, models


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    def _invoice_sale_orders(self):
        rya_transactions = self.filtered(
            lambda tx: tx.sale_order_ids.filtered(
                lambda order: order._has_event_ticket_lines(),
            ),
        )

        normal_transactions = self - rya_transactions

        # Keep standard Odoo behavior for all non-event orders.
        if normal_transactions:
            super(
                PaymentTransaction,
                normal_transactions,
            )._invoice_sale_orders()

        # Event orders: create the full invoice, not a downpayment invoice.
        for tx in rya_transactions:
            tx = tx.with_company(tx.company_id)

            confirmed_orders = tx.sale_order_ids.filtered(
                lambda order: order.state == "sale",
            )

            if not confirmed_orders:
                continue

            confirmed_orders._force_lines_to_invoice_policy_order()

            invoices = confirmed_orders.with_context(
                raise_if_nothing_to_invoice=False,
            )._create_invoices(final=True)

            for invoice in invoices:
                invoice._portal_ensure_token()

            if invoices:
                tx.invoice_ids = [Command.set(invoices.ids)]
