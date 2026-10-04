# What was tested

Every script in this repo was run before it was published, on real footage wherever that costs nothing. This is the record: what ran, on what, and what was not run and why.

- **Machine:** an Apple Silicon Mac, macOS, Python 3.12. The install and the main steps were repeated on Python 3.14.
- **A clean install:** `requirements.txt` was installed into a brand-new environment and the scripts were run again from there. That is how two version pins were found (see the bottom of this page).
- **Windows and Linux:** not tested. Out of Office's five scripts use only x264 and the font fallback, so they should run anywhere Python and ffmpeg do. The skills' scripts call `nice` and other POSIX functions in places: macOS and Linux only as written.
- **Nothing here was run against a paid service.** The job runners were checked up to the point where they would submit.

## out-of-office/tools

| Script | Result | How it was tested |
|---|---|---|
| `build_jobs.py` | **Pass** | Run on the repo's `storyboard.json`: the two prompt files it writes are byte-identical to the ones in the repo |
| `captions.py`, `edit.py` | **Pass** | The film's first 12 shots cut from the real clips (one shot deliberately left as a still), with the song: 44 s of 1080p, all three caption styles and the end card drawn correctly with substitute fonts on a Mac |
| `transcribe.py` | **Pass** | A 20-second stretch of the song: every word timed |
| `more/analyze.py` | **Pass** | Run on the song: tempo, bars and sections equal to the repo's `timing.json` |
| `more/contact.py` | **Pass** | A contact sheet of 12 stills (it now creates its output folder) |
| `gen.py` | **Not run** | Needs the Higgsfield tool, signed in, with credits. Checked instead: the commands and flags it uses exist in the current tool (1.1.26), and all five model names in the job files are still listed |
| `more/falgen.py` | **Not run** | Needs a fal.ai key and paid jobs |
| `more/gpt_edit.py` | **Not run** | Needs the Codex command-line tool signed in to a ChatGPT plan |
| `more/reels.py`, `more/shorts.py`, `fixes/*.py` | **Not runnable from this repo** | They work on the finished film and its frames, which are not here. They compile; they are published to be read |

## skills/sara-music-video/scripts

Tested on a copy of a later video's project (its storyboard, stems, clips and lip-sync takes), because these scripts expect the newer board format: rows with `type`, `voice`, `look` and a place, as in `skills/sara-music-video/references/storyboard-spec.md`. Out of Office's board predates that format, so `lip_slices.py`, `lipsync_audit.py` and `lip_lag.py` stop on it with a missing `type`.

| Script | Result | Notes |
|---|---|---|
| `align_lines.py` | **Pass** | 92 lyric lines pinned to word times |
| `analyze.py` | **Pass** | Same output as Out of Office's `timing.json` |
| `board_lint.py` | **Pass** | Run on two boards, including Out of Office's |
| `carflow.py` | **Pass** | |
| `casting_scan.py` | **Pass** | Needs a vocal stem and a reference stem with lines marked by singer |
| `casting_clip.py` | **Pass** | A 16-second listening clip with title cards |
| `clipsheet.py`, `contact.py` | **Pass** | Sheets checked by eye |
| `cut_audit.py` | **Pass** | Reads `type` and `voice` on the rows; without them it says it checked nothing |
| `lipscore.py`, `lip_lag.py`, `lipsync_audit.py` | **Pass** | Mouth opening against the vocal; need the face model (included) and a vocal stem |
| `lip_slices.py`, `masked_slice.py` | **Pass** | Slices identical to the ones used in production |
| `lip_retime.py`, `lip_v2v.py`, `v2v_prep.py` | **Pass** | Each encodes video. `v2v_prep.py` was also run with `VENC=libx264` to prove the fallback encoder |
| `pick_lip_takes.py` | **Pass** | Picked the same takes as in production |
| `glassfix.py` | **Pass** | Output frames identical to the production result |
| `outfit_audit.py` | **Pass** | Needs `look`, `still` and `still_file` on the rows |
| `transcribe.py`, `transcribe_gaps.py` | **Pass** | Local Whisper |
| `voice_id.py` | **Pass** | Its reference times are examples: edit them for your song |
| `fal_env.py` | **Pass** | Import only: the branch that reads a real key was not exercised |
| `gen.py`, `falgen.py` | **Not run** | Paid. Each was run on a job whose output already existed, which exercises the resume path only |
| `fonts.py`, `venc.py` | **Pass** | Font fallback checked with no fonts available; encoder checked on VideoToolbox and on x264 |

Stems are made with Demucs (`pip install demucs`, then `python -m demucs --two-stems vocals -o sep song.mp3`). It is not in `requirements.txt` because it brings PyTorch with it.

## skills/shot-continuity/scripts

Tested on a copy of a later video's project: a 75-second stretch of a cut, its storyboard, a dozen clips and stills. Each script was run before and after it was cleaned for publication and the outputs compared.

| Script | Result | Notes |
|---|---|---|
| `chainlib.py`, `chain_frame.py` | **Pass** | The saved frame is identical before and after |
| `framecheck.py`, `regioncheck.py` | **Pass** | |
| `seam_blend.py` | **Pass** | On VideoToolbox and on x264. It now checks there are frames to blend with before it touches a clip |
| `story_sheets.py` | **Pass** | On 25 fps and 30 fps cuts (it used to assume 25) |
| `join_check.py` | **Pass** | 19 joins from a cut and 19 from stills. Its side check is tuned to Sara and Kevin: change the two finders for your own cast |
| `face_sheet.py` | **Pass** | Same tuning |
| `clip_screen.py` | **Pass** | The frame strips; and the vision judge on two clips |
| `join_judge.py` | **Pass** | The vision judge on two cuts. The second "confirm" look was switched off for the test |
| `gen.py` | **Not run** | Paid. Run against a stand-in for the Higgsfield tool: the upload cache, the end-frame option and skip-if-done all behaved |

The two judges (`clip_screen.py --judge`, `join_judge.py`) call the Codex command-line tool, signed in to a ChatGPT plan. Any command-line tool that can look at an image and answer in text can be swapped in.

The chaining tools assume an editor that plays every frame of a clip once, at 25 frames a second, from a start offset per shot (`WINDOW`). Out of Office's editor runs at 30 fps and picks its own start offset (40% into the spare length of a longer clip; `out-of-office/README.md`), so these tools' frame numbers do not describe an Out of Office cut: they came from the later videos. Give `join_check.py` and `story_sheets.py` the cut's rate with `--fps`.

## What a clean install found

Installing the newest version of everything broke two things, so `requirements.txt` holds them back:

- **MediaPipe 1.0** stopped inside the face-landmark call on macOS. Held below 1.0 (tested on 0.10.35).
- **PyAV 19** breaks audio loading in faster-whisper 1.2.1. Held below 19 (tested on 18.1).

With those two pins, the scripts above ran from a new environment made by the commands in the README.

## A stranger's test

After the tests above, a second reader who had never seen the project cloned the repo, followed only its documents, and cut a 23-second film of six shots with `edit.py` (own song, own storyboard, own stills and clips), with no system ffmpeg, no Higgsfield tool and no keys on the machine. What stopped them, all fixed since: `analyze.py` crashed on a song shorter than 14 bars; the song's filename was given three ways; clips and stills named any other way than `<id>.mp4` and `<id>.png` fell back to black frames without a word; the skill's `contact.py` could not write into a new folder; `chain_frame.py` reported success and wrote nothing when a shot ran past its clip; a skill script copied on its own lost its helpers; `cp -R … ~/.claude/skills/` failed when that folder did not exist. The documents now say where a new project lives, which per-shot tables to empty, and that the editor cuts at 30 fps while the chaining tools assume 25. What that reader could not run is the same list as above: the paid job runners and the two judges.
