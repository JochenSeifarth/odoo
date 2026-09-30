from odoo import api, fields, models
from odoo.tools import float_is_zero


class EventRegistration(models.Model):
    _inherit = 'event.registration'

# we badly need this to be a stored field so that it can be properly sorted by on kanban and list views etc,
# properties should be merged by Odoo - so we do not lose any of the compute logic
    event_begin_date = fields.Datetime(store=True, index=True)

    sale_status = fields.Selection(
        selection_add=[
            ("partial", "Deposit paid"),
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
        """Show what is paid for a registration of an event order.

        The standard implementation marks a registration of a confirmed order as
        sold, whatever has been paid for that order. An event order is invoiced
        for its whole total while it is paid in the installments of its payment
        term, so a registration only counts as sold once its invoices are paid
        for. Until then it shows what is missing, a deposit paid as partial.
        """
        super()._compute_registration_status()

        for order, registrations in (
            self.filtered("sale_order_id").grouped("sale_order_id").items()
        ):
            if order.state != "sale":
                continue

            invoices = order.invoice_ids.filtered(
                lambda invoice:
                    invoice.state == "posted"
                    and invoice.move_type == "out_invoice",
            )

            if not invoices:
                sale_status = "to_pay"
            else:
                total = sum(invoices.mapped("amount_total"))
                residual = sum(invoices.mapped("amount_residual"))
                rounding = order.currency_id.rounding

                if float_is_zero(total, precision_rounding=rounding):
                    sale_status = "free"
                elif float_is_zero(residual, precision_rounding=rounding):
                    sale_status = "sold"
                elif residual < total:
                    sale_status = "partial"
                else:
                    sale_status = "to_pay"

            for registration in registrations:
                if (
                    registration.event_ticket_id
                    and registration.sale_status != "free"
                    and registration.state != "cancel"
                ):
                    registration.sale_status = sale_status
