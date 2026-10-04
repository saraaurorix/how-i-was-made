# Intent screen: calibration (one cut of a later video)

**Why this file exists.** A screen is only useful if it catches what the director catches, without burying it in false alarms. This file records how `scripts/clip_screen.py`'s judge was tuned and measured, and how to measure it again after any change to its question.

## The labelled set

- **The cut had 77 screenable clips** (lip shots excluded).
- **The director watched it and flagged exactly two:**
  - **M08:** she is waving something about at random, and a viewer has no idea what she is doing.
  - **D02:** as the people move around, an aeroplane sits stacked behind them and is dragged around with them, which makes no sense.
- **Those two are the positives.** The other 75 are counted as accepted, under the house rule that a clip is only wrong where the director has said so. Some of them may still have problems the director didn't mention, so treat a hit on an accepted clip as "look by eye", not as proof of an error.
- **Judge each clip against its row as it stood when the clip was made.** After the director's note, M08's and D02's rows were rewritten, and D02's now literally says "no aeroplane". Keep a snapshot of the rows as they stood for the cut, and pass it with `--sb`.
- **Strips are re-used, not re-sampled:** `--rejudge <that cut's screen folder>` re-asks the judge about the same strips.

## Results

| Rule | The director's flags caught | Accepted clips failed |
|---|---|---|
| v1: FAIL on any "appears" or "moves wrong" answer, or no action (the first run) | 2 of 2 | 35 of 75 |
| v2: severity 3, first wording | 2 of 2 | 7 of 75 (V02, C03, H02, M02, M09, Q08, Q11) |
| v2: severity 3, plus "a tracking shot's passing background is normal" | 2 of 2 | 7 of 75 (H02, M02, M06, M09, Q04, Q08, Q11) |
| v2 plus a confirm pass: a second fresh answer must also be 3 | **2 of 2** | **5 of 75** (H02, M02, M09, Q08, Q11); M06 and Q04 dropped to CHECK on the second look |

**How the positives read,** in the judge's answers: on M08, she is dancing and waving a prop about, and the dance replaces the row's gag. On D02, a visible aircraft contradicts the gag, which needs there to be none. Both scored 3 on every run with the v2 wording.

**The v2 wording that mattered.** The first v2 prompt rated M08 only 2, because a character bouncing about is normal in a music video. Two changes fixed it: naming the director's class of problem in generic words ("they could not say what a main character is doing: she moves about or waves a prop with no evident purpose"), and asking for the viewer read first ("what would a first-time viewer think she is doing?").

**The run-to-run noise.** On borderline clips the severity flips between runs: V02 went 3 to 2, C03 3 to 1, M06 1 to 3. The positives never moved. That is why a FAIL needs a second fresh answer of 3 (`--confirm 1`, the default). The confirm pass removes random flips (M06, Q04), not systematic misreadings: the five that survive are the same misreadings every time (camera travel, a receding car, a prop that swings), so they are read by eye.

## The false alarms, read by eye

| Clip | What the judge said (quoted, or in short) | By eye |
|---|---|---|
| C03, M02, Q11 | "the seated crowd slides sideways" | tracking shots: the camera travels with the walkers and the crowd passes by parallax. Normal. (C03 stopped firing after the tracking line; M02 and Q11 still do) |
| Q08 | "the car goes backwards away from the finish" | someone on foot outruns the car, which falls behind. The director reviewed this exact shot and accepted its fix |
| M09 | "the mannequin glides away by itself" | a costume on a stand walks off it (a heel shows under the hem); the scene's staging allows it, and the same figures walk in an earlier scene too |
| H02 | a tag flies up from its attachment | the tag flips up for a moment; an attentive viewer might notice, and nothing is confusing |
| V02 | a pile of props empties instead of building up | the pile sinks a little; minor |
| Q04 | she gestures instead of doing the row's small action | a small action that half-reads; a 2 on the second look |
| M06 | the action is unclear; she is dancing and swatting at tiny things | **the nearest to a real problem of the director's kind:** she darts about with her head out of frame, and only two of the hits read. Reported to the director as a candidate, not remade |

**Known blind spots:**
- **Headless figures:** the judge can't tell front from back, so it reverses which way they walk (it said two shots' headless figures walk toward the camera; they walk away).
- **Camera travel:** it can't separate camera travel from a sliding crowd using 8 still frames.

## How to re-run

Run from the video's project folder (`scripts/` is this skill's folder; `ROWS.json` is the snapshot of the rows as they stood).

```bash
S=scripts/clip_screen.py
# all 77 against the rows as they stood (about 12 minutes with 3 workers)
python $S --sb ROWS.json --rejudge review/screen_cutN --workers 3 --out review/screen_calX
# only the two positives (about 20 s)
python $S --sb ROWS.json --rejudge review/screen_cutN --only M08,D02 --out review/screen_calX_pos
# the confirm pass alone, over a finished run's answers
python $S --sb ROWS.json --rejudge review/screen_calX --keep --out review/screen_calXc
```
Accept a change to the question only if both positives still FAIL and the accepted-clip count doesn't rise. Add every future flag from the director to this set, with its clip and the row as it stood.

## Correction: the camera-travel excuse was wrong once

On a later cut the screen FAILed C02 twice: "Kevin and Sara move backward toward the camera while facing the far doors". I measured it:
the background grew 1.2x, the seated row streamed past, and his feet stepped away. I overruled it as camera travel. The director watched it
and saw Kevin slide backwards before he walked forwards. **C02 was a true positive.** The cause was the end frame: it had them close to
the camera, the start had Kevin far ahead, so Kling brought him back toward the camera.

**The narrowed rule:** a tracking shot where the background passes is a known false alarm. A subject who grows faster than the background
while facing away IS moving toward the camera, whatever the camera does, and it reads as a backwards slide. Don't measure a
direction-of-travel flag away. Watch the subject at tenth-of-a-second steps against the things beside it. If it isn't plainly moving the
way it faces, it fails.
