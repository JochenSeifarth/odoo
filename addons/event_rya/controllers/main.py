# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import logging
import html
import pprint

_logger = logging.getLogger(__name__)

class DebugInspector(http.Controller):

    @http.route('/debug/inspector', type='http', auth='user', website=True)
    def debug_inspector(self, **kwargs):
        """
        Full recursive inspector for qcontext + request params + sample model data.
        """
        qcontext = request.params.copy()  # start with request params
        model_name = kwargs.get('model')
        if model_name:
            try:
                model_obj = request.env[model_name]
                qcontext['sample_records'] = model_obj.search([], limit=5)
            except Exception as e:
                qcontext['model_error'] = f"Could not fetch {model_name}: {e}"

        # Recursive renderer
        def render(value, level=0):
            indent = '&nbsp;' * 4 * level
            try:
                if value is None:
                    return f"{indent}<em>None</em>"
                elif isinstance(value, (list, tuple, set)):
                    return '<br/>'.join(render(v, level+1) for v in value)
                elif isinstance(value, dict):
                    return '<br/>'.join(f"{indent}{html.escape(str(k))}: {render(v, level+1)}" for k,v in value.items())
                elif hasattr(value, '_fields'):  # Odoo Recordset
                    return render_recordset(value, level)
                else:
                    return f"{indent}{html.escape(str(value))}"
            except Exception as e:
                return f"{indent}[ERROR rendering value: {e}]"

        def render_recordset(rs, level=0):
            output = []
            indent = '&nbsp;' * 4 * level
            for r in rs:
                row = f"{indent}<strong>{r._name} ID={r.id}</strong>"
                # show first 5 fields only to avoid huge output
                try:
                    fields = {f: getattr(r, f) for f in list(r._fields)[:25]}
                    row += "<br/>" + render(fields, level+1)
                except Exception as e:
                    row += f"<br/>{indent}[Error reading fields: {e}]"
                output.append(row)
            return '<br/>'.join(output)

        # Prepare full locals-style dump
        locals_dump = {
            'qcontext': qcontext,
            'request_params': request.params,
        }

        # Log to server
        _logger.debug("Full Inspector Dump:\n%s", pprint.pformat(locals_dump))

        # Render HTML
        html_output = "<div style='padding:10px; font-family:monospace; background:#f0f0f0;'>"
        html_output += "<h2>Odoo 19 CE Full Inspector</h2>"
        html_output += render(locals_dump)
        html_output += "</div>"

        return html_output