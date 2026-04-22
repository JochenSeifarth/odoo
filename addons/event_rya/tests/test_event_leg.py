from __future__ import annotations

from datetime import datetime, timedelta

from odoo import Command, fields
from odoo.tests import common, tagged


@tagged("event_rya", "at_install", "post_install")
class TestEventLegFields(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.event_leg_model = cls.env["event.leg"]
        cls.partner_a = cls.env["res.partner"].create(
            {
                "name": "Leg A",
                "partner_latitude": 50.0,
                "partner_longitude": 1.0,
            }
        )
        cls.partner_b = cls.env["res.partner"].create(
            {
                "name": "Leg B",
                "partner_latitude": 50.5,
                "partner_longitude": 1.0,
            }
        )
        cls.partner_c = cls.env["res.partner"].create(
            {
                "name": "Leg C",
                "partner_latitude": 51.0,
                "partner_longitude": 1.0,
            }
        )

    def _create_event_with_legs(self, leg_specs):
        start = datetime(2026, 1, 1, 10, 0, 0)
        end = start + timedelta(hours=8)
        return self.env["event.event"].create(
            {
                "name": "Leg Distance Test Event",
                "date_begin": fields.Datetime.to_string(start),
                "date_end": fields.Datetime.to_string(end),
                "event_leg_ids": [
                    Command.create({"sequence": sequence, "address_id": partner.id})
                    for sequence, partner in leg_specs
                ],
            }
        )

    def test_leg_columns_can_be_marked_non_sortable(self):
        field_descriptions = self.event_leg_model.fields_get(
            [
                "event_id",
                "address_id",
                "partner_latitude",
                "partner_longitude",
                "distance_from_prev_nm",
            ],
            attributes=["sortable"],
        )

        self.assertTrue(field_descriptions["event_id"]["sortable"])
        self.assertFalse(field_descriptions["address_id"]["sortable"])
        self.assertFalse(field_descriptions["partner_latitude"]["sortable"])
        self.assertFalse(field_descriptions["partner_longitude"]["sortable"])
        self.assertFalse(field_descriptions["distance_from_prev_nm"]["sortable"])

    def test_distance_from_previous_uses_sequence_order(self):
        event = self._create_event_with_legs(
            [
                (20, self.partner_b),
                (10, self.partner_a),
                (30, self.partner_c),
            ]
        )

        legs_by_partner = {
            leg.address_id.id: leg for leg in event.event_leg_ids
        }
        expected_ab = self.event_leg_model._haversine_distance_nm(
            self.partner_a.partner_latitude,
            self.partner_a.partner_longitude,
            self.partner_b.partner_latitude,
            self.partner_b.partner_longitude,
        )
        expected_bc = self.event_leg_model._haversine_distance_nm(
            self.partner_b.partner_latitude,
            self.partner_b.partner_longitude,
            self.partner_c.partner_latitude,
            self.partner_c.partner_longitude,
        )

        self.assertEqual(legs_by_partner[self.partner_a.id].distance_from_prev_nm, 0.0)
        self.assertEqual(legs_by_partner[self.partner_b.id].distance_from_prev_nm, expected_ab)
        self.assertEqual(legs_by_partner[self.partner_c.id].distance_from_prev_nm, expected_bc)

    def test_event_leg_onchange_recomputes_resequenced_distances(self):
        event = self.env["event.event"].new(
            {
                "name": "Leg Distance Onchange Test Event",
                "date_begin": fields.Datetime.to_string(datetime(2026, 1, 2, 10, 0, 0)),
                "date_end": fields.Datetime.to_string(datetime(2026, 1, 2, 18, 0, 0)),
                "event_leg_ids": [
                    Command.create({"sequence": 10, "address_id": self.partner_a.id}),
                    Command.create({"sequence": 20, "address_id": self.partner_b.id}),
                    Command.create({"sequence": 5, "address_id": self.partner_c.id}),
                ],
            }
        )
        event._onchange_event_leg_ids()

        legs_by_partner = {
            leg.address_id.id: leg for leg in event.event_leg_ids
        }
        expected_ca = self.event_leg_model._haversine_distance_nm(
            self.partner_c.partner_latitude,
            self.partner_c.partner_longitude,
            self.partner_a.partner_latitude,
            self.partner_a.partner_longitude,
        )
        expected_ab = self.event_leg_model._haversine_distance_nm(
            self.partner_a.partner_latitude,
            self.partner_a.partner_longitude,
            self.partner_b.partner_latitude,
            self.partner_b.partner_longitude,
        )

        self.assertEqual(legs_by_partner[self.partner_c.id].distance_from_prev_nm, 0.0)
        self.assertEqual(legs_by_partner[self.partner_a.id].distance_from_prev_nm, expected_ca)
        self.assertEqual(legs_by_partner[self.partner_b.id].distance_from_prev_nm, expected_ab)
        self.assertEqual(event.total_distance_nm, expected_ca + expected_ab)
