
from odoo import models
from odoo.tools import format_datetime


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _get_rya_start_date(self):
        """Return the start date of this line, the slot it books or its event.

        A line booking a slot of a multi slot event starts at that slot, any
        other line starts at its event. Returns False without a start.
        """
        self.ensure_one()

        return self.event_slot_id.start_datetime or self.event_id.date_begin

    def _get_sale_order_line_multiline_description_sale(self):
        description = super()._get_sale_order_line_multiline_description_sale()

        # Odoo already adds the slot's display_name here, which contains
        # the slot's date/time. Do not add the event date/time as well.
        if self.event_slot_id:
            return description

        # For an event ticket without a slot, add the event's
        # start and end date/time.
        if self.event_id and self.event_id.date_begin and self.event_id.date_end:
            start = format_datetime(
                self.env,
                self.event_id.date_begin,
                dt_format="short",
            )
            end = format_datetime(
                self.env,
                self.event_id.date_end,
                dt_format="short",
            )

            description += f"\n{start} – {end}"

        return description
