# How I Was Made

The files behind the music videos of **Sara Aurorix**, an openly AI pop star whose films are written and directed by one human and built with Claude Code.

Each video gets a folder here with its storyboard, every prompt and the scripts that made it. The two Claude Code skills that came out of the work are in `skills/`. It is all free to take.

- The film: [Out of Office](https://www.youtube.com/watch?v=Hp5b646QNtg)
- The page that goes with this repo: [aurorix.ai/studio/out-of-office](https://aurorix.ai/studio/out-of-office/)

## What is here

```
out-of-office/                 single 1: Out of Office (74 shots)
  storyboard.json              all 74 rows: when the shot plays, the line sung, the picture, the one thing that moves
  jobs_stills.json             the 74 still prompts, as sent
  jobs_clips.json              the 74 clip prompts, as sent
  more-prompts/                the reference-picture prompts, the lip-sync jobs and the four rounds of fixes
  words.json, timing.json      every sung word with its time; the beat grid
  lyrics.md                    the lyric sheet, with the Suno style line and exclude list
  tools/                       the five small scripts that made the film, plus the other helpers and the per-shot fixes
skills/
  sara-music-video/            the skill: the order of work, the prompt wrapper, what each model gets wrong
  shot-continuity/             the second skill: making separately generated shots connect, and checking every cut
```

## Start here

You need Python 3.10 to 3.12 (tested on 3.12; one package, MediaPipe, has no build for newer versions yet).

```bash
git clone https://github.com/saraaurorix/how-i-was-made.git
cd how-i-was-made
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Then rebuild the film's 148 prompts from its storyboard:

```bash
cd out-of-office
python tools/build_jobs.py
```

It prints `74 stills, 74 clips` and writes `jobs_stills.json` and `jobs_clips.json`, identical to the ones in the repo. Change a row in `storyboard.json`, run it again, and you have new prompts. That is the whole idea: one storyboard file, and everything else is made from it.

`out-of-office/README.md` walks through the rest: making the pictures and clips, timing the words, and cutting a film with `edit.py`.

## Use the skills

A Claude Code skill is a folder of instructions and helper scripts that Claude Code reads when a task calls for it. Copy both into your skills folder:

```bash
cp -R skills/sara-music-video skills/shot-continuity ~/.claude/skills/
```

Then open Claude Code in an empty project folder with your song in it and ask, for example: "Use the sara-music-video skill to plan a music video for this song." It will follow the order of work in `skills/sara-music-video/SKILL.md`, and it uses `shot-continuity` when shots have to connect.

Three things in the skills are Sara's and need swapping for your own artist: the sentence that describes her face, the reference pictures, and her house rules on taste. `SKILL.md` says where each one is.

## What you need to make your own

| For | You need | Cost |
|---|---|---|
| The song | a [Suno](https://suno.com) account | Suno's plans |
| Stills and clips | the Higgsfield command-line tool (`npm install -g @higgsfield/cli`, then `higgsfield auth login`) with credits; `tools/gen.py` drives it | per picture and per clip |
| Lip-sync | a [fal.ai](https://fal.ai) key in the environment as `FAL_KEY`; `falgen.py` drives it | per second |
| Word times, beat grid, the edit, every check | nothing: they run on your machine | free |

The scripts were written on Windows and then a Mac. `fonts.py` finds the closest fonts on your machine, and the skills' `venc.py` picks your GPU's video encoder, falling back to x264. Out of Office's five scripts should run anywhere Python does; the skills' scripts use `nice` and are macOS and Linux only as written.

Some of the lip-sync checks need the vocal on its own. That is Demucs: `pip install demucs`, then `python -m demucs --two-stems vocals -o sep song.mp3`. It is not in `requirements.txt` because it brings PyTorch with it.

What changed between the director's machine and this repo is in [`CHANGES.md`](CHANGES.md).

## What was tested

Every script in this repo was run before it was published, or is marked as not run with the reason. The list, with the command used for each, is in [`TESTED.md`](TESTED.md).

## What is not here

- **Pictures, clips and audio.** The film is on YouTube. The song is not in the repo.
- **Sara's reference pictures.** The prompts say "from the reference images": bring your own artist's.
- **Later videos' files.** They arrive in their own folders as those videos come out.

## Licence

Code: MIT (`LICENSE`). Storyboard, prompts and documents: CC BY 4.0 (`LICENSE-CONTENT.md`). Sara Aurorix's name, face and voice, the song and the films are not licensed: make your own artist.

## Credits

Out of Office was made with Suno v6 (the song), Claude Code on Opus 5.5 (the storyboard and the production), Nano Banana Pro (stills), Kling 3.0 on Higgsfield (video), Wan 2.7 (lip-sync), Veo 3.1 (reshoots), ChatGPT images through Codex (still fixes), and Python and ffmpeg (the edit). Written and directed by one human.
