"""Re-transcribe the stretches Whisper skipped on the full pass (music-heavy choruses, bridges), one window at a time.
The full pass (transcribe.py) drops whole sections under dense music; windowed passes recover them.
Usage: GAP_PROMPT="a few lyric words from the gap" python tools/transcribe_gaps.py <vocals.wav> 127-141 183-213
Prints absolute song times; paste them into lines_timed.json for lines align_lines.py marked GUESS."""
import os, sys, json
from faster_whisper import WhisperModel
import soundfile as sf
if len(sys.argv) < 3 or sys.argv[1] in ("-h", "--help"):
    sys.exit(__doc__)
m = WhisperModel("small.en", device="cpu", compute_type="int8")
y, sr = sf.read(sys.argv[1])
for arg in sys.argv[2:]:
    a, b = map(float, arg.split("-"))
    seg = y[int(a*sr):int(b*sr)].mean(axis=1) if y.ndim > 1 else y[int(a*sr):int(b*sr)]
    sf.write("_gap.wav", seg, sr)
    s, _ = m.transcribe("_gap.wav", word_timestamps=True, vad_filter=False, beam_size=5, condition_on_previous_text=False,
                        initial_prompt=(os.environ.get("GAP_PROMPT") or None))
    for x in s:
        print(f"{a + x.start:7.2f}-{a + x.end:7.2f}  {x.text.strip()}", flush=True)
