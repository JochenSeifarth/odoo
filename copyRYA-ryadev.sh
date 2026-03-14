#!/bin/bash
set -x
DUMPFILE=$(mktemp /tmp/rya.XXXXXX.zip)
sudo chgrp odoo $DUMPFILE
chmod 660 $DUMPFILE
# odoo is particularly picky about position of options
ssh rya "sudo -u odoo odoo db -c /etc/odoo/odoo.conf dump rya" 2> >(cat >&2) | pv -ptrab > $DUMPFILE
# odoo is particularly picky about position of options
###sudo -u odoo odoo db load --force --neutralize ryadev $DUMPFILE && rm -f $DUMPFILE
cd /home/jochen/git/odoo
. ./source venv_odoo/bin/activate 
python3 odoo-bin.py db -c ./odoo.conf load --force --neutralize ryadev $DUMPFILE
### (odoo_env) jochen@bruno:~/odoo$ ./odoo-bin db --db_host=127.0.0.1 --db_user odoo --db_password db_password load  --force --neutralize ryadev ryaPROD.zip