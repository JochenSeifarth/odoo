from odoo import api, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.depends("company_id", "order_line.event_id")
    def _compute_prepayment_percent(self):
        super()._compute_prepayment_percent()

        for order in self:
            if order.order_line.filtered("event_id"):
                order.prepayment_percent = 0.20

    def _has_prepayment(self):
        self.ensure_one()
        return 0.0 < self.prepayment_percent < 1.0

    def _has_event_ticket_lines(self):
        """
        Return True if this order contains event ticket products.
        """

        self.ensure_one()

        products = self.order_line.filtered(
            lambda l: l.product_id,
        ).mapped("product_id")

        if not products:
            return False

        return bool(
            self.env["event.event.ticket"].search_count(
                [
                    ("product_id", "in", products.ids),
                ],
                limit=1,
            ),
        )

    @api.depends(
        "partner_id",
        "partner_shipping_id",
        "company_id",
    )
    def _compute_fiscal_position_id(self):
        """
        Let Odoo determine the fiscal position normally.

        Exception:
        Event tickets are taxed where the event takes place,
        therefore automatic fiscal positions based on the
        customer's country must not be applied.
        """

        super()._compute_fiscal_position_id()

        for order in self:
            if order._has_event_ticket_lines():
                order.fiscal_position_id = False
