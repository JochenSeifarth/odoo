from datetime import timedelta

from odoo import fields, models


class AccountPaymentTermLine(models.Model):
    _inherit = "account.payment.term.line"

    delay_type = fields.Selection(
        selection_add=[
            ("rya_days_after_event", "Days after Event"),
        ],
        ondelete={
            "rya_days_after_event": "set default",
        },
    )

    def _get_due_date(self, date_ref):
        self.ensure_one()

        if self.delay_type == "rya_days_after_event":
            event_date = self.env.context.get("rya_event_date")
            if event_date:
                due_date = event_date + timedelta(days=self.nb_days)
                # Never make an invoice due before its invoice date.
                return max(due_date, date_ref)

        return super()._get_due_date(date_ref)
