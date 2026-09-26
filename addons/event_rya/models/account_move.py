from odoo import api, models
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.depends(
        "invoice_payment_term_id",
        "invoice_date",
        "currency_id",
        "amount_total_in_currency_signed",
        "invoice_date_due",
        "invoice_line_ids.sale_line_ids.event_id.date_begin",
    )
    def _compute_needed_terms(self):
        for move in self:
            events = move.invoice_line_ids.mapped("sale_line_ids.event_id").filtered(
                lambda event: event.date_begin,
            )

            if len(events) > 1:
                raise ValidationError("An invoice cannot contain tickets for multiple events.")

            if events:
                move = move.with_context(
                    rya_event_date=events.date_begin.date(),
                )

            super(AccountMove, move)._compute_needed_terms()
