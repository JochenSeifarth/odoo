# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, timedelta
from unittest.mock import patch

from odoo import Command, fields
from odoo.tests import TransactionCase


class TestEventPaymentTerms(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.today = fields.Date.context_today(cls.env.user)
        cls.event_date = cls.today + timedelta(days=180)
        cls.later_event_date = cls.event_date + timedelta(days=30)
        cls.product = cls.env['product.product'].create({
            'name': 'Test Event Ticket',
            'type': 'service',
            'service_tracking': 'event',
            'list_price': 100.0,
        })
        cls.event_type = cls.env['event.type'].create({
            'name': 'Test Event Type',
            'event_type_ticket_ids': [Command.create({
                'name': 'Test Ticket',
                'product_id': cls.product.id,
            })],
        })
        cls.event = cls._create_event('Test Event', cls.event_date)
        cls.later_event = cls._create_event('Later Test Event', cls.later_event_date)
        cls.ticket = cls.event.event_ticket_ids
        cls.later_ticket = cls.later_event.event_ticket_ids
        cls.payment_term = cls.env.ref('event_rya.payment_term_event_20_80_90')
        cls.standard_product = cls.env['product.product'].create({
            'name': 'Test Service',
            'type': 'service',
            'list_price': 100.0,
        })
        cls.partner = cls.env['res.partner'].create({'name': 'Test Customer'})
        cls.sale_order = cls._create_sale_order(cls.ticket)

    @classmethod
    def _create_event(cls, name, event_date):
        return cls.env['event.event'].create({
            'name': name,
            'event_type_id': cls.event_type.id,
            'date_begin': datetime.combine(event_date, datetime.min.time()),
            'date_end': datetime.combine(event_date + timedelta(days=1), datetime.min.time()),
        })

    @classmethod
    def _create_sale_order(cls, *tickets, slot=None, with_payment_term=True):
        values = {
            'partner_id': cls.partner.id,
            'order_line': [Command.create({
                'product_id': cls.product.id,
                'event_id': ticket.event_id.id,
                'event_slot_id': slot.id if slot else False,
                'event_ticket_id': ticket.id,
                'price_unit': 100.0,
            }) for ticket in tickets],
        }
        if with_payment_term:
            values['payment_term_id'] = cls.payment_term.id
        return cls.env['sale.order'].create(values)

    def _create_slot(self):
        """Turn the test event into a multi slot event running over the slot date."""
        slot_date = self.event.date_begin.date() + timedelta(days=30)
        self.event.write({
            'is_multi_slots': True,
            'date_end': datetime.combine(slot_date + timedelta(days=1), datetime.min.time()),
        })
        return self.env['event.slot'].create({
            'event_id': self.event.id,
            'date': slot_date,
            'start_hour': 14.0,
            'end_hour': 16.0,
        })

    def test_schedule_of_event_order(self):
        schedule = self.sale_order._get_rya_payment_schedule()

        self.assertEqual(len(schedule), 2)
        self.assertEqual([line['amount'] for line in schedule], [20.0, 80.0])
        self.assertEqual([line['due'] for line in schedule], [True, False])
        self.assertEqual(schedule[1]['date'], self.event_date - timedelta(days=90))

    def test_due_amount_of_event_order(self):
        self.assertEqual(self.sale_order._get_rya_due_payment_amount(), 20.0)
        self.assertEqual(self.sale_order._get_rya_payment_amount(), 20.0)

    def test_paid_amount_is_no_longer_due(self):
        self.sale_order.action_confirm()
        self._create_payment_transaction(20.0)

        self.assertEqual(self.sale_order.amount_paid, 20.0)
        self.assertEqual(self.sale_order._get_rya_due_payment_amount(), 20.0)
        self.assertEqual(self.sale_order._get_rya_payment_amount(), 0.0)
        self.assertFalse(self.sale_order._has_to_be_paid())

    def test_partially_paid_amount_leaves_a_rest(self):
        self.sale_order.action_confirm()
        self._create_payment_transaction(5.0)

        self.assertEqual(self.sale_order._get_rya_due_payment_amount(), 20.0)
        self.assertEqual(self.sale_order._get_rya_payment_amount(), 15.0)
        self.assertTrue(self.sale_order._has_to_be_paid())

    def test_paid_later_installment_is_not_due_yet(self):
        self.sale_order.action_confirm()
        self._create_payment_transaction(100.0)

        self.assertEqual(self.sale_order._get_rya_payment_amount(), 0.0)

    def test_due_amount_without_event_term_lines(self):
        """A standard payment term has no installment, the whole amount is due."""
        self.sale_order.payment_term_id = self.env['account.payment.term'].create({
            'name': 'Test Payment Term',
        })

        schedule = self.sale_order._get_rya_payment_schedule()

        self.assertEqual(len(schedule), 1)
        self.assertEqual(schedule[0]['amount'], 100.0)
        self.assertTrue(schedule[0]['due'])
        self.assertEqual(self.sale_order._get_rya_due_payment_amount(), 100.0)

    def test_prepayment_amount_of_an_event_order_is_the_due_amount(self):
        """The share of the term that is due confirms the order."""
        self.assertEqual(
            self.sale_order._get_prepayment_required_amount(),
            self.sale_order._get_rya_due_payment_amount(),
        )

    def test_prepayment_amount_keeps_standard_behaviour(self):
        """An order without event lines confirms on the share of the company."""
        product = self.env['product.product'].create({
            'name': 'Test Service',
            'type': 'service',
            'list_price': 100.0,
        })
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [Command.create({
                'product_id': product.id,
                'price_unit': 100.0,
            })],
        })

        self.assertEqual(
            order._get_prepayment_required_amount(),
            order.currency_id.round(
                order.amount_total * order.prepayment_percent,
            ),
        )

    def test_prepayment_amount_without_online_payment(self):
        """A company that asks for no online payment confirms without a payment."""
        self.sale_order.require_payment = False

        self.assertEqual(self.sale_order._get_prepayment_required_amount(), 0.0)
        self.assertTrue(self.sale_order._is_confirmation_amount_reached())

    def test_prepayment_amount_without_online_payment_keeps_standard_behaviour(self):
        """Turning off online payment does not change a standard order."""
        self.sale_order.require_payment = False
        product = self.env['product.product'].create({
            'name': 'Test Service',
            'type': 'service',
            'list_price': 100.0,
        })
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [Command.create({
                'product_id': product.id,
                'price_unit': 100.0,
            })],
        })
        order.require_payment = False

        self.assertEqual(order._get_prepayment_required_amount(), 0.0)
        self.assertTrue(order._is_confirmation_amount_reached())

    def test_paying_the_due_amount_confirms_the_order(self):
        """The payment of the first installment confirms the order and invoices it."""
        self.env['ir.config_parameter'].sudo().set_param('sale.automatic_invoice', 'True')
        transaction = self._create_payment_transaction(20.0)
        transaction._post_process()

        self.assertEqual(self.sale_order.state, 'sale')
        self.assertTrue(self.sale_order.invoice_ids)
        self.assertEqual(self.sale_order.invoice_ids.move_type, 'out_invoice')
        self.assertEqual(self.sale_order.invoice_ids.invoice_payment_term_id, self.payment_term)

    def test_payment_term_of_another_company_is_not_proposed(self):
        """A payment term of another company is left to the customer default."""
        self.event.payment_term_id = self.env['account.payment.term'].create({
            'name': 'Payment Term Of Another Company',
            'company_id': self.env['res.company'].create({'name': 'Other Company'}).id,
        })
        customer_term = self.env['account.payment.term'].create({
            'name': 'Customer Payment Term',
        })
        self.partner.property_payment_term_id = customer_term.id
        order = self._create_sale_order(self.ticket, with_payment_term=False)
        self.env.flush_all()

        self.assertEqual(order.payment_term_id, customer_term)

    def test_payment_term_of_event_is_proposed(self):
        """The term of the event is proposed when the customer has none."""
        self.event.payment_term_id = self.payment_term
        order = self._create_sale_order(self.ticket, with_payment_term=False)
        self.env.flush_all()

        self.assertEqual(order.payment_term_id, self.payment_term)

    def test_payment_term_of_event_wins_over_the_customer_default(self):
        self.partner.property_payment_term_id = self.env['account.payment.term'].create({
            'name': 'Customer Payment Term',
        }).id
        self.event.payment_term_id = self.payment_term
        order = self._create_sale_order(self.ticket, with_payment_term=False)
        self.env.flush_all()

        self.assertEqual(order.payment_term_id, self.payment_term)

    def test_customer_default_applies_when_the_event_proposes_none(self):
        customer_term = self.env['account.payment.term'].create({
            'name': 'Customer Payment Term',
        })
        self.partner.property_payment_term_id = customer_term.id
        order = self._create_sale_order(self.ticket, with_payment_term=False)
        self.env.flush_all()

        self.assertEqual(order.payment_term_id, customer_term)

    def test_payment_term_of_event_is_proposed_on_a_later_event_line(self):
        """The shop adds the event line to an existing cart."""
        self.event.payment_term_id = self.payment_term
        order = self.env['sale.order'].create({'partner_id': self.partner.id})
        self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product.id,
            'event_id': self.event.id,
            'event_ticket_id': self.ticket.id,
            'price_unit': 100.0,
        })
        self.env.flush_all()

        self.assertEqual(order.payment_term_id, self.payment_term)

    def test_start_and_term_come_from_the_earliest_event_line(self):
        """Both values have to come from the line that starts first."""
        self.event.payment_term_id = self.payment_term
        order = self._create_sale_order(self.ticket, self.later_ticket)

        start_date, payment_term = order._get_rya_event_start_and_term()

        self.assertEqual(start_date, self.event.date_begin)
        self.assertEqual(payment_term, self.payment_term)

    def test_start_and_term_come_from_the_booked_slot(self):
        """A line books a slot, the slot starts the event line."""
        self.event.payment_term_id = self.payment_term
        slot = self._create_slot()
        order = self._create_sale_order(self.ticket, slot=slot)

        start_date, payment_term = order._get_rya_event_start_and_term()

        self.assertEqual(start_date, slot.start_datetime)
        self.assertEqual(payment_term, self.payment_term)

    def test_start_date_ignores_an_event_line_without_a_date(self):
        """An event line whose event has no date dates nothing."""
        order = self._create_sale_order(self.ticket)

        with patch.object(type(self.event), 'date_begin', False):
            self.assertEqual(
                order._get_rya_event_start_and_term(),
                (False, self.env['account.payment.term']),
            )

    def test_start_and_term_of_an_order_without_event_line(self):
        """An order without an event line has neither a start nor a term."""
        order = self.env['sale.order'].create({'partner_id': self.partner.id})
        self.env.flush_all()

        self.assertEqual(
            order._get_rya_event_start_and_term(),
            (False, self.env['account.payment.term']),
        )

    def test_payment_term_of_event_is_proposed_on_a_later_event_slot_line(self):
        """The shop adds a slot of a multi slot event to an existing cart."""
        self.event.payment_term_id = self.payment_term
        slot = self._create_slot()
        order = self.env['sale.order'].create({'partner_id': self.partner.id})
        self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product.id,
            'event_id': self.event.id,
            'event_slot_id': slot.id,
            'event_ticket_id': self.ticket.id,
            'price_unit': 100.0,
        })
        self.env.flush_all()

        self.assertEqual(order.payment_term_id, self.payment_term)

    def test_customer_default_applies_without_event_line(self):
        customer_term = self.env['account.payment.term'].create({
            'name': 'Customer Payment Term',
        })
        self.partner.property_payment_term_id = customer_term.id
        order = self.env['sale.order'].create({'partner_id': self.partner.id})
        self.env.flush_all()

        self.assertEqual(order.payment_term_id, customer_term)

    def test_payment_term_line_due_date_accepts_any_date_type(self):
        line = self._event_line.with_context(rya_event_date=self.event_date)
        expected = self.event_date - timedelta(days=90)

        self.assertEqual(line._get_due_date(self.today), expected)
        self.assertEqual(
            line._get_due_date(datetime.combine(self.today, datetime.min.time())),
            expected,
        )
        self.assertEqual(line._get_due_date(fields.Date.to_string(self.today)), expected)

    def test_payment_term_line_due_date_never_before_document(self):
        line = self._event_line.with_context(rya_event_date=self.today - timedelta(days=1))

        self.assertEqual(line._get_due_date(self.today), self.today)

    def test_payment_term_line_due_date_without_event_date(self):
        """Without an event date the line is due immediately, not in the past."""
        self.assertEqual(self._event_line._get_due_date(self.today), self.today)

    def test_invoice_terms_are_dated_from_the_event(self):
        invoice = self._create_invoice(self.sale_order.order_line)

        self.assertEqual(invoice._get_rya_event_start_date(), self.event.date_begin)
        self.assertEqual(
            sorted(term['date_maturity'] for term in invoice.needed_terms),
            [self.today, self.event_date - timedelta(days=90)],
        )

    def test_invoice_date_of_multiple_events_is_the_earliest(self):
        invoice = self._create_invoice(*self.sale_order.order_line, self.later_order_line)

        self.assertEqual(invoice._get_rya_event_start_date(), self.event.date_begin)

    def test_terms_of_a_set_of_invoices_are_dated_from_their_event(self):
        """A batch of moves hands the date to the event invoice only."""
        event_invoice = self._create_invoice(self.sale_order.order_line)
        standard_invoice = self._create_invoice(self.standard_order_line)
        without_term = self._create_invoice(self.standard_order_line)
        without_term.invoice_payment_term_id = False

        (event_invoice + standard_invoice + without_term)._compute_needed_terms()

        self.assertEqual(
            sorted(term['date_maturity'] for term in event_invoice.needed_terms),
            [self.today, self.event_date - timedelta(days=90)],
        )
        self.assertEqual(
            sorted(term['date_maturity'] for term in standard_invoice.needed_terms),
            [self.today],
        )
        self.assertEqual(
            sorted(term['date_maturity'] for term in without_term.needed_terms),
            [self.today],
        )

    @property
    def standard_order_line(self):
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [Command.create({
                'product_id': self.standard_product.id,
                'price_unit': 100.0,
            })],
        })
        return order.order_line

    @property
    def _event_line(self):
        return self.payment_term.line_ids.filtered(
            lambda line: line.delay_type == 'rya_days_after_event',
        )

    @property
    def later_order_line(self):
        later_order = self._create_sale_order(self.later_ticket)
        return later_order.order_line

    def _create_invoice(self, *order_lines):
        return self.env['account.move'].new({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'invoice_date': self.today,
            'invoice_payment_term_id': self.payment_term.id,
            'invoice_line_ids': [Command.create({
                'name': line.name,
                'quantity': line.product_uom_qty,
                'price_unit': line.price_unit,
                'sale_line_ids': [Command.set(line.ids)],
            }) for line in order_lines],
        })

    def test_paying_the_due_amount_matches_it(self):
        """The shop shows the payment as the one the term asked for."""
        self.sale_order.action_confirm()
        transaction = self._create_payment_transaction(20.0)

        self.assertTrue(
            self.sale_order._rya_transaction_matches_due_amount(transaction),
        )

    def test_paying_another_amount_does_not_match_it(self):
        self.sale_order.action_confirm()
        transaction = self._create_payment_transaction(5.0)

        self.assertFalse(
            self.sale_order._rya_transaction_matches_due_amount(transaction),
        )

    def test_paying_the_due_amount_of_a_standard_order_does_not_match_it(self):
        """Only an event order has a due amount to match."""
        product = self.env['product.product'].create({
            'name': 'Test Service',
            'type': 'service',
            'list_price': 100.0,
        })
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [Command.create({
                'product_id': product.id,
                'price_unit': 100.0,
            })],
        })
        transaction = self._create_payment_transaction(20.0, order=order)

        self.assertFalse(order._rya_transaction_matches_due_amount(transaction))

    def _create_payment_transaction(self, amount, order=None):
        """Register a confirmed payment on the order, as the shop does."""
        order = order or self.sale_order
        return self.env['payment.transaction'].create({
            'provider_id': self.env['payment.provider'].search([], limit=1).id,
            'payment_method_id': self.env['payment.method'].search([], limit=1).id,
            'partner_id': order.partner_id.id,
            'amount': amount,
            'currency_id': order.currency_id.id,
            'reference': 'TEST-TRANSACTION',
            'state': 'done',
            'sale_order_ids': [Command.set(order.ids)],
        })
