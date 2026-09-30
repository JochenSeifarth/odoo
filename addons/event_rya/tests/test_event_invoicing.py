# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, timedelta

from odoo import Command, fields
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestEventInvoicing(TransactionCase):
    """How a payment of an event order turns into an invoice.

    An event order is paid in the installments of its payment term. The standard
    invoicing would turn the first installment into a down payment invoice and
    leave the rest of the order to a second one, spreading the tickets of one
    event over two documents. An event order gets one invoice for its whole
    total instead, and a later installment does not invoice it again.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.today = fields.Date.context_today(cls.env.user)
        cls.event_date = cls.today + timedelta(days=180)
        cls.product = cls.env['product.product'].create({
            'name': 'Test Event Ticket',
            'type': 'service',
            'service_tracking': 'event',
            'list_price': 100.0,
        })
        cls.standard_product = cls.env['product.product'].create({
            'name': 'Test Service',
            'type': 'service',
            'list_price': 100.0,
        })
        cls.event_type = cls.env['event.type'].create({
            'name': 'Test Event Type',
            'event_type_ticket_ids': [Command.create({
                'name': 'Test Ticket',
                'product_id': cls.product.id,
            })],
        })
        cls.event = cls.env['event.event'].create({
            'name': 'Test Event',
            'event_type_id': cls.event_type.id,
            'date_begin': datetime.combine(cls.event_date, datetime.min.time()),
            'date_end': datetime.combine(
                cls.event_date + timedelta(days=1), datetime.min.time(),
            ),
        })
        cls.ticket = cls.event.event_ticket_ids
        cls.payment_term = cls.env.ref('event_rya.payment_term_event_20_80_90')
        cls.partner = cls.env['res.partner'].create({'name': 'Test Customer'})
        cls.event_order = cls._create_event_order()
        cls.standard_order = cls._create_standard_order()

    @classmethod
    def _create_event_order(cls, confirm=True):
        order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
            'payment_term_id': cls.payment_term.id,
            'order_line': [Command.create({
                'product_id': cls.product.id,
                'event_id': cls.event.id,
                'event_ticket_id': cls.ticket.id,
                'price_unit': 100.0,
            })],
        })
        if confirm:
            order.action_confirm()
        return order

    @classmethod
    def _create_standard_order(cls):
        order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
            'payment_term_id': cls.payment_term.id,
            'order_line': [Command.create({
                'product_id': cls.standard_product.id,
                'price_unit': 100.0,
            })],
        })
        order.action_confirm()
        return order

    def _create_transaction(self, order, amount, *other_orders):
        """Register a done payment, on `order` alone or on all the given orders."""
        return self.env['payment.transaction'].create({
            'provider_id': self.env['payment.provider'].search([], limit=1).id,
            'payment_method_id': self.env['payment.method'].search([], limit=1).id,
            'partner_id': order.partner_id.id,
            'amount': amount,
            'currency_id': order.currency_id.id,
            'reference': f'TEST-{order.id}-{amount}',
            'state': 'done',
            'sale_order_ids': [Command.set((order + sum(other_orders, self.env['sale.order'])).ids)],
        })

    def test_event_order_is_invoiced_once_for_its_total(self):
        """The first installment invoices the whole order, not a down payment."""
        transaction = self._create_transaction(self.event_order, 20.0)

        transaction._invoice_sale_orders()

        invoices = self.event_order.invoice_ids
        self.assertEqual(len(invoices), 1)
        self.assertEqual(invoices.amount_total, self.event_order.amount_total)
        self.assertEqual(invoices.invoice_payment_term_id, self.payment_term)
        self.assertEqual(invoices.state, 'draft')

    def test_second_installment_does_not_invoice_again(self):
        """Its lines are billed already, a later installment bills nothing."""
        self._create_transaction(self.event_order, 20.0)._invoice_sale_orders()
        second = self._create_transaction(self.event_order, 80.0)

        second._invoice_sale_orders()

        self.assertEqual(len(self.event_order.invoice_ids), 1)

    def test_standard_order_keeps_the_standard_downpayment_invoice(self):
        """Only an event order is invoiced for its total, a standard one is not."""
        transaction = self._create_transaction(self.standard_order, 20.0)

        transaction._invoice_sale_orders()

        invoices = self.standard_order.invoice_ids
        self.assertEqual(len(invoices), 1)
        self.assertLess(invoices.amount_total, self.standard_order.amount_total)

    def test_invoice_carries_the_due_date_of_every_installment(self):
        """The one invoice shows when each installment of the term is due."""
        self._create_transaction(self.event_order, 20.0)._invoice_sale_orders()

        invoice = self.event_order.invoice_ids

        self.assertEqual(
            sorted(term['date_maturity'] for term in invoice.needed_terms),
            sorted([
                self.today,
                self.event_date - timedelta(days=90),
            ]),
        )

    def test_invoice_of_an_event_order_is_reachable_in_the_portal(self):
        """The customer has to be able to open the invoice that pays the event."""
        self._create_transaction(self.event_order, 20.0)._invoice_sale_orders()

        self.assertTrue(self.event_order.invoice_ids.access_token)

    def test_draft_event_order_is_not_invoiced(self):
        """A quotation has nothing to invoice yet."""
        draft_order = self._create_event_order(confirm=False)
        transaction = self._create_transaction(draft_order, 20.0)

        transaction._invoice_sale_orders()

        self.assertFalse(draft_order.invoice_ids)

    def test_a_mixed_transaction_invoices_both_orders(self):
        """A transaction may pay an event order and a standard one at once.

        The event order is invoiced for its total, the standard one keeps the
        down payment invoice. Neither of them may be left uninvoiced because
        the other is there.
        """
        transaction = self._create_transaction(
            self.event_order,
            20.0,
            self.standard_order,
        )

        transaction._invoice_sale_orders()

        self.assertEqual(len(self.event_order.invoice_ids), 1)
        self.assertEqual(
            self.event_order.invoice_ids.amount_total,
            self.event_order.amount_total,
        )
        self.assertEqual(len(self.standard_order.invoice_ids), 1)
        self.assertLess(
            self.standard_order.invoice_ids.amount_total,
            self.standard_order.amount_total,
        )
        self.assertEqual(
            transaction.invoice_ids,
            self.event_order.invoice_ids | self.standard_order.invoice_ids,
        )

    def test_a_mixed_transaction_keeps_both_invoices_on_the_transaction(self):
        """The transaction points at both invoices, neither replaces the other."""
        transaction = self._create_transaction(
            self.event_order,
            20.0,
            self.standard_order,
        )

        transaction._invoice_sale_orders()

        self.assertEqual(len(transaction.invoice_ids), 2)

    def test_a_standard_transaction_is_untouched(self):
        """A transaction without event orders keeps the standard behaviour."""
        transaction = self._create_transaction(self.standard_order, 20.0)

        transaction._invoice_sale_orders()

        self.assertEqual(
            transaction.invoice_ids,
            self.standard_order.invoice_ids,
        )
