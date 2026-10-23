# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import api, fields, models

from odoo.addons.event.models.event_mail import _INTERVALS

_logger = logging.getLogger(__name__)


class EventMail(models.Model):
    _inherit = 'event.mail'

    interval_type = fields.Selection(
        selection_add=[('after_event_slot', 'After the slot ends')],
        ondelete={'after_event_slot': 'set default'},
    )

    only_attendees = fields.Boolean(
        string='Only for attendees',
        default=True,
        help='Send this communication only to the participants that actually took '
             'part, so that a guest who never showed up is not contacted. It '
             'applies once the event or the slot has started, where the '
             'attendance is known. It has no effect before the event starts and '
             'on the communication sent on each registration.')

    def _contacts_only_attendees(self):
        """Whether this scheduler has to skip the participants that did not attend.

        True for every trigger that runs once the event or the slot has started,
        because the attendance is known by then. Before the event starts, and for
        the communication sent on each registration, everybody still has to be
        reached whatever their attendance is.
        """
        self.ensure_one()
        return self.only_attendees and self.interval_type not in ('before_event', 'after_sub')

    def _is_slot_based(self):
        """Whether this scheduler runs once per slot instead of once per event.

        The trigger "After the slot ends" always means per slot, even on an event
        that defines none. The stock triggers keep the core behaviour, which is
        also per slot on an event that defines slots. A communication sent on each
        registration is never slot based.
        """
        self.ensure_one()
        if self.interval_type == 'after_sub':
            return False
        if self.interval_type == 'after_event_slot':
            return True
        return self.event_id.is_multi_slots and bool(self.event_id.event_slot_ids)

    def _execute_event_based_for_registrations(self, registrations):
        """Skip the registrations of guests that did not attend.

        Only relevant once the event or the slot has started, because that is when
        the attendance is known. Before that, everybody who is not cancelled or
        unconfirmed still has to be reached.
        """
        if self._contacts_only_attendees():
            attended = registrations.filtered(lambda registration: registration.state == 'done')
            if len(attended) != len(registrations):
                _logger.info(
                    "Event mail %s: %s registration(s) of event %s skipped, they did not attend",
                    self.id, len(registrations) - len(attended), self.event_id.id,
                )
            registrations = attended
            if not registrations:
                return True
        return super()._execute_event_based_for_registrations(registrations)

    def _get_slot_scheduled_date(self, slot):
        """Return the date a single slot is scheduled for.

        Single place deciding the sign of the interval, shared with the per slot
        schedulers in ``event.mail.slot``, so that both models agree on when a
        slot based communication is due.
        """
        self.ensure_one()
        if self.interval_type in ('before_event', 'after_event_start'):
            date = slot.start_datetime
            sign = -1 if self.interval_type == 'before_event' else 1
        else:
            date = slot.end_datetime
            sign = -1 if self.interval_type == 'before_event_end' else 1
        if not date:
            return False
        return date.replace(microsecond=0) + _INTERVALS[self.interval_unit](sign * self.interval_nbr)

    def _get_event_scheduled_date(self):
        """Return the date the whole event is scheduled for, after the interval."""
        self.ensure_one()
        date = self.event_id.date_end
        if not date:
            return False
        return date.replace(microsecond=0) + _INTERVALS[self.interval_unit](self.interval_nbr)

    @api.depends(
        'event_id.date_begin', 'event_id.date_end',
        'event_id.is_multi_slots',
        'event_id.event_slot_ids.start_datetime', 'event_id.event_slot_ids.end_datetime',
        'mail_slot_ids.mail_done',
        'interval_type', 'interval_unit', 'interval_nbr',
    )
    def _compute_scheduled_date(self):
        """Make the scheduler slot aware for multi-slot events.

        RYA keeps a far away ``date_end`` on multi-slot events so that they stay
        bookable for the whole season. The stock schedule is derived from that end
        date, so the cron would never wake up for those events. The date used to
        trigger the cron is therefore the earliest slot still waiting to be
        notified, which is also what is displayed as schedule date.
        """
        super()._compute_scheduled_date()
        slot_schedules = []
        for scheduler in self:
            if scheduler.interval_type == 'after_sub':
                continue
            if not scheduler._is_slot_based():
                continue
            if not scheduler.event_id.event_slot_ids:
                # "After the slot ends" picked on an event without slots: keep it
                # working on the end of the event instead of never firing.
                scheduler.scheduled_date = scheduler._get_event_scheduled_date()
                continue
            done_slots = scheduler.mail_slot_ids.filtered('mail_done').event_slot_id
            pending_slots = scheduler.event_id.event_slot_ids - done_slots
            dates = [date for date in map(scheduler._get_slot_scheduled_date, pending_slots) if date]
            if dates:
                scheduler.scheduled_date = min(dates)
                slot_schedules.extend(dates)
        if slot_schedules and (cron := self.env.ref('event.event_mail_scheduler', raise_if_not_found=False)):
            cron._trigger(min(slot_schedules))
