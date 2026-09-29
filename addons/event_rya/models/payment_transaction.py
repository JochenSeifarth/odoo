from odoo import Command, models


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    def _invoice_sale_orders(self):
        """Invoice the sales orders of the transactions, event orders their own way.

        An event order is paid in the installments of its payment term, so what
        the customer pays is only a part of its total. The standard
        implementation turns such a part into a down payment invoice and leaves
        the rest of the order to a second invoice, which would spread the
        tickets of one event over two documents. An event order therefore gets
        one invoice for its whole total, carrying the payment term with the due
        date of every installment. A later installment does not invoice it
        again, its lines are billed already.
        """
        event_transactions = self.filtered(
            lambda tx: tx.sale_order_ids.filtered(
                lambda order: order._has_event_ticket_lines(),
            ),
        )

        standard_transactions = self - event_transactions

        # Keep standard Odoo behavior for all non-event orders.
        if standard_transactions:
            super(
                PaymentTransaction,
                standard_transactions,
            )._invoice_sale_orders()

        for tx in event_transactions:
            tx = tx.with_company(tx.company_id)

            event_orders = tx.sale_order_ids.filtered(
                lambda order:
                    order._has_event_ticket_lines()
                    and order.state == "sale",
            )

            if not event_orders:
                continue

            event_orders._force_lines_to_invoice_policy_order()

            invoices = event_orders.with_context(
                raise_if_nothing_to_invoice=False,
            )._create_invoices(final=True)

            for invoice in invoices:
                invoice._portal_ensure_token()

            if invoices:
                tx.invoice_ids = [Command.set(invoices.ids)]
