from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def action_post(self):
        result = super().action_post()

        for move in self:
            for invoice_line in move.invoice_line_ids:
                if not invoice_line.sale_line_ids.filtered("is_downpayment"):
                    continue

                event_lines = invoice_line.sale_line_ids.order_id.order_line.filtered(
                    lambda line: line.event_id and not line.is_downpayment,
                )

                if not event_lines:
                    continue

                event_description = "\n".join(
                    dict.fromkeys(
                        line._get_sale_order_line_multiline_description_sale()
                        for line in event_lines
                    ),
                )

                if event_description:
                    invoice_line.name = (
                        f"*** {invoice_line.name} ***\n{event_description}"
                    )

        return result
