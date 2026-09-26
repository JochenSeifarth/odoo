from odoo import api, fields, models
from odoo.tools import float_is_zero


class EventRegistration(models.Model):
    _inherit = 'event.registration'

# we badly need this to be a stored field so that it can be properly sorted by on kanban and list views etc,
# properties should be merged by Odoo - so we do not lose any of the compute logic
    event_begin_date = fields.Datetime(store=True, index=True)

    sale_status = fields.Selection(
        selection_add=[
            ("partial", "Angezahlt"),
        ],
        ondelete={"partial": "set null"},
    )

    @api.depends(
        "sale_order_id.state",
        "sale_order_id.currency_id",
        "sale_order_id.amount_total",
        "sale_order_id.invoice_ids.state",
        "sale_order_id.invoice_ids.move_type",
        "sale_order_id.invoice_ids.amount_total",
        "sale_order_id.invoice_ids.amount_residual",
    )
    def _compute_registration_status(self):
        super()._compute_registration_status()

        for registration in self:
            order = registration.sale_order_id

            if (
                not order
                or not registration.event_ticket_id
                or registration.sale_status == "free"
                or registration.state == "cancel"
                or order.state != "sale"
            ):
                continue

            invoices = order.invoice_ids.filtered(
                lambda invoice:
                    invoice.state == "posted"
                    and invoice.move_type == "out_invoice",
            )

            if not invoices:
                registration.sale_status = "to_pay"
                continue

            total = sum(invoices.mapped("amount_total"))
            residual = sum(invoices.mapped("amount_residual"))
            paid = total - residual

            if float_is_zero(
                total,
                precision_rounding=order.currency_id.rounding,
            ):
                registration.sale_status = "free"
            elif float_is_zero(
                residual,
                precision_rounding=order.currency_id.rounding,
            ):
                registration.sale_status = "sold"
            elif paid > 0:
                registration.sale_status = "partial"
            else:
                registration.sale_status = "to_pay"
