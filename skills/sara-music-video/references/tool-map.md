# Tool map: every script, where it lives, and when to reach for it

**The continuity scripts** (`join_check.py`, `clip_screen.py`, `story_sheets.py`, `join_judge.py` and the chaining kit: `chain_frame.py`, `seam_blend.py`, `framecheck.py` and `regioncheck.py`, on `chainlib.py`) are in `../shot-continuity/scripts/`. Copy a tool into your video's `tools/` folder and point it at that video's storyboard and stems (`--sb` names another board).

**`scripts/board_lint.py`** is the board gate's mechanical check (`storyboard-spec.md` §3): stdlib only. It reads older boards through field aliases; a board written in the spec's field names gets every check.

**The skill's `scripts/`:**
- **The base** is the pipeline the later videos were built on, with their QA tools and casting helpers.
- **Encoding and fonts:** the scripts were written on a Mac and encode on the GPU (Apple VideoToolbox) at low priority. `scripts/venc.py` gives the ffmpeg arguments for the machine's own GPU encoder where there is one, and x264 otherwise. Fonts go through `scripts/fonts.py`. `scripts/fal_env.py` reads `FAL_KEY` from the environment or a login shell.
- **Not in this repo, all optional:** sync.so (a lip-sync service, routes B and C in generation-playbook §5), the Codex command-line tool (the two vision judges and `gpt_edit.py`), the Grok command-line tool (small image edits) and the Apple super-resolution tool (macOS 26, generation-playbook §7). Nothing in `TESTED.md` needed them except the judges.
- **Setup:** copy the whole `scripts/` folder into your video as `tools/` (several scripts import `lipscore.py`, `fonts.py`, `venc.py` or `fal_env.py` and need `models/` beside them). The scripts assume the project root is `tools/..`, with `storyboard.json`, `words.json`, `gen/stills/`, `gen/clips/`, the song, and the stems under `sep_wav/htdemucs/<name>/`. Run each script once on a real shot before relying on it.
- **Needs:** Python 3.10 or newer (tested on 3.12 and 3.14) and the repo's `requirements.txt` (it pins `mediapipe<1.0` and `av<19`); the Higgsfield command-line tool for `gen.py`; a fal.ai key for `falgen.py`; Demucs for the stems. Out of Office's own board predates the spec's field names (no `type`, `voice`, `look`, `set`), so the lip and casting scripts stop on it; `out-of-office/tools/build_jobs.py` and `edit.py` read that older format, not the spec's.
- **Worked example:** `out-of-office/tools/build_jobs.py`, `out-of-office/tools/edit.py` and `out-of-office/tools/captions.py` contain Out of Office's per-shot content. Replace the dicts; keep the machinery.

## Scripts by stage

In this skill's `scripts/` unless the path says otherwise.

| Stage | Script | What it does | Notes |
|---|---|---|---|
| Analysis | `analyze.py` | tempo, bar grid, sections → `timing.json` | |
| | `transcribe.py` | faster-whisper word times | |
| | `align_lines.py` | lyric lines → timed lines | |
| Casting | `casting_scan.py` | **the standard first pass:** per-line timbre (cross-song references) + pitch hint → `casting.json` | |
| | `casting_clip.py` | passage cards (control first) + audio, one clip for the director's ear | |
| | `transcribe_gaps.py` | windowed Whisper for the stretches the full pass dropped | |
| | `voice_id.py` | same-song REFS per storyboard shot (older; still fine once a storyboard exists) | |
| Storyboard | `cut_audit.py` | phrase-safe cuts: flags lip shots that cut mid-word or mid-phrase | |
| Stills | `contact.py` | contact sheet | |
| | `outfit_audit.py` | one row per look, anchor still first; `--clips` adds each clip's last frame | the outfit-drift gate after every stills round and before the animatic |
| Video | `gen.py` | Higgsfield CLI runner (paid; 4 concurrent; resumes; the same file as `../shot-continuity/scripts/gen.py`: upload cache keyed on content, `end` frame key) | |
| | `falgen.py` + `fal_env.py` | fal runner (paid; resumes; upload cache keyed on path + mtime) | |
| QA (clips) | `clipsheet.py` | start/mid/end frames of the used window | |
| | `carflow.py` | signed sideways flow of a region | |
| Lip-sync | `lip_slices.py` | energy-gated vocal slices, `lip_jobs.json` | |
| | `masked_slice.py` | Whisper-word-masked slice (older) | |
| | `pick_lip_takes.py` | scores the Wan 2.7 takes (2 per shot) and keeps the better one | |
| | `lip_v2v.py` | route B prep: the word-masked slice with a run-up, the 30 fps base window (GPU encode), the sync.so job, offsets | the vocal stem is found automatically |
| | `v2v_prep.py` | route C prep for a flagged Wan shot | |
| | `lipscore.py` | mouth opening vs vocal loudness (MediaPipe; `models/face_landmarker.task`) | |
| | `lipsync_audit.py` | Wan visual lag over ±600 ms → `gen/lip_offsets.json`; flags mouthing on non-lip shots | |
| | `lip_lag.py` | **the lag on rendered segments** (sub-frame, lag > 0 means the mouth trails) | |
| | `lip_retime.py` | smooth re-time only (0.75–1.25×, blended frames) | |
| | `glassfix.py` | put back a prop sync.so erased | size-agnostic |
| Edit | `out-of-office/tools/edit.py` + `out-of-office/tools/captions.py` | the editor (see below) | |
| | `out-of-office/tools/more/reels.py` | 9:16 re-frame with face-aware crops and the captions moved up; `FIT` and `CROPX` per shot; `VOCAL_END` fades the vocal stem out at a join | |
| | `out-of-office/tools/more/shorts.py` | the 9:16 shorts, one continuous stretch each (`CLIPS`, `CROPX`, `FIT`) | |
| Shared | `fonts.py` | Windows font names → faces on this machine; `truetype()`, `font_path()` | |
| | `venc.py` | ffmpeg H.264 arguments: the machine's GPU encoder where there is one, x264 otherwise | |

## The editor: which features live where
`out-of-office/tools/edit.py` is Out of Office's editor, and the only editor in this repo. It cuts the clips to the beat-aligned storyboard, burns in the captions, flashes the drops (`DROPS`) and adds the song; stills stand in for missing clips in either mode, and a black frame where there is no still; `--draft` is the faster encode.

**Per video, set `SONG`, the end card and `OUT_NAME` at the top of `edit.py`, and empty its per-shot tables** (`DROPS` and `SPLIT` there; `SYSTEM`, `HUMAN` and `HOOK` in `captions.py`). This skill's scripts find the vocal stem automatically.

**The later videos' editors have more** (their per-shot dicts are listed in generation-playbook §8). Those editors are not in this repo: when a video needs one of these, build it into your `edit.py` under the same name.

| Feature | Why you'd need it |
|---|---|
| Shared timing helpers: `pick_clip()`, `clip_len()`, `timing()`, `used_range()` | One source of truth for where each shot starts and which seconds of its clip the cut plays |
| Lip clips may overrun: `tpad` after decode | A nudge that skips into the clip needs its last frame held |
| Super-resolution sources (and skip `unsharp` on them) | Sharper 1080p from 720p Kling |
| Band reverse: `BAND_REVERSE` | Reverse only part of the frame, warped onto a moving camera |
| Joining 5 s clips at any size: `JOIN` | Shots longer than 5 s |
| Documentary grade, glitch-out: `DOCGRADE`, `GLITCH_OUT` | Look effects |

They also have: a GPU encode with `-g 60`; `--animatic` (with a label per shot), `--only` and `--mux`; the frame-exact trim and the frame-exact lip seek; `LIP_NUDGE` (whole frames at the clip's own rate); `WINDOW`, `REVERSE`, `OVERRIDE`, a clip `SPLIT` (with a tail; Out of Office's own `SPLIT` only splits a caption), `INSERT` and `LIPTAIL`; `SFX` from the caption tables; and `-framerate 30` on still inputs.

## Project-specific tools (look before rewriting)
- `out-of-office/tools/`: Out of Office's own build. `more/` holds its reel and shorts cuts, its runner for stills through ChatGPT images (`gpt_edit.py`) and its own copies of the analysis, contact-sheet and fal scripts; `fixes/` holds one-off repairs to single shots, named by shot ID (garbled text, a logo, a sign).
