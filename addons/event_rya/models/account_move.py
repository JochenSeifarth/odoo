from odoo import api, models


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
            event = move.invoice_line_ids.mapped(
                "sale_line_ids.event_id",
            )[:1]

            if event and event.date_begin:
                move = move.with_context(
                    rya_event_date=event.date_begin.date(),
                )

            super(AccountMove, move)._compute_needed_terms()
