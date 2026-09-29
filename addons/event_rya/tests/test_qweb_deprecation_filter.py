# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo.tests.common import TransactionCase, tagged

from odoo.addons.event_rya.tools import qweb_deprecation_filter as filter_mod


@tagged('post_install', '-at_install')
class TestQwebDeprecationFilter(TransactionCase):
    """The filter that keeps the deprecation warnings of this module only."""

    def setUp(self):
        super().setUp()
        self._had_ids = 'ids' in filter_mod._kept_view_ids
        self._ids = filter_mod._kept_view_ids.get('ids')

    def tearDown(self):
        if self._had_ids:
            filter_mod._kept_view_ids['ids'] = self._ids
        else:
            filter_mod._kept_view_ids.pop('ids', None)
        super().tearDown()

    def _record(self, view_id, message=filter_mod._MESSAGE_PREFIX, args=None):
        return logging.LogRecord(
            filter_mod.IR_QWEB_LOGGER, logging.WARNING, '', 0,
            message, args if args is not None else ('@t-esc="x"', view_id), None,
        )

    def test_deprecation_of_own_template_is_kept(self):
        view_id = self.env.ref('event_rya.event_ticket_price_block').id
        filter_mod._kept_view_ids['ids'] = {view_id}
        self.assertTrue(filter_mod.KeepOwnModuleDeprecationFilter().filter(self._record(view_id)))

    def test_deprecation_of_foreign_template_is_dropped(self):
        view_id = self.env.ref('event_rya.event_ticket_price_block').id
        filter_mod._kept_view_ids['ids'] = {view_id}
        self.assertFalse(filter_mod.KeepOwnModuleDeprecationFilter().filter(self._record(view_id + 1)))

    def test_other_ir_qweb_records_are_kept(self):
        """The filter is on the ir_qweb logger: its other records must pass."""
        filter_mod._kept_view_ids['ids'] = set()
        record = self._record(1, message='Rendering template %r', args=('web.layout',))
        self.assertTrue(filter_mod.KeepOwnModuleDeprecationFilter().filter(record))

    def test_unresolvable_view_ids_keep_everything(self):
        filter_mod._kept_view_ids['ids'] = None
        self.assertTrue(filter_mod.KeepOwnModuleDeprecationFilter().filter(self._record(1)))

    def test_malformed_args_are_dropped(self):
        filter_mod._kept_view_ids['ids'] = {1}
        self.assertFalse(filter_mod.KeepOwnModuleDeprecationFilter().filter(self._record(1, args='nope')))

    def test_resolution_finds_the_views_of_the_module(self):
        """The read-only query runs on the database of the test."""
        filter_mod._kept_view_ids.pop('ids', None)
        view_ids = filter_mod._get_kept_view_ids()
        self.assertIsNotNone(view_ids)
        self.assertIn(self.env.ref('event_rya.event_ticket_price_block').id, view_ids)

    def test_install_is_idempotent(self):
        logger = logging.getLogger(filter_mod.IR_QWEB_LOGGER)
        before = sum(isinstance(f, filter_mod.KeepOwnModuleDeprecationFilter) for f in logger.filters)
        filter_mod.install()
        filter_mod.install()
        after = sum(isinstance(f, filter_mod.KeepOwnModuleDeprecationFilter) for f in logger.filters)
        self.assertLessEqual(after - before, 1)
