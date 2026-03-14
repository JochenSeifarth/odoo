#!/usr/bin/env python3
import requests
import sys

# -------------------------------
# Konfiguration
# -------------------------------
source_odoo = "http://10.10.3.2:8069"  # Quellserver
target_odoo = "http://localhost:8069"  # Zielserver

source_db = "rya"
target_db = "ryadev"

# Master-Passwörter für die Database Manager
source_master_pwd = "j0ch3n$RYA"   # Quellserver
target_master_pwd = "j0ch3n$RYA"   # Zielserver

# Temporäre Backup-Datei
backup_file = "/tmp/rya_backup.zip"

# -------------------------------
# Backup von Quell-DB herunterladen
# -------------------------------
print(f"Backup der Datenbank '{source_db}' von {source_odoo} wird heruntergeladen...")

backup_url = f"{source_odoo}/web/database/backup"
data = {
    'master_pwd': source_master_pwd,
    'name': source_db,
    'backup_format': 'zip',
    'filestore': 1
}

try:
    r = requests.post(backup_url, data=data, stream=True)
    r.raise_for_status()
except requests.RequestException as e:
    print(f"Fehler beim Backup: {e}")
    sys.exit(1)

with open(backup_file, "wb") as f:
    for chunk in r.iter_content(chunk_size=8192):
        f.write(chunk)

print(f"Backup erfolgreich heruntergeladen: {backup_file}")

# -------------------------------
# Delete Ziel-DB
# -------------------------------
print(f"Datenbank '{target_db}' auf {target_odoo} wird gelöscht-..")

drop_url = f"{target_odoo}/web/database/drop"

with open(backup_file, "rb") as f:
    data = {
        'master_pwd': target_master_pwd,
        'name': target_db,
    }
    try:
        r = requests.post(drop_url, data=data)
        r.raise_for_status()
    except requests.RequestException as e:
        print(f"Fehler beim Drop: {e}")
        sys.exit(1)

print(f"Datenbank '{target_db}' erfolgreich gelöscht auf {target_odoo}")

# -------------------------------
# Restore auf Ziel-DB
# -------------------------------
print(f"Datenbank wird als '{target_db}' auf {target_odoo} wiederhergestellt...")

restore_url = f"{target_odoo}/web/database/restore"

with open(backup_file, "rb") as f:
    files = {'backup_file': f}
    data = {
        'master_pwd': target_master_pwd,
        'name': target_db,
        'neutralize_database': 'on',
        'copy': 'true'
    }
    try:
        r = requests.post(restore_url, data=data, files=files)
        r.raise_for_status()
    except requests.RequestException as e:
        print(f"Fehler beim Restore: {e}")
        sys.exit(1)

print(f"Datenbank '{target_db}' erfolgreich wiederhergestellt auf {target_odoo}")