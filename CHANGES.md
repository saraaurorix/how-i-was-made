# What differs from the files on the director's machine

This repo is the production as it was used, with these changes. Nothing else was touched.

## Left out
- Pictures, clips, audio and the reference pictures.
- Upload caches, run logs and working notes (they hold local paths, account details and spend).
- From the skills: the documents that are private history (the director's own messages, the build-by-build record, price lists, machine setup), and the scripts that drive a website from a browser.
- From the skills' scripts: the builders that hold another, unreleased video's storyboard, prompts and captions. The same jobs are shown here by Out of Office's own `tools/build_jobs.py`, `captions.py` and `edit.py`. One checker (`motion_scan.py`) is out because it needs an editor that is not in this repo.

## Reworded
- The skills' documents are a public edition: the director's messages are paraphrased, later videos are referred to as "a later video", and prices, accounts and private paths are gone. The method, the section numbers and the tables are as they are used.
- Comments that quoted the director or named another video.

## Changed so the scripts run on your machine
- **Fonts.** The scripts ask for Windows fonts by file name. `fonts.py` (added, in `tools/more/` and in each skill's `scripts/`) finds the closest face on a Mac or on Linux, or falls back to a built-in font. Out of Office's `captions.py`, `edit.py` and `contact.py` now go through it.
- **Video encoder.** The skills' scripts encoded with Apple VideoToolbox only. `venc.py` (added) picks the machine's GPU encoder and falls back to x264.
- **Folders.** Out of Office's helper scripts were sorted into `tools/` (the five the film names), `tools/more/` and `tools/fixes/`; the moved ones had their folder paths corrected.
- **The two prompt files** were rewritten by `build_jobs.py` so that a rebuild is byte-identical. The content is unchanged.
- **Starting without arguments** prints how to use a script instead of an error: the skills' scripts, and Out of Office's tools that take arguments.
- **Private defaults** became arguments: `casting_scan.py` takes its reference stem and lines as arguments; `outfit_audit.py` reads its anchors from `outfit_ref.json`.

## Fixed along the way
- `story_sheets.py` assumed a 25 fps cut and showed the wrong frames on a 30 fps one.
- `seam_blend.py` could leave a clip renamed and missing when there was nothing to blend with. It now checks first.
- `clip_screen.py` ignored `--sb` when it loaded the join checker.
- `masked_slice.py` wrote a silent slice when no vocal stem was found. It now stops and says so.
- `contact.py` (both copies) now creates its output folder.
- `analyze.py` crashed on a song shorter than 14 bars (it always asked for 14 sections). It now asks for about one per four bars, 14 at most; a full-length song gets the same answer as before.
- `chain_frame.py` said it had saved a frame when the shot ran past its clip, and nothing was written. It now stops and says so, and it and `seam_blend.py` say when a clip is missing.
- `edit.py` says which shots fell back to a black frame, stops at once when the song is not where it expects it, and keeps the song name, the end card and the output name in constants at the top.
- `cut_audit.py` says when no row has a `type` for it to check; `join_check.py` prints the frame rate it reads the cut at.
- `clip_screen.py` looked for the later videos' editor (`tools/cut.py`) by default; it now looks for `tools/edit.py`.
