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

        A transaction may hold several orders. Its event orders are invoiced as
        described above and the others keep the standard behaviour, so that a
        standard order is never left uninvoiced by a transaction that also pays
        for an event.
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
                lambda order: order._has_event_ticket_lines(),
            )
            standard_orders = tx.sale_order_ids - event_orders

            invoices = tx._rya_invoice_event_orders(event_orders)

            if standard_orders:
                invoices |= tx._rya_invoice_standard_orders(standard_orders)

            # One assignment for both kinds, `Command.set` replaces the records
            # instead of adding to them.
            if invoices:
                tx.invoice_ids = [Command.set(invoices.ids)]

    def _rya_invoice_event_orders(self, event_orders):
        """Invoice the event orders of this transaction for their whole total.

        Returns the invoices it created, an empty recordset for an order that is
        not confirmed or whose lines are billed already.
        """
        self.ensure_one()

        event_orders = event_orders.filtered(lambda order: order.state == "sale")

        if not event_orders:
            return self.env["account.move"]

        event_orders._force_lines_to_invoice_policy_order()

        invoices = event_orders.with_context(
            raise_if_nothing_to_invoice=False,
        )._create_invoices(final=True)

        for invoice in invoices:
            invoice._portal_ensure_token()

        return invoices

    def _rya_invoice_standard_orders(self, standard_orders):
        """Invoice the standard orders of this transaction, as the core does.

        `payment.transaction._invoice_sale_orders` only takes a whole
        transaction, and the transaction handled here also pays for an event
        order, so the steps of the core implementation are repeated for these
        orders alone: a fully paid order is invoiced finally, a partially paid
        one becomes a down payment invoice.

        The amount of the down payment is the amount of the whole transaction,
        which is what the core uses as well. Splitting it between the orders of
        a transaction is not attempted, the shop pays one order per transaction
        anyway.
        """
        self.ensure_one()

        standard_orders = standard_orders.filtered(lambda order: order.state == "sale")

        if not standard_orders:
            return self.env["account.move"]

        fully_paid = standard_orders.filtered(lambda order: order._is_paid())

        invoices = (standard_orders - fully_paid).with_context(
            downpayment_fixed_amount=self.amount,
        )._generate_downpayment_invoices()

        fully_paid._force_lines_to_invoice_policy_order()
        invoices += fully_paid.with_context(
            raise_if_nothing_to_invoice=False,
        )._create_invoices(final=True)

        for invoice in invoices:
            invoice._portal_ensure_token()

        return invoices
