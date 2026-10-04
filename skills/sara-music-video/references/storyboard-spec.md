# The storyboard spec: the board is the contract

**Why this file exists.** Across three later videos the director caught 33 problems (the map is in §6). On a reading of the record, **29 of the 33 were decided, or left undecided, in the storyboard**: a story that was a list of pictures, a scene with no camera positions, a costume change nobody planned, an action Kling can't do, a lip line with no route. Every later check compares a still or a clip against its board row, so when the row is silent, no check can find the fault; the director finds it, and we patch. The director's verdict: a lot of it should have come from the storyboard, and much of the later work was patching what could have been sorted out a lot earlier.

**How to use this (light touch).** This is the toolbox for the parts of a board that need more than the wrapper (`wrapper.md`): mainly continuous scenes, home sets, and anything that recurs. **A montage video needs only what Out of Office had:** id, times, the lyric, who sings, the picture, the action, the references, plus the join type. Everything else here is offered for when a scene needs it, not demanded: too many constraints lead to poorer work.

**The one idea.** The board decides what a later stage would otherwise guess. When shots have to connect (one event over several lines), decide the connection on the board: the set, the angles, where everyone is and what they wear and hold, how each shot is made. When they don't, don't.

`creative-playbook.md` §5 holds pacing, captions and wardrobe detail; the shot-continuity skill (Parts 1 and 1b) holds the continuity reasons behind the fields below.

---

## §1 The three layers

A board has three layers, written in this order. The machine form is `bible.json` (layers A and B) and `storyboard.json` (layer C); the human form can be one Markdown file that a builder parses.

### A. The bible (once per video, signed off by the director before any shot row)

| Field | What it holds | Prevents |
|---|---|---|
| `frame` | the one idea every section lives in (for example: one couture fashion show) | two concepts spliced into one video |
| `benchmark` | planned counts against Out of Office: shots, mean shot length, lip shots and their share of the runtime, gags, places, world switches, Sara's look changes | a stale board: close-ups with nothing happening in the backgrounds |
| `identity` | one fixed line per character, word for word in every prompt, naming the marks that drift (seams, make-up, lanyard, hair) | Sara's seams growing across 17 lip shots; a round-faced Kevin |
| `looks` | per section: the look id and its reference image, from your artist's wardrobe references or signed off for this song | outfit drift (the dress changes in the close-up); a look too covered and basic for her |
| `sets` | the video's set list, kept short and reused (a home set for the chorus, the places continuous scenes happen). Per set: an EMPTY reference per lighting state, a floor plan in words (what is where, where the exits are, where the line runs), and **2–4 named camera setups**, each with an empty plate from that angle (§1c) | five pubs in six shots; people coming out gigantic; one plaza drawn as five buildings |
| `props` | every thing seen in more than one shot (a portal, a key, a creature, a sign, a costume piece): one sheet image | a key that changes design; a creature in two designs; a portal changing shape |
| `designs` | each character version (a second version of the artist, a costume variant) as its own reference image | one character version in three designs |
| `money` | which shots need paid work and why (a lip fix fallback, a 2K still), with the quote | surprise spend |

### B. Scenes (one per place and stretch of time)

| Field | What it holds | Prevents |
|---|---|---|
| `id`, `set`, `light` | the place and its lighting state (from the bible) | the day reference used for night |
| `kind` | **continuous** (one event: a walk, a procession, a performance), **montage** (a list of gags, each shot a new situation), **home** (a recurring set revisited with escalation, like a chorus), or **single**; a section can hold several scenes of different kinds. Judged against the song (§1b), with the reason written in `why` | writing a continuous event as a list of pictures (a later video's first chorus, another's intro) |
| `story` | continuous scenes: the event in two sentences, with every change of place, costume or crowd happening on camera | a character outside, then inside, with nothing shown in between; a whole sequence that doesn't flow |
| `axis`, `cams` | the line the action runs along, and which of the set's camera positions this scene uses | the flipped angle; the reverse angle read as a flip |
| `relations` | who is where relative to whom ("Sara stays on Kevin's left arm"), not screen sides; screen sides follow from the camera | "always screen-left" being wrong from the reverse angle |
| `direction` | which way travel runs along the axis, per camera | screen direction reversing |
| `moves` | how many physical hand-offs the scene asks for (walk away, reach the doors, the stamp, the pivot, out, carried back = 6) | too many blind hand-offs in 30 s: every one is a place for a break |
| `ledger` | continuous scenes: a table, one row per shot, each character's and the crowd's start and end state (where, doing, wearing, holding); row n+1 starts where row n ends, word for word | costume flips across gaps; the crowd seated, then leaving, then seated |

**The move budget.** Each physical move is generated blind, so each is a place the chain can break. A later video's chorus asked for six in 30 seconds and went round in circles for two cuts. As a working limit (an inference from that section, not a measured law): more than about 4 moves in 30 s of a continuous scene means simplify the story, or plan each extra move as a designed start + end frame pair.

### C. Shots (one row each)

Fields the existing tools already read are marked ●; keep those names. "always" means Out of Office had it or it costs nothing; everything else is for when the scene needs it.

| Field | When | What it holds |
|---|---|---|
| ● `id`, `t0`, `t1` | always | song times. One Kling clip plays at most 4.7 s (a 5 s clip is 4.84 s at 25 fps); longer needs `long: true` (a 10 s clip) or a chained second clip |
| ● `cap` | always | the lyric under the shot |
| ● `voice` | always | who is heard: S (Sara), K (Kevin), M (male), a code for any other vocalist, none. From the casting check, *as sung* |
| ● `type` | always | `gen` (a Kling clip), `lip` (a mouth shot), `graphic`, `still` |
| ● `scene_id`, `set`, `look` | always (a montage shot's set can be its own) | from the bible and the scene |
| ● `scene` | always | **the picture**: what the still shows, in one camera, with every visible character's state |
| ● `motion` | gen and lip | **the action**: one action, what visibly happens, in words Kling can do (§4). No editing notes |
| ● `join` | always | FLOW, SAME, JUMP, TRANSITION or MONTAGE (shot-continuity Part 1) |
| `join_why` | JUMP, TRANSITION, MONTAGE | the reason a first-time viewer follows it: the device in the picture ("a white flash on the chorus into a new place", "the curtains part") |
| `cam` | continuous and home-set scenes | which named camera position |
| `scale` | when more than one subject, a crowd, a vehicle or architecture | a scale anchor in words ("the same height as the fans around him, the stands tower behind") |
| `start`, `end` | continuous scenes; any shot with a costume, prop or crowd change | the state at the first and last played frame; for FLOW, `start` = the previous row's `end` |
| `not` | when the gag depends on something being absent, or Kling is likely to add something | explicit negatives ("no aeroplane anywhere", "his head stays bare", "the aisle stays empty") |
| `route` | inside a scene where shots connect | how the shot is made: `chain` (from the previous shot's played frame), `end` (landed on a designed end frame), `fresh` (from the anchors; only a scene's first shot or a montage shot) |
| `perform` | music shots | the motion of the music, mapped from the stems: where the instrument plays, where it stops, the rests. Htdemucs' "other" stem isn't the guitar (synths stay loud after a riff): split with `htdemucs_6s` or mark the guitar passages by ear. For the guitar: strap, pick over the strings, fingertips on the frets, big down-strokes; a dead stop in the music is a dead stop in the hands |
| `lip_route` | lip | `kling` (the default: a singing take, sound on, the lyric in the prompt) or `omni` (only after a Kling take failed and the director said yes) |
| `props` | when a sheet exists | which prop sheets to attach |
| ● `refs`, `still_file` | filled by the builder | the reference images; the made still |
| `read` | worth writing for any gag; a must for a continuous scene | one sentence: what a first-time viewer understands in one second at phone size. If you can't write it, the shot isn't designed yet |

---

## §1b Montage, continuous, or both: judged against the song

The form is dictated by the storyboard against the song (the director's rule): judge which works better, and it can be continuous plus montage. If it is continuous, it is like directing a film: it needs sets that are reused, planned angles and so on. Neither form is the default: read each section's lyric and music and choose. Write the choice and the reason into the scene's `kind` and `why`.

| The song does this | The form that usually works | Example |
|---|---|---|
| each line is its own joke, claim or list item | **montage:** a gag per line, each shot its own situation and place | Out of Office's verses: an office, a desert of data centres, VR pods, the Moon, a zoo |
| the hook comes back several times | **home set:** one set revisited on every chorus, escalating each time | Out of Office's server-hall nightclub on every "O-O-O, OUT OF OFFICE!" (0:46, 1:09, 1:46); by the last one the floor has fallen away to show the Earth |
| several lines tell one event (a walk, an arrival, a meeting, a chase, a ceremony) | **continuous:** directed like a film (§1c) | a later video's first chorus: one character's walk to a pair of doors and back |
| a riff, a solo, a dance break | **performance:** one set, coverage round the performer, the playing or dancing fitted to the beat | a later video's guitar riff |
| a continuous event with jokes hanging off it | **mixed:** a continuous scene with cutaways; a cutaway never contains someone who is in the main scene | a later video's cutaway to a doorway, once Sara was taken out of it |
| a list inside a story (a rapped list) | **montage inside the section,** with a device in and out (a whip, a flash, a dip) | a later video's rap |

**Judging it:**
- **The words lead.** If the listener hears one situation developing, the viewer should see it develop in one place. If the listener hears a list, a list of pictures is right.
- **The music confirms it.** A held, building passage suits one space; a fast, choppy passage suits cuts between places.
- **Continuous costs more.** Every shot is chained to the one before (serial, not parallel), every cut is a place it can break, and it needs a set, a floor plan, camera setups and a ledger. Use it where the song tells one event, not everywhere.
- **Montage is cheap and forgiving,** but only if each shot is a real situation with a gag. A montage of close-ups in front of backdrops is what the director found tame and boring.
- **The mix of forms is part of the pacing.** Out of Office alternated gag verses with the nightclub chorus; the return to the home set is what makes the chorus land.

## §1c Directing a continuous scene (like a film)

A continuous scene is made the way a film scene is shot: the place is designed once, the actors are blocked in it, the camera setups are planned, and the coverage is cut together. Each AI shot is still generated on its own, so everything a film crew holds in their heads has to be written down.

1. **The set, designed once and reused.** One empty reference per lighting state, and a floor plan in words: where the fixed things are, where the doors are, where the audience sits, which way the light falls. The same set comes back later in the video when the song returns to it (a callback costs nothing in design).
2. **The blocking.** Where each character starts, where they move, where they end, beat by beat against the lyric. This is the ledger (§1 B): each row's start and end state. Keep physical moves within the budget; every move is a hand-off Kling does blind.
3. **The line and the setups.** Draw the axis the action runs along. Name 2–4 camera setups on one side of it: a **master** (wide, the whole geography), a **closer** angle (a two-shot or a single), an **insert** (hands, a prop, a screen), a **reaction** angle (the crowd, Kevin's face). A **reverse** angle across the line is planned as its own setup with the relation that holds written down ("Sara stays on Kevin's left arm": screen-left from one side, screen-right from the other).
4. **A plate per setup** (recommended, not yet tried as a rule): an empty frame of the set from each setup's angle, made once from the set reference. Every still from that setup takes its plate as the geography and scale reference. A later video's giant people came from making every still off the establishing wide; its finale held together once the shots were grouped by camera position (back wide, the pit, stage front).
5. **The coverage plan.** Which setup each shot uses, so the cut follows film grammar:
   - establish with the master before going close;
   - go back to the master when the geography changes (someone arrives, leaves, the crowd moves);
   - cut on the action (a FLOW join), matching the movement across the cut;
   - match eyelines: if she looks off-frame right, what she looks at is screen-right in the next shot;
   - after a cutaway, re-establish before continuing.
6. **Make it in setup order within the scene.** Make each setup's stills together from its plate (like a crew shooting everything from one camera position before moving it), then chain the clips in story order from the played frames.
7. **The script supervisor.** The ledger is checked shot by shot as the stills and clips arrive: position, costume, props, crowd, screen direction. In a later video a crown, a cloak and a backpack flipped on four cuts running because nobody held this job.

---

## §2 Writing the board, step by step

Do these in order. Each step's output is reviewed before the next starts; the director signs off at the steps marked ✋.

1. **The frame and the spine** ✋. One frame for the whole video. The spine table: section → premise → escalation. Count world switches: a second version is rebuilt as one world, never bolted on.
2. **The benchmark.** Planned shots, lip shots, gags and places against Out of Office (74 shots, 14 lip, a gag per line, a mean of 3.2 s; `creative-playbook.md` §5). About 15–26 lip shots, each inside a gag, never a talking head in front of a backdrop.
3. **The form of each section, judged against the song** (§1b): montage, home set, continuous, performance or a mix, with the reason. This decides how many sets the video needs and where the expensive continuous scenes are.
4. **The bible** ✋: identity lines, looks per section (from your artist's wardrobe references), the set list (short, reused), each set's pack with its floor plan and camera setups, prop and design sheets. **Make and sign off these images before any shot still** (the director's rule: a location used in more than one scene gets its set references before the video starts).
5. **The scenes**: place, light, kind. For every **continuous** scene, direct it (§1c): the story in two sentences, the blocking, the axis, the setups, the relations, the direction, the move count, the coverage plan. If the move count is over budget, simplify now.
6. **The ledger** for every continuous scene: each character's and the crowd's state per row. Read it top to bottom as one story. Every costume, prop or crowd change is something someone does on screen.
7. **The shot rows**, from the ledger (continuous scenes) or the gag list (montage). Fill every required field.
8. **Design each action for Kling** (§4): one action per shot; an action that must finish starts already under way; the target sits where the action naturally lands; the end frame is the moment of contact; the explicit negatives; the risky words replaced from the wording library.
9. **The mouth shots**: who sings each line as sung; head-and-shoulders framing with the face at about a third of the height; eyes on the lens; nothing in front of the mouth; everyone else's mouth shut in the picture; `lip_route: kling`. Lip shots start no more than 0.4 s before her first word and stop before another voice's first word.
10. **The music**: every riff gets Sara playing (strap, hands on the strings); every dance is one repeated step; plan the beat fit in the edit.
11. **The route** per shot: chain inside a scene, end frames where both keyframes are designed and the camera and place are shared, fresh only at a scene's start. Never two adjacent shots from one still.
12. **The viewer read** per shot. Then read all the `read` sentences in order: they should tell the video's story on their own.
13. **The board read** (§3), with the lint (`scripts/board_lint.py`, optional) as a list of things to look at, then ✋ the director signs off the board.
14. **The animatic** ✋ (stills in order with the song) once the first stills exist, before any clip.

---

## §3 The board gate

**The lint** (optional; mechanical, deterministic, free): a list of things to look at, not a gate. `python tools/board_lint.py storyboard.json [--bible bible.json]`. It reads the board text for the known mistakes: adjacent shots sharing a still, editing notes in a motion line, walkers with no stop, filter words, over-long shots, lip rows with no singer or route, labelled joins with no reason, continuous scenes with no ledger, FLOW joins whose states don't match, missing camera or scale, props with no sheet, risky verbs, multi-action lines, and the counts against the benchmark. **Run on four real boards** (FIX / LOOK):
- Out of Office 3 / 7, nearly clean;
- three later videos: 7 / 82, 7 / 118 and 4 / 22.

**What it found:**
- **The move-budget rule flagged exactly the two broken sections of one later video:** a riff that jerked and switched, and a first chorus that went round in circles.
- **It found the rows in another board that caused known failures,** still unfixed in the board: "walk down the aisle toward the camera" (the walker that hit the lens) and "sits on the edge of the bed" (the pose wording ChatGPT blocked).

**Its limits:**
- It reads the board, not the text a builder adds to prompts later: one board's builder adds the playing wording to its riff prompts, so the lint still flags those rows.
- Its word lists are heuristics.

Read what it lists and decide; fix the board when it's right, ignore it when it isn't. A board written to this spec gets new checks too: kind and why per scene, directed continuous scenes, ledgers, setups in the scene's list, and prop sheets.

**The board read** (a person or a Claude Code session, in order, before the director sees it):
0. **The forms.** Play the song with the board open. Does each section's form (§1b) suit what the words and music do? Is every continuous scene directed (§1c): a set from the set list, a floor plan, blocking, named setups, a coverage plan? Does the chorus have a home to come back to?
1. **The counts.** Do the numbers beat or match Out of Office? More places and gags, not more close-ups.
2. **The story.** Read the ledger and the `read` sentences top to bottom. Could someone who has never seen the video retell each section?
3. **Every state change is shown.** Costume, props, crowd, place: someone does it on screen, or a device carries it.
4. **Every labelled join has a viewer reason.** No label passes a join by itself.
5. **One axis per scene.** Every shot names a camera position from the scene's list; a reverse angle is planned, not an accident.
6. **Scale.** Anyone who could come out bigger than the architecture has an anchor.
7. **Recurring things.** Every prop, creature, device and character version seen twice has a sheet.
8. **Each action.** Can Kling do it in one 5 s clip from this picture? Does it finish inside the played seconds? Are the negatives written?
9. **Each mouth shot.** Who sings, framed for a mouth, the route, everyone else silent.
10. **The music.** Riffs played, dances one step.
11. **The money.** Every shot that might need paid work, listed with a quote for the director.

---

## §4 The wording library

*Moved to `wrapper.md` §3: it applies to every shot, not only continuous scenes.*

### §4b Other board-time rules (from earlier videos)

- **Plan the key action inside about 0.5–3.3 s of a 5 s clip.** Kling often does the key action only in the first or last second, and reverses or stalls late (in one video a clip flipped at 3.42 s, another stalled and a third drifted through its first half). For beats over about 2.8 s, split into two shots or plan a chained second clip. The hard limit is 4.7 s on one clip.
- **Every montage shot has its own location and palette.** The director found one video's first 37 s of white voids generic: the same aesthetic repeating.
- **Say which way an onboard camera faces:** "camera looks forward over the driver's helmet down the tunnel", not "T-cam above the cockpit", which gave a camera looking back at the driver.
- **Chanted multi-voice lines** (one word chanted by many voices): one lip-synced close-up tiled into a grid, not a crowd mouthing it.
- **Text-only beats** (a chat emptying, a survey card, telemetry) are motion graphics built in code: free, legible, exact.
- **Real people only as silhouettes with job titles;** parody brand names and logos only; made-up sponsors scoped to where they belong.
- **Logic gags must read in one look.** Sara flying out of a car made no sense; the gag became a pit-crew lollipop sign reading FIRED. Show the social point in action (a multi-generation family ignoring each other), not a generic crowd.
- **Characters on screen during someone else's line** get "lips closed, not speaking" in the still and motion prompts.
- **Phrase-safe cuts:** a singing shot ends after the last word of its line, and held notes run long; check with `scripts/cut_audit.py`.
- **A closed-mouth tail** after a sung line, rather than more lip-sync through the silence.
- **Consecutive mouth lines in one place:** a Kling take per line, chained, rather than one still reused.

---

## §5 The machine form (example)

`bible.json`:
```json
{
  "frame": "a couture fashion show",
  "benchmark": {"shots": 90, "lip": 20, "places": 12},
  "identity": {"SARA": "platinum-silver bob, glowing cyan eyes, two thin chrome seam lines, one each side of the chin, none on the cheeks"},
  "looks": {"HOST": "gen/looks/host.png"},
  "sets": {"runway": {"day": "gen/sets/runway_day.png", "layout": "curtains at the top, glass doors at the far end, front row both sides",
                      "cams": {"C1": "top of the runway looking down it", "C2": "outside the glass doors looking in"}}},
  "props": {"stamp": "gen/props/stamp.png"},
  "scenes": [{"id": "S05", "set": "runway", "light": "day", "kind": "continuous",
              "story": "Kevin struts to the glass doors; Sara lets him through, stamps him and he pivots back. At the top the attendants carry him down on a chair.",
              "axis": "the runway", "cams": ["C1", "C2"], "relations": "Sara stays on Kevin's left arm",
              "direction": "away from C1, toward C2", "moves": 4}]
}
```

A shot in `storyboard.json`:
```json
{"id": "X02", "t0": 106.5, "t1": 107.8, "cap": "(the sung line)", "voice": "S", "type": "gen",
 "scene_id": "S05", "set": "runway", "look": "ENCORE", "cam": "C2",
 "scene": "In the open glass doorway Kevin steps in beside Sara; she raises the stamp; the front row seated behind",
 "motion": "she stamps the seat of his shorts once; he hops on the spot; the camera does not move",
 "join": "SAME", "route": "chain", "scale": "Kevin and Sara the same height; the doorway twice their height",
 "start": {"KEVIN": "in the doorway, crown on, facing camera", "SARA": "beside him, stamp raised", "crowd": "seated"},
 "end": {"KEVIN": "hopping, a red stamp mark on his shorts", "SARA": "stamp lowered", "crowd": "seated"},
 "not": "no second stamp mark; the doors stay open",
 "read": "She stamps his backside and he hops"}
```

---

## §6 The shift-left map: where each problem should have been caught

Every problem the director caught in those builds, the stage that could have prevented it, and the board field or rule that now does. "Board" includes the bible. The reading of each is this skill's; the catches are the director's, put in plain words.

| # | The director caught | Should have been caught at | Now prevented by |
|---|---|---|---|
| 1 | a stale board: close-ups, nothing happening in the backgrounds | board | `benchmark`, step 2 |
| 2 | looks too covered and basic for her | board (bible) | `looks` from your artist's wardrobe references |
| 3 | the dress changes in the close-up | board | `look` per row, pinned to a reference |
| 4 | the first 30 seconds a mess (shots made from one still) | board | lint: adjacent stills |
| 5 | a dance that was too fast and looked uncoordinated | board | `perform`: one step; §4 |
| 6 | portals the wrong way, different shapes, no enter or exit | board (bible) | `props` sheet; ENTER and EXIT rows |
| 7 | a key that changes design; a creature in two designs | board (bible) | `props` sheets |
| 8 | a costume going from chrome to orange to red with no visible reason | board | `start`/`end` + route `end` for the change |
| 9 | faults only a frame check finds (a portal rim over a leg; a boat jumping) | board + clip check | FLOW + `route: chain`; clip strips |
| 10 | the scale completely broken: people gigantic | board (bible) | `cams`, `scale` |
| 11 | setting continuity problems throughout (five pubs) | board (bible) | `sets` pack, scene `set` |
| 12 | good individual scenes with no continuity between them (flipped sides, Sara in two places) | board | `axis`, `relations`, cutaway rule |
| 13 | lots of little breaks (a plaza as five buildings, one character version in three designs, seams drifting) | board (bible) | `sets` per light, `designs`, `identity` |
| 14 | she seems to wave something at random (the gag's hit never happened) | board + clip check | §4 target placement; the intent screen |
| 15 | an aeroplane drawn in behind the characters | board + clip check | `not`; the intent screen |
| 16 | a disjointed stretch: he is outside, then he is inside | board | scene `kind: continuous`, `ledger` |
| 17 | he is suddenly wearing a cloak nobody put on him | board | `ledger` costume per character |
| 18 | guitar playing that looks fake | board | `perform`, the still spec |
| 19 | she slides backwards to the door, which makes no sense | reading the note | the notes protocol in SKILL.md |
| 20 | a whole sequence that doesn't flow, after going round in circles on it | board | `story`, `moves`, `cams` |
| 21 | Kevin slides backwards (an end frame closer to camera than the start) | board + clip check | end frames drawn along `direction`; a direction flag stands |
| 22 | something odd happens to her hands mid-shot | clip check | the read in motion |
| 23 | the man sings the lyric as well as her | board | mouth rows: everyone else silent |
| 24 | a flick to a new pose with no transition | board | FLOW + `route: chain` |
| 25 | frozen stills left in the cut | the edit | placeholder labels |
| 26 | she looks like a cartoon; a cartoon Kevin | the stills gate | the look check against an approved frame |
| 27 | every mouth shot sent to OmniHuman; bad stills paid for | board | `lip_route: kling`; stills shown before any paid lip-sync |
| 28 | early scenes with several Saras that needed to be consistent and dancing to the music | board | one scene; `perform` |
| 29 | people walking in, then seated in chairs; inside, then suddenly outside | board | `ledger` |
| 30 | two concepts spliced together | board (bible) | `frame`, world-switch count |
| 31 | she nearly taps its head and the clip ends | board | the action finishes inside `t0`–`t1` |
| 32 | a prop that isn't the same as in the shot it comes from (the scene wasn't mapped to its references) | board | `refs` from the real shot's frame, `route: chain` |
| 33 | she vanished from the mic stage in the wide shots | board | `ledger` |

**Totals:** 29 at the board: 25 there alone, and 4 where the board should have prevented it and a clip check should have caught what got through (9, 14, 15, 21). The other 4: reading the note (19), the clip check alone (22), the stills gate (26) and the edit (25). The later checks still matter for those four, and as a net for the board's own mistakes; they are not where quality comes from.
