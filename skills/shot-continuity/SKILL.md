---
name: shot-continuity
description: Plan, make and check continuity between shots in AI-generated video (Kling or any image-to-video), where every shot is generated on its own and nothing connects them unless the storyboard and the pipeline make it. Use it when writing a storyboard, before making stills or clips (set pack, identity line, each shot chained from the last frame of the one before), before paying for clips (check the stills' joins), after a cut (every join, the character sheet, the thread ledger), before any cut is sent (the whole film read in order with a state ledger, plus the join judge), and whenever the director reports a continuity problem - it's disjointed, someone is outside then inside, a costume piece appears from nowhere, the angle has flipped, the fixes are going in circles, she looks like a cartoon, people are gigantic. Covers the 180-degree rule, screen direction, action over a cut, place, set references, identity drift, props and costume state, light, scale and eyelines. Works with the sara-music-video skill.
---

# Shot continuity

**The order of work agreed with the director:** `references/generation-flow.md`. Start there for a new video.

**Why this exists.** The director watched the first cut of a later video: the individual scenes were good, and there was no continuity between them. On another video, lots of little breaks showed between characters and from one scene to the next. Then the director's diagnosis: the issue was the way the clips were produced, and the next clip should be prompted with the previous clip's end as its reference.
- **The cause was the method, not the model.** Every shot was made from its own still, from its own prompt, in parallel. Kling was only ever told where a clip starts.
- **Places, people and props were described in words,** and every generation read the words differently.
- **Every review looked at shots, never at cuts.** Strips, minute sheets and contact sheets show one shot at a time. A continuity error lives in the join between two shots.
- **So the unit here is the join.** Plan joins, make joins, check joins. And check every clip against its own row (Part 3b): a clip can join perfectly and still not do what it's for.
- **And the film, in order (Part 3c).** Joins and clips that each pass can still add up to no story, and one cut was sent before anyone had read it end to end. No cut goes to the director before the end-to-end pass.

The director's two asks: avoid it happening in the first place, and have a skill that looks at the joins between shots for continuity issues across the whole video.

**Who is who.** Sara is the AI pop star these videos are about; Kevin is the human office worker opposite her; the director is the human who makes the calls. The automatic face tests (SIDES, `face_sheet.py --who`, TRAVEL) are tuned to those two faces: for your own cast, edit the finders at the end of `faces()` in `scripts/join_check.py`, or rely on the eye checklist. Both skills are published at github.com/saraaurorix/how-i-was-made; the `out-of-office/` paths below mean that repo's folder.

## Part 1. Plan it: the storyboard rules

*In the `sara-music-video` skill (install it alongside this one), `../sara-music-video/references/storyboard-spec.md` is the toolbox for scenes that must connect: each section's form judged against the song (montage, home set, continuous, performance, or a mix), directing a continuous scene like a film (a reused set, a floor plan, blocking, named camera setups, a coverage plan), the optional `../sara-music-video/scripts/board_lint.py`, and the map of where each past problem should have been caught. A montage needs only the prompt wrapper (`../sara-music-video/references/wrapper.md`). The rules below are the continuity reasons behind those fields.*

**1. Scenes, not shots.** Group shots into scenes: one place, one stretch of time. Every scene gets a **staging line** under its heading. The builder (the script that turns board rows into prompts, like Out of Office's `tools/build_jobs.py`) appends it to every still and clip prompt in the scene.
- **Geography,** in one sentence: where the fixed things are (the desk, the doors, the aisle).
- **The camera side:** which side of the action the camera stays on. This is the 180-degree line.
- **Who is where:** who is screen-left and who is screen-right.
- **Direction of travel:** for example "left to right", or "down the aisle toward camera".
- **Light and time:** the light source, the time of day, the weather.

Example: *Staging: the office floor's central aisle runs from the big desk (near) to the tall front doors (far), desks on both sides; the camera stays in the aisle looking toward the doors; Kevin is always screen-left of Sara; movement is toward camera; warm lamp light with cyan from the screens.*

**2. Every cut has a type.** Mark the cut into each shot. In a Markdown board, put a trailing marker in the Motion cell, like `[FLOW]`; the builder strips and records it as `join`.

| Type | Meaning | The rule |
|---|---|---|
| **FLOW** | the action carries over the cut | A's end state is B's start state, in the same words. Same sides, same direction |
| **SAME** | same scene, new angle | the sides, the direction and the geography hold. The default inside a scene |
| **JUMP** | a time skip inside the scene, motivated by the lyric | the sides still hold. The picture shows what changed (the lyric has her sit down at the desk) |
| **TRANSITION** | a new place | a device in the picture carries it: a door, a curtain, a flash, a match cut, a whip, something falling from one place into the next |
| **MONTAGE** | a list (a rap, an epilogue of clips) | each shot stands alone; the cut is on the beat |

**3. Every shot states its start and end state.** Say where each person is, what they are doing, what they hold and which way they face. For a FLOW join, write A's end state and B's start state as the same sentence.
- **This is a gate, not advice** (Part 3c). For a scene that is one continuous event, write the start and end states as a table for every row before any still. Row n+1 starts where row n ends. Every costume, prop or crowd change is something someone does on screen.
- **One later video's first chorus skipped it.** Kevin went outside, then inside; the front row was seated, then half-way out of the door, then seated again; his hat, cloak and bag came and went.

**4. Running props carry a state line in every shot they appear in:** hat on or off, mask on or pushed up, who holds what, who plays which part. The thread ledger (Part 3) is built from these lines.

**5. Music is written as motion.** A riff means "her strumming hand moves on every beat for the whole shot, her fretting hand moves on the neck". "Hits the first chord" is one event: Kling plays it once, then she poses. The same goes for a stomp, a clap or a beat drop.
- **Real playing starts in the still** (the director's note on a first attempt: the guitar playing needed to be realistic, and it looked fake). Draw a strap over her shoulder, a pick in the strumming hand over the strings, and the fretting fingertips on the frets in a chord shape. Without them Kling floats and swings the guitar and waves the hands near it.
- **The clip prompt then carries the mechanics:** the guitar keeps its angle on the strap; big, visible down-strokes from the elbow; the fingertips change shapes; the hands never leave the guitar. "Short, quick" strokes under-strum.
- **Kling can't hear the beat.** Measure the stroke rate in the take and fit it in the edit, like a dance (rule 5b).

**5b. A dance is ONE repeated step, then fitted to the beat in the edit** (the director's note on a shot with several dancers: they should be consistent and dancing to the music). Kling cannot hear the song: prompt one simple step ("a slow synchronised step-touch to a steady beat, hips swaying, arms swinging loosely, over and over, never speeding up"), make two takes, measure each clip's own tempo (the lead dancer's sway extremes → the step length → 1 or 2 beats per step, whichever keeps the playback rate nearest 1× → the window that puts the extremes on the beats), keep the take with the natural rate and the steadier steps, and retime by motion-compensated interpolation (ffmpeg's `minterpolate`), never by dropping or holding frames. Multi-move prompts come back too fast; a take that walks into the lens or only poses is rejected before fitting.

**6. One action per shot, and it finishes inside the clip.** If the action has to land at the end, start the still with it already under way, or use an end frame (Part 2).

**7. Screen direction holds.** Something that leaves frame right enters the next shot from frame left. A chase that runs left-to-right keeps running left-to-right.

**8. Cross the line only on purpose.** You can cross the 180-degree line with a shot that moves the camera across it, a shot straight down the line, or a new scene. Never on a plain cut.

**9. Time of day moves forward only,** inside a section. Name it in the staging line.

**10. A cutaway to another place must not contain someone who is in the main scene.** One cut went from Sara in the main scene to Sara at a city crossroads and back: she was in two places at once.

## Part 1b. Anchors: what every still is made from

**A set pack, signed off by the director, before the storyboard is final.** Before a video starts, it needs set references for its multi-scene locations. For every place used in more than one shot:
- **An empty establishing wide per lighting state it is seen in** (day, dusk, night, lit). A daytime wide used for night shots invented five different buildings on one video.
- **Empty means empty.** A reference with people in it copies the people.
- **One layout line:** what is where, which side the camera lives on, where the exits are.
- **Fixed sheets for recurring props and creatures:** a portal, a chair, a monster, a robot dog.

**A set reference fixes the geography, not the framing** (a later video's final chorus: the scale was completely broken, people were gigantic, and it cut rapidly between characters without flowing). All 19 stills were made in one parallel batch from the empty establishing wide, so the image model kept the wide camera and pasted each subject in front of it at giant size, a new character every 2 s.
- **Plan 2–4 camera positions per scene** (for example the back-of-arena wide, stage-front, the pit) and say which one each shot uses.
- **Write scale anchors into every prompt:** "the same height as the fans around him, the stands tower behind".
- **Keep each character in one place** across the scene's cuts, and chain the stills in order.
- **Eye check before sending:** is anyone bigger than the architecture? Does each change of camera position have a reason?

**One fixed identity line per character,** with exact words for the marks that drift. For example: "two thin chrome seam lines, one each side of the chin, from the corner of the mouth to the jawline, none on the cheeks; no coloured eyeshadow; a royal-blue lanyard".
- **The line never varies between prompts.** Loose wording let Sara's seams grow from none to long cheek lines across 17 lip shots.

**A design reference per character generation.** When a character has versions (a robot version, a costume variant), each version has its own reference and its own name. A prompt never describes a version from words.

**A reused clip from an older generation is a break by default.** It stays only if the join check clears it, and the board lists it as REUSE with its source.

**Inserts of body parts take the outfit reference.** A hand, a foot or a fingertip is prompted with the sleeve, glove or boot named and the outfit reference attached. Without it, it comes back as a bare chrome limb.

**Every world change is ENTER plus EXIT, and a portal cut shows the arrival.**
- **ENTER:** from behind, the ring dead ahead and centred, and no face reference on from-behind stills.
- **EXIT:** the ring facing the camera, the character walking straight out toward the lens.
- **The device is in both pictures.**

**An outfit changes through a portal, or on camera with a start and end frame:**
- **Start:** the previous shot's last used frame.
- **End:** an image-model edit of that frame that changes only the costume.
- **A hard cut between two colours reads as an error.**

## Part 2. Make it: each shot is produced from the one before

**The core rule:** inside a scene, no shot is made from scratch. Its first frame comes from where the shot before it ended. Only a scene's first shot starts from the set and character anchors.

| Join into B | B's first frame comes from | Notes |
|---|---|---|
| FLOW, camera holds (one continuous take split by a cut) | A's cut frame, cleaned (below). B's clip starts from it | seamless; B keeps A's framing |
| FLOW or SAME, new angle | a new still made with A's cut frame as its continuity reference; the prompt keeps the place, light and props and writes the sides in ("KEVIN screen-left, SARA screen-right, the desk on the right") | the image model changes the angle; the reference holds everything else |
| JUMP | a new still with A's cut frame as reference; the prompt says what changed and that the place and sides hold | |
| TRANSITION | a new still; the device is in both pictures | |
| MONTAGE | its own still, from the anchors | only look and light matter |

**Chain from the real frame, never from A's still.** On another video's intro, shot B was first made from shot A's still, so Kevin was already in the aisle before he had moved: a teleport. Made again from A's actual cut frame, it joined.

**A's cut frame is the last frame of A that the cut actually plays,** not the clip's final frame.
- **Its index** is `round(window × clip_fps) + nf − 1`, where `nf` is the shot's frame count in the cut. This assumes an editor at 25 fps that plays every source frame once from the window (a start offset per shot), with no slow-down; the chaining scripts take `--window` for those offsets.
- **`scripts/chain_frame.py`** saves that frame.
- **Window the chained shot B at 0.04 s,** not 0.042: at 24 fps the seek would skip frame 1.
- **So fix A's window first, then take the frame.**
- **When a shot is as long as its clip,** the cut frame is the clip's final frame: the softest and most drifted one. Clean it, or make the clip longer than the shot (a 10 s clip) so the window ends on a sharp mid-clip frame.

**Clean the frame before reusing it.** A Kling frame is 720p, often motion-blurred, and carries whatever drift built up in the clip.
- **Pass it through the image model first:** "an improved version of this exact frame", with the character's face and look references attached.
- **Re-anchor after two or three hops:** make the next still fresh from the character references, with the chain frame only as the continuity reference.

**Or land the clip on the next shot (end frames).** Kling 3.0 takes an end frame: `--end-image`, or the job key `end` in `scripts/gen.py`.
- **How:** make B's still first, then generate A from A's still to B's still. A lands exactly where B starts.
- **In the cut:** play A's tail, so the played part ends on the clip's last frame.
- **Parallel:** a scene's clips can run at the same time, because each needs only two reviewed stills.
- **Limit:** only when the two frames share the camera and the place. A very different end frame makes Kling morph.
- **Not for group dances:** a big pose change across many dancers came back as a swirling vortex or a static crossfade. Use a closer medium-wide still with everyone mid-move, a simple repeating move and no end frame. Keep end frames for one subject or a scene-state change (a costume whirlwind, seasons, a clock).

**When the action leaves the frame, cut on the action.** In one riff shot she jumped up and out of the top of the frame, so the clip's last frames were a blur with her head cut off, useless as a start frame.
- **End the shot mid-action** in the editor (an early clip end), while the move is still readable.
- **Open the next shot on its completion,** a new still made with that frame as the continuity reference: she lands.
- **The viewer reads the cut as one movement.** This is the oldest trick in editing, and it is more robust than chaining from a spoiled frame.

**Designed end frames suit moves along a line.** A slide, a walk or a glide from one spot to another is what Kling's start-and-end interpolation does best. A backwards knee slide across a room landed exactly on the designed frame, with the doors open and Kevin in the doorway.
- **An end frame makes Kling obey; it doesn't make the idea right.** The director's note on that very shot: a slide backwards to the door makes no sense. It was built from a misread note. Read the move as a viewer before designing its end frame: a knee slide goes toward the camera.

**Which to use:**
- **Chain from the cut frame** when the action is unpredictable (a jump, a slide, a fall). You build on where it actually ended.
- **Use end frames** when both keyframes are designed and you want the clips in parallel.
- **When a clip ends somewhere other than planned,** rebuild the next still from where it really ended.

**Blend the seam.** Kling's first frames step a little and shift brightness. Blend 3–6 frames across every chained cut (`scripts/seam_blend.py`).

**Lip-sync shots are in the chain too.** The lip shot is a Kling singing take first (sound on, the lyric in the prompt), fitted against the vocal: lip-sync is used where Kling fails, not on every mouth shot. OmniHuman is the paid fix for a take that fails. Both animate a still:
- **The lip shot's still** is made from the previous shot's cut frame, and the next shot chains from the lip clip's cut frame.
- **Fix the still before the lip.** If the still's hair is pink, the lip clip's hair is pink. If the still looks CGI, so does the clip: judge it at full size against an approved frame first.
- **Everyone else in frame keeps their mouth shut** in the still and the prompt. In one shot the man beside her sang her line too.
- **OmniHuman looks where the still looks** (one take sang to her lap, twice): put her eyes on the lens in the still.
- **It drops hand props** unless the prompt pins the hands: "both hands stay exactly where they are in the image, holding what they hold".
- **It starts moving the mouth about 0.5 s in,** whatever the audio does, so don't open a lip shot on more than about 0.4 s of silence.

**Kling habits to write around:**
- **Walkers:** say where they stop ("takes two steps and stops under the arch"), lock the camera, and say the aisle stays clear.
- **Crowds:** a packed group gets a move that stays inside each body's outline.
- **Vehicles and lifts:** Kling moves them whichever way the still leaves room, so draw the vehicle where the move starts.
- **Fabric near a head:** a flowing gown or cloth next to a character's head gets pulled over it like a hood (one shot ended with Kevin hooded in Sara's gown). Say "his head stays bare and uncovered the whole time" and keep the fabric on the far side of the frame.
- **Slow motion:** ask for it in the prompt. Change speed in the edit only by frame blending, never by dropping frames. Below about 0.5× a clip reads as frozen (one clip at 0.44× did): re-roll with motion instead.
- **Every word of the motion line is obeyed.** An editing note ("the title slams on the hit (white flash)") came back as a white title card. Keep captions, flashes and overlays out of it.
- **Violent verbs become accidents.** "Rolls away waving both arms" tipped the chair over twice; "glides away slowly and smoothly, upright, the chair flat on its wheels, nobody falls" worked.
- **An action that must finish in the clip should start finished in the still** (the hat already over Kevin's eyes, the clip only lifts it).
- **Mirrors confuse it:** frame straight on.

**Remaking a flipped shot:** don't mirror the old still and ask for "an improved version".
- **Mirroring flips the set too:** the clock and the desk change walls.
- **Instead:** take the place, the camera side and the light from the neighbouring shot's frame, and only the action from the old still, attached mirrored so its sides already run the right way. Write the sides in words as well.
- **Check the result.** The image model sometimes flips the sides back anyway. If a new still has no text and symmetric identity marks, mirror that new still itself; it's free.

**Housekeeping:**
- **The previous shot beats the set anchor.** Its reference label says "the SAME place and camera side: keep every position and the sides; only the action changes". Never "new camera angle": that invites the flip.
- **Key the upload cache on the file's content hash,** never the path. A regenerated still at the same path was sent stale to Kling on two projects.
- **The still gate:** `scripts/join_check.py --stills`, the character sheet and the thread ledger, all before any clip is paid for. A flipped still is cheap to redo; a flipped clip costs a re-roll.

**What chaining costs:**
- **Time:** generation inside a scene is serial, so run scenes in parallel.
- **Re-rolls:** a bad clip early in a scene forces redoing the clips after it, so check every clip's cut frame before building on it.
- **Money:** unchanged. Each clip is still one Kling job.

## Part 3. Check it: every join, twice

**When:**
1. **After the stills:** before any video spend.
2. **After every cut:** as part of the cut review. The cut is what the viewer sees, captions included.

**The join check.** Run it from the video's project folder. The scripts live in this skill's folder: call them by full path (`python ~/.claude/skills/shot-continuity/scripts/join_check.py …`) or copy the whole `scripts/` folder into the project as `tools/` (each script finds its helpers and the face model beside itself). Python 3.10 or newer with the repo's `requirements.txt` (cv2, mediapipe below 1.0, imageio-ffmpeg, Pillow, numpy). The commands below assume the copy. `--fps` is the cut's frame rate (25 unless you say otherwise); `--montage-sets` names the places whose internal cuts are a list by design (`rap,epilogue` are examples from a later video).
```bash
python tools/join_check.py --cut CUT.mp4 --fps 25 --montage-sets rap,epilogue
```
```bash
python tools/join_check.py --stills --montage-sets rap,epilogue
```
- **Options:** `--from S --to S` for a window; `--out DIR` (the default is `review/joins` or `review/joins_stills`); `--sb` for another storyboard.
- **Storyboard fields it reads:** `id`, `t0`, `t1` and a place, `set` (or `fmt`); and optionally `look`, `scene` (naming KEVIN turns the Kevin test on), `join`, `scene_id`, `staging` and `still_file`. Without a place per shot, the light check over-fires.
- **What it writes:**
  - `min_MM_x.jpg`: one join per row. From a cut: A at −0.6 s, A's last frame, B's first frame, B at +0.6 s. From stills: the two stills. Under each row: the automatic flags and what B is meant to be.
  - `joins.json` and `JOINS_auto.md`. Copy `JOINS_auto.md` to `JOINS.md` and fill in the verdicts.
- **Speed:** about 4 s a join at 720p and about 13 s at 1080p on an M-series Mac at low priority (the side check reads six frames of every shot). Pass `--fps` if the cut isn't 25 fps.

**The automatic flags are hints, not verdicts:**

| Flag | What it measures |
|---|---|
| **SIDES** | Sara's side of Kevin reverses across a cut, or differs from where the scene set its line (the first shot in the scene that showed them both). Sara is found by her cyan irises, or by her platinum fringe when her eyes are down. Kevin is found by his dark moustache, and only in shots whose board row names KEVIN. Crowds and small background faces are ignored. Faces are searched in tiles, because a whole-frame pass misses mid-shots |
| **LOOK** | her outfit (storyboard `look`) changes inside one place |
| **PLACE** | the place changes without a TRANSITION, JUMP or MONTAGE mark |
| **LIGHT** | a colour or brightness jump inside one place, measured above the caption band. A white flash at the head of a shot is read as a transition device. On one video it agreed with a separate luma/warmth measure on 8 of 9 flags: keep this one implementation |
| **info: action** | A ends in fast movement and B starts still: did the action carry over? |
| **info: motion** | the dominant movement reverses at the cut |

Validated against a full eye review of the 100 joins in a later video's first cut: see `references/worked-example.md`.

**What it can't see, so the eye must:**
- a place change inside one named set;
- props and costume state;
- scale, eyelines and performance on the beat;
- sides when a face is covered or turned away (Kevin with a hat pulled over his eyes).

**The eye checklist, for every join, flagged or not.** Look at the four frames and answer:
1. **Place.** Is it the same place? If not, is there a transition in the picture?
2. **Sides.** Is everyone on the same side of the frame, with the camera on the same side of the action? Check against the scene's first two-shot, not only the shot before.
3. **Direction.** Does movement across the frame keep its direction?
4. **Action.** Does B start where A ended? Watch for teleports: on a board, then on the floor; kneeling, then sitting; by the door, then at the desk.
5. **State.** Are the props and costume the same? Guitar in hand, hat on or off, a mark on a costume, the audience in or out.
6. **Light and time.** Same light, time of day, weather and grade?
7. **Scale.** Same sizes and distances? Kevin and Sara are the same height.
8. **Eyeline.** If someone looks off-frame in A, is what they look at on that side in B?
9. **The beat.** On a riff or a hit, is the action performed (strumming, not posing)?

**The character sheet.** One face crop per shot, in story order, per character.
- **What it catches:** drift in seams, make-up, hair colour, neckline, lanyard, glasses and moustache, all in one row.
- **Run:** `scripts/face_sheet.py --cut CUT.mp4 --who sara`, then again with `--who kevin`, and also with `--stills`.
- **Expression is judged on the crops,** never on numbers alone. An energy scan missed a grimace.

**The thread ledger.** One table, one row per running prop, its state in every shot it appears in.
- **Filled from the board's state lines, checked against the frames.**
- **It catches what no face or colour measure can:** on one video Kevin played a part in one scene and was asleep somewhere else a few shots later, while someone else carried on in that part.

**Record it in `JOINS.md`,** one row per join: the time, A → B, the automatic flags, the verdict, the category and the fix.
- **Verdict:** `OK`, `FLAG`, or `BY DESIGN` (a MONTAGE cut, a TRANSITION with its device, a JUMP the lyric motivates). BY DESIGN needs a written reason a first-time viewer would follow; the board's label alone is never the reason (Part 3c).
- **Category:** PLACE, SIDES, DIRECTION, ACTION, STATE, LIGHT, SCALE, EYELINE, PERFORM or IDENTITY.

**Write the repair list only after the whole read, grouped by cause.** One cause usually explains several joins.
- **Fix order: prevention first** (the identity line, the set pack, the staging line), **then remakes by cause.** Nothing gets remade under the old rules.
- **Send the director the flagged joins as one sheet,** not all of them.

## Part 3b. Screen every clip against its row (the intent screen)

**Why it exists.** The director caught two clips in a later video that every continuity check had passed:
- **The action never happened.** She was waving something about at random, and a viewer had no idea what she was doing. The row's gag never took place.
- **Something appeared that the row ruled out.** An aeroplane sat behind the people and was dragged around as they moved, which made no sense. Kling had drawn a real aircraft into a shot whose joke needed there to be none.

Both were in the frame strips that had been read, but strips were read for faces, outfits and sides, never against the row's action. A continuity check asks "does this cut join?"; this one asks "does this shot do what it says, and nothing else?"

**Run it** after every batch of clips (and on the cut):
```bash
python tools/clip_screen.py --judge --workers 3
```
- **Options:** `--only ID,ID`, `--lips` (lip shots too), `--clip FILE --only ID` (a take that isn't installed yet), `--out DIR` (the default is `review/screen`).
- **What it screens:** 8 frames from the seconds the cut actually plays. The editor's `WINDOW`, `CLIPEND` and slow-down are read from the edit script given with `--editor`, if it defines them (a plain Python file with those dicts is enough; without one, every shot is screened from 0.15 s in).
- **What it writes:** `review/screen/<id>.jpg` (the frames, with the lyric, PICTURE, ACTION and STAGING printed above), `SCREEN.md` (worst first) and `screen.json`.
- **Automatic flags:**
  - **TRAVEL:** Sara's face moves across or toward the frame when the row has no travel word.
  - **SLIDE:** a big part of the picture slides one way while the camera should hold.
- **The judge** (`--judge`): ChatGPT through the Codex command-line tool (installed and signed in; any command-line tool that can look at an image and answer in text can be swapped in), read-only, about 15–20 s a clip. The prompt carries the row's full text (lyric, PICTURE, ACTION, STAGING), not just the strip's header, which cuts long rows off. It also carries EARLIER, the scene's previous two shots, so things carried over from them don't count as new. It answers fixed questions:
  - does the ACTION happen, and from which frame;
  - what APPEARS that the row, staging and earlier shots don't explain;
  - what MOVES WRONG: props sliding by themselves, crowds sliding like flat pictures while the camera holds, vehicles backwards, characters wandering off;
  - would it READ in one second at phone size, and is anything BROKEN;
  - **VIEWER READ:** what a first-time viewer would think the main character is doing;
  - **SEVERITY** for that viewer, watching once on a phone: 3 confused or looks like a mistake (can't say what she's doing, something big that shouldn't be there or contradicts the joke, something large moving impossibly, a melting face), 2 an attentive viewer notices, 1 only in still frames, 0 nothing.
- **Verdict:** **FAIL** is severity 3, and it must be confirmed. A second, fresh look (`--confirm 1`, the default) must also say 3, or the clip drops to CHECK. **CHECK** is severity 2, or the action never happens. Everything else is OK.
- **Calibrated on one cut of a later video** (`references/intent-screen-calibration.md`). The director flagged exactly two of its 77 clips, so the other 75 count as accepted.
  - The first rule (FAIL on any "appears" or "moves wrong" answer) caught both flags and failed 35 accepted clips. A vision model can always fill those lists, so that rule was noise.
  - The calibrated rule catches both, in words close to the director's: she is dancing and waving a prop about; a visible aircraft contradicts the gag. It also passes both fixes. With the confirm pass it fails 5 of the 75 accepted clips (it was 35), all misreadings a glance at the strip clears; the list is in the reference.
- **Known false alarms:**
  - tracking shots (the background passing reads as a sliding crowd, even with a line in the prompt saying that's normal). NOT a subject who grows faster than the background while facing away: that is a backwards slide however the camera moves (one was measured away as a camera move, and the director saw it at once). Watch it at tenth-of-a-second steps; a direction-of-travel flag stands unless the subject plainly moves the way it faces;
  - a car receding from a fixed camera;
  - a prop that swings;
  - headless figures: it can't tell front from back, so it reverses which way they walk;
  - things the staging allows, such as a costume on a stand that is meant to walk off.
- **Practice:** read every FAIL's strip by eye before it reaches the director, and glance at the CHECKs. Report what's confirmed; remake only what the director agrees to.
- **Screen the sung shots too** (`--lips`). One screen skipped them, so nobody looked at her hands rising mid-shot or at the man beside her mouthing her line.
- **A wrong-direction flag stands** unless you can show in motion that the subject moves the way it faces. Once the flag was measured away as a camera move, and the director saw the backwards slide at once.
- **After changing the question, re-calibrate:** `--rejudge <an earlier run> --sb <the rows as they stood>` re-asks about existing strips without re-sampling (`--keep` runs only the confirm pass). Judge a flagged clip against its row as it stood BEFORE the director's note, or the answer leaks in: one flagged row now literally says "no aeroplane".

**Write rows the screen can check.** The judge compares against the words, so the ACTION must say what visibly happens and what doesn't: "no aeroplane anywhere", "nothing slides", "his head stays bare". Keep the row in step with the take that's in the cut. A row edited after its clip was made shows up as a false FAIL.

**Design the action so it can't miss.**
- **Put the target where the action naturally lands.** A mallet swung at a target above her head passed under it; a target at head height beside her got hit.
- **Make the end frame the moment of contact,** or the state change you need, not just the aftermath.
- **An end frame identical to the start freezes the shot.** Nothing moves for 4 seconds. Use a designed end frame with the same camera and new poses instead.

## Part 3c. Read the whole film in order (the end-to-end story pass): the gate before any cut is sent

**Why it exists.** One cut of a later video passed the join check (56 fine, 44 "by design", no flags) and the intent screen. The director watched it once:
- **From the first chorus on it was disjointed, with no continuity.** Kevin was outside, then inside; Sara was further down the room, then he was on a big chair, then it cut to her and back to him; the audience was sitting, and in the next cut it was half-way out of the door.
- **Nobody had looked at the video end to end.** It was true.
- **The problem was endemic,** and the protocol that should have caught it had a gap.

**What was missing:**
- **Nobody read the film in order.** Parts 3 and 3b are local: four frames round one cut, eight frames of one clip. A run of shots that each pass can still tell no story.
- **The join check tracks the wrong state.** It compares faces, Sara's outfit, sides, place labels and light, never where each character is, what they do, wear and hold, or what the crowd is doing.
- **Costume was compared only with the neighbouring shot.** Kevin's hat, cloak and bag flipped on four cuts running, with other shots in between.
- **A board label switched the checks off.** Any cut marked JUMP or TRANSITION was verdicted "by design": 44 of 100.
- **The board wrote a continuous event as a list of pictures.** The first chorus is one walk: down the room, out of the doors, and back. It was written, stilled and animated as 13 separate gags.

**The pass, on every cut, before it is sent** (and on the stills before any clip is made):
1. **Sequence sheets:** `scripts/story_sheets.py CUT.mp4 review/story_cutN`. It writes six shots per sheet, in order, each with its first, middle and last played frame, its time, lyric and board picture. It also writes one four-frame image per cut for the judge. Decoding once takes about 30 s.
2. **Read every sheet in order and keep the STATE LEDGER as you go.** Per shot, record for each character:
   - **where:** the set, inside or outside, where along the aisle or in the room, screen side;
   - **what they are doing:** sitting, standing, walking which way, kneeling, riding;
   - **what they wear:** every item, including hat, cloak, straps, bag, gloves and look;
   - **what they hold.**
   Per shot for the crowd: seated, standing, cheering or leaving; present or empty.
3. **Every change between one state and the next must be SHOWN** (someone does it on screen) **or be an obvious move to another place or time that a first-time viewer follows.** Anything else is a break. Compare costume and props with the **last shot that character appeared in**, not only the neighbouring shot.
4. **The join judge on every cut, labelled or not:** `scripts/join_judge.py review/story_cutN`. A vision model (ChatGPT through the Codex CLI, about 20 s a cut) compares A and B for place, action, costume and props, lists the unexplained changes and rates them. A severity 3 is asked again and stays a FLAG only if the second look agrees. On the cut above it confirmed 15, including 10 the director had called out. It can't see a costume change across a gap (the ledger does), and it flags gag-to-gag jumps in list sections, which you read as MONTAGE.
5. **Merge the ledger breaks and the judge's flags into `review/E2E_cutN.md`,** in time order, each with what a viewer sees. Send that with the cut.

**What the pass still missed, and now includes:**
6. **Read every shot in motion,** a frame every 0.25 s (per clip: `scripts/framecheck.py`), and at 0.1 s where anything moves oddly. Three frames a shot missed her hands rising mid-shot and a backwards slide.
7. **Nothing is exempt.** Not the ending the director liked before (a pose snap went through), not a minute that was "approved" earlier (one shot there, never re-checked, was the cartoon face), not the sung shots.
8. **Look at every shot at full size for the look:** photoreal live action, not CGI, a Pixar face or a doll; no melted face; no ugly expression. A vision model can shortlist them if it is asked *relative to* an approved frame, because asked absolutely it calls every AI frame "CGI". A freeze measure finds shots that barely move. Both came from the director's notes on one cut: frozen stills in it, and a shot where she looked like a cartoon, none of them caught before sending.
9. **A still standing in for a clip carries a burned-in label** ("STILL <id> - NOT ANIMATED YET"), and the message lists every one. Saying so in the message wasn't enough.

**No free passes.** A board label never makes a join BY DESIGN on its own. A JUMP, TRANSITION or MONTAGE verdict needs a written reason a first-time viewer would follow ("a white flash on the chorus into a new place", "the curtains part on the show"). Inside one continuous event (a walk, a procession, a performance), a costume, prop or crowd change must be done on screen.

**The planning half (Part 1, rule 3, made a gate).** Before any still for a scene that is one continuous event, write its ledger as a table: for every row, each character's start and end state, and the crowd's. Row n+1's start state is row n's end state, word for word. That table is where the end frames come from (Part 2). A scene written as a list of gags, one per line, is a MONTAGE: each shot may be a new situation, but recurring characters keep their costume from the last shot they were in.

## Part 3d. When a section's fixes go in circles: stop and restage it as one event

**Why it exists.** A later video's first chorus was fixed shot by shot through two cuts and got worse. On the second, Kevin was at the door, then Sara was back in the middle of the room with no Kevin, and in the next shot he was back again and walking. The director's verdict: the whole sequence didn't flow or make sense, the fixes were going in circles, and it was time to stop and rethink it rather than make knee-jerk fixes. Another video's intro broke the same way (inside, then suddenly outside). The read found five breaks where the director had named two.

**Why fixes go in circles:**
- **Every fix is local.** Each remake moves people between shots its neighbours don't know about.
- **Too many physical moves for shot-by-shot generation.** Six moves in 30 seconds, each generated blind, so every hand-off can break.
- **Old paid shots bend the new staging.** The sung shots, framed for the old staging, were kept because they cost money, and the new staging was bent around them.
- **The story itself doesn't hold** (he left through the doors and was carried back in four seconds later, with no reason).

**The restage:**
1. **Stop remaking.** Say the section is being rethought.
2. **The story in two sentences.** Who goes where and why, with every change happening on camera. Keep the director's picked gags on that one line.
3. **One axis and its camera positions.** Draw the set as a line (one end of the room ↔ the doors at the other) and name 2–3 camera positions on it.
4. **Sides are relative to the camera, not the frame.** Write the relation that holds ("Sara stays on Kevin's left arm"); from camera 1 she is screen-left, from the reverse angle screen-right. An older rule, "always screen-left", was wrong for a reverse angle.
5. **A shot list of start → end states,** one row per shot, each start equal to the previous end. Mark which clips are kept, which are new, and which kept shots now contradict the staging.
6. **The decisions for the director,** with the free and paid routes for each (a sung shot that only a paid lip-sync can fix; a free alternative, such as a wide where her mouth doesn't read).
7. **A section animatic** with the song: kept shots as cut, new shots as their start still fading into their end still. **No video until the director says yes.**
8. **Then** the stills (each start = the previous end), the clips chained (each shot generated to the next one's first frame as its end frame), every clip checked in motion, **a preview of the section with sound**, and only then the full cut with the end-to-end pass.

## Part 4. Fix it: free first

| Category | Free fix | Paid fix (quote it, get a yes) |
|---|---|---|
| SIDES | mirror the clip in the editor. Not when anything in frame reads (text, numbers, a logo, a clock with numerals) or the story needs a clock's time. A clock with tick marks only flips its time; a one-sided mark (an ear cuff, a side parting) changes side, so check it against the rest of the film. Look at full-size crops, as cut and mirrored, before calling it safe | a new still with the neighbour as reference and the sides written in, then a re-roll |
| ACTION | move the window so A's played part ends where B's action starts, if the clip contains that moment | re-roll A with an end frame = B's still (same camera), or remake B's still from A's cut frame and re-roll B |
| PLACE (inside a scene) | reorder or cut the shot, if the lyric allows; a whip or a dip in the editor as the device | a new still from the set reference and the previous shot, then a re-roll |
| LIGHT | a grade match in the editor for small steps | regenerate |
| PERFORM | none | re-roll with the beat written as continuous motion |
| STATE | move the window to avoid the moment; paint it out from the clip's own plate on a locked-off shot | regenerate |
| IDENTITY | recolour hair on a finished lip clip | fix the still first (an image-model edit that changes one thing only), then redo the lip or clip |
| DIRECTION | mirror (same limits as SIDES) | re-roll with the direction written in |
| LOOK (a CGI or cartoon face, a melted face, an ugly expression) | a photoreal remake of the still (ChatGPT images), judged at full size against an approved frame, then a new Kling take | an OmniHuman redo only if it's a sung shot whose Kling take fails (stills shown, quote first) |
| SCALE | none, once stills are made at the wrong camera | new stills from the scene's planned camera positions with scale anchors, chained in order, then re-rolls |

**After any fix:**
- **Re-render only those shots.**
- **Blend the seams** of any chained joins.
- **Run `scripts/join_check.py --cut` again** over a window around them, and show the before and after.

## Files
- **Scripts** (`scripts/`):
  - `scripts/join_check.py`: the join checker. Its face model is in `scripts/models/face_landmarker.task`.
  - `scripts/face_sheet.py`: the character sheet.
  - `scripts/clip_screen.py`: the intent screen (Part 3b), each clip against its row, with the vision judge.
  - `scripts/story_sheets.py`: the end-to-end pass (Part 3c): the whole cut in order, six shots a sheet (first, middle, last frame + lyric + board picture), plus one four-frame image per cut.
  - `scripts/join_judge.py`: the vision judge on every cut (Part 3c): place, action, costume and props across A and B, with a confirm pass.
  - `scripts/chainlib.py`, `scripts/chain_frame.py`, `scripts/seam_blend.py`: the chaining kit (parametrised with `--sb`, `--clips` and `--window`).
  - `scripts/framecheck.py` and `scripts/regioncheck.py`: every Nth frame of a clip's used seconds, and one region at full size.
  - `scripts/gen.py`: Higgsfield jobs with the `end` key and the content-hash upload cache (it writes its cache, `uploads.json`, beside itself).
  - `scripts/fonts.py` and `scripts/venc.py`: fonts on any machine; the machine's GPU encoder, x264 otherwise.
- **References** (`references/`):
  - `references/generation-flow.md`: the order of work and post-processing, agreed with the director.
  - `references/worked-example.md`: one stretch of a later video's first cut examined, the full join review in numbers, and the scene restaged under these rules.
  - `references/intent-screen-calibration.md`: how the intent screen's judge was tuned and measured, and how to measure it again.
  - `references/project-pack.md`: optional: the `project_pack.json` a video can keep (no script for it is shipped), with everything stored and mapped to the project so it can be used as content (a website, a making-of). The join sheets, character sheets and repair lists go in its `qa` block; the review boards count as content too. The script that writes the pack and the website that reads it are not in this repo; the format is here to write your own.
