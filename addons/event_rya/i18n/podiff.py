import polib

# File paths
de_old_path = "de.po.original"       # previous committed German
de_new_path = "de.po"       # updated German
es_path =     "de.po"               # Spanish file
output_path = "en_GB_needs_update_with_context.po"

# Load PO files
de_old = polib.pofile(de_old_path)
de_new = polib.pofile(de_new_path)
es = polib.pofile(es_path)

# Step 1: find changed German msgids and store old/new translations
changed_entries = {}
for entry_old in de_old:
    entry_new = de_new.find(entry_old.msgid)
    if entry_new and entry_old.msgstr != entry_new.msgstr:
        changed_entries[entry_old.msgid] = {
            "old": entry_old.msgstr,
            "new": entry_new.msgstr
        }

print(f"Found {len(changed_entries)} changed entries in German.")

# Step 2: filter Spanish entries with these msgids
es_changed = []
for entry in es:
    if entry.msgid in changed_entries:
        # Add old/new German translations as translator comments
        old_new = changed_entries[entry.msgid]
        entry.comment = (
            f"German translation changed:\n"
            f"OLD: {old_new['old']}\n"
            f"NEW: {old_new['new']}"
        )
        es_changed.append(entry)

# Step 3: write to new PO file
po_out = polib.POFile()
for entry in es_changed:
    po_out.append(entry)

po_out.save(output_path)
print(f"Spanish entries needing update saved to {output_path}")