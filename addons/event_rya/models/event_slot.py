import pytz
from datetime import datetime, timedelta

from odoo import models, fields, api
from odoo.tools.date_utils import float_to_time
from odoo.tools import (
    format_date,
    format_datetime,
    formatLang,
    format_time,
)


class EventSlot(models.Model):
    _inherit = "event.slot"

    # --------------------------------------------------
    # UI FIELDS (calendar / form)
    # --------------------------------------------------

    start_datetime = fields.Datetime(
        compute="_compute_datetimes",
        inverse="_inverse_datetimes",
        store=True,
    )

    end_datetime = fields.Datetime(
        compute="_compute_datetimes",
        inverse="_inverse_datetimes",
        store=True,
    )

    # --------------------------------------------------
    # TIMEZONE HELPERS
    # --------------------------------------------------

    def _get_tz(self):
        self.ensure_one()
        return pytz.timezone(self.date_tz or "UTC")

    def _to_utc(self, naive_dt, tz):
        return tz.localize(naive_dt).astimezone(pytz.UTC).replace(tzinfo=None)

    def _from_utc(self, dt, tz):
        return pytz.UTC.localize(dt).astimezone(tz)

    # --------------------------------------------------
    # COMPUTE: base fields → datetime
    # --------------------------------------------------

    @api.depends("date", "date_tz", "start_hour", "end_hour")
    def _compute_datetimes(self):
        for slot in self:
            if not slot.date:
                slot.start_datetime = False
                slot.end_datetime = False
                continue

            tz = slot._get_tz()

            start_dt = datetime.combine(
                slot.date,
                float_to_time(slot.start_hour or 0.0),
            )

            end_dt = datetime.combine(
                slot.date,
                float_to_time(slot.end_hour or 0.0),
            )

            # 🌙 OVERNIGHT SUPPORT
            if slot.end_hour < slot.start_hour:
                end_dt += timedelta(days=1)

            slot.start_datetime = slot._to_utc(start_dt, tz)
            slot.end_datetime = slot._to_utc(end_dt, tz)

    # --------------------------------------------------
    # INVERSE: datetime → base fields
    # --------------------------------------------------

    def _inverse_datetimes(self):
        for slot in self:
            if not slot.start_datetime or not slot.end_datetime:
                continue

            tz = slot._get_tz()

            start_local = slot._from_utc(slot.start_datetime, tz)
            end_local = slot._from_utc(slot.end_datetime, tz)

            # base date comes from start
            slot.date = start_local.date()

            slot.start_hour = (
                start_local.hour
                + start_local.minute / 60.0
                + start_local.second / 3600.0
            )

            same_day = start_local.date() == end_local.date()

            if same_day:
                slot.end_hour = (
                    end_local.hour
                    + end_local.minute / 60.0
                    + end_local.second / 3600.0
                )
            else:
                # 🌙 overnight encoding (> 24h)
                slot.end_hour = (
                    24.0
                    + end_local.hour
                    + end_local.minute / 60.0
                    + end_local.second / 3600.0
                )

    @api.constrains("start_hour", "end_hour")
    def _check_hours(self):
        for slot in self:
    
            # -----------------------------------
            # BASIC SANITY
            # -----------------------------------
            if slot.start_hour is None or slot.end_hour is None:
                raise ValidationError(_("Start and end hour must be set."))
    
            if slot.start_hour < 0 or slot.end_hour < 0:
                raise ValidationError(_("Slot hours cannot be negative."))
    
            # -----------------------------------
            # ORDER VALIDATION (MULTI-DAY SAFE)
            # -----------------------------------
            if slot.end_hour <= slot.start_hour:
                raise ValidationError(_(
                    "A slot end time must be after its start time.\n\n"
                    "Slot: %s",
                    slot.display_name
                ))
    
            # -----------------------------------
            # OPTIONAL SAFETY LIMIT (prevent insane values)
            # -----------------------------------
            max_span_days = 30  # adjust as needed
            max_allowed = max_span_days * 24.0
    
            duration = slot.end_hour - slot.start_hour
    
            if duration > max_allowed:
                raise ValidationError(_(
                    "Slot duration cannot exceed %s days.",
                    max_span_days
                ))

    @api.depends("seats_available", "date", "start_hour", "end_hour")
    @api.depends_context("name_with_seats_availability")
    def _compute_display_name(self):
        for slot in self:
    
            # --------------------------------------------------
            # BASE DATE
            # --------------------------------------------------
            base_dt = datetime.combine(slot.date, datetime.min.time()) if slot.date else datetime.now()
    
            # --------------------------------------------------
            # MULTI-DAY SAFE TIME COMPUTATION
            # --------------------------------------------------
            start_dt = base_dt + timedelta(hours=slot.start_hour or 0.0)
            end_dt = base_dt + timedelta(hours=slot.end_hour or 0.0)
    
            # If simple overnight (within same-day encoding)
            if slot.end_hour and slot.start_hour and slot.end_hour < slot.start_hour:
                end_dt += timedelta(days=1)
    
            # --------------------------------------------------
            # FORMATTING
            # --------------------------------------------------
            
            start_date_str = format_date(self.env, start_dt.date(), date_format="short")
            end_date_str = format_date(self.env, end_dt.date(), date_format="short")
            
            start_time_str = format_time(self.env, start_dt.time(), time_format="short")
            end_time_str = format_time(self.env, end_dt.time(), time_format="short")
            
            event_name = slot.event_id.name or ""
            
            # --------------------------------------------------
            # SAME DAY vs MULTI DAY
            # --------------------------------------------------
            
            if start_dt.date() == end_dt.date():
                # same-day format
                name = f"{event_name} {start_date_str}, {start_time_str} → {end_time_str}"
            else:
                # multi-day format
                name = f"{event_name} {start_date_str} {start_time_str} → {end_date_str} {end_time_str}"    
                
            # --------------------------------------------------
            # SEAT LOGIC (UNCHANGED BUT SAFE)
            # --------------------------------------------------
            if (
                self.env.context.get("name_with_seats_availability")
                and slot.event_id.seats_limited
                and not slot.event_id.is_multi_slots
            ):
                if not slot.seats_available:
                    name = _("%(slot_name)s (Sold out)", slot_name=name)
                else:
                    name = _(
                        "%(slot_name)s (%(count)s seats remaining)",
                        slot_name=name,
                        count=formatLang(self.env, slot.seats_available, digits=0),
                    )
    
            slot.display_name = name                