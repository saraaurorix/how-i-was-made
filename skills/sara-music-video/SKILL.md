---
name: sara-music-video
description: Make an AI music video from a song to a finished cut, the way the Sara Aurorix videos are made - concept and lyrics, the song (Suno), who sings each line, a storyboard with a row per line, stills from a fixed prompt wrapper, one action per clip (Kling), mouth shots, an edit written as code, and a read of the whole cut before anyone sees it. Use it when planning or building a music video, an AI character's clips or any multi-shot AI film where shots must look like one piece, and when a director's note ("the lip-sync is off", "it's disjointed", "she's off-model") has to become a fix.
---

# Sara Aurorix music videos (public edition)

This is the skill behind the music videos of Sara Aurorix, an openly AI pop star whose films are written and directed by one human and built with Claude Code. Kevin is the human office worker who plays opposite her in those videos. The skill is published as it is used, minus the private parts, in the repo github.com/saraaurorix/how-i-was-made, together with the `shot-continuity` skill (install both). The first video made this way, **Out of Office** (74 shots), is the benchmark throughout; its storyboard, prompts and scripts are in that repo's `out-of-office/` folder (paths written `out-of-office/…` below mean that folder), so every rule here can be checked against a real file. Its board predates the field names in `references/storyboard-spec.md`: it has no `type`, `voice`, `look` or `set`, so the scripts that need those stop on it.

**Using it for your own artist.** Three things are Sara's and need swapping for yours: the **identity line** (the one sentence about her face, `references/wrapper.md` §1), the **reference pictures** (one portrait, one full-length picture per look, one per recurring character), and the **house rules on taste** (non-negotiable 4). Everything else is method. The human who makes the calls is called "the director" below: that is you.

**How it is meant to be used.** Lightly. Too many constraints lead to poorer work. So: six things that are never broken, ten principles with the reason each one earned its place, a flow you can hold in your head, and a toolbox you reach into when a shot needs it. Judgement is yours. When something new goes wrong, add a line and its reason, and take an old one out if it has stopped earning its keep.

## The six non-negotiables

1. **Money.** Ask the director before anything paid, per batch, and quote the cost first. Say first whether it can be done on something already paid for or free (a subscription's image generation, a local tool). Report spend from the real balance, not an estimate.
2. **Nothing public without asking.** Songs, cuts and pages stay private until the director says otherwise. The director does sign-ins, CAPTCHAs, payments and keys; never type or store a key.
3. **Encode on the GPU, at low priority.** Batches of CPU x264 encodes froze the machine more than once. `scripts/venc.py` picks the machine's GPU encoder (and falls back to x264 only where there is none).
4. **Taste (Sara's house rules; swap in your own).** Satire, funny, dark, glamorous. She owns the room: cool, never the victim. Out: nudity, swimwear, cheap innuendo, religious imagery, real brands, logos, organisations or politicians (real people only as silhouettes with job titles). Wardrobe starts from the artist's wardrobe references; in prompts describe the garment and the cut, never an adjective about how it should feel.
5. **Look at what you send.** Every cut is read end to end, in order, in motion, before it goes; a still standing in for a clip carries a label.
6. **Fix only what's flagged, and show the original next to the fix.** The rest of the cut is right until the director says otherwise, and the original clip is sometimes better than the fix. Send the fix on its own at the flagged times, with the original as a still sheet, never as the first half of a before/after clip (a director reviews the "before" half and reports the old problem). When a note says a fault is everywhere, the flagged times are examples: fix the class.

## Ten principles, and why each earned its place

1. **Pilot one, then batch.** The first instruction ever given on Out of Office: *"just do 1 first so we can check style"*, and then *"1 is perfect."* Repeated at every scale since: one still, one clip, the first minute, ten clips. Nothing is sent as a batch that hasn't been sent as one.
2. **Consistency is the wrapper, not the map.** Out of Office kept its office lighting across 74 shots made four at a time with no set map: every prompt carried the same identity line and the same style line, and five reference images covered the whole video. Write the style line once (palette, world nouns, lens, finish) and repeat it word for word; it can change per section when the song flips style. The template is in `references/wrapper.md`.
3. **One look per act, pinned to a reference.** Variety between acts; one image within an act, so outfits don't drift. The character's identity marks in the same words every time.
4. **Structure scales with what has to connect.** Judge each section against the song. A list of jokes is a montage: the wrapper is enough, and parallel generation is fine. A returning hook wants a home set: one empty set reference, revisited and escalating. One event told over several lines is a continuous scene: directed like a film (a reused set, blocking, named angles, a state ledger) and made in sequence, each shot from the one before. Out of Office in parallel worked; a later video's chorus only flowed once it was restaged as one walk. The second skill in this repo, `shot-continuity`, is the method for the continuous kind.
5. **A gag per line, the artist as the agent, escalate, flip the pace.** Boards without this came back as stale, tame and linear. Count a board against Out of Office before showing it: shots, gags, places, look changes, lip shots (about 15–26, inside gags, never a talking head against a backdrop).
6. **Her voice comes first.** Check by ear who actually sings each line before the board: the song generator handed her lines to another voice on half of the songs. Mouth shots: a Kling singing take with its audio on, then the master soundtrack in the edit; a dedicated lip-sync model only where a take fails (`references/field-lessons.md` §1). End each on the sung notes; nobody else's mouth moves. Lip-sync was flagged on every single video, so this is where the eye goes first.
7. **Kling does one thing per clip.** Write what visibly happens, where it stops, and what must not appear. Design the still so the action can't miss (the target where the swing lands; the action already under way if it must finish). Wording that works and fails is in `references/wrapper.md` §3.
8. **Look at what you made, against the plan.** Full size, in motion, each clip against its own row, and each recurring face next to its own reference image, not "does it look photoreal". Tools shortlist; eyes decide. A wrong-direction flag stands unless you can show otherwise in motion. "Aren't you checking the clips?" is the most repeated complaint in this project's history.
9. **Notes: read as a viewer, classify, don't kneejerk.** A story or staging note goes back to the board (restage the section: two sentences, one axis, start → end per shot, a section animatic, the director's yes). A glitch on a correct row gets the flag table below. A note that could be a complaint or an instruction gets the sensible reading, said out loud.
10. **Kill what says nothing new.** A single was parked because it said nothing the others hadn't; a second version is rebuilt as one world, never bolted on. Ask whether the topic is weak before writing the lyric.

## The flow

The order Out of Office ran, with the additions that earned their place. Each line names where the detail lives.

1. **Concept and spine** → the director picks (`references/creative-playbook.md` §1–2).
2. **Lyrics** as line → picture; the listen test, no in-jokes; locked before the song is generated (`references/creative-playbook.md` §3).
3. **The song** (Suno), two takes, on the director's go; they pick by ear (`references/creative-playbook.md` §4).
4. **Casting check** by ear, when the song has more than one voice: who sings each line, as sung (`references/generation-playbook.md` §1; `scripts/align_lines.py`, `casting_scan.py`, `casting_clip.py`). On a first song there is no earlier song to take reference lines from: mark lines of this song you are sure of.
5. **Analysis:** beats, stems, word times (`scripts/analyze.py`, `transcribe.py`).
6. **The board:** the section forms judged against the song; the wrapper written; one look per act; a set list only as long as the sets that recur; continuous scenes directed; every row a picture, an action, who sings, the join. Count it against Out of Office. Read it with the song. The director signs it off. (`references/storyboard-spec.md`; `scripts/board_lint.py` if you want a list of things to look at.)
7. **Pilot stills** (a handful across looks and sets) → the director's eye → the rest. Inside a continuous scene, in sequence from the previous frame (`references/field-lessons.md` §3).
8. **The animatic** (stills cut to the song) → the director's notes before any clip.
9. **Pilot clips** (about 10: one per set and look, plus a text gag) → then the rest; continuous scenes chained in order (`references/field-lessons.md` §2).
10. **Mouth shots:** a Kling singing take with audio on → keep the take for reference → the master soundtrack in the edit → check the same lyric passage in motion with sound. A lip-sync model only for the fails, and only after the director has seen the still and the quote (`references/field-lessons.md` §1).
11. **The edit**, written as code from the storyboard and the word times; speed changes by blending only (`references/generation-playbook.md` §8). The skill ships no editor: start from Out of Office's (`out-of-office/tools/edit.py` and `captions.py` in the repo) or write your own from §8. Edit at 25 fps; Out of Office was cut at 30, which is why the playbook's frame arithmetic says 30 in places.
12. **The read before sending:** in order, in motion, each shot against its row, the look, the joins, the placeholders (the shot-continuity skill, Part 3c).
13. **Send** with what changed, where to look (m:ss), and the round's cost.
14. **Notes** → principle 9 → re-render only those shots → step 12 again.
15. **Deliverables**, once the director approves the cut: the master, a compact copy, and at least six separate vertical shorts, each one continuous stretch of the song, never a stitched medley (`references/generation-playbook.md` §8).

## When the director flags a shot

Find the shot from the time (relative to the file they watched); strip the cut around it. Confirm the cause before choosing a fix; fixes that cost nothing first.

| The director says | Likely cause | Fix, cheapest first | Tool |
|---|---|---|---|
| "no continuity" / "it's disjointed" / "he's outside, he's inside" / "going in circles" / "people are gigantic" | a board problem: the story, staging, a state, the form | principle 9: back to the board; restage the section; then remake | shot-continuity Parts 3c–3d, `references/storyboard-spec.md` §1c |
| "lip-sync is a bit off" | the mouth trails or leads; or a Kling take sings the line at its own pace, so no single offset fits | measure the lag, then nudge by whole frames; a smooth re-time where the pace is close (`scripts/lip_retime.py`, for the Wan route); for a Kling take, a word-anchored retime as described in `references/field-lessons.md` §1 (no script shipped), then check the mouth shapes land on their words. A low sync score on a smiling singer is a reason to look, not a verdict | `scripts/lip_lag.py`, `scripts/lip_retime.py` |
| "starts good, then drifts" / "she sings longer than the audio" | the shot runs past her notes; a mask muted held notes | end the shot on the sung notes → a new Kling take → a lip-sync model on a yes | `scripts/cut_audit.py`, `scripts/lipsync_audit.py` |
| "the guy is singing too" | the lip model moved every mouth | close his mouth in the still itself (an image edit), then the take; a prompt line alone didn't stop it | a new take |
| "she's miming his line" | the song generator gave it to the other voice | re-cast: a closed-mouth gag, a shot of the other singer, or split the row | the board |
| "frozen stills" / "looks like a cartoon" / a melted face | an unlabelled placeholder; a CGI-looking still animated | label placeholders; judge against an approved frame; a photoreal still, then a new take | `references/field-lessons.md` §4 |
| "the car goes backwards" | Kling slid it tail-first or reversed late | measure; play only the part before the flip, or play it reversed; else re-roll with the direction written | `scripts/carflow.py`, a strip every 0.1 s |
| "too fast" / "should be dancing to the music" | a routine in one clip; Kling can't hear the song | one slow repeated move, two takes, fit to the beat in the edit | `references/field-lessons.md` §6 |
| "the guitar looks fake" | no strap or hands on the strings in the still | redraw the still, prompt the mechanics, fit the strokes to the beat | `references/wrapper.md` §3 |
| "X disappears" (glasses, a mic, a held prop) | the lip model repaints the mouth box or drops held props | composite the prop back; pin the hands in the prompt | `scripts/glassfix.py` |
| "the words on the screen changed" | the lip model rewrites text | lay the still's screen back over a locked shot in the edit | the edit |
| "garbage text" | Kling garbles text after a few seconds | play only the good part; text beats as graphics made in code | the edit |
| "off-model" | the still drifted | a new still with the identity line, then a new clip | `references/wrapper.md` |
| "the outfit changed" | a look not pinned to its reference | pin every look to its first approved still; audit the rest against it | `scripts/outfit_audit.py` |
| "the angle has flipped" | a shot made off its angle | mirror if nothing in frame reads; else a still from the neighbour's angle and a re-roll | shot-continuity Part 4 |

## The toolbox (read the one you need)

- `references/wrapper.md`: Out of Office's prompt wrapper as a template, the look-per-act rule, and the wording that works and fails in Kling and the image models.
- `references/storyboard-spec.md`: for continuous scenes: judging the form against the song (§1b), directing a scene like a film (§1c), the ledger, the optional fields, the board lint, and the map of where past problems should have been caught (§6).
- `references/field-lessons.md`: lessons from the videos after Out of Office: mouth shots, chaining, stills routes and refusals, the checks, the edit.
- `references/generation-playbook.md`: every known failure by asset type; `references/creative-playbook.md`: ideation, the spine, lyrics, the song, pacing, captions; `references/qa-gates.md`: checklists; `references/tool-map.md`: which script does what.
- `scripts/`: the helpers. They are written to be copied into a project's `tools/` folder and run from the project folder (`python tools/board_lint.py storyboard.json`). `scripts/fonts.py` and `scripts/venc.py` make them run on a Mac, Windows or Linux.
- The worked example: this repo's `out-of-office/` folder (the storyboard, every prompt, the five scripts that made the film).
- The continuity tools (`join_check.py`, `clip_screen.py`, `story_sheets.py`, `join_judge.py`, the chaining kit) are in the `shot-continuity` skill: install it alongside this one (`../shot-continuity/scripts/` once both are in `~/.claude/skills/`).
- **What the scripts need:** Python 3.10–3.12 and the repo's `requirements.txt` (it pins `mediapipe<1.0` and `av<19`); the Higgsfield command-line tool for `scripts/gen.py`; a fal.ai key for `scripts/falgen.py`; the Codex command-line tool for the vision judges in `shot-continuity`; Demucs for the vocal stems. A project is a folder with `storyboard.json`, `words.json`, `gen/stills/`, `gen/clips/`, the song, the stems under `sep_wav/htdemucs/<name>/`, and the scripts copied into `tools/` (copy the whole `scripts/` folder: several scripts import `lipscore.py`, `fonts.py`, `venc.py` or `fal_env.py` and need `models/` beside them).
