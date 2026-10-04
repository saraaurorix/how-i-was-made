# Worked example: one cut, reviewed join by join

The cut: a later video's first cut, 5:26 long, 101 shots, 100 joins. The video isn't named here. People are given as roles (the lead, a colleague) and the place as a generic office floor; the timings, the counts and the technique are as they were.

## The director's four notes, and what the frames showed

The director's notes on the cut: at 0:14 she should actually be playing the guitar riff. At 0:17 and the next shot she should jump off what she is riding and onto the walkway, and then the figures walk. At 0:27 the location switches: it should stay where the scene began, or the two should be parts of one walkway, and she is sliding backwards. At 0:34 the colleague is on her right, and the next shot is good but the angle has flipped. The individual scenes are good, but there is no continuity.

| Time | Join | What the frames showed | Why |
|---|---|---|---|
| 0:12–0:16 | into R01 | she stands up on a desk holding the guitar up and never plays | the motion line said "hits the first power chord": one event, played once, then a pose |
| 0:16.7 | R01 → R02 | on the desk, then already riding a rolling trolley | two separate stills; nothing made the jump |
| 0:21.4 | R02 → R03 | riding at speed, then standing still on the floor beside a rolling amp | R03's still was made from the set anchor, not from where R02 ended |
| 0:26.2 | R03 → R04 | a walkway between desks with figures marching, then an open floor by the doors with neither | R04's still took R01 as its reference and its prompt described other geography ("the central aisle… the doors behind her") |
| 0:35.2 | V01 → V02 | the colleague screen-left of the lead, then screen-right; V03 puts him back | V02's still was made with "new camera angle" and no sides written in |

**The root cause, the same for all five:** every shot was made from its own still, from its own prompt, in parallel, and every review looked at shots, not cuts.

## How the checker did against a full eye review of all 100 joins

| | Count |
|---|---|
| joins | 100 |
| breaks found by eye | 18 (in 6 causes) |
| ... also flagged automatically | 10 (11 with the action hint) |
| ... found only by eye | 7: the riff's action and performance (3 joins), a flip with the colleague's face covered by his hat (2), the flip back out of one shot (1), an audience that returns after leaving (1) |
| SIDES flags | 5, all real |
| automatic flags on joins the eye cleared | 22: 18 transitions that are by design (a board with join types stops flagging them), 4 fine |

**The lessons built into `scripts/join_check.py` along the way:**
- **Tile the frame for faces.** A whole-frame pass missed every mid-shot face.
- **A fine second pass** finds a face turned down to a prop.
- **Find the lead by her cyan irises, or by her fringe when her eyes are hidden,** never by white hair: wigs are white too.
- **Find the colleague by his moustache,** and only in shots the board says he's in. Upper lip against cheeks: him 0.36–0.43, everyone else 0.83 or more.
- **Hold sides to the scene's first two-shot.** Compare them across the whole shot, not one frame.
- **Ignore crowds.** An extra's side is not a continuity fact.

## The repair list, by cause

| Cause | What went wrong | Joins | The fix |
|---|---|---|---|
| 1 | The riff was made shot by shot | 0:12–0:31 (5) | restage it as one scene and remake R01–R04 by chaining. The shots are as long as their 5 s clips, so each chain frame is a clip's final (softest) frame: clean it, or use 10 s clips |
| 2 | Five shots are the mirror of their scene (V02, V05, V11, V12, C04) | 8 | mirror them in the editor. Checked at full size: the clock has tick marks, not numerals, but its hands flip from after noon to before; the lead's earpiece changes ear in V11 (its side already varies) |
| 3 | New places with nothing carrying the cut | 3 | a whip in the editor (the door), a dip to black on a whispered line |
| 4 | A cutaway puts the lead in two places at once | 2 | remake the cutaway without her |
| 5 | An audience that had left returns | 1 | accept, or remake the shot (still + lip) |
| 6 | The lead's face seams drift between close-ups (the character sheet) | – | the identity line, for the shots still to be made |

## The riff (0:12–0:31), restaged under these rules

*Staging: the office floor's central aisle is a glossy walkway between two rows of desks whose screens glow cyan. Headless figures stand in ranks along it. The tall front doors close it at the far end, always centre-background. The camera stays on the walkway looking toward the doors. The lead faces the camera; everything moves down the walkway toward the camera. Warm lamp light, cyan from the screens.*

| Shot | Join | Start state | Action (the motion line) | End state | Made from |
|---|---|---|---|---|---|
| R01 0:12.0 | TRANSITION (the flash) | the lead up on the near desk, guitar in hand | she plays the riff: her strumming hand moves on every beat for the whole shot, her fretting hand moves on the neck; the screens light in a wave down both sides toward the doors | she drops off the desk onto the rolling trolley | the set anchor and the look and guitar anchors |
| R02 0:16.7 | FLOW | on the trolley, just landed | she rides it down the walkway toward camera like a surfboard, still playing, the camera travelling back ahead of her | she jumps off the trolley onto the walkway | R01's cut frame, cleaned |
| R03 0:21.4 | FLOW | landing on the walkway, facing camera | she keeps playing; behind her the figures step off their stands and walk down the walkway after her; a rolling amp skids backwards past her on each chord | she drops to her knees | R02's cut frame, cleaned, re-anchored to the lead's references |
| R04 0:26.2 | FLOW | on her knees, playing | she knee-slides down the walkway toward camera, the figures walking behind her; on the last chord the far doors blow open and the colleague stands small in the light | the doors open, the colleague in them | R03's cut frame, cleaned |
| V01 0:31.0 | JUMP (the lyric has her sit down at the desk) | the colleague screen-left | the lead sets the guitar down and sits at the desk | the colleague left, the lead seated right | R04's cut frame as the continuity reference, sides written in |

**Read as an interpretation:** the note about her sliding backwards is taken as the knee slide staying on this walkway, with the figures behind her. If the director means she slides backwards (away from the camera, toward the doors), R04's action changes and nothing else does.

**Staging for the next scene** (0:31–1:13), the one that flipped: *a corner of the office floor: the desk and a low platform, curtains behind the platform, the big clock above; the camera stays on the platform's open side; the colleague is always screen-left of the lead; warm light.* V02, V05, V11 and V12 break it; mirroring them restores it.
