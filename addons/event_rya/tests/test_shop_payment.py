# Part of Odoo. See LICENSE file for full copyright and licensing details.

import uuid
from datetime import datetime, timedelta
from unittest.mock import patch

import odoo.tools
from odoo import Command, fields
from odoo.exceptions import AccessError, MissingError, UserError, ValidationError
from odoo.tests.common import TransactionCase

from odoo.addons.event_rya.controllers.website_sale_payment_portal import (
    CustomerPortal,
    PaymentPortal,
)
from odoo.addons.payment.tests.common import PaymentCommon
from odoo.addons.website_sale.tests.common import MockRequest, WebsiteSaleCommon


class TestShopPayment(WebsiteSaleCommon, PaymentCommon, TransactionCase):
    """The shop route `/shop/payment/transaction/<order_id>` of event orders.

    An event order pays the part of its payment term that is due instead of its
    total, the amount is computed on the server for that reason. An order
    without event lines keeps the standard behaviour, including the checks on
    the amount sent by the browser.
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
        cls.standard_product = cls.env['product.product'].create({
            'name': 'Test Service',
            'type': 'service',
            'list_price': 100.0,
        })
        cls.event_cart = cls._create_cart(cls.product, cls.ticket, cls.payment_term)
        cls.standard_cart = cls._create_cart(cls.standard_product)

    @classmethod
    def _create_cart(cls, product, ticket=None, payment_term=None):
        """Create a cart holding a single line, an event line when given a ticket."""
        values = {
            'partner_id': cls.public_partner.id,
            'website_id': cls.website.id,
            'access_token': str(uuid.uuid4()),
            'order_line': [Command.create({
                'product_id': product.id,
                'event_id': ticket.event_id.id if ticket else False,
                'event_ticket_id': ticket.id if ticket else False,
                'price_unit': 100.0,
            })],
        }
        if payment_term:
            values['payment_term_id'] = payment_term.id
        return cls.env['sale.order'].create(values)

    def _pay(self, order, **kwargs):
        """Run the shop payment route on an order, as the frontend does."""
        route_kwargs = {
            'provider_id': self.provider.id,
            'payment_method_id': self.payment_method_id,
            'token_id': False,
            'amount': order.amount_total,
            'flow': 'redirect',
            'tokenization_requested': False,
            'landing_route': '/shop/payment/confirm',
        }
        route_kwargs.update(kwargs)

        with MockRequest(self.env, website=self.website, sale_order_id=order.id):
            return PaymentPortal().shop_payment_transaction(
                order.id,
                order.access_token,
                **route_kwargs,
            )

    def test_event_order_pays_the_due_amount_of_its_term(self):
        """The transaction holds what the term asks for now, not the order total."""
        self._pay(self.event_cart)

        transaction = self.event_cart.transaction_ids

        self.assertEqual(len(transaction), 1)
        self.assertEqual(transaction.amount, 20.0)

    def test_event_order_ignores_the_amount_of_the_browser(self):
        """A manipulated amount is replaced by the amount due on the server."""
        self._pay(self.event_cart, amount=100.0)

        self.assertEqual(self.event_cart.transaction_ids.amount, 20.0)

    def test_event_order_without_a_due_amount_is_refused(self):
        """An event order whose first installment is paid has nothing left to pay."""
        self.event_cart.action_confirm()
        self._create_done_transaction(self.event_cart, 20.0)

        self.assertEqual(self.event_cart.amount_paid, 20.0)

        with self.assertRaises(ValidationError) as catcher:
            self._pay(self.event_cart)

        self.assertIn("no payment currently due", str(catcher.exception))
        self.assertFalse(self.event_cart.transaction_ids.filtered(
            lambda transaction: transaction.state == 'draft',
        ))

    def test_standard_order_pays_its_total(self):
        """An order without event lines pays its total, as before."""
        self._pay(self.standard_cart)

        self.assertEqual(self.standard_cart.transaction_ids.amount, 100.0)

    def test_standard_order_rejects_an_amount_that_is_not_its_total(self):
        """The check on the amount of the browser stays in place for them."""
        with self.assertRaises(ValidationError) as catcher:
            self._pay(self.standard_cart, amount=50.0)

        self.assertIn("cart has been updated", str(catcher.exception))
        self.assertFalse(self.standard_cart.transaction_ids)

    def test_standard_order_rejects_a_second_payment(self):
        """An order that is paid is refused, as before."""
        self.standard_cart.action_confirm()
        self._create_done_transaction(self.standard_cart, 100.0)

        with self.assertRaises(UserError) as catcher:
            self._pay(self.standard_cart)

        self.assertIn("already been paid", str(catcher.exception))

    def test_portal_order_pays_the_due_amount_of_its_term(self):
        """The My Account route shares the override, it also pays what is due."""
        self.event_cart.action_confirm()
        controller = self._get_payment_controller(
            '/my/orders/<int:order_id>/transaction',
        )

        with MockRequest(self.env, website=self.website, sale_order_id=self.event_cart.id):
            controller.portal_order_transaction(
                self.event_cart.id,
                self.event_cart.access_token,
                provider_id=self.provider.id,
                payment_method_id=self.payment_method_id,
                token_id=False,
                amount=80.0,
                flow='redirect',
                tokenization_requested=False,
                landing_route='/my',
            )

        transaction = self.event_cart.transaction_ids.filtered(
            lambda tx: tx.state == 'draft',
        )

        self.assertEqual(len(transaction), 1)
        self.assertEqual(transaction.amount, 20.0)

    def test_payment_values_of_a_confirmed_event_order(self):
        """The portal form is filled with the amount the term asks for now.

        The order pays 20 of its 100, which the core would read as a down
        payment. The override says it is not one, it is an installment of the
        term, so the form asks for the due share and not for the total.
        """
        self.event_cart.action_confirm()

        with MockRequest(self.env, website=self.website):
            values = CustomerPortal()._get_payment_values(
                self.event_cart.sudo(),
                website_id=self.website.id,
                is_down_payment=True,
            )

        self.assertEqual(values['payment_amount'], 20.0)
        self.assertEqual(values['amount'], 20.0)

    def test_payment_values_of_a_draft_event_order(self):
        """A quotation asks for the share of its term that is due as well."""
        with MockRequest(self.env, website=self.website):
            values = CustomerPortal()._get_payment_values(
                self.event_cart.sudo(),
                website_id=self.website.id,
                is_down_payment=True,
            )

        self.assertEqual(values['payment_amount'], 20.0)
        self.assertEqual(values['amount'], 20.0)

    def test_payment_values_of_a_standard_order_are_untouched(self):
        """An order without event lines keeps the amounts the core computed."""
        with MockRequest(self.env, website=self.website):
            values = CustomerPortal()._get_payment_values(
                self.standard_cart.sudo(),
                website_id=self.website.id,
                is_down_payment=False,
            )

        self.assertEqual(values['payment_amount'], None)
        self.assertEqual(values['amount'], self.standard_cart.amount_total)

    def test_cancelled_event_order_is_refused(self):
        """A cancelled order is not paid for, standard or not."""
        self.event_cart.action_confirm()
        self.event_cart.action_cancel()

        with self.assertRaises(ValidationError) as catcher:
            self._pay(self.event_cart)

        self.assertIn("cancelled", str(catcher.exception))

    def test_wrong_access_token_is_refused(self):
        """An access error becomes a readable message, the core raises the same."""
        with MockRequest(self.env, website=self.website, sale_order_id=self.event_cart.id):
            with patch.object(
                PaymentPortal,
                '_document_check_access',
                side_effect=AccessError("no"),
            ):
                with self.assertRaises(ValidationError) as catcher:
                    PaymentPortal().shop_payment_transaction(
                        self.event_cart.id,
                        'not-the-access-token',
                        provider_id=self.provider.id,
                        payment_method_id=self.payment_method_id,
                        token_id=False,
                        amount=20.0,
                        flow='redirect',
                        tokenization_requested=False,
                        landing_route='/shop/payment/confirm',
                    )

        self.assertIn("access token is invalid", str(catcher.exception))

    def test_a_missing_order_is_not_swallowed(self):
        """A missing order raises the core error, it is re-raised on purpose."""
        with MockRequest(self.env, website=self.website, sale_order_id=self.event_cart.id):
            with patch.object(
                PaymentPortal,
                '_document_check_access',
                side_effect=MissingError("gone"),
            ):
                with self.assertRaises(MissingError):
                    PaymentPortal().shop_payment_transaction(
                        self.event_cart.id,
                        self.event_cart.access_token,
                        provider_id=self.provider.id,
                        payment_method_id=self.payment_method_id,
                        token_id=False,
                        amount=20.0,
                        flow='redirect',
                        tokenization_requested=False,
                        landing_route='/shop/payment/confirm',
                    )

    def test_validation_does_not_pay_and_does_not_refuse(self):
        """A validation only checks the payment method, it charges nothing.

        A confirmed event order whose first installment is paid has nothing due,
        which refuses a payment. Token validation has to keep working on it.
        """
        self.event_cart.action_confirm()
        self._create_done_transaction(self.event_cart, 20.0)

        with MockRequest(self.env, website=self.website, sale_order_id=self.event_cart.id):
            PaymentPortal()._create_transaction(
                self.provider.id,
                self.payment_method_id,
                False,
                self.event_cart.amount_total,
                self.event_cart.currency_id.id,
                self.event_cart.partner_id.id,
                'redirect',
                False,
                '/shop/payment/confirm',
                is_validation=True,
                sale_order_id=self.event_cart.id,
            )

        self.assertEqual(len(self.event_cart.transaction_ids), 1)
        self.assertEqual(self.event_cart.amount_paid, 20.0)

    @classmethod
    def _get_payment_controller(cls, route):
        """Return the controller the server binds a payment route to.

        The server rebuilds one controller per hierarchy, so a route of `sale`
        can be served by a class of another addon. Only the bound controller
        tells which overrides apply to it.
        """
        installed = cls.env['ir.module.module'].search(
            [('state', '=', 'installed')],
        ).mapped('name')
        modules = sorted(set(installed) | set(odoo.tools.config['server_wide_modules']))
        for url, endpoint in cls.env['ir.http']._generate_routing_rules(
            modules,
            cls.env['ir.http']._get_converters(),
        ):
            if url == route:
                return endpoint.func.__self__

        raise AssertionError(f"no controller is bound to {route}")

    def _create_done_transaction(self, order, amount):
        return self.env['payment.transaction'].sudo().create({
            'provider_id': self.provider.id,
            'payment_method_id': self.payment_method_id,
            'partner_id': order.partner_id.id,
            'amount': amount,
            'currency_id': order.currency_id.id,
            'reference': 'TEST-PAID',
            'state': 'done',
            'sale_order_ids': [Command.set(order.ids)],
        })
