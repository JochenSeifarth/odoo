from odoo import fields, models
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _get_rya_event(self):
        """Return the single event for this event order."""
        self.ensure_one()

        if not self._has_event_ticket_lines():
            return self.env["event.event"]

        events = self.order_line.mapped("event_id")
        if len(events) > 1:
            raise ValidationError(
                "An event order can contain only one event.",
            )

        return events

    def _has_event_ticket_lines(self):
        """Return True if this order contains event ticket lines."""
        self.ensure_one()
        return bool(self.order_line.filtered("event_id"))

    def _get_rya_payment_schedule(self):
        """Return the payment-term schedule for an event order."""
        self.ensure_one()

        if not self._has_event_ticket_lines():
            return []

        event = self._get_rya_event()
        payment_term = self.payment_term_id

        if not event or not event.date_begin or not payment_term:
            return []

        date_ref = fields.Date.context_today(self)

        terms = payment_term.with_context(
            rya_event_date=event.date_begin.date(),
        )._compute_terms(
            date_ref,
            self.currency_id,
            self.company_id,
            self.currency_id._convert(
                self.amount_tax,
                self.company_id.currency_id,
                self.company_id,
                date_ref,
            ),
            self.amount_tax,
            1,
            self.currency_id._convert(
                self.amount_untaxed,
                self.company_id.currency_id,
                self.company_id,
                date_ref,
            ),
            self.amount_untaxed,
        )

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

    def _get_rya_payment_amount(self):
        """amount actually due according to payment terms considering amount_paid"""
        self.ensure_one()

        return self.currency_id.round(
            max(self._get_rya_due_payment_amount() - self.amount_paid, 0),
        )

    def _get_rya_due_payment_amount(self):
        """amount currently due according to payment terms"""
        self.ensure_one()

        if not self._has_event_ticket_lines():
            return self.amount_total

        event = self._get_rya_event()
        payment_term = self.payment_term_id

        if not event or not event.date_begin or not payment_term:
            return self.amount_total

        date_ref = fields.Date.context_today(self)

        terms = payment_term.with_context(
            rya_event_date=event.date_begin.date(),
        )._compute_terms(
            date_ref,
            self.currency_id,
            self.company_id,
            self.currency_id._convert(
                self.amount_tax,
                self.company_id.currency_id,
                self.company_id,
                date_ref,
            ),
            self.amount_tax,
            1,
            self.currency_id._convert(
                self.amount_untaxed,
                self.company_id.currency_id,
                self.company_id,
                date_ref,
            ),
            self.amount_untaxed,
        )

        return sum(
            line["foreign_amount"]
            for line in terms["line_ids"]
            if line["date"] <= date_ref
        )

    def _get_prepayment_required_amount(self):
        if self._has_event_ticket_lines():
            return self._get_rya_due_payment_amount()

        return super()._get_prepayment_required_amount()

    def _rya_transaction_matches_due_amount(self, transaction):
        """Return True if an event payment matches the amount due before it."""
        self.ensure_one()

        if not self._has_event_ticket_lines():
            return False

        due_amount = self._get_rya_due_payment_amount()
        paid_before_transaction = self.amount_paid - transaction.amount
        expected_amount = due_amount - paid_before_transaction

        return (
            self.currency_id.compare_amounts(
                transaction.amount,
                expected_amount,
            )
            == 0
        )

    def _has_to_be_paid(self):
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
