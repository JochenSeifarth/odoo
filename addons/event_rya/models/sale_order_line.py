
from odoo import models
from odoo.tools import format_datetime


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

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
            )
            end = format_datetime(
                self.env,
                self.event_id.date_end,
            )

            description += f"\n{start} – {end}"

        return description
