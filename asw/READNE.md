Sailing Route infrastructure:
from https://github.com/auto-sea-way/asw
- download binary https://github.com/auto-sea-way/asw/releases/download/v0.4.0/asw-linux-amd64
- download graph https://github.com/auto-sea-way/asw/releases/download/v0.4.0/asw.graph (whole world)

into /asw(/export)

jochen@bruno:~/git/odoo/asw$ ./asw-linux-amd64 build --bbox -20,27,30,62 --output export/europe.graph
... or copy a pre-created file into export/europe.graph


cp asw.service /etc/systemd/system/asw.service

sudo systemctl daemon-reload
sudo systemctl enable asw
sudo systemctl start asw
sudo systemctl status asw