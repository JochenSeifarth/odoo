# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, timedelta

from odoo import fields
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestEventMailSchedulers(TransactionCase):
    """Manual trigger of due mail schedulers for an event."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.today = fields.Date.context_today(cls.env.user)
        cls.event_date = cls.today - timedelta(days=1)
        cls.event_type = cls.env['event.type'].create({'name': 'Test Event Type'})
        cls.event = cls._create_event(
            datetime.combine(cls.event_date, datetime.min.time()),
            datetime.combine(cls.event_date + timedelta(days=1), datetime.min.time()),
            is_multi_slots=True,
        )
        cls.slot1, cls.slot2 = cls._create_slots(cls.event, [cls.event_date] * 2)

        cls.template = cls.env['mail.template'].create({
            'name': 'Test Review Template',
            'model_id': cls.env.ref('event.model_event_registration').id,
            'subject': 'Test Review',
            'body_html': '<p>Hello ${object.name}, please leave a review.</p>',
            'email_to': False,
            'use_default_to': True,
            'lang': '{{ object.partner_id.lang or object.event_id.lang }}',
        })

        cls.event.event_mail_ids.unlink()
        cls.scheduler = cls._create_scheduler(cls.event)
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Customer',
            'email': 'customer@example.com',
        })

    @classmethod
    def _create_event(cls, date_begin, date_end, is_multi_slots):
        return cls.env['event.event'].create({
            'name': 'Test Event',
            'event_type_id': cls.event_type.id,
            'date_begin': date_begin,
            'date_end': date_end,
            'is_multi_slots': is_multi_slots,
        })

    @classmethod
    def _create_slots(cls, event, dates):
        return cls.env['event.slot'].create([
            {
                'event_id': event.id,
                'date': slot_date,
                'start_hour': 9.0,
                'end_hour': 13.0,
            }
            for slot_date in dates
        ])

    @classmethod
    def _create_scheduler(cls, event, interval_type='after_event_slot', interval_nbr=0):
        event.event_mail_ids.unlink()
        return cls.env['event.mail'].create({
            'event_id': event.id,
            'interval_type': interval_type,
            'interval_unit': 'hours',
            'interval_nbr': interval_nbr,
            'template_ref': 'mail.template,%d' % cls.template.id,
            'only_attendees': True,
        })

    def _create_registration(self, event, slot=None, state='done'):
        return self.env['event.registration'].create({
            'event_id': event.id,
            'event_slot_id': slot.id if slot else False,
            'partner_id': self.partner.id,
            'email': self.partner.email,
            'name': self.partner.name,
            'state': state,
        })

    def _count_outgoing_mails(self, registrations):
        return self.env['mail.mail'].search_count([
            ('model', '=', 'event.registration'),
            ('res_id', 'in', registrations.ids),
        ])

    def _create_event_with_slot_dates(self, slot_dates):
        event_start = datetime.combine(min(slot_dates), datetime.min.time())
        event_end = datetime.combine(max(slot_dates) + timedelta(days=1), datetime.min.time())
        event = self._create_event(event_start, event_end, is_multi_slots=True)
        slots = self._create_slots(event, slot_dates)
        scheduler = self._create_scheduler(event)
        return event, slots, scheduler

    def test_due_scheduler_sends_one_mail_per_attended_registration(self):
        registration = self._create_registration(self.event, self.slot1)

        self.event.action_run_mail_schedulers()

        self.assertEqual(self._count_outgoing_mails(registration), 1)

    def test_old_slot_is_skipped_but_recent_slot_is_sent(self):
        old_date = self.today - timedelta(days=40)
        recent_date = self.today - timedelta(days=1)
        event, slots, scheduler = self._create_event_with_slot_dates([old_date, recent_date])
        old_registration = self._create_registration(event, slots[0])
        recent_registration = self._create_registration(event, slots[1])

        event.action_run_mail_schedulers()

        mail_slots = scheduler.mail_slot_ids.sorted('event_slot_id')
        self.assertTrue(mail_slots[0].mail_done, "The old slot must be marked done")
        self.assertTrue(mail_slots[1].mail_done, "The recent slot must be processed")
        self.assertTrue(scheduler.mail_done, "The scheduler is complete once all slots are handled")
        self.assertEqual(self._count_outgoing_mails(old_registration | recent_registration), 1)
        self.assertEqual(
            self.env['mail.mail'].search_count([
                ('model', '=', 'event.registration'),
                ('res_id', '=', recent_registration.id),
            ]),
            1,
        )

    def test_all_old_slots_are_skipped_and_scheduler_is_completed(self):
        old_date = self.today - timedelta(days=40)
        event, slots, scheduler = self._create_event_with_slot_dates([old_date, old_date])
        registrations = self._create_registration(event, slots[0])

        event.action_run_mail_schedulers()

        self.assertEqual(self._count_outgoing_mails(registrations), 0)
        self.assertTrue(scheduler.mail_slot_ids)
        self.assertTrue(all(scheduler.mail_slot_ids.mapped('mail_done')))
        self.assertTrue(scheduler.mail_done)

    def test_due_scheduler_creates_missing_slot_entries(self):
        self.assertFalse(self.scheduler.mail_slot_ids)

        self.event.action_run_mail_schedulers()

        self.assertEqual(len(self.scheduler.mail_slot_ids), 2)

    def test_done_scheduler_is_not_sent_again(self):
        registration = self._create_registration(self.event, self.slot1)
        self.scheduler.write({'mail_done': True})

        self.event.action_run_mail_schedulers()

        self.assertEqual(self._count_outgoing_mails(registration), 0)

    def test_only_attendees_filter_skips_confirmed_non_attendee(self):
        registration = self._create_registration(self.event, self.slot1, state='open')

        self.event.action_run_mail_schedulers()

        self.assertEqual(self._count_outgoing_mails(registration), 0)

    def test_old_after_subscription_scheduler_still_processes_due_registration(self):
        self.scheduler.write({'mail_done': True})
        scheduler = self._create_scheduler(self.event, interval_type='after_sub')
        registration = self._create_registration(self.event, self.slot1)
        scheduler.scheduled_date = fields.Datetime.now() - timedelta(days=40)

        self.event.action_run_mail_schedulers()

        self.assertFalse(scheduler.mail_done)
        self.assertEqual(self._count_outgoing_mails(registration), 1)

    def test_old_event_scheduler_is_completed_without_sending(self):
        old_date = self.today - timedelta(days=40)
        event_start = datetime.combine(old_date - timedelta(days=1), datetime.min.time())
        event_end = datetime.combine(old_date, datetime.min.time())
        event = self._create_event(event_start, event_end, is_multi_slots=False)
        scheduler = self._create_scheduler(event, interval_type='after_event')
        registration = self._create_registration(event)

        event.action_run_mail_schedulers()

        self.assertTrue(scheduler.mail_done)
        self.assertEqual(self._count_outgoing_mails(registration), 0)

    def test_after_slot_interval_is_used_by_slot_scheduler(self):
        scheduler = self._create_scheduler(self.event, interval_nbr=1)
        mail_slot = self.env['event.mail.slot'].create({
            'scheduler_id': scheduler.id,
            'event_slot_id': self.slot1.id,
        })

        self.assertEqual(
            mail_slot.scheduled_date,
            self.slot1.end_datetime + timedelta(hours=1),
        )

    def test_multi_slot_event_without_slots_uses_event_schedule(self):
        event_start = datetime.combine(self.today - timedelta(days=2), datetime.min.time())
        event_end = datetime.combine(self.today - timedelta(days=1), datetime.min.time())
        event = self._create_event(event_start, event_end, is_multi_slots=True)
        scheduler = self._create_scheduler(event)

        event.action_run_mail_schedulers()

        self.assertTrue(scheduler.mail_done)
