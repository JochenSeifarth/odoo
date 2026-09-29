import logging
import threading

from odoo.orm.registry import Registry
from odoo.sql_db import db_connect
from odoo.tools import config

_logger = logging.getLogger(__name__)

IR_QWEB_LOGGER = 'odoo.addons.base.models.ir_qweb'

# Only the deprecation warnings of the templates of this module are kept; the
# same warnings coming from any other module are silenced. The core ir_qweb
# compiler only reports the template's view id, not the module it belongs to,
# so the view ids of this module are resolved from ir_model_data.
_KEPT_MODULE = __name__.split('.')[2]

# "Found deprecated directive @t-esc=%r in template %r. Replace by @t-out"
_MESSAGE_PREFIX = 'Found deprecated directive'

_lock = threading.Lock()
_kept_view_ids = None


class _KeepOwnModuleDeprecationFilter(logging.Filter):
    """ Drop the deprecation warnings of every module but this one. """

    def filter(self, record):
        if not isinstance(record.msg, str) or not record.msg.startswith(_MESSAGE_PREFIX):
            return True
        args = record.args
        if not isinstance(args, tuple) or len(args) < 2:
            return False
        kept_view_ids = _get_kept_view_ids()
        if kept_view_ids is None:
            # Resolution failed: keep everything rather than hide a warning
            # about our own templates.
            return True
        return args[1] in kept_view_ids


def _get_kept_view_ids():
    """ View ids of the templates of this module, read without using the ORM.

    The ORM is not available when this module is imported: templates are
    compiled while the module data is loaded, which is before the models are
    set up. A plain read-only query is enough here. The result is cached for
    the process; when it cannot be resolved the filter keeps every record, so
    that a lookup failure never hides a warning about our own templates.
    """
    global _kept_view_ids
    if _kept_view_ids is not None:
        return _kept_view_ids
    with _lock:
        if _kept_view_ids is not None:
            return _kept_view_ids
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
                        (_KEPT_MODULE,),
                    )
                    view_ids.update(row[0] for row in cr.fetchall())
            except Exception:
                _logger.debug(
                    "Could not read the view ids of %s from database %s",
                    _KEPT_MODULE, db_name, exc_info=True,
                )
        if view_ids:
            _kept_view_ids = view_ids
            _logger.debug("Keeping QWeb deprecation warnings for view ids %s", sorted(view_ids))
        else:
            _logger.warning(
                "No view id of %s could be resolved, no QWeb deprecation warning is filtered",
                _KEPT_MODULE,
            )
    return _kept_view_ids


def install():
    """ Keep the QWeb deprecation warnings of this module's templates only.

    Must run before the templates are compiled, i.e. on module import.
    """
    logger = logging.getLogger(IR_QWEB_LOGGER)
    if not any(isinstance(f, _KeepOwnModuleDeprecationFilter) for f in logger.filters):
        logger.addFilter(_KeepOwnModuleDeprecationFilter())
    return logger
