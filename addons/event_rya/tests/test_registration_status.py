# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, timedelta

from odoo import Command, fields
from odoo.tests.common import TransactionCase, tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged('post_install', '-at_install')
class TestRegistrationStatus(AccountTestInvoicingCommon, TransactionCase):
    """What a registration of an event order shows as paid.

    The standard implementation marks a registration of a confirmed order as
    sold, whatever has been paid for it. An event order is invoiced for its
    whole total while it is paid in the installments of its payment term, so a
    registration only counts as sold once its invoices are paid for.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # The accounting user of the base class has no right on events, and
        # what is tested here is the status the compute gives, not the rights
        # to create the data it reads.
        event_env = cls.env['event.event'].sudo()
        models = event_env.env

        cls.today = fields.Date.context_today(event_env)
        cls.event_date = cls.today + timedelta(days=180)
        cls.product = models['product.product'].create({
            'name': 'Test Event Ticket',
            'type': 'service',
            'service_tracking': 'event',
            'list_price': 100.0,
        })
        cls.event_type = models['event.type'].create({
            'name': 'Test Event Type',
            'event_type_ticket_ids': [Command.create({
                'name': 'Test Ticket',
                'product_id': cls.product.id,
            })],
        })
        cls.event = event_env.create({
            'name': 'Test Event',
            'event_type_id': cls.event_type.id,
            'date_begin': datetime.combine(cls.event_date, datetime.min.time()),
            'date_end': datetime.combine(
                cls.event_date + timedelta(days=1), datetime.min.time(),
            ),
            'payment_term_id': cls.quick_ref(
                'event_rya.payment_term_event_20_80_90',
            ).id,
        })
        cls.ticket = cls.event.event_ticket_ids
        cls.partner = models['res.partner'].create({'name': 'Test Customer'})
        cls.order = cls._create_order()
        cls.registration = cls.order.order_line.registration_ids

    @classmethod
    def _create_order(cls):
        return cls.env['sale.order'].sudo().create({
            'partner_id': cls.partner.id,
            'order_line': [Command.create({
                'product_id': cls.product.id,
                'event_id': cls.event.id,
                'event_ticket_id': cls.ticket.id,
                'price_unit': 100.0,
            })],
        })

    def _create_invoice(self):
        """Invoice the order, as the payment of its first installment does."""
        return self.order._create_invoices(final=True)

    def _confirm(self):
        """Confirm the order and return the registration it books."""
        self.order.action_confirm()
        return self.order.order_line.registration_ids

    def _pay_in_full(self, invoice):
        self._register_payment(invoice, amount=invoice.amount_total)

    def test_confirmed_order_without_invoice_is_to_pay(self):
        """Nothing invoiced means nothing paid, not sold."""
        registration = self._confirm()

        self.assertEqual(registration.sale_status, 'to_pay')

    def test_invoiced_order_without_payment_is_to_pay(self):
        registration = self._confirm()
        self._create_posted_invoice()

        self.assertEqual(registration.sale_status, 'to_pay')

    def test_partially_paid_order_is_partial(self):
        """A deposit paid on the order is what the term asks for now."""
        registration = self._confirm()
        invoice = self._create_posted_invoice()
        self._register_payment(invoice, amount=20.0)

        self.assertEqual(
            invoice.amount_residual,
            invoice.amount_total - 20.0,
        )
        self.assertEqual(registration.sale_status, 'partial')

    def test_paid_order_is_sold(self):
        registration = self._confirm()
        invoice = self._create_posted_invoice()
        self._pay_in_full(invoice)

        self.assertEqual(invoice.amount_residual, 0.0)
        self.assertEqual(registration.sale_status, 'sold')

    def test_registration_without_event_ticket_keeps_the_standard_status(self):
        """A registration of another kind is not paid for by the event order."""
        registration = self._confirm()
        self._register_payment(self._create_posted_invoice(), amount=20.0)
        self.assertEqual(registration.sale_status, 'partial')

        registration.event_ticket_id = False
        registration._compute_registration_status()

        self.assertEqual(registration.sale_status, 'sold')

    def test_cancelled_registration_keeps_the_standard_status(self):
        registration = self._confirm()
        self._pay_in_full(self._create_posted_invoice())
        self.assertEqual(registration.sale_status, 'sold')

        registration.state = 'cancel'
        registration._compute_registration_status()

        self.assertEqual(registration.sale_status, 'to_pay')

    def _create_posted_invoice(self):
        invoice = self._create_invoice()
        invoice.action_post()
        return invoice

    def test_draft_invoice_does_not_count_as_paid(self):
        """Only a posted invoice is paid for, a draft one is not an invoice yet."""
        registration = self._confirm()
        invoice = self._create_invoice()

        self.assertEqual(invoice.state, 'draft')
        self.assertEqual(registration.sale_status, 'to_pay')

    def test_registration_of_a_draft_order_keeps_the_standard_status(self):
        """A quotation is not paid for, whatever its invoices say."""
        self.order.action_confirm()
        self._pay_in_full(self._create_posted_invoice())
        registrations = self.order.order_line.registration_ids

        self.order.state = 'draft'
        registrations._compute_registration_status()

        self.assertEqual(registrations.mapped('sale_status'), ['to_pay'])

    def test_free_order_is_free_and_not_to_pay(self):
        """Nothing to pay for means free, the event logic leaves it alone."""
        self.order.order_line.price_unit = 0.0
        self.env.flush_all()
        registration = self._confirm()

        self.assertEqual(self.order.amount_total, 0.0)
        self.assertEqual(registration.sale_status, 'free')

    def test_every_registration_of_an_order_shares_its_status(self):
        """The status comes from the order, so all of its registrations agree."""
        self.order.order_line.product_uom_qty = 2
        self.env.flush_all()
        registrations = self._confirm()

        self._pay_in_full(self._create_posted_invoice())

        self.assertEqual(len(registrations), 2)
        self.assertEqual(registrations.mapped('sale_status'), ['sold', 'sold'])
