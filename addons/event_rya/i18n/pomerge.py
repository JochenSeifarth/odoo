import polib

# File paths
es_path = "es.po"
updates_path = "te_es_needs_update_with_context.txt"
output_path = "es_merged.po"

# Load PO files
es = polib.pofile(es_path)
updates = polib.pofile(updates_path)

# Create a lookup dict of updates: msgid -> new msgstr
update_dict = {e.msgid: e.msgstr for e in updates}

# Merge: update only msgstr in original es.po
for entry in es:
    if entry.msgid in update_dict:
        entry.msgstr = update_dict[entry.msgid]

# Save merged PO
es.save(output_path)
print(f"Merged Spanish PO saved to {output_path}")