from __future__ import annotations

import math
from collections.abc import Collection

from odoo import api, fields, models


class EventLeg(models.Model):
    _name = "event.leg"
    _description = "Event Leg"
    _order = "sequence, id"

    sequence = fields.Integer("Sequence")
    address_id = fields.Many2one("res.partner", "Leg", required=True)
    event_id = fields.Many2one(
        "event.event",
        string="Event",
        ondelete="cascade",
        required=True,
    )

    partner_latitude = fields.Float(
        string="Latitude",
        related="address_id.partner_latitude",
        readonly=True,
        store=True,
    )
    partner_longitude = fields.Float(
        string="Longitude",
        related="address_id.partner_longitude",
        readonly=True,
        store=True,
    )

    distance_from_prev_nm = fields.Float(
        string="Distance [nm]",
        compute="_compute_distance_from_previous",
        store=True,
        digits=(16, 0),
    )

    def _compute_distance_from_previous(self) -> None:
        self.mapped("event_id")._recompute_leg_distances()  # type: ignore
