import sys
sys.path.insert(0, '02-src')
from lousardzag.database import CardDatabase

db = CardDatabase()
rows = db.get_vocabulary_from_cache('Armenian (Western)')
entry = [r for r in rows if r.get('lemma') == 'Õ¥Õ¶'][0] if any(r.get('lemma') == 'Õ¥Õ¶' for r in rows) else None

if entry:
    trans = entry.get('translation', '')
    print(f'Translation: {repr(trans)}')
    word_count = len(trans.split())
    print(f'Word count: {word_count}')
    print(f'Starts with "they": {trans.lower().startswith("they")}')
    print(f'Starts with "I": {trans.lower().startswith("i ")}')
    print(f'Has comma: {"," in trans}')
else:
    print("Entry not found")

