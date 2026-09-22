from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    event_participant_names = fields.Char(
        string="Attendees",
        compute="_compute_event_participant_names",
        store=True,
    )

    @api.depends("sale_line_ids", "sale_line_ids.order_id")
    def _compute_event_participant_names(self):
        registrations = self.env["event.registration"].search([
            ("sale_order_id", "in", self.sale_line_ids.order_id.ids),
            ("state", "!=", "cancel"),
        ], order="id")

        registrations_by_order = {}
        for registration in registrations:
            registrations_by_order.setdefault(
                registration.sale_order_id.id, [],
            ).append(registration.name)

        for line in self:
            names = []
            for order in line.sale_line_ids.order_id:
                names.extend(registrations_by_order.get(order.id, []))
            line.event_participant_names = ", ".join(names)


class EventRegistration(models.Model):
    _inherit = "event.registration"

    def write(self, vals):
        result = super().write(vals)

        if "name" in vals or "state" in vals:
            self.env["account.move.line"].search([
                ("sale_line_ids.order_id", "in", self.mapped("sale_order_id").ids),
            ])._compute_event_participant_names()

        return result
