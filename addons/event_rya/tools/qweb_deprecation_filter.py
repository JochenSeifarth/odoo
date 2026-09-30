import logging
import threading

import psycopg2

from odoo.orm.registry import Registry
from odoo.sql_db import db_connect
from odoo.tools import config

_logger = logging.getLogger(__name__)

IR_QWEB_LOGGER = 'odoo.addons.base.models.ir_qweb'

_MODULE_NAME = 'event_rya'

# "Found deprecated directive @t-esc=%r in template %r. Replace by @t-out"
_MESSAGE_PREFIX = 'Found deprecated directive'

_lock = threading.Lock()

# Resolved view ids of _MODULE_NAME, or None when they could not be read. Held
# in a dict so that the value is set exactly once per process without a global
# statement; the presence of the key means "already resolved".
_kept_view_ids = {}


def _resolve_kept_view_ids():
    """ View ids of the templates of _MODULE_NAME, or None if they are unreadable.

    The ORM is not available when this runs: templates are compiled while the
    module data is loaded, which is before the models are set up. A plain
    read-only query is enough here.

    The ids are database specific while the logging module is process-wide, so
    with several databases the result is their union.
    """
    view_ids = set()
    db_names = set(Registry.registries.keys())
    # config['db_name'] is a list of database names, possibly empty
    db_names.update(config.get('db_name') or [])
    for db_name in db_names:
        try:
            with db_connect(db_name).cursor() as cr:
                cr.execute(
                    """
                    SELECT v.id
                      FROM ir_ui_view v
                      JOIN ir_model_data d ON d.model = 'ir.ui.view' AND d.res_id = v.id
                     WHERE d.module = %s
                    """,
                    (_MODULE_NAME,),
                )
                view_ids.update(row[0] for row in cr.fetchall())
        except psycopg2.Error:
            # Narrow on purpose: any other error is a bug, not a missing view.
            _logger.warning(
                "Could not read the view ids of %s from database %s",
                _MODULE_NAME, db_name, exc_info=True,
            )
    return view_ids or None


def _get_kept_view_ids():
    if 'ids' not in _kept_view_ids:
        with _lock:
            if 'ids' not in _kept_view_ids:
                _kept_view_ids['ids'] = _resolve_kept_view_ids()
                _logger.debug(
                    "Filtering QWeb deprecation warnings, keeping view ids %s",
                    sorted(_kept_view_ids['ids'] or ()),
                )
    return _kept_view_ids['ids']


class KeepOwnModuleDeprecationFilter(logging.Filter):
    """ Keep the QWeb deprecation warnings of this module's templates only. """

    def filter(self, record):
        if not isinstance(record.msg, str) or not record.msg.startswith(_MESSAGE_PREFIX):
            return True
        args = record.args
        if not isinstance(args, tuple) or len(args) < 2:
            return False
        kept_view_ids = _get_kept_view_ids()
        if kept_view_ids is None:
            # Unresolved: keep everything rather than hide a warning about our
            # own templates. The result is cached, so a module that is not
            # installed in this database costs two queries per process, not two
            # per warning. Restart the server to pick up a module installed in
            # the meantime.
            return True
        return args[1] in kept_view_ids


def install():
    """ Keep the QWeb deprecation warnings of this module's templates only.

    The core ir_qweb compiler emits those warnings only when the server runs
    with --dev=qweb, so in any other run there is nothing to filter and the
    view id lookup is skipped altogether.

    Note that this changes the logging of the whole instance, since the filter
    is attached to a process-wide logger. Starting the server without 'qweb'
    in --dev silences the same warnings without the side effect.

    Must run before the templates are compiled, i.e. on module import.
    """
    if 'qweb' not in (config.get('dev_mode') or []):
        return False
    logger = logging.getLogger(IR_QWEB_LOGGER)
    if not any(isinstance(f, KeepOwnModuleDeprecationFilter) for f in logger.filters):
        logger.addFilter(KeepOwnModuleDeprecationFilter())
    return True
