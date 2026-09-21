
from odoo import _, http
from odoo.fields import Domain
from odoo.http import request
from odoo.tools.json import scriptsafe as json_scriptsafe

from odoo.addons.website.controllers.main import QueryURL
from odoo.addons.website_event.controllers.main import WebsiteEventController


class WebsiteEventControllerRYA(WebsiteEventController):

    @http.route()
    def events(self, page=1, slug_tags=None, **searches):
        if (slug_tags or searches.get('tags', '[]').count(',') > 0) and request.httprequest.method == 'GET' and not searches.get('prevent_redirect'):
            # Previously, the tags were searched using GET, which caused issues with crawlers (too many hits)
            # We replaced those with POST to avoid that, but it's not sufficient as bots "remember" crawled pages for a while
            # This permanent redirect is placed to instruct the bots that this page is no longer valid
            # Note: We allow a single tag to be GET, to keep crawlers & indexes on those pages
            # What we really want to avoid is combinatorial explosions
            # (Tags are formed as a JSON array, so we count ',' to keep it simple)
            # TODO: remove in a few stable versions (v19?), including the "prevent_redirect" param in templates
            return request.redirect('/event', code=301)

        Event = request.env['event.event']
        SudoEventType = request.env['event.type'].sudo()

        searches.setdefault('search', '')
        searches.setdefault('date', 'scheduled')
        searches.setdefault('tags', '')
        searches.setdefault('type', 'all')
        searches.setdefault('country', 'all')
        # The previous name of the 'scheduled' filter is 'upcoming' and may still be present in URL's saved by users.
        if searches['date'] == 'upcoming':
            searches['date'] = 'scheduled'

        website = request.website

        step = 18  # Number of events per page

        options = self._get_events_search_options(slug_tags, **searches)
        order = 'date_begin'
        if searches.get('date', 'scheduled') == 'old':
            order = 'date_begin desc'
        order = 'is_published desc, ' + order + ', id desc'
        search = searches.get('search')
        event_count, details, fuzzy_search_term = website._search_with_fuzzy("events", search,
            limit=page * step, order=order, options=options)
        event_details = details[0]
        events = event_details.get('results', Event)
        events = events[(page - 1) * step:page * step]

        # count by domains without self search
        domain_search = Domain('name', 'ilike', fuzzy_search_term or searches['search']) if searches['search'] else Domain.TRUE

        no_date_domain = Domain.AND(event_details['no_date_domain'])
        dates = event_details['dates']
        for date in dates:
            if date[0] not in ['all', 'old']:
                date[3] = Event.search_count(no_date_domain & domain_search & Domain(date[2]))

        no_country_domain = Domain.AND(event_details['no_country_domain'])
        country_groups = Event._read_group(
            no_country_domain & domain_search,
            ["country_id"], ["__count"], order="country_id")
        countries = [{
            'country_id_count': sum(count for __, count in country_groups),
            'country_id': (0, _("All Countries")),
        }]
        for g_country, count in country_groups:
            countries.append({
                'country_id_count': count,
                'country_id': g_country and (g_country.id, g_country.sudo().display_name),
            })

        search_tags = self._extract_searched_event_tags(searches, slug_tags)
        current_date = event_details['current_date']
        current_type = None
        current_country = None

        if searches["type"] != 'all':
            current_type = SudoEventType.browse(int(searches['type']))

        if searches["country"] != 'all' and searches["country"] != 'online':
            current_country = request.env['res.country'].browse(int(searches['country']))

        pager = website.pager(
            url=f"/event/tags/{slug_tags}" if slug_tags else "/event",
            url_args=searches,
            total=event_count,
            page=page,
            step=step,
            scope=5)

        keep = QueryURL('/event', ['tags'],
            tags=slug_tags,
            **{
            key: value for key, value in searches.items() if (
                key != 'tags' and (
                    key == 'search' or
                    (value != 'scheduled' if key == 'date' else value != 'all'))
                )
            })

        searches['search'] = fuzzy_search_term or search

        product_markup_data = [
            item
            for event in events
            for item in event.sudo()._get_slots_as_events(request.website, max_slots=6)
        ]

        values = {
            'current_date': current_date,
            'current_country': current_country,
            'current_type': current_type,
            'event_ids': events,  # event_ids used in website_event_track so we keep name as it is
            # Add our event JSON-LD data as 'product_markup_data' so it gets picked up by the template website_sale.website_sale_layout
            'product_markup_data': json_scriptsafe.dumps(product_markup_data),
            'dates': dates,
            'categories': request.env['event.tag.category'].search([
                ('is_published', '=', True), '|', ('website_id', '=', website.id), ('website_id', '=', False),
            ]),
            'countries': countries,
            'pager': pager,
            'searches': searches,
            'search_tags': search_tags,
            'keep_event_url': keep,
            'slugify_tags': self._slugify_tags,
            'search_count': event_count,
            'original_search': fuzzy_search_term and search,
            'website': website,
        }

        return request.render("website_event.index", values)

    @http.route()
    def event(self, event, **post):
        if event.menu_id and event.menu_id.child_id:
            target_url = event.menu_id.child_id[0].url
        else:
            values = self._prepare_event_register_values(event, **post)
            return request.render("website_event.event_description_full", values)
            ### target_url = '/event/%s/register' % str(event.id)
        if post.get('enable_editor') == '1':
            target_url += '?enable_editor=1'
        return request.redirect(target_url)
