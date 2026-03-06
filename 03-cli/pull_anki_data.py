"""Read-only export of all Anki data, then import into local SQLite.

Flow:
1) Read notes from Anki via AnkiConnect (no writes to Anki)
2) Export full payload to 08-data/anki_export.json
3) Upsert all notes into 08-data/armenian_cards.db
4) Delete 08-data/anki_export.json after successful processing
5) Save note-type field map to 08-data/anki_field_names_by_note_type.json
"""

from __future__ import annotations

import base64
import html
import json
import os
import re
import shutil
import sqlite3
import sys
import tempfile
import time
import zipfile
from pathlib import Path

# Add 02-src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "02-src"))

from lousardzag.anki_connect import AnkiConnect
from lousardzag.database import CardDatabase

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "08-data"
OUT_PATH = DATA_DIR / "anki_export.json"
MEDIA_DIR = DATA_DIR / "anki_media"
FIELD_MAP_PATH = DATA_DIR / "anki_field_names_by_note_type.json"
DEDUP_FIELDS_PATH = DATA_DIR / "anki_field_names_dedup.json"

# Patterns for media references in Anki field HTML
RE_SOUND = re.compile(r"\[sound:([^\]]+)\]")
RE_IMG = re.compile(r"<img[^>]+src=[\"']([^\"']+)[\"']", re.IGNORECASE)


def request_with_retry(ac: AnkiConnect, action: str, retries: int = 3, **params):
    for attempt in range(retries):
        try:
            return ac._request(action, **params)
        except Exception as e:
            if attempt == retries - 1:
                raise
            wait = 2 ** (attempt + 1)
            print(f"    Retry {attempt + 1} in {wait}s: {e}")
            time.sleep(wait)


def parse_apkg(apkg_path: str) -> list[dict]:
    """Extract notes and media from an .apkg file."""
    notes: list[dict] = []
    with tempfile.TemporaryDirectory() as tmp:
        with zipfile.ZipFile(apkg_path, "r") as zf:
            zf.extractall(tmp)

        db_path = None
        for name in ["collection.anki21", "collection.anki2"]:
            candidate = os.path.join(tmp, name)
            if os.path.exists(candidate):
                db_path = candidate
                break
        if not db_path:
            print(f"    WARNING: No SQLite db found in {apkg_path}")
            return notes

        media_map_path = os.path.join(tmp, "media")
        media_count = 0
        if os.path.exists(media_map_path):
            with open(media_map_path, "r", encoding="utf-8") as mf:
                media_map = json.load(mf)
            MEDIA_DIR.mkdir(exist_ok=True)
            for numeric_name, real_name in media_map.items():
                src = os.path.join(tmp, numeric_name)
                dst = MEDIA_DIR / real_name
                if os.path.exists(src) and not dst.exists():
                    shutil.copy2(src, dst)
                    media_count += 1
        if media_count:
            print(f"    Extracted {media_count} media files")

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        col_row = cur.execute("SELECT models FROM col").fetchone()
        models = json.loads(col_row["models"])

        for row in cur.execute("SELECT id, mid, flds, tags FROM notes"):
            model_id = str(row["mid"])
            model = models.get(model_id, {})
            model_name = model.get("name", "Unknown")
            field_names = [f["name"] for f in model.get("flds", [])]
            field_values = row["flds"].split("\x1f")
            fields = {}
            for i, name in enumerate(field_names):
                fields[name] = field_values[i] if i < len(field_values) else ""
            tags = row["tags"].strip().split() if row["tags"].strip() else []
            notes.append(
                {
                    "noteId": row["id"],
                    "modelName": model_name,
                    "tags": tags,
                    "fields": fields,
                }
            )
        conn.close()
    return notes


def export_via_apkg(ac: AnkiConnect, deck_name: str) -> list[dict]:
    """Export one deck via exportPackage, parse, then remove temp file."""
    tmp_dir = tempfile.gettempdir()
    apkg_path = os.path.join(tmp_dir, "_anki_temp_export.apkg").replace("\\", "/")
    result = request_with_retry(
        ac,
        "exportPackage",
        deck=deck_name,
        path=apkg_path,
        includeSched=False,
    )
    if not result:
        print(f"    exportPackage returned false for {deck_name}")
        return []
    notes = parse_apkg(apkg_path)
    os.remove(apkg_path)
    return notes


def find_media_refs(fields: dict) -> set[str]:
    refs: set[str] = set()
    for value in fields.values():
        refs.update(RE_SOUND.findall(value))
        refs.update(RE_IMG.findall(value))
    return refs


def fetch_media_via_api(ac: AnkiConnect, media_filenames: set[str]) -> int:
    MEDIA_DIR.mkdir(exist_ok=True)
    fetched = 0
    for fname in media_filenames:
        dst = MEDIA_DIR / fname
        if dst.exists():
            continue
        try:
            data = request_with_retry(ac, "retrieveMediaFile", filename=fname)
            if data:
                dst.write_bytes(base64.b64decode(data))
                fetched += 1
        except Exception:
            pass
    return fetched


def export_via_notesinfo(ac: AnkiConnect, deck_name: str) -> list[dict]:
    """Fallback export path for unstable exportPackage calls."""
    note_ids = request_with_retry(ac, "findNotes", query=f'deck:"{deck_name}"')
    if not note_ids:
        return []

    batch_size = 25
    actions = []
    for i in range(0, len(note_ids), batch_size):
        chunk = note_ids[i : i + batch_size]
        actions.append({"action": "notesInfo", "params": {"notes": chunk}})

    results = request_with_retry(ac, "multi", actions=actions)

    notes: list[dict] = []
    all_media: set[str] = set()
    for batch_result in results:
        if isinstance(batch_result, dict) and batch_result.get("error"):
            print(f"    Batch error: {batch_result['error']}")
            continue
        batch_notes = (
            batch_result
            if isinstance(batch_result, list)
            else batch_result.get("result", [])
        )
        for n in batch_notes:
            fields = {k: v["value"] for k, v in n["fields"].items()}
            all_media.update(find_media_refs(fields))
            notes.append(
                {
                    "noteId": n["noteId"],
                    "modelName": n["modelName"],
                    "tags": n["tags"],
                    "fields": fields,
                }
            )

    if all_media:
        fetched = fetch_media_via_api(ac, all_media)
        if fetched:
            print(f"    Fetched {fetched} media files via API")

    return notes


def _extract_field(fields: dict, candidates: list[str]) -> str:
    """Extract first non-empty candidate field (case-insensitive)."""
    for candidate in candidates:
        for field_name, value in fields.items():
            if field_name.lower() == candidate.lower() and isinstance(value, str):
                stripped = value.strip()
                if stripped:
                    return stripped
    return ""


def _clean_html(text: str) -> str:
    """Remove HTML tags and decode HTML entities from text."""
    if not text:
        return text
    
    # Remove HTML tags (e.g., <span style="...">text</span> -> text)
    text = re.sub(r'<[^>]+>', '', text)
    
    # Decode HTML entities (e.g., &nbsp; -> space, &amp; -> &)
    text = html.unescape(text)
    
    # Clean up multiple spaces and trim
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def _first_nonempty_short(fields: dict) -> str:
    for value in fields.values():
        if isinstance(value, str):
            stripped = value.strip()
            if stripped and len(stripped) < 200:
                return stripped
    return ""


def write_field_name_map(ac: AnkiConnect) -> None:
    models = request_with_retry(ac, "modelNamesAndIds")
    by_model: dict[str, list[str]] = {}
    dedup: set[str] = set()

    for model_name in sorted(models.keys()):
        fields = request_with_retry(ac, "modelFieldNames", modelName=model_name)
        by_model[model_name] = fields
        dedup.update(fields)

    FIELD_MAP_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(FIELD_MAP_PATH, "w", encoding="utf-8") as f:
        json.dump(by_model, f, ensure_ascii=False, indent=2)

    with open(DEDUP_FIELDS_PATH, "w", encoding="utf-8") as f:
        json.dump(sorted(dedup), f, ensure_ascii=False, indent=2)

    print(f"Saved note-type field map: {FIELD_MAP_PATH}")
    print(f"Saved deduplicated field list: {DEDUP_FIELDS_PATH}")


def cleanup_test_data(db: CardDatabase) -> int:
    """Remove test/junk data from database before import."""
    print(f"Cleaning up test data from database: {db.db_path}")
    
    with db._connect() as conn:
        # Delete test cards from anki_cards (cascades to card_enrichment)
        result = conn.execute("DELETE FROM anki_cards WHERE word LIKE 'test_%'")
        test_word_count = result.rowcount
        
        conn.commit()
    
    if test_word_count > 0:
        print(f"  Deleted {test_word_count} test cards")
    
    return test_word_count


def cleanup_html_in_existing_cards(db: CardDatabase) -> int:
    """Clean HTML tags and entities from existing database records."""
    print(f"Cleaning HTML from existing cards in database: {db.db_path}")
    
    with db._connect() as conn:
        # Find cards with HTML tags or entities
        cursor = conn.execute("""
            SELECT id, word, translation, pos 
            FROM anki_cards
            WHERE word LIKE '%<%' OR word LIKE '%&%;%'
               OR translation LIKE '%<%' OR translation LIKE '%&%;%'
               OR pos LIKE '%<%' OR pos LIKE '%&%;%'
        """)
        
        rows = cursor.fetchall()
        cleaned_count = 0
        
        for row_id, word, translation, pos in rows:
            cleaned_word = _clean_html(word) if word else word
            cleaned_translation = _clean_html(translation) if translation else translation
            cleaned_pos = _clean_html(pos) if pos else pos
            
            conn.execute("""
                UPDATE anki_cards
                SET word = ?, translation = ?, pos = ?
                WHERE id = ?
            """, (cleaned_word, cleaned_translation, cleaned_pos, row_id))
            cleaned_count += 1
        
        conn.commit()
    
    if cleaned_count > 0:
        print(f"  Cleaned HTML from {cleaned_count} existing cards")
    
    return cleaned_count


def load_export_into_db(export_payload: dict[str, list[dict]]) -> int:
    db = CardDatabase()
    print(f"Loading data into database: {db.db_path}")

    total_upserted = 0
    for deck_name, notes in export_payload.items():
        if not notes:
            continue

        deck_upserted = 0
        for note in notes:
            note_id = note.get("noteId")
            model_name = note.get("modelName", "")
            fields = note.get("fields", {})
            tags = note.get("tags", [])

            word = _extract_field(fields, ["Word", "Armenian", "Front", "Question"])
            if not word:
                word = _first_nonempty_short(fields)
            if not word:
                word = f"note_{note_id}" if note_id is not None else "note_unknown"
            
            # Clean HTML from word
            word = _clean_html(word)

            translation = _extract_field(
                fields,
                ["Translation", "English", "Meaning", "Back", "Answer"],
            )
            
            # Clean HTML from translation
            translation = _clean_html(translation)
            
            pos = _extract_field(fields, ["PartOfSpeech", "POS", "Type", "Word Type"])
            
            # Clean HTML from POS
            pos = _clean_html(pos)

            metadata = {
                "anki_note_id": note_id,
                "anki_model_name": model_name,
                "anki_deck_name": deck_name,
                "anki_tags": tags,
                "anki_fields": fields,
            }

            card_type = f"anki_note:{note_id}" if note_id is not None else "anki_note:unknown"

            # Parse deck path: split on "::" to get parent deck and sub-deck
            if "::" in deck_name:
                parent_deck, child_deck = deck_name.split("::", 1)
            else:
                parent_deck = deck_name
                child_deck = ""

            try:
                db.upsert_card(
                    word=word,
                    translation=translation,
                    pos=pos,
                    card_type=card_type,
                    metadata=metadata,
                    anki_note_id=note_id,
                    deck_name=parent_deck,
                    sub_deck_name=child_deck,
                )
                total_upserted += 1
                deck_upserted += 1
            except Exception as e:
                print(f"    WARNING: failed upsert note {note_id}: {e}")

        print(f"  {deck_name}: upserted {deck_upserted} notes")

    return total_upserted


def main() -> None:
    ac = AnkiConnect()
    assert ac.ping(), "AnkiConnect not reachable - is Anki running?"

    # Field inventory by note type.
    write_field_name_map(ac)

    decks = ac.deck_names()
    print(f"Found {len(decks)} decks")

    # Only export leaf decks (avoid duplicate notes from parent + child decks).
    leaf_decks = []
    for d in sorted(decks):
        if not any(other.startswith(d + "::") for other in decks):
            leaf_decks.append(d)
        else:
            print(f"  Skipping parent deck: {d}")

    export: dict[str, list[dict]] = {}
    for deck in leaf_decks:
        try:
            notes = export_via_apkg(ac, deck)
            print(f"  {deck}: {len(notes)} notes (via exportPackage)")
        except Exception as e:
            print(f"  {deck}: exportPackage failed ({e}), trying notesInfo fallback...")
            try:
                notes = export_via_notesinfo(ac, deck)
                print(f"  {deck}: {len(notes)} notes (via multi+notesInfo)")
            except Exception as e2:
                print(f"  {deck}: FAILED - {e2}")
                notes = []
        export[deck] = notes
        time.sleep(0.5)

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(export, f, ensure_ascii=False, indent=2)

    total = sum(len(v) for v in export.values())
    media_count = len(list(MEDIA_DIR.glob("*"))) if MEDIA_DIR.exists() else 0
    print(f"Exported {total} notes across {len(export)} decks -> {OUT_PATH}")
    print(f"Media files: {media_count} in {MEDIA_DIR.name}/")

    # Clean up test data before importing
    db = CardDatabase()
    cleanup_test_data(db)
    cleanup_html_in_existing_cards(db)

    total_upserted = load_export_into_db(export)
    print(f"Upserted {total_upserted} notes into database")

    try:
        OUT_PATH.unlink()
        print(f"Deleted processed export file: {OUT_PATH}")
    except Exception as e:
        print(f"WARNING: Could not delete {OUT_PATH}: {e}")


if __name__ == "__main__":
    main()
