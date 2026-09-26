import logging
from datetime import timedelta

from odoo import fields, models

_logger = logging.getLogger(__name__)


class AccountPaymentTermLine(models.Model):
    _inherit = "account.payment.term.line"

    delay_type = fields.Selection(
        selection_add=[
            ("rya_days_after_event", "Days after event start"),
        ],
        ondelete={
            "rya_days_after_event": "set default",
        },
    )

    def _get_due_date(self, date_ref):
        """Return the due date of this line.

        A line of type ``rya_days_after_event`` is relative to the start of an
        event instead of the document date. The event date is passed in the
        ``rya_event_date`` context key by the callers that link a document to an
        event, see `sale.order._get_rya_payment_schedule` and
        `account.move._compute_needed_terms`.
        """
        self.ensure_one()
        date_ref = fields.Date.to_date(date_ref)

        if self.delay_type == "rya_days_after_event":
            event_date = fields.Date.to_date(self.env.context.get("rya_event_date"))
            if event_date:
                # A document is never due before its own date, e.g. when the
                # event is closer than the requested number of days.
                return max(event_date + timedelta(days=self.nb_days), date_ref)

            _logger.warning(
                "Payment term %s has a line relative to an event date, but no "
                "event date is known for this document: it is due immediately.",
                self.payment_id.display_name,
            )
            return date_ref

        return super()._get_due_date(date_ref)
