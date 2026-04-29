from __future__ import annotations

import math

from odoo import api, fields, models
from ..services.o2_router_service import O2RouterService


class EventEvent(models.Model):
    _inherit = "event.event"

    event_leg_ids: fields.One2many = fields.One2many(
        "event.leg",
        "event_id",
        string="Legs",
    )

    total_distance_nm = fields.Float(
        compute="_compute_total_distance_nm",
        store=True,
        string="Total Distance [nm]",
        digits=(16, 0),
    )

    def get_route(self):
        self.ensure_one()

        legs = self.event_leg_ids.sorted("sequence")

        return {
            "event_id": self.id,
            "legs": [
                {
                    "sequence": leg.sequence,
                    "name": leg.address_id.name,
                    "lat": leg.partner_latitude,
                    "lng": leg.partner_longitude,
                    "distance": leg.distance_from_prev_nm,
                    "hops": [
                        {"lat": hop[1], "lng": hop[0]}
                        for hop in (leg.asw_json or {})
                        .get("geometry", {})
                        .get("coordinates", [])
                    ],
                }
                for leg in legs
            ],
            "route": [
                {
                    "lat": hop[1],
                    "lng": hop[0],
                }
                for leg in legs
                for hop in (leg.asw_json or {})
                .get("geometry", {})
                .get("coordinates", [])
            ],
        }

    def _recompute_legs(self) -> None:
        o2_router = O2RouterService()
        for event in self:
            previous_leg = None
            ordered_legs = event.event_leg_ids.sorted(key=lambda leg: leg.sequence or 0)
            for leg in ordered_legs:
                if previous_leg is None:
                    leg.distance_from_prev_nm = 0.0
                    leg.asw_json = None
                else:
                    leg.asw_json = o2_router.route(
                        (previous_leg.partner_latitude, previous_leg.partner_longitude),
                        (leg.partner_latitude, leg.partner_longitude),
                    )
                    leg.distance_from_prev_nm = round(
                        ((leg.asw_json or {}).get("distance_nm") or 0.0) * 1.1, 2
                    )
                previous_leg = leg

    @api.depends(
        "event_leg_ids.distance_from_prev_nm",
    )
    def _compute_total_distance_nm(self):
        for event in self:
            event.total_distance_nm = sum(
                leg.distance_from_prev_nm or 0.0 for leg in event.event_leg_ids  # type: ignore
            )

    @api.onchange("event_leg_ids")
    def _onchange_event_leg_ids(self):
        self._recompute_legs()

    def write(self, vals):
        res = super().write(vals)

        if "event_leg_ids" in vals:
            # recompute right before saving event
            self._recompute_legs()

        return res
