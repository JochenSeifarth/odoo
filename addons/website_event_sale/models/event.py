# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from datetime import datetime
import json
import re
import copy
import pytz
from odoo.tools.json import scriptsafe as json_scriptsafe

def _format_datetime_with_tz(dt, tz_name):
    if not dt:
        return None
    tz = pytz.timezone(tz_name)
    local_dt = dt.astimezone(tz)
    return local_dt.isoformat()  # e.g., 2026-05-13T16:00:00+02:00

class EventEvent(models.Model):
    _inherit = 'event.event'

    def _to_markup_data(self, website, max_slots=30):
        return json_scriptsafe.dumps(self._get_slots_as_events(website), indent=2)
        
    def _get_slots_as_events(self, website, max_slots=None):

        self.ensure_one()
        cutoff_date = datetime(2099, 1, 1, 0, 0, 0)
        base_url = website.get_base_url()
        cover_image_url = re.search(r'url\(\\"?(.*?)\\"?\)', self.cover_properties).group(1)

        # Build offers
        offers = []
        now = datetime.utcnow().replace(second=0, microsecond=0)
        for ticket in self.event_ticket_ids:
            ticket_alternate_names = {}
            for lang in ticket.env['res.lang'].search([]):
                lang_ticket = ticket.with_context(lang=lang.code)
                with self.env.cr.savepoint():
                    if lang_ticket.name != ticket.name:
                        ticket_alternate_names[lang.code] = lang_ticket.name

            offers.append({
                "@type": "Offer",
                "name": ticket.name,
                **({"alternateName": ticket_alternate_names} if ticket_alternate_names else {}),
                "price": str(ticket.price),
                "priceCurrency": ticket.currency_id.name if ticket.currency_id else "EUR",
                "availability": "https://schema.org/SoldOut" if ticket.is_sold_out else "https://schema.org/InStock",
                "validFrom": _format_datetime_with_tz(ticket.start_sale_datetime, self.date_tz) if ticket.start_sale_datetime else _format_datetime_with_tz(now, self.date_tz),
                "url": self.event_register_url,
                "potentialAction": {
                    "@type": "ReserveAction",
                    "target": {
                        "@type": "EntryPoint",
                        "urlTemplate": self.event_register_url,
                        "actionPlatform": [
                            "http://schema.org/DesktopWebPlatform",
                            "http://schema.org/MobileWebPlatform"
                        ]
                    }
                }
            })

        # Build geo
        geo = None
        if self.address_id and self.address_id.partner_latitude and self.address_id.partner_longitude:
            geo = {
                "@type": "GeoCoordinates",
                "latitude": str(self.address_id.partner_latitude),
                "longitude": str(self.address_id.partner_longitude)
            }

        # Build alternate names for translations
        event_alternate_names = {}
        event_alternate_descriptions = {}
        for lang in self.env['res.lang'].search([]):
            lang_event = self.with_context(lang=lang.code)
            with self.env.cr.savepoint():
                if lang_event.name != self.name:
                    event_alternate_names[lang.code] = lang_event.name
                if lang_event.subtitle != self.subtitle:
                    event_alternate_descriptions[lang.code] = lang_event.subtitle                    
            
        # Base template for an event
        additional_types = []
        if any(tag.id == 1 for tag in self.tag_ids):
            additional_types.append("https://schema.org/TouristTrip")
        
        base_event = {
            "@context": "https://schema.org",
            "@type": "Event",
            "@id": self.event_share_url,
            **({"additionalType": additional_types} if additional_types else {}),            
            "name": self.name,
            "alternateName": event_alternate_names if event_alternate_names else None,            
            "description": self.subtitle,
            "alternateDescription": event_alternate_descriptions if event_alternate_descriptions else None,
            "startDate": _format_datetime_with_tz(self.date_begin, self.date_tz),
            "endDate": _format_datetime_with_tz(self.date_end, self.date_tz),
            "url": self.event_register_url,
            "image": f"{base_url}{cover_image_url}",
            "eventStatus": "https://schema.org/EventScheduled",
            "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
            "location": {
                "@type": "Place",
                "name": self.address_id.name,
                "address": {
                    "@type": "PostalAddress",
                    "streetAddress": "\n".join(filter(None, [self.address_id.street, self.address_id.street2])),
                    "postalCode": self.address_id.zip,
                    "addressLocality": self.address_id.city,
                    "addressCountry": self.address_id.country_code,
                },
                **({"geo": geo} if geo else {})
            },
            "organizer": {
                "@id": self.company_id.website,
            },
            "performer": {
                "@id": self.company_id.website,
            },
            "offers": offers
        }

        # Build final events list
        events = []
        now = datetime.utcnow()
        upcoming_slots = sorted(
            [slot for slot in self.event_slot_ids if slot.start_datetime and slot.start_datetime >= now],
            key=lambda s: s.start_datetime
        )

        if max_slots is not None:
            upcoming_slots = upcoming_slots[:max_slots]

        if upcoming_slots:
            for slot in upcoming_slots:
                # Copy base event
                slot_event = copy.deepcopy(base_event)
                # Overwrite slot-specific fields
                slot_event["@id"] = re.sub(r'/event/.*+', f'/event/{slot.id}-{self.id}', self.event_share_url)
                slot_event["url"] = slot_event["@id"]
                slot_event["startDate"] = _format_datetime_with_tz(slot.start_datetime, slot.date_tz)
                slot_event["endDate"] = _format_datetime_with_tz(slot.end_datetime, slot.date_tz)
                slot_event["name"] = f"{self.name} - {slot.display_name}"
                # Update alternate names with slot display_name
                slot_alternate_names = {}
                if base_event.get("alternateName"):
                    slot_alternate_names = base_event["alternateName"].copy()
                    for lang_code, translated_name in slot_alternate_names.items():
                        slot_alternate_names[lang_code] = f"{translated_name} - {slot.display_name}"

                if slot_alternate_names:
                    slot_event["alternateName"] = slot_alternate_names
                
                events.append(slot_event)
        else:
            # No slots → use base event, assign slot_id = 0 to @id
            if self.date_begin and self.date_begin <= cutoff_date:
                 events.append(base_event)

        return events