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

Run them from this folder.

| Script | What it does | Needs |
|---|---|---|
| `tools/build_jobs.py` | turns `storyboard.json` into `jobs_stills.json` and `jobs_clips.json` | nothing |
| `tools/gen.py jobs_stills.json 4` | runs a job file, four at a time, downloads the results, and can be re-run after a failure | the Higgsfield command-line tool, signed in, with credits; your reference pictures in `gen/char/` |
| `tools/transcribe.py song.mp3 words.json` | times every word of the song | nothing (local Whisper) |
| `tools/captions.py` | draws the word-timed captions in three voices; `edit.py` calls it | `words.json` |
| `tools/edit.py` | cuts the clips to the storyboard, burns in the captions, flashes the drops, adds the song | the song as `out-of-office.mp3` here, clips in `gen/clips/`, stills in `gen/stills/` |

`edit.py` uses a still wherever a clip is missing and a black frame wherever both are, so you can run it on whatever you have; `--draft` encodes faster. The identity sentences, the style line and which reference goes with which act are at the top of `tools/build_jobs.py`. The per-shot captions and flashes are at the top of `tools/captions.py` and `tools/edit.py`.

## Making your own with it

1. **The song.** Write the lyric as one picture per line, generate it (the style line that made this one is in `lyrics.md`), and save it here.
2. **Time it.** `python tools/more/analyze.py song.mp3 timing.json`, then `python tools/transcribe.py song.mp3 words.json`.
3. **The storyboard.** One row per line, in the format above. Verses as a montage; the chorus always in the same place.
4. **The references.** One portrait of your artist, one full-length picture per look, one per recurring character, in `gen/char/`. Edit the reference list and the identity sentence at the top of `tools/build_jobs.py`.
5. **One still first.** `python tools/build_jobs.py`, then run a single job to check the style before the batch. Then the batch: `python tools/gen.py jobs_stills.json 4`.
6. **The clips.** `python tools/gen.py jobs_clips.json 4`. One action per clip.
7. **The edit.** `python tools/edit.py --draft` as soon as the stills exist; again without `--draft` when the clips are in.

Steps 5 and 6 cost money on Higgsfield. Everything else runs on your machine.

## The rest of `tools/`

- `tools/fonts.py`: the scripts ask for Windows fonts by file name; this finds the closest face on your machine. Put your own `.ttf` files in `tools/fonts/` to choose them.
- `tools/more/`: `analyze.py` (beat grid), `contact.py` (contact sheets of a folder of stills), `falgen.py` with `fal_env.py` (runs the lip-sync jobs on fal.ai), `gpt_edit.py` (stills through ChatGPT images, by way of the Codex command-line tool), and `reels.py` and `shorts.py`, which cut the vertical versions of the finished film.
- `tools/fixes/`: one script per shot that was repaired after the first cut (the stamp that read BOLVED, the queue sign, the sky ticker, the street signs, the empty pods). They work on frames of the finished film, which is not in this repo. They are here to be read, not run: each one's docstring says what was wrong and how it was fixed.

`reels.py` and `shorts.py` also need the finished film and its stems, so treat them the same way.
