# QA gates: the checklist for each gate, with commands

Every item once cost a paid redo or a review round. Run a gate's list before moving past it, and before showing the director anything. `scripts/<name>.py` is in this skill's folder: copy the ones you use into your video's `tools/` folder and run them from the video's folder (`tool-map.md`, Setup).

## §1 Before spending anything (storyboard gate)
- [ ] **The board read** (`storyboard-spec.md` §3) in order with the song, and the director's sign-off. Run `scripts/board_lint.py` if you want a list of things to look at. The items below are the older list; the spec includes them.
- [ ] **Casting confirmed by ear (the standard method, generation-playbook §1).** `scripts/casting_scan.py` has been run on the chosen take (timbre first, pitch as a hint). The flagged lines, grouped into passages with a control card first, have gone into a labelled clip (`scripts/casting_clip.py`); the director has answered per card; the answers are in `casting.json` (`ear`) and `casting.md`; a part-2 clip has covered flagged lines that weren't on a card.
- [ ] **Lines the director wants left alone** (e.g. an unsynced male voice) sit on non-singing shots.
- [ ] **Visual variety:** a distinct location and palette per shot; no run of white voids.
- [ ] **Lip-sync shots:** front-facing head-and-shoulders, face ≥ 1/3 of the frame height, mouth well inside the frame, **no prop crossing the eyes-to-chin band while she sings**.
- [ ] **Phrase-safe cuts:** `scripts/cut_audit.py`. Each singing shot ends after its line's last word (the script flags the ones that don't). Check by hand that each slice meets its model's minimum length (Wan 2.7 needs at least 3 s).
- [ ] **Silence after a sung line** is planned as a closed-mouth tail (`LIPTAIL`), not as more lip-sync.
- [ ] **Silent characters** are written as "lips closed, not speaking" in both prompts.
- [ ] **Chants** are one close-up, tiled into a grid, not a mouthing crowd.
- [ ] **Vehicles:** every car's nose direction has been read in its still, and the direction is written in the motion line, including background packs.
- [ ] **Onboard cameras** have their facing stated.
- [ ] **Shot lengths plan for about 0.5–3.3 s of usable Kling clip;** longer beats are split or chained.
- [ ] **Taste** (Sara's house rules; swap in your own): no suggestive gag poses, no religious imagery, no real brands, organisations or politicians, and real people only as silhouettes.
- [ ] **Cost quoted** for anything paid, and any cheaper route named. The director has said yes.

## §2 Stills gate
- [ ] The first ~20 of a batch spot-checked before the rest run.
- [ ] A contact sheet reviewed (`scripts/contact.py`, or a story-order sheet):
  - [ ] identity: face, bob, cyan eyes, chrome seams, including background clones;
  - [ ] outfit matches your artist's wardrobe references for the act;
  - [ ] `scripts/outfit_audit.py`: every repeated look matches its anchor still (neckline, colour, cut, material); rerun with `--clips` once clips land;
  - [ ] Kevin stays Kevin; the second vocalist keeps his fixed look and scale; no random strangers;
  - [ ] in-scene text is legible, spelled right, and has no stray style words or years;
  - [ ] anatomy and proportions (extra arms, head size);
  - [ ] continuity of props across neighbouring shots.
- [ ] **No real logos:** every *edited* still checked at full size.
- [ ] **Lip stills:** the face height is measured, with a free crop-in where it's under about 30%.

## §3 Animatic gate (before paying for any video)
- [ ] The animatic rendered: every shot's keyframe with a slow push-in, the real song, all captions and a label per shot (ID, song time, LIP marker, who sings).
- [ ] Sent to the director with the shot-ID convention; their notes fixed (timing, pacing, casting, captions, continuity, samey sections).

## §4 Clips gate (check each as it lands)
- [ ] **Clipsheet** start/middle/end against the still (`scripts/clipsheet.py`). Check identity drift, morphing crowds, garbled text and camera roll.
- [ ] **A mouth moving on a non-singing shot:** measured on a face crop (`scripts/lipsync_audit.py` flags it). Re-render closed-mouthed, or fall back to the still.
- [ ] **Motion:** look for flips of direction in the seconds the cut plays. Look at a 0.1 s strip of every flagged *vehicle* shot, and compare the nose direction with the background stream (`scripts/carflow.py` for a signed number).
- [ ] **Logic:** watch the *used* window for breaks (a head floating after a hatch shuts, a car changing).
- [ ] **Fixes go into your editor first** (per-shot tables such as `WINDOW`, `REVERSE`, `BAND_REVERSE`, `OVERRIDE`, listed in generation-playbook §8; they belong to the later videos' editor, which is not in this repo, so add the ones you need to your own). Re-roll only when a free fix can't work.
- [ ] **Frame 0 matches the new still** (mean abs diff under about 12): a stale upload wasted paid clips twice.
- [ ] **The intent screen:** `../shot-continuity/scripts/clip_screen.py --judge --workers 3` on every batch (`--lips` for sung shots). Read every FAIL's strip by eye.
- [ ] **In motion:** a 0.25 s strip of every clip; 0.1 s steps where anything moves oddly. A wrong-direction flag is a failure unless you can show it in motion.
- [ ] **Pace and beat** on performance clips (`field-lessons.md` §4).

## §5 Lip-sync gate

*The mouth shot is a Kling singing take first. Gate it with the fit in `field-lessons.md` §1 (PASS ≥ 0.40, CHECK 0.25–0.40 watch with sound, FAIL < 0.25) plus a full-size eye check, and check every other face in frame keeps its mouth shut. Only failed takes go to OmniHuman, after the director has seen the still at full size with the cost quoted. The Wan and sync.so lines below apply only if those engines are used.*
- [ ] **Inputs have colour** (a mean-RGB scan of every `gen/v2v_in` or start frame) **before** paying. Outputs have colour and the same frame count as their inputs **before** anything is marked done.
- [ ] **Wan:** two takes per shot, scored with `scripts/pick_lip_takes.py` or `scripts/lipscore.py`, plus `scripts/lipsync_audit.py --write` for the visual lag. Scores: about 0.45–0.5 and up is good (the scripts label > 0.5 as good), under 0.3 is weak. Short lines and choir lines score unreliably, so judge those by eye.
- [ ] **sync.so:** diff the output against its input to see the repainted box, and check every prop inside it (`scripts/glassfix.py` if one vanished).
- [ ] **Casting:** no Sara lip-sync on a line someone else sings.

## §6 WIP gate (the cut you are about to send)

Render the cut first. The checks below use the editor's own outputs: one segment per shot in `build/<id>.mp4` and the joined picture in `build/video.mp4` (`out-of-office/tools/edit.py` writes both).
- [ ] **The drift** between the picture and the song is within a frame (about ±17 ms plus rounding). If your editor doesn't print it, compare the concatenated video's duration (`build/video.mp4`) with the song plus the end card by hand.
- [ ] **Every segment's frame count** equals `round(t1*30) - round(t0*30)` (a framemd5 packet count per `build/<id>.mp4`).
- [ ] **A full GPU decode is clean:** `ffmpeg -v error -hwaccel videotoolbox -i CUT.mp4 -f null -`.
- [ ] **A whole-film colour scan:** no green-dominated samples at 4 per second.
- [ ] **Lip lag:** `scripts/lip_lag.py`, median near 0 over the shots with correlation ≥ 0.3. The shots that never score are checked by eye.
- [ ] **Motion:** no unexplained flips in the flagged shots (§4).
- [ ] **The audio lines up with the song** (cross-correlation, 0 ms).
- [ ] **Sample frames** at the title, the first chorus, the bridge, the outro and the survey card.
- [ ] **Named `NAME_wipN.mp4`** without overwriting a sent cut. The editor writes `NAME.mp4` or `NAME_draft.mp4`, so rename it by hand.
- [ ] **Evidence prepared:** a contact or before/after sheet under 30 MB. The message lists what changed, what to watch and at which m:ss, and what the round cost.
- [ ] **No unlabelled placeholder:** every still standing in for a clip carries a burned-in "STILL <id> - NOT ANIMATED YET" bar, and the message lists them.
- [ ] **Freeze and look** (`field-lessons.md` §4): no frozen shots, nothing CGI-looking against an approved frame, no melted faces or ugly expressions. Earlier "approved" minutes aren't exempt.
- [ ] **The end-to-end story pass** (shot-continuity Part 3c): `../shot-continuity/scripts/story_sheets.py` read in order with the state ledger, every shot in motion, `../shot-continuity/scripts/join_judge.py` on every cut, merged into `review/E2E_cutN.md` and sent with the cut.

## §7 Deliverables gate
- [ ] **Full master:** 1080p30 H.264 High, AAC 256k, faststart.
- [ ] **Compact** within about 5% of 130 MB (bitrate = MB × 8 / duration − audio).
- [ ] **Shorts 9:16:** at least 6 separate clips, each one continuous stretch (no medley), opening on its hook; edges in vocal-stem gaps; frame count = span × 25 and audio = video; the thing each line names is in frame and clear of the captions (a strip every ~0.75 s); faces inside the safe area (`out-of-office/tools/more/shorts.py`, generation-playbook §8).
- [ ] Your project notes updated with the final filenames.

## Lip shots vs the other voice
Before any WIP or delivery, list every word inside each lip shot's window with its pitch on the vocal stem.
- A low (male) word inside Sara's shot means she mimes his line, because sync-3 keeps her mouth moving.
- **Fix:** move the cut to the frame where her mouth is at rest before his first word (measure the lip gap with MediaPipe), or use an `INSERT` cutaway.
- Pitch trackers make octave errors on low sung notes, so ask the director's ear about any flag you can't settle.
