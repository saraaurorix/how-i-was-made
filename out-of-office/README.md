# Out of Office

Seventy-four shots, 148 prompts, one human. This folder is the production as it was: the storyboard, every prompt, and the scripts that turned them into [the film](https://www.youtube.com/watch?v=Hp5b646QNtg).

Sara was called NOVA when this was made, so every row and every prompt says NOVA.

## The files

| File | What it is |
|---|---|
| `storyboard.json` | 74 rows. Each has `id`, `t0` and `t1` (song time in seconds), `cap` (the line under the shot), `refs` (which reference pictures it uses: `o` office look, `c` nightclub look, `s` orbit look, `k` Kevin), `still` (the picture) and `motion` (the one thing that moves) |
| `jobs_stills.json` | the 74 still prompts as sent: the identity sentence, the row's picture, the style line, and the references attached |
| `jobs_clips.json` | the 74 clip prompts as sent: the row's motion line and a fixed suffix, started from the row's still |
| `more-prompts/jobs_refs.json` | the 4 prompts that made the reference pictures: her three looks and Kevin |
| `more-prompts/jobs_lipsync*.json` | the lip-sync jobs for the shots where she sings to camera: a first try on Seedance, then Wan 2.7 (three more of the 14 are in the fix rounds) |
| `more-prompts/jobs_stills_fix*.json`, `jobs_fix_*.json` | the four rounds of fixes |
| `words.json` | every sung word with its start and end time (Whisper) |
| `timing.json` | tempo, bar grid and section boundaries |
| `lyrics.md` | the lyric sheet as pasted into Suno, with the style line and the exclude list |

## The five scripts

Run them from this folder to look at Out of Office. To make your own film, copy `tools/` into an empty folder and work there (the steps below), so these files stay as they are.

| Script | What it does | Needs |
|---|---|---|
| `tools/build_jobs.py` | turns `storyboard.json` into `jobs_stills.json` and `jobs_clips.json` | nothing |
| `tools/gen.py jobs_stills.json 4 [S01,S02]` | runs a job file, four at a time, downloads the results, and can be re-run after a failure; a third argument runs only those ids | the Higgsfield command-line tool, signed in, with credits; your reference pictures in `gen/char/` |
| `tools/transcribe.py out-of-office.mp3 words.json` | times every word of the song | nothing paid: local Whisper. The first run downloads its `small.en` model (about 0.5 GB). English-only; change the model name in the script for another language |
| `tools/captions.py` | draws the word-timed captions in three voices; `edit.py` calls it | `words.json` |
| `tools/edit.py` | cuts the clips to the storyboard, burns in the captions, flashes the drops, adds the song | the song as `out-of-office.mp3` here; clips as `gen/clips/<id>.mp4` and stills as `gen/stills/<id>.png`, named after the row ids |

`edit.py` uses a still wherever a clip is missing and a black frame wherever both are (it prints a line for each), so you can run it on whatever you have; `--draft` only encodes faster. It cuts at 30 fps. A clip longer than its shot starts 40% of the way into the spare length, so the action is under way; a shorter one is slowed to fit; a lip-synced clip (`gen/lipsync_wan/`) starts on its first frame. The identity sentences, the style line and which reference goes with which act are at the top of `tools/build_jobs.py`. Out of Office's own per-shot content is at the top of `tools/captions.py` (`SYSTEM`, `HUMAN`, `HOOK`, plus two special cases for S57 and S72 inside `build()`) and of `tools/edit.py` (`DROPS`, `SPLIT`, the end card `TITLE` and `SUBTITLE`, `OUT_NAME`). Your own shots inherit them by id, so empty or change those tables for your own film.

## Making your own with it

1. **A folder.** Copy `tools/` into an empty folder. Everything below happens there.
2. **The song.** Write the lyric as one picture per line, generate it (the style line that made this one is in `lyrics.md`), and save it in that folder as `out-of-office.mp3` (or change `SONG` at the top of `tools/edit.py`).
3. **Time it.** `python tools/more/analyze.py out-of-office.mp3 timing.json`, then `python tools/transcribe.py out-of-office.mp3 words.json`.
4. **The storyboard.** One row per line, in the format above, with your own ids (`S01`, `S02`...): the still and clip files are named after them. Verses as a montage; the chorus always in the same place.
5. **The references.** One portrait of your artist, one full-length picture per look, one per recurring character, in `gen/char/`. Edit the reference list and the identity sentence at the top of `tools/build_jobs.py`.
6. **One still first.** `python tools/build_jobs.py`, then one job to check the style: `python tools/gen.py jobs_stills.json 1 S01`. Then the batch: `python tools/gen.py jobs_stills.json 4`.
7. **The clips.** `python tools/gen.py jobs_clips.json 4`. One action per clip.
8. **The edit.** `python tools/edit.py --draft` as soon as the stills exist; again without `--draft` when the clips are in.

Steps 6 and 7 cost money on Higgsfield. Everything else runs on your machine.

## The rest of `tools/`

- `tools/more/`: `fonts.py` (the scripts ask for Windows fonts by file name; this finds the closest face on your machine; put your own `.ttf` files in `tools/more/fonts/` to choose them; run on its own it writes `fonts_proof.png`, a sheet of the faces it picked), `analyze.py` (beat grid), `contact.py` (contact sheets of a folder of stills), `falgen.py` with `fal_env.py` (runs jobs on fal.ai, the later videos' lip-sync route; Out of Office's lip-sync ran on Higgsfield through `gen.py`), `gpt_edit.py` (stills through ChatGPT images, by way of the Codex command-line tool), and `reels.py` and `shorts.py`, which cut the vertical versions of the finished film.
- `tools/fixes/`: one script per shot that was repaired after the first cut (the stamp that read BOLVED, the queue sign, the sky ticker, the street signs, the empty pods). They work on frames of the finished film, which is not in this repo. They are here to be read, not run: each one's docstring says what was wrong and how it was fixed.

`reels.py` and `shorts.py` also need the finished film and its stems, so treat them the same way.
