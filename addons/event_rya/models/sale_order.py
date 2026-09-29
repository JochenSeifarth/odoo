import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _get_rya_event_start_and_term(self):
        """Return what dates and what terms the payment of this order follows.

        An event line starts at the slot it books, at its event otherwise. The
        line that starts first dates the payment terms of the order, and the
        event of that same line holds the payment term they are computed with.

        :return: The start date, False without an event line, and the payment
            term of that event, empty when the order has no event line or when
            the event proposes a payment term of another company, so that the
            default of the customer applies. A payment term without a company is
            used by every company, as it is on a sales order.
        :rtype: tuple[datetime | bool, account.payment.term]
        """
        self.ensure_one()

        start_date = False
        event = self.env["event.event"]

        for line in self.order_line.filtered("event_id"):
            line_start = line.event_slot_id.start_datetime or line.event_id.date_begin
            if line_start and (not start_date or line_start < start_date):
                start_date = line_start
                event = line.event_id

        if len(self.order_line.event_id) > 1:
            _logger.warning(
                "Sale order %s: an event order should contain only one event. "
                "Using the earliest starting event at %s",
                self.name,
                start_date,
            )

        payment_term = event.payment_term_id
        if payment_term.company_id and payment_term.company_id != self.company_id:
            payment_term = self.env["account.payment.term"]

        return start_date, payment_term

    @api.depends("order_line.event_id.payment_term_id")
    def _compute_payment_term_id(self):
        """Propose the payment term of the event, the default of the customer comes second."""
        super()._compute_payment_term_id()

        for order in self:
            _, payment_term = order._get_rya_event_start_and_term()
            if payment_term:
                order.payment_term_id = payment_term

    def _get_prepayment_required_amount(self):
        """Return the amount that has to be paid to confirm the order.

        A company that asks for no online payment confirms its quotations
        without one, that holds for event orders as well. An event order is
        otherwise confirmed by paying what its payment term asks for now, the
        rest of the term is paid later on. Every other order keeps the standard
        amount, a share of the total given by the company.
        """
        self.ensure_one()

        if not self.require_payment:
            return 0.0

        if self._has_event_ticket_lines():
            return self._get_rya_due_payment_amount()

        return super()._get_prepayment_required_amount()

    def _has_event_ticket_lines(self):
        """Return True if this order contains event ticket lines."""
        self.ensure_one()
        return bool(self.order_line.event_id)

    def _get_rya_payment_schedule(self):
        """Return the payment term schedule of an event order.

        Each entry is a dict with the installment ``date``, its ``amount`` and
        whether it is ``due`` already. Orders without event lines, without an
        event date or without a payment term have no schedule.
        """
        self.ensure_one()

        if not self._has_event_ticket_lines():
            return []

        start_date, _payment_term = self._get_rya_event_start_and_term()
        payment_term = self.payment_term_id

        if not start_date or not payment_term:
            return []

        date_ref = fields.Date.context_today(self)
        terms = self._get_rya_payment_terms(payment_term, start_date, date_ref)

        return [
            {
                "date": line["date"],
                "amount": line["foreign_amount"],
                "due": line["date"] <= date_ref,
            }
            for line in sorted(
                terms["line_ids"],
                key=lambda line: line["date"],
            )
        ]

    def _get_rya_payment_terms(self, payment_term, start_date, date_ref):
        """Return the computed terms of `payment_term` for this order.

        The start date of the event, which is the start of the booked slot when
        a line books one, is handed to the payment term lines through the
        ``rya_event_date`` context key, see
        `account.payment.term.line._get_due_date`.
        """
        self.ensure_one()
        return payment_term.with_context(
            rya_event_date=start_date,
        )._compute_terms(
            date_ref=date_ref,
            currency=self.currency_id,
            company=self.company_id,
            tax_amount=self.currency_id._convert(
                self.amount_tax,
                self.company_id.currency_id,
                self.company_id,
                date_ref,
            ),
            tax_amount_currency=self.amount_tax,
            sign=1,
            untaxed_amount=self.currency_id._convert(
                self.amount_untaxed,
                self.company_id.currency_id,
                self.company_id,
                date_ref,
            ),
            untaxed_amount_currency=self.amount_untaxed,
        )

    def _get_rya_due_payment_amount(self):
        """Return the amount of an event order that is due according to its terms."""
        self.ensure_one()

        schedule = self._get_rya_payment_schedule()
        if not schedule:
            return self.amount_total

        return sum(
            line["amount"]
            for line in schedule
            if line["due"]
        )

    def _get_rya_payment_amount(self):
        """Return the amount of an event order that is due and not paid yet."""
        self.ensure_one()

        outstanding = self._get_rya_due_payment_amount() - self.amount_paid

        if self.currency_id.compare_amounts(outstanding, 0.0) <= 0:
            return 0.0

        return self.currency_id.round(outstanding)

    def _rya_transaction_matches_due_amount(self, transaction):
        """Return True if an event payment matches the amount due before it.

        The amount paid up to and including the transaction has to be the amount
        that was due, which is what the order of the payments shows. Paying it
        is what the transaction matching the due amount means.
        """
        self.ensure_one()

        if not self._has_event_ticket_lines():
            return False

        return (
            self.currency_id.compare_amounts(
                self._get_rya_due_payment_amount(),
                self.amount_paid,
            )
            == 0
        )

    def _has_to_be_paid(self):
        """Return True if the order still expects a payment.

        Contrary to the standard implementation, which asks whether a quotation
        has to be paid to be confirmed, an event order asks whether an amount of
        its payment term is due already.
        """
        if (
            self._has_event_ticket_lines()
            and self.state == "sale"
            and not self.is_expired
            and self.require_payment
            and self.amount_total > 0
        ):
            return self._get_rya_payment_amount() > 0

        return super()._has_to_be_paid()

    def _compute_fiscal_position_id(self):
        """
        Let Odoo determine the fiscal position normally.

        Exception:
        Event tickets are taxed where the event takes place,
        therefore automatic fiscal positions based on the
        customer's country must not be applied.
        """

        super()._compute_fiscal_position_id()

        for order in self:
            if order._has_event_ticket_lines():
                order.fiscal_position_id = False
