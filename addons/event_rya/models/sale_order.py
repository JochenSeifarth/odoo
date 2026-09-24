from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _has_event_ticket_lines(self):
        """Return True if this order contains event ticket products."""
        self.ensure_one()

        products = self.order_line.filtered(
            lambda line: line.product_id,
        ).mapped("product_id")

        if not products:
            return False

        return bool(
            self.env["event.event.ticket"].search_count(
                [
                    ("product_id", "in", products.ids),
                ],
                limit=1,
            ),
        )

    def _get_rya_payment_schedule(self):
        """Return the payment-term schedule for an event order."""
        self.ensure_one()

        if not self._has_event_ticket_lines():
            return []

        event = self.order_line.mapped("event_id")[:1]
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
            self.amount_tax,
            self.amount_tax,
            1,
            self.amount_untaxed,
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

    def _get_rya_due_payment_amount(self):
        """Return the payment-term amount currently due for an event order."""
        self.ensure_one()

        if not self._has_event_ticket_lines():
            return self.amount_total

        event = self.order_line.mapped("event_id")[:1]
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
            self.amount_tax,
            self.amount_tax,
            1,
            self.amount_untaxed,
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
