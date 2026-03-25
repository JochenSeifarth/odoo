#!/bin/bash
set -x
DUMPFILE=$(mktemp /tmp/rya.XXXXXX.zip)
sudo chgrp odoo $DUMPFILE
chmod 660 $DUMPFILE
# odoo is particularly picky about position of options
ssh rya@rya "cd ~rya/git/odoo && ./venv_odoo/bin/python ./odoo-bin db -c ./rya-odoo-PROD.conf dump rya" 2> >(cat >&2) | pv -ptrab > $DUMPFILE
# odoo is particularly picky about position of options
cd /home/jochen/git/odoo
. ./venv_odoo/bin/activate 
python3 odoo-bin.py db -c ./rya-odoo-DEV.conf load --force --neutralize ryadev $DUMPFILE
