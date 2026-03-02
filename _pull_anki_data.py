"""Read-only export of all Anki data to a local JSON file.
Does NOT modify anything in Anki — only reads."""

import json
from armenian_anki.anki_connect import AnkiConnect

ac = AnkiConnect()
assert ac.ping(), "AnkiConnect not reachable"

decks = ac.deck_names()
print(f"Found {len(decks)} decks")

export = {}
for deck in sorted(decks):
    note_ids = ac._request("findNotes", query=f'deck:"{deck}"')
    if not note_ids:
        print(f"  {deck}: 0 notes")
        continue
    notes = ac._request("notesInfo", notes=note_ids)
    print(f"  {deck}: {len(notes)} notes")
    export[deck] = []
    for n in notes:
        export[deck].append({
            "noteId": n["noteId"],
            "modelName": n["modelName"],
            "tags": n["tags"],
            "fields": {k: v["value"] for k, v in n["fields"].items()},
        })

out_path = "anki_export.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(export, f, ensure_ascii=False, indent=2)

total = sum(len(v) for v in export.values())
print(f"\nExported {total} notes across {len(export)} decks → {out_path}")
