#!/bin/bash
set -euo pipefail
set -x
DUMPFILE=$(find /tmp -maxdepth 1 -type f -name 'rya.*.zip' -printf '%T@ %p\n' | sort -nr | head -n 1 | cut -d' ' -f2-)
if [[ -z "$DUMPFILE" || ! -f "$DUMPFILE" ]]; then
    echo "ERROR: No dump file found in /tmp (rya.*.zip)" >&2
    exit 1
fi
cd /home/jochen/git/odoo
. ./venv_odoo/bin/activate
python3 odoo-bin.py db -c ./rya-odoo-DEV.conf load --force --neutralize ryadev $DUMPFILE
