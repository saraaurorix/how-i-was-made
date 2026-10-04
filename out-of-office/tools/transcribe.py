"""Word-level transcript of the song (local Whisper), saved as JSON for lyric alignment.

Usage: python transcribe.py song.mp3 words.json
The first run downloads Whisper's small.en model (about 0.5 GB). It is English-only: use "small" for another language.
"""
import json
import sys

if len(sys.argv) < 3 or sys.argv[1] in ("-h", "--help"):
    sys.exit(__doc__)

from faster_whisper import WhisperModel

model = WhisperModel("small.en", device="cpu", compute_type="int8")
segments, info = model.transcribe(sys.argv[1], word_timestamps=True, vad_filter=False, beam_size=5,
                                  condition_on_previous_text=False)
out = []
for s in segments:
    words = [{"w": w.word.strip(), "s": round(w.start, 2), "e": round(w.end, 2)} for w in (s.words or [])]
    out.append({"s": round(s.start, 2), "e": round(s.end, 2), "text": s.text.strip(), "words": words})
    print(f"{s.start:7.2f}-{s.end:7.2f}  {s.text.strip()}", flush=True)
json.dump(out, open(sys.argv[2], "w"), indent=1)
