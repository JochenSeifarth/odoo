from __future__ import annotations

import math

from odoo import api, fields, models


class EventEvent(models.Model):
    _inherit = ["event.event"]

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

    def _recompute_leg_distances(self) -> None:
        for event in self:
            prev_lat = prev_lon = None
            ordered_legs = event.event_leg_ids.sorted(key=lambda leg: leg.sequence or 0)
            for leg in ordered_legs:
                if prev_lat is None or prev_lon is None:
                    leg.distance_from_prev_nm = 0.0
                else:
                    leg.distance_from_prev_nm = self.env[
                        "event.event"
                    ]._haversine_distance_nm(
                        prev_lat,
                        prev_lon,
                        leg.partner_latitude,
                        leg.partner_longitude,
                    )
                prev_lat, prev_lon = leg.partner_latitude, leg.partner_longitude

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
        self._recompute_leg_distances()

    def write(self, vals):
        res = super().write(vals)

        if "event_leg_ids" in vals:
            # recompute right before saving event
            self._recompute_leg_distances()

        return res

    @staticmethod
    def _haversine_distance_nm(lat1, lon1, lat2, lon2) -> float:
        """Returns distance in nautical miles between two points"""
        R_km = 6371  # Earth radius in km
        if None in [lat1, lon1, lat2, lon2]:
            return 0.0
        phi1: float = math.radians(lat1)
        phi2: float = math.radians(lat2)
        d_phi: float = math.radians(lat2 - lat1)
        d_lambda: float = math.radians(lon2 - lon1)

        a: float = (
            math.sin(d_phi / 2) ** 2
            + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
        )
        c: float = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance_km: float = R_km * c
        distance_nm: float = distance_km * 0.539957  # Convert km to nautical miles
        return round(distance_nm * 1.19, 0)
