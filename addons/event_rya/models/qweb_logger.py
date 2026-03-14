from odoo import models
import logging

_logger = logging.getLogger(__name__)

def patch_qweb_render():
    """Patch IrQweb._render method to log every template + record IDs"""
    try:
        from odoo.addons.base.models.ir_qweb import IrQweb
    except ImportError:
        _logger.warning("Cannot patch QWeb render: IrQweb not available yet")
        return

    if hasattr(IrQweb, "_original__render"):
        return  # already patched

    # Keep original _render method
    IrQweb._original__render = IrQweb._render

    def patched__render(self, template, values=None, engine='ir.qweb', minimal_qcontext=False):
        record_ids = []
        if values:
            for key in ['doc', 'docs', 'o']:
                if key in values:
                    val = values[key]
                    try:
                        record_ids.extend(val.ids)
                    except AttributeError:
                        pass

        if record_ids:
            _logger.info("Rendering template '%s' with record IDs %s", template, record_ids)
        else:
            _logger.info("Rendering template '%s'", template)

        if values:
            _logger.debug("Context keys: %s", list(values.keys()))

        return IrQweb._original__render(
            self, template, values=values, engine=engine, minimal_qcontext=minimal_qcontext
        )

    # Patch
    IrQweb._render = patched__render
    _logger.info("QWeb _render method patched successfully")

# Patch immediately when module loads
###patch_qweb_render()