#!/usr/bin/env python3
"""Interactive web viewer for Armenian letter cards and vocab audio triage."""

import json
import os
from pathlib import Path
from flask import Flask, render_template_string, jsonify, request  # type: ignore[reportMissingImports]

# Add src directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "02-src"))

from lousardzag.letter_data import ARMENIAN_LETTERS
from lousardzag.core_shims.linguistics_core import ARMENIAN_PHONEMES, ARMENIAN_DIGRAPHS

app = Flask(__name__)

# Audio files directories
AUDIO_DIR = Path(__file__).parent.parent / "08-data" / "letter_audio"
VOCAB_AUDIO_DIR = Path(__file__).parent.parent / "08-data" / "vocab_audio"
COMP_AUDIO_DIR = Path(__file__).parent.parent / "08-data" / "audio_comparison"
TRIAGE_FILE = Path(__file__).parent.parent / "08-data" / "vocab_audio_triage.json"

# Vocab list matching the generator output
VOCAB_LIST = [
    {'word': '\u0570\u0561\u0575', 'meaning': 'Armenian'},
    {'word': '\u0563\u056b\u0580', 'meaning': 'letter/writing'},
    {'word': '\u0574\u0565\u056e', 'meaning': 'big'},
    {'word': '\u0583\u0578\u0584\u0580', 'meaning': 'small'},
    {'word': '\u057f\u0578\u0582\u0576', 'meaning': 'house'},
    {'word': '\u0574\u0561\u0580\u0564', 'meaning': 'person'},
    {'word': '\u056c\u0561\u0582', 'meaning': 'good'},
    {'word': '\u057b\u0578\u0582\u0580', 'meaning': 'water'},
    {'word': '\u0565\u0580\u056f\u0578\u0582', 'meaning': 'two'},
    {'word': '\u0574\u0567\u056f', 'meaning': 'one'},
]


def armenian_to_ipa(word: str) -> str:
    """Convert Armenian word to Western Armenian IPA."""
    ipa_parts = []
    i = 0
    while i < len(word):
        if i + 1 < len(word):
            digraph = word[i:i+2]
            if digraph in ARMENIAN_DIGRAPHS:
                ipa_parts.append(ARMENIAN_DIGRAPHS[digraph]['ipa'])
                i += 2
                continue
        letter = word[i]
        if letter in ARMENIAN_PHONEMES:
            ipa = ARMENIAN_PHONEMES[letter]['ipa']
            if '~' in ipa:
                ipa = ipa.split('~')[0]
            ipa_parts.append(ipa)
        i += 1
    return ''.join(ipa_parts)


def load_triage():
    """Load triage ratings from disk."""
    if TRIAGE_FILE.exists():
        return json.loads(TRIAGE_FILE.read_text(encoding='utf-8'))
    return {}


def save_triage(data):
    """Save triage ratings to disk."""
    TRIAGE_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

HTML_TEMPLATE = r"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Armenian Letter Cards</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        h1 {
            color: white;
            margin-bottom: 30px;
            text-align: center;
            font-size: 2.5em;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }
        .card {
            background: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            cursor: pointer;
            transition: all 0.3s ease;
            text-align: center;
        }
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 12px rgba(0,0,0,0.15);
        }
        .card.selected {
            background: #667eea;
            color: white;
        }
        .letter {
            font-size: 3em;
            font-weight: bold;
            margin: 15px 0;
            font-family: 'Arial Unicode MS', sans-serif;
        }
        .card.selected .letter { color: white; }
        .name { font-size: 0.9em; color: #666; margin: 5px 0; }
        .card.selected .name { color: #ddd; }
        .phonetic { font-size: 0.85em; color: #888; }
        .card.selected .phonetic { color: #aaa; }
        
        .detail-panel {
            background: white;
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin-top: 30px;
        }
        .detail-header {
            display: flex;
            align-items: center;
            gap: 30px;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #f0f0f0;
        }
        .detail-letter {
            font-size: 5em;
            font-weight: bold;
            min-width: 120px;
            text-align: center;
            font-family: 'Arial Unicode MS', sans-serif;
        }
        .detail-info {
            flex: 1;
        }
        .detail-info h2 {
            margin: 10px 0;
            color: #333;
        }
        .detail-info p {
            margin: 5px 0;
            color: #666;
            line-height: 1.6;
        }
        .audio-controls {
            display: flex;
            gap: 10px;
            margin: 20px 0;
            flex-wrap: wrap;
        }
        button {
            background: #667eea;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1em;
            transition: background 0.3s;
            flex: 1;
            min-width: 200px;
        }
        button:hover { background: #764ba2; }
        button:active { transform: scale(0.98); }
        button:disabled {
            background: #ccc;
            cursor: not-allowed;
            opacity: 0.5;
        }
        .audio-status {
            color: #666;
            font-size: 0.9em;
            margin-top: 10px;
        }
        
        .examples {
            margin-top: 20px;
        }
        .examples h3 {
            margin: 15px 0 10px;
            color: #333;
        }
        .example {
            background: #f9f9f9;
            padding: 10px 15px;
            border-radius: 6px;
            margin: 8px 0;
            border-left: 3px solid #667eea;
            font-size: 0.95em;
        }
        .example-arm {
            font-family: 'Arial Unicode MS', sans-serif;
            font-weight: bold;
            color: #333;
        }
        .example-meaning {
            color: #666;
            font-size: 0.9em;
            margin-top: 3px;
        }
        
        .difficulty {
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            margin: 10px 0;
        }
        
        .instruction {
            background: #f0f4ff;
            border-left: 4px solid #667eea;
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 20px;
            color: #333;
        }
        
        .empty-state {
            text-align: center;
            padding: 40px 20px;
            color: #999;
        }
        .empty-state p {
            font-size: 1.1em;
            margin-bottom: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🇦🇲 Armenian Letter Cards</h1>
        <div style="text-align:center;margin-bottom:15px;"><a href="/vocab" style="color:#667eea;font-size:0.95em;">→ Vocab Audio Triage</a></div>
        
        <div class="instruction">
            Click on any letter to view details and listen to pronunciation. All 38 letters of the Western Armenian alphabet.
        </div>
        
        <div class="grid" id="grid"></div>
        
        <div class="detail-panel" id="detail">
            <div class="empty-state">
                <p>Select a letter to view details</p>
            </div>
        </div>
    </div>

    <script>
        const letters = {{ letters_json | safe }};
        
        function renderGrid() {
            const grid = document.getElementById('grid');
            grid.innerHTML = '';
            
            letters.forEach((letter, idx) => {
                const card = document.createElement('div');
                card.className = 'card';
                card.innerHTML = `
                    <div class="letter">${letter.uppercase}</div>
                    <div class="name">${letter.name}</div>
                    <div class="phonetic">/${letter.ipa}/</div>
                `;
                card.onclick = () => selectLetter(idx);
                grid.appendChild(card);
            });
        }
        
        function selectLetter(idx) {
            // Update selection visual
            document.querySelectorAll('.card').forEach((c, i) => {
                c.classList.toggle('selected', i === idx);
            });
            
            // Show details
            const letter = letters[idx];
            console.log('[DEBUG] Selected letter:', letter);
            
            const nameAudioFile = letter.audio_file_name || '';
            const soundAudioFile = letter.audio_file_sound || '';
            console.log('[DEBUG] Name audio file:', nameAudioFile);
            console.log('[DEBUG] Sound audio file:', soundAudioFile);
            
            let examplesHtml = '';
            if (letter.example_words && letter.example_words.length > 0) {
                examplesHtml = `
                    <div class="examples">
                        <h3>Example Words</h3>
                        ${letter.example_words.map(word => {
                            const wordText = typeof word === 'string' ? word : word.word;
                            const meaning = typeof word === 'string' ? '' : (word.meaning || '');
                            return `
                                <div class="example">
                                    <div class="example-arm">${wordText}</div>
                                    ${meaning ? `<div class="example-meaning">${meaning}</div>` : ''}
                                </div>
                            `;
                        }).join('')}
                    </div>
                `;
            }
            
            const difficultyColor = {
                1: '#4CAF50',
                2: '#8BC34A',
                3: '#FFC107',
                4: '#FF9800',
                5: '#F44336'
            };
            
            const detail = document.getElementById('detail');
            detail.innerHTML = `
                <div class="detail-header">
                    <div class="detail-letter">${letter.uppercase}</div>
                    <div class="detail-info">
                        <h2>${letter.name}</h2>
                        <p><strong>IPA:</strong> /${letter.ipa}/</p>
                        <p><strong>English approx:</strong> sounds like "${letter.english_approx}"</p>
                        <p><strong>Lowercase:</strong> ${letter.lowercase}</p>
                        <div class="difficulty" style="background: ${difficultyColor[letter.difficulty]};">
                            Difficulty: ${letter.difficulty}/5
                        </div>
                    </div>
                </div>
                
                <div class="audio-controls">
                    <button id="playNameBtn" onclick="playAudio('${nameAudioFile}', 'Letter Name')">
                        🎤 Hear Letter Name
                    </button>
                    <button id="playSoundBtn" onclick="playAudio('${soundAudioFile}', 'Letter Sound')">
                        🔊 Hear Letter Sound
                    </button>
                </div>
                <div class="audio-status" id="audioStatus"></div>
                
                ${examplesHtml}
            `;
            
            // Update play button state
            updatePlayButtons(nameAudioFile, soundAudioFile);
        }
        
        function updatePlayButtons(nameAudioFile, soundAudioFile) {
            const nameBtn = document.getElementById('playNameBtn');
            const soundBtn = document.getElementById('playSoundBtn');
            const status = document.getElementById('audioStatus');
            
            console.log('[DEBUG] updatePlayButtons - name:', nameAudioFile, 'sound:', soundAudioFile);
            
            // Enable/disable name button
            if (!nameAudioFile || nameAudioFile === '') {
                nameBtn.disabled = true;
                nameBtn.style.opacity = '0.5';
            } else {
                nameBtn.disabled = false;
                nameBtn.style.opacity = '1';
            }
            
            // Enable/disable sound button
            if (!soundAudioFile || soundAudioFile === '') {
                soundBtn.disabled = true;
                soundBtn.style.opacity = '0.5';
            } else {
                soundBtn.disabled = false;
                soundBtn.style.opacity = '1';
            }
            
            status.textContent = '';
        }
        
        function playAudio(audioFile, audioType) {
            console.log('[DEBUG] playAudio called with:', audioFile, audioType);
            
            if (!audioFile) {
                alert('Audio file not available');
                return;
            }
            
            const audioUrl = '/audio/' + encodeURIComponent(audioFile);
            console.log('[DEBUG] Audio URL:', audioUrl);
            
            const audio = new Audio(audioUrl);
            const status = document.getElementById('audioStatus');
            
            audio.onplay = () => {
                console.log('[DEBUG] Audio playing');
                status.textContent = `Playing ${audioType}...`;
            };
            audio.onended = () => {
                console.log('[DEBUG] Audio ended');
                status.textContent = 'Done';
            };
            audio.onerror = (e) => {
                console.error('[DEBUG] Audio error:', e);
                status.textContent = 'Error playing audio';
            };
            
            audio.play().catch(err => {
                console.error('[DEBUG] Error playing audio:', err);
                status.textContent = 'Error: ' + err.message;
            });
        }
        
        // Initial render
        renderGrid();
        selectLetter(0);
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    # Convert dict to list and add audio file references
    import urllib.parse
    letters_list = []
    for letter_char, letter_data in ARMENIAN_LETTERS.items():
        letter_info = letter_data.copy()
        # Add both types of audio file references - properly encoded
        audio_name_file = f"letter_{urllib.parse.quote(letter_char)}_name.mp3"
        audio_sound_file = f"letter_{urllib.parse.quote(letter_char)}_sound.mp3"
        letter_info['audio_file_name'] = audio_name_file
        letter_info['audio_file_sound'] = audio_sound_file
        letter_info['letter_char'] = letter_char
        # Convert example_words from strings to objects if needed
        if 'example_words' in letter_info:
            example_words = []
            for ex in letter_info['example_words']:
                if isinstance(ex, str):
                    # Parse "word (meaning)" format
                    if '(' in ex and ')' in ex:
                        word = ex[:ex.index('(')].strip()
                        meaning = ex[ex.index('(')+1:ex.index(')')].strip()
                        example_words.append({'word': word, 'meaning': meaning})
                    else:
                        example_words.append({'word': ex, 'meaning': ''})
                else:
                    example_words.append(ex)
            letter_info['example_words'] = example_words
        letters_list.append(letter_info)
    
    return render_template_string(HTML_TEMPLATE, letters_json=json.dumps(letters_list))

@app.route('/audio/<filename>')
def serve_audio(filename):
    """Serve audio files from the audio directory."""
    import urllib.parse
    # Decode the filename in case it's URL-encoded
    decoded_filename = urllib.parse.unquote(filename)
    audio_path = AUDIO_DIR / decoded_filename
    
    print(f"[DEBUG] Serving audio: {decoded_filename}")
    print(f"[DEBUG] Full path: {audio_path}")
    print(f"[DEBUG] Exists: {audio_path.exists()}")
    
    if audio_path.exists():
        from flask import send_file  # type: ignore[reportMissingImports]
        # Detect MIME type based on file extension
        if audio_path.suffix.lower() == '.wav':
            mimetype = 'audio/wav'
        elif audio_path.suffix.lower() == '.mp3':
            mimetype = 'audio/mpeg'
        else:
            mimetype = 'audio/mpeg'  # default
        return send_file(audio_path, mimetype=mimetype)
    
    print(f"[ERROR] Audio file not found: {audio_path}")
    return 'Not found', 404

@app.route('/api/letters')
def api_letters():
    """API endpoint for letter data."""
    return jsonify(ARMENIAN_LETTERS)


# ── Vocab Audio Triage ────────────────────────────────────────────────

VOCAB_TRIAGE_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Vocab Audio Triage</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #2d3436 0%, #636e72 100%);
            min-height: 100vh;
            padding: 20px;
            color: #dfe6e9;
        }
        .container { max-width: 900px; margin: 0 auto; }
        h1 { color: white; margin-bottom: 10px; text-align: center; font-size: 2em; }
        .subtitle { text-align: center; color: #b2bec3; margin-bottom: 25px; }
        .nav { text-align: center; margin-bottom: 20px; }
        .nav a { color: #74b9ff; text-decoration: none; font-size: 0.95em; }
        .nav a:hover { text-decoration: underline; }

        .summary {
            display: flex; gap: 15px; justify-content: center; margin-bottom: 25px; flex-wrap: wrap;
        }
        .summary .stat {
            background: rgba(255,255,255,0.1); padding: 10px 20px; border-radius: 8px;
            text-align: center; min-width: 90px;
        }
        .stat .num { font-size: 1.6em; font-weight: bold; }
        .stat .label { font-size: 0.8em; color: #b2bec3; }
        .stat.good .num { color: #00b894; }
        .stat.bad .num { color: #d63031; }
        .stat.pending .num { color: #fdcb6e; }

        .word-card {
            background: rgba(255,255,255,0.08);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 20px;
            transition: all 0.2s;
        }
        .word-card:hover { background: rgba(255,255,255,0.12); }
        .word-card.rated-good { border-left: 4px solid #00b894; }
        .word-card.rated-bad { border-left: 4px solid #d63031; }
        .word-card.rated-redo { border-left: 4px solid #e17055; }
        .word-card.rated-pending { border-left: 4px solid #636e72; }

        .word-num {
            font-size: 0.85em; color: #636e72; min-width: 30px; text-align: right;
        }
        .word-armenian {
            font-size: 1.8em; font-weight: bold; font-family: 'Arial Unicode MS', sans-serif;
            min-width: 100px; color: white;
        }
        .word-info { flex: 1; }
        .word-meaning { color: #b2bec3; font-size: 0.95em; }
        .word-ipa { color: #74b9ff; font-size: 0.85em; font-family: monospace; }
        .word-note {
            font-size: 0.8em; color: #fdcb6e; margin-top: 3px; font-style: italic;
        }

        .word-actions { display: flex; gap: 6px; align-items: center; flex-wrap: wrap; }

        .play-btn {
            background: #0984e3; color: white; border: none; padding: 8px 16px;
            border-radius: 6px; cursor: pointer; font-size: 0.95em; white-space: nowrap;
        }
        .play-btn:hover { background: #74b9ff; }
        .play-btn:active { transform: scale(0.97); }
        .play-btn.playing { background: #6c5ce7; }

        .rate-btn {
            border: none; padding: 6px 12px; border-radius: 6px; cursor: pointer;
            font-size: 0.85em; transition: all 0.15s; opacity: 0.6;
        }
        .rate-btn:hover { opacity: 1; }
        .rate-btn.active { opacity: 1; transform: scale(1.05); box-shadow: 0 2px 8px rgba(0,0,0,0.3); }
        .rate-btn.good { background: #00b894; color: white; }
        .rate-btn.bad { background: #d63031; color: white; }
        .rate-btn.redo { background: #e17055; color: white; }

        .note-input {
            background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2);
            color: #dfe6e9; padding: 5px 8px; border-radius: 4px; font-size: 0.8em;
            width: 140px;
        }
        .note-input::placeholder { color: #636e72; }

        .actions-bar {
            display: flex; gap: 10px; justify-content: center; margin: 25px 0; flex-wrap: wrap;
        }
        .action-btn {
            background: #0984e3; color: white; border: none; padding: 10px 24px;
            border-radius: 8px; cursor: pointer; font-size: 0.95em;
        }
        .action-btn:hover { background: #74b9ff; }
        .action-btn.danger { background: #d63031; }
        .action-btn.danger:hover { background: #e17055; }

        .toast {
            position: fixed; bottom: 20px; right: 20px; background: #00b894; color: white;
            padding: 12px 24px; border-radius: 8px; display: none; z-index: 100;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        }
        .toast.error { background: #d63031; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Vocab Audio Triage</h1>
        <p class="subtitle">Listen, rate, and flag vocabulary audio for quality</p>
        <div class="nav"><a href="/">← Back to Letter Cards</a></div>

        <div class="summary" id="summary"></div>

        <div class="actions-bar">
            <button class="action-btn" onclick="playAll()">▶ Play All</button>
            <button class="action-btn" onclick="playUnrated()">▶ Play Unrated</button>
            <button class="action-btn" onclick="saveTriage()">💾 Save Ratings</button>
        </div>

        <div id="wordList"></div>

        <div class="actions-bar">
            <button class="action-btn" onclick="saveTriage()">💾 Save Ratings</button>
        </div>
    </div>

    <div class="toast" id="toast"></div>

    <script>
        const vocab = {{ vocab_json | safe }};
        const triage = {{ triage_json | safe }};
        let currentAudio = null;
        let playQueue = [];
        let playIdx = -1;

        function renderList() {
            const list = document.getElementById('wordList');
            list.innerHTML = vocab.map((v, i) => {
                const rating = triage[v.file] || {};
                const status = rating.status || 'pending';
                const note = rating.note || '';
                return `
                <div class="word-card rated-${status}" id="card-${i}">
                    <div class="word-num">${i + 1}</div>
                    <div class="word-armenian">${v.word}</div>
                    <div class="word-info">
                        <div class="word-meaning">${v.meaning}</div>
                        <div class="word-ipa">/${v.ipa}/</div>
                        ${note ? `<div class="word-note">${note}</div>` : ''}
                    </div>
                    <div class="word-actions">
                        <button class="play-btn" id="play-${i}" onclick="playWord(${i})">▶</button>
                        <button class="rate-btn good ${status==='good'?'active':''}" onclick="rate(${i},'good')">✓ Good</button>
                        <button class="rate-btn bad ${status==='bad'?'active':''}" onclick="rate(${i},'bad')">✗ Bad</button>
                        <button class="rate-btn redo ${status==='redo'?'active':''}" onclick="rate(${i},'redo')">↻ Redo</button>
                        <input class="note-input" placeholder="note..." value="${note}" onchange="setNote(${i}, this.value)">
                    </div>
                </div>`;
            }).join('');
            updateSummary();
        }

        function updateSummary() {
            const counts = { good: 0, bad: 0, redo: 0, pending: 0 };
            vocab.forEach(v => {
                const s = (triage[v.file] || {}).status || 'pending';
                counts[s] = (counts[s] || 0) + 1;
            });
            document.getElementById('summary').innerHTML = `
                <div class="stat good"><div class="num">${counts.good}</div><div class="label">Good</div></div>
                <div class="stat bad"><div class="num">${counts.bad}</div><div class="label">Bad</div></div>
                <div class="stat"><div class="num">${counts.redo}</div><div class="label">Redo</div></div>
                <div class="stat pending"><div class="num">${counts.pending}</div><div class="label">Pending</div></div>
                <div class="stat"><div class="num">${vocab.length}</div><div class="label">Total</div></div>
            `;
        }

        function playWord(idx) {
            if (currentAudio) { currentAudio.pause(); currentAudio = null; }
            const btn = document.getElementById('play-' + idx);
            document.querySelectorAll('.play-btn').forEach(b => { b.classList.remove('playing'); b.textContent = '▶'; });
            btn.classList.add('playing');
            btn.textContent = '⏸';

            const audio = new Audio('/vocab-audio/' + encodeURIComponent(vocab[idx].file));
            currentAudio = audio;
            audio.onended = () => {
                btn.classList.remove('playing');
                btn.textContent = '▶';
                currentAudio = null;
                // Continue play queue
                if (playQueue.length > 0 && playIdx >= 0) {
                    playIdx++;
                    if (playIdx < playQueue.length) {
                        setTimeout(() => playWord(playQueue[playIdx]), 400);
                    } else {
                        playQueue = []; playIdx = -1;
                    }
                }
            };
            audio.onerror = () => {
                btn.classList.remove('playing'); btn.textContent = '▶';
                showToast('Error playing ' + vocab[idx].file, true);
            };
            audio.play().catch(() => { btn.classList.remove('playing'); btn.textContent = '▶'; });

            // Scroll into view
            document.getElementById('card-' + idx).scrollIntoView({ behavior: 'smooth', block: 'center' });
        }

        function playAll() {
            playQueue = vocab.map((_, i) => i);
            playIdx = 0;
            playWord(playQueue[0]);
        }

        function playUnrated() {
            playQueue = vocab.map((v, i) => ({ i, s: (triage[v.file] || {}).status || 'pending' }))
                .filter(x => x.s === 'pending').map(x => x.i);
            if (playQueue.length === 0) { showToast('All rated!'); return; }
            playIdx = 0;
            playWord(playQueue[0]);
        }

        function rate(idx, status) {
            const file = vocab[idx].file;
            if (!triage[file]) triage[file] = {};
            // Toggle off if clicking same status
            if (triage[file].status === status) {
                triage[file].status = 'pending';
            } else {
                triage[file].status = status;
            }
            renderList();
            // Auto-save
            saveTriage(true);
        }

        function setNote(idx, note) {
            const file = vocab[idx].file;
            if (!triage[file]) triage[file] = {};
            triage[file].note = note;
        }

        function saveTriage(silent) {
            // Include notes from inputs
            document.querySelectorAll('.note-input').forEach((input, i) => {
                const file = vocab[i].file;
                if (!triage[file]) triage[file] = {};
                triage[file].note = input.value;
            });

            fetch('/api/vocab-triage', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(triage)
            }).then(r => r.json()).then(data => {
                if (!silent) showToast('Saved!');
            }).catch(() => showToast('Save failed', true));
        }

        function showToast(msg, error) {
            const t = document.getElementById('toast');
            t.textContent = msg;
            t.className = 'toast' + (error ? ' error' : '');
            t.style.display = 'block';
            setTimeout(() => t.style.display = 'none', 2000);
        }

        renderList();
    </script>
</body>
</html>
"""


@app.route('/vocab')
def vocab_triage():
    """Vocab audio triage page."""
    vocab_data = []
    for i, item in enumerate(VOCAB_LIST, 1):
        word = item['word']
        vocab_data.append({
            'word': word,
            'meaning': item['meaning'],
            'ipa': armenian_to_ipa(word),
            'file': f"{i:03d}.wav",
        })

    triage_data = load_triage()
    return render_template_string(
        VOCAB_TRIAGE_TEMPLATE,
        vocab_json=json.dumps(vocab_data, ensure_ascii=False),
        triage_json=json.dumps(triage_data, ensure_ascii=False),
    )


@app.route('/vocab-audio/<filename>')
def serve_vocab_audio(filename):
    """Serve vocab audio WAV files."""
    import urllib.parse
    from flask import send_file  # type: ignore[reportMissingImports]
    decoded = urllib.parse.unquote(filename)
    audio_path = VOCAB_AUDIO_DIR / decoded
    if audio_path.exists():
        return send_file(audio_path, mimetype='audio/wav')
    return 'Not found', 404


@app.route('/api/vocab-triage', methods=['POST'])
def api_save_triage():
    """Save vocab audio triage ratings."""
    data = request.get_json()
    if data is None:
        return jsonify({'error': 'Invalid JSON'}), 400
    save_triage(data)
    return jsonify({'ok': True, 'count': len(data)})


# ── Audio Comparison Page ─────────────────────────────────────────────

COMPARISON_TEMPLATE = r"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Audio Processing Comparison</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #1a1a2e; color: #eee; padding: 20px; min-height: 100vh;
        }
        .container { max-width: 1000px; margin: 0 auto; }
        h1 { text-align: center; margin-bottom: 5px; }
        .subtitle { text-align: center; color: #888; margin-bottom: 20px; }
        .nav { text-align: center; margin-bottom: 20px; }
        .nav a { color: #74b9ff; text-decoration: none; margin: 0 10px; }

        .group { margin-bottom: 30px; }
        .group-title {
            font-size: 1.2em; color: #fdcb6e; margin-bottom: 10px;
            padding-bottom: 5px; border-bottom: 1px solid #333;
        }
        .sample {
            display: flex; align-items: center; gap: 12px; padding: 10px 15px;
            background: rgba(255,255,255,0.05); border-radius: 8px; margin-bottom: 6px;
            transition: background 0.2s;
        }
        .sample:hover { background: rgba(255,255,255,0.1); }
        .sample.favorite { border-left: 3px solid #00b894; background: rgba(0,184,148,0.1); }
        .sample-num { color: #636e72; min-width: 30px; text-align: right; font-size: 0.85em; }
        .sample-name { flex: 1; font-size: 0.95em; }
        .sample-desc { color: #888; font-size: 0.8em; }
        .sample-size { color: #636e72; font-size: 0.8em; min-width: 60px; text-align: right; }

        .play-btn {
            background: #0984e3; color: white; border: none; padding: 6px 16px;
            border-radius: 5px; cursor: pointer; font-size: 0.9em;
        }
        .play-btn:hover { background: #74b9ff; }
        .play-btn.playing { background: #6c5ce7; }

        .fav-btn {
            background: none; border: 1px solid #636e72; color: #636e72;
            padding: 4px 10px; border-radius: 5px; cursor: pointer; font-size: 0.85em;
        }
        .fav-btn:hover { border-color: #00b894; color: #00b894; }
        .fav-btn.active { background: #00b894; color: white; border-color: #00b894; }

        .legend {
            background: rgba(255,255,255,0.05); border-radius: 8px; padding: 15px;
            margin-bottom: 20px; font-size: 0.85em; color: #b2bec3;
        }
        .legend h3 { color: #dfe6e9; margin-bottom: 8px; }
        .legend-item { margin: 3px 0; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Audio Processing Comparison</h1>
        <p class="subtitle">Compare espeak-ng settings &amp; FFmpeg post-processing chains</p>
        <div class="nav">
            <a href="/">Letter Cards</a>
            <a href="/vocab">Vocab Triage</a>
        </div>

        <div class="legend">
            <h3>Processing Chains</h3>
            <div class="legend-item"><strong>01-08:</strong> espeak-ng parameter tuning (speed, pitch, gap)</div>
            <div class="legend-item"><strong>09-15:</strong> FFmpeg post-processing on #08 (EQ, reverb, compression, pitch shift, vibrato)</div>
            <div class="legend-item"><strong>20-23:</strong> Longer word test (երկou) with best post-processing chains</div>
        </div>

        <div id="groups"></div>
    </div>

    <script>
        const files = {{ files_json | safe }};
        const favorites = JSON.parse(localStorage.getItem('audio_comp_favs') || '{}');
        let currentAudio = null;

        const groups = [
            { title: 'MMS - Ultra Smooth (5-pass denoise)', filter: f => f.name.match(/^105/) },
            { title: 'MMS - Smooth Noise Reduced (3-pass denoise)', filter: f => f.name.match(/^100/) },
            { title: 'MMS - Warm Pitch (subtle downward shift)', filter: f => f.name.match(/^95/) },
            { title: 'MMS - Saturation (analog warmth)', filter: f => f.name.match(/^90/) },
            { title: 'MMS - Resonant (presence boost)', filter: f => f.name.match(/^85/) },
            { title: 'MMS - Warm Enhanced (low-mid boost)', filter: f => f.name.match(/^80/) },
            { title: 'MMS Western Armenian - Smooth Enhanced (0.90x)', filter: f => f.name.match(/^75/) },
            { title: 'MMS Western Armenian - Clarity Enhanced (0.90x)', filter: f => f.name.match(/^70/) },
            { title: 'MMS Western Armenian - Slightly Slower (0.90x speed)', filter: f => f.name.match(/^6\d.*slow/) },
            { title: 'MMS Western Armenian - Natural (original)', filter: f => f.name.match(/^6\d.*mms/) && !f.name.includes('slow') },
            { title: 'Coqui XTTS v2 (multilingual neural)', filter: f => f.name.match(/^4\d.*xtts/) },
            { title: 'Bark Neural TTS (CPU)', filter: f => f.name.match(/^3\d.*bark/) },
            { title: 'espeak-ng Tuning (մարդ = person)', filter: f => f.name.match(/^0[1-8]/) },
            { title: 'FFmpeg Post-Processing (մարդ)', filter: f => f.name.match(/^(09|1[0-5])/) },
            { title: 'Longer Word Test (երկou = two)', filter: f => f.name.match(/^2/) },
        ];

        const descriptions = {
            '01': 'Default: speed 130',
            '02': 'Slower: speed 100',
            '03': 'Very slow: speed 80',
            '04': 'Slow + low pitch (35)',
            '05': 'Slow + high pitch (70)',
            '06': 'Slow + word gap 10',
            '07': 'Very slow + loud (amp 200)',
            '08': 'Balanced: speed 90, pitch 40',
            '09': 'EQ warm (cut highs, boost mids)',
            '10': 'Slight reverb',
            '11': 'EQ + reverb',
            '12': 'EQ + compressor + reverb (full chain)',
            '13': 'Deeper voice + EQ + reverb',
            '14': 'Low-pass filter (4kHz cutoff)',
            '15': 'Vibrato + EQ + reverb + normalize (humanize)',
            '20': 'Balanced (base for processing)',
            '21': 'Full chain (EQ+comp+reverb)',
            '22': 'Humanize (vibrato+EQ+reverb+norm)',
            '23': 'Deeper + EQ + reverb',
            '30': 'Bark neural: մարդ (person)',
            '31': 'Bark neural: հայ (Armenian)',
            '32': 'Bark neural: երկou (two)',
            '40': 'XTTS v2: մարդ (person)',
            '41': 'XTTS v2: հայ (Armenian)',
            '42': 'XTTS v2: երկou (two)',
            '60': 'MMS hyw: մարդ (person)',
            '61': 'MMS hyw: հայ (Armenian)',
            '62': 'MMS hyw: երկու (two)',
            '63': 'MMS hyw: տուն (house)',
            '64': 'MMS hyw: մեծ (big)',
            '65': 'MMS hyw 0.90x: մարդ (person)',
            '66': 'MMS hyw 0.90x: հայ (Armenian)',
            '67': 'MMS hyw 0.90x: երկու (two)',
            '68': 'MMS hyw 0.90x: տուն (house)',
            '69': 'MMS hyw 0.90x: մեծ (big)',
            '70': 'Clarity Enhanced: մարդ (person)',
            '71': 'Clarity Enhanced: հայ (Armenian)',
            '72': 'Clarity Enhanced: երկու (two)',
            '73': 'Clarity Enhanced: տուն (house)',
            '74': 'Clarity Enhanced: մեծ (big)',
            '75': 'Smooth Enhanced: մարդ (person)',
            '76': 'Smooth Enhanced: հայ (Armenian)',
            '77': 'Smooth Enhanced: երկու (two)',
            '78': 'Smooth Enhanced: տուն (house)',
            '79': 'Smooth Enhanced: մեծ (big)',
            '80': 'Warm Enhanced: մարդ (person)',
            '81': 'Warm Enhanced: հայ (Armenian)',
            '82': 'Warm Enhanced: երկու (two)',
            '83': 'Warm Enhanced: տուն (house)',
            '84': 'Warm Enhanced: մեծ (big)',
            '85': 'Resonant: մարդ (person)',
            '86': 'Resonant: հայ (Armenian)',
            '87': 'Resonant: երկու (two)',
            '88': 'Resonant: տուն (house)',
            '89': 'Resonant: մեծ (big)',
            '90': 'Saturation: մարդ (person)',
            '91': 'Saturation: հայ (Armenian)',
            '92': 'Saturation: երկու (two)',
            '93': 'Saturation: տուն (house)',
            '94': 'Saturation: մեծ (big)',
            '95': 'Warm Pitch: մարդ (person)',
            '96': 'Warm Pitch: հայ (Armenian)',
            '97': 'Warm Pitch: երկու (two)',
            '98': 'Warm Pitch: տուն (house)',
            '99': 'Warm Pitch: մեծ (big)',
            '100': 'Smooth Noise Reduced: մարդ (person)',
            '101': 'Smooth Noise Reduced: հայ (Armenian)',
            '102': 'Smooth Noise Reduced: երկու (two)',
            '103': 'Smooth Noise Reduced: տուն (house)',
            '104': 'Smooth Noise Reduced: մեծ (big)',
            '105': 'Ultra Smooth: մարդ (person)',
            '106': 'Ultra Smooth: հայ (Armenian)',
            '107': 'Ultra Smooth: երկու (two)',
            '108': 'Ultra Smooth: տուն (house)',
            '109': 'Ultra Smooth: մեծ (big)',
        };

        function render() {
            const container = document.getElementById('groups');
            container.innerHTML = groups.map(g => {
                const items = files.filter(g.filter);
                if (!items.length) return '';
                return `<div class="group">
                    <div class="group-title">${g.title}</div>
                    ${items.map(f => {
                        const num = f.name.substring(0, 2);
                        const desc = descriptions[num] || '';
                        const isFav = favorites[f.name];
                        const kb = Math.round(f.size / 1024);
                        return `<div class="sample ${isFav ? 'favorite' : ''}" id="s-${f.name}">
                            <div class="sample-num">${num}</div>
                            <button class="play-btn" onclick="play('${f.name}', this)">▶</button>
                            <div class="sample-name">
                                ${f.name}<br>
                                <span class="sample-desc">${desc}</span>
                            </div>
                            <div class="sample-size">${kb}KB</div>
                            <button class="fav-btn ${isFav ? 'active' : ''}" onclick="toggleFav('${f.name}')">
                                ${isFav ? '★' : '☆'}
                            </button>
                        </div>`;
                    }).join('')}
                </div>`;
            }).join('');
        }

        function play(name, btn) {
            if (currentAudio) { currentAudio.pause(); }
            document.querySelectorAll('.play-btn').forEach(b => { b.classList.remove('playing'); b.textContent = '▶'; });
            btn.classList.add('playing'); btn.textContent = '⏸';
            const audio = new Audio('/comp-audio/' + encodeURIComponent(name));
            currentAudio = audio;
            audio.onended = () => { btn.classList.remove('playing'); btn.textContent = '▶'; };
            audio.onerror = () => { btn.classList.remove('playing'); btn.textContent = '▶'; };
            audio.play();
        }

        function toggleFav(name) {
            favorites[name] = !favorites[name];
            localStorage.setItem('audio_comp_favs', JSON.stringify(favorites));
            render();
        }

        render();
    </script>
</body>
</html>
"""


@app.route('/compare')
def audio_comparison():
    """Audio processing comparison page."""
    files = []
    if COMP_AUDIO_DIR.exists():
        for f in sorted(COMP_AUDIO_DIR.glob('*.wav')):
            files.append({'name': f.name, 'size': f.stat().st_size})
    return render_template_string(
        COMPARISON_TEMPLATE,
        files_json=json.dumps(files),
    )


@app.route('/comp-audio/<filename>')
def serve_comp_audio(filename):
    """Serve comparison audio WAV files."""
    import urllib.parse
    from flask import send_file  # type: ignore[reportMissingImports]
    decoded = urllib.parse.unquote(filename)
    audio_path = COMP_AUDIO_DIR / decoded
    if audio_path.exists():
        return send_file(audio_path, mimetype='audio/wav')
    return 'Not found', 404


if __name__ == '__main__':
    print(f"Starting Armenian Letter Cards Viewer...")
    print(f"Letter audio: {AUDIO_DIR} (exists={AUDIO_DIR.exists()})")
    print(f"Vocab audio:  {VOCAB_AUDIO_DIR} (exists={VOCAB_AUDIO_DIR.exists()})")
    if AUDIO_DIR.exists():
        print(f"  Letter audio files: {len(list(AUDIO_DIR.glob('*.mp3')))} mp3")
    if VOCAB_AUDIO_DIR.exists():
        print(f"  Vocab audio files:  {len(list(VOCAB_AUDIO_DIR.glob('*.wav')))} wav")
    if COMP_AUDIO_DIR.exists():
        print(f"  Comparison files:   {len(list(COMP_AUDIO_DIR.glob('*.wav')))} wav")
    print(f"\n[WEB] Letter Cards:    http://localhost:5001")
    print(f"[WEB] Vocab Triage:    http://localhost:5001/vocab")
    print(f"[WEB] Audio Compare:   http://localhost:5001/compare")
    app.run(debug=True, port=5001, use_reloader=False)
