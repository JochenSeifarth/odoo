from odoo import api, models


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.depends(
        "invoice_payment_term_id",
        "invoice_date",
        "currency_id",
        "amount_total_in_currency_signed",
        "invoice_date_due",
        "invoice_line_ids.sale_line_ids.order_id",
        "invoice_line_ids.sale_line_ids.order_id.order_line.event_id.date_begin",
        "invoice_line_ids.sale_line_ids.order_id.order_line.event_slot_id.start_datetime",
    )
    def _compute_needed_terms(self):
        for move in self:
            start_date = move._get_rya_event_start_date()
            if start_date:
                move = move.with_context(rya_event_date=start_date)
            super(AccountMove, move)._compute_needed_terms()

    def _get_rya_event_start_date(self):
        """Return the start date of the events this invoice covers.

        The date comes from the sale orders of the invoice, see
        `sale.order._get_rya_event_start_and_term`, and an invoice may cover
        orders of several events, in which case the earliest start dates the
        payment terms. Returns False for an invoice without an event order.
        """
        self.ensure_one()

        starts = (
            order._get_rya_event_start_and_term()
            for order in self.invoice_line_ids.mapped("sale_line_ids.order_id")
        )

        return min(
            (
                start_date
                for start_date, _payment_term in starts
                if start_date
            ),
            default=False,
        )
