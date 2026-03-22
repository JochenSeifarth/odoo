from odoo import models, fields

class EventSlotCalendarEntry(models.Model):

    _name = "event.slot.calendar.entry"
    _description = "Kalendereinträge aus Events und Event Slots"
    _auto = False  # SQL-View
    _rec_name = "name"
    
    start = fields.Datetime(string='Start Date', readonly=True)
    stop = fields.Datetime(string='End Date', readonly=True)
    name = fields.Char(related="event_id.name", store=False, readonly=True)
    """
    name = fields.Char(readonly=True, compute="_compute_name")
    def _compute_name(self):
        for rec in self:
            rec.name = rec.event_id.name
            """
    
    event_id = fields.Many2one('event.event', string="Event", readonly=True)
    slot_id = fields.Many2one('event.slot', string="Slot", readonly=True)
    color = fields.Integer("Color", default=0)

    badge_image = fields.Binary(related="event_id.badge_image", readonly=True)    

    def init(self):
        self.env.cr.execute("""
            DROP VIEW IF EXISTS event_slot_calendar_entry;
            CREATE OR REPLACE VIEW event_slot_calendar_entry AS (
            select
                s.id + 1000000 * e.id as id,
                e.id as event_id,
                s.id as slot_id,
                e.name as name,
                coalesce(s.start_datetime, e.date_begin) as start,
                coalesce(s.end_datetime, e.date_end) as stop,
                (mod(abs(e.id), 11))::int AS color,
                coalesce(s.create_date, e.create_date) as create_date,
                coalesce(s.create_uid, e.create_uid) as create_uid,
                coalesce(s.write_date, e.write_date) as write_date,
                coalesce(s.write_uid, e.write_uid) as write_uid,
                active,
                address_id,
                community_menu,
                company_id,
                country_id,
                cover_properties,
                date_tz,
                description,
                event_type_id,
                event_url,
                footer_visible,
                header_visible,
                introduction_menu,
                is_multi_slots,
                is_published,
                is_seo_optimized,
                kanban_state,
                lang,
                menu_id,
                note,
                organizer_id,
                register_menu,
                registration_properties_definition,
                seats_limited,
                seats_max,
                seo_name,
                stage_id,
                subtitle,
                ticket_instructions,
                user_id,
                website_id,
                website_menu,
                website_meta_description,
                website_meta_keywords,
                website_meta_og_img,
                website_meta_title,
                website_visibility
            from
                public.event_event e
            left join event_slot s on
                e.id = s.event_id
                        )
        """)