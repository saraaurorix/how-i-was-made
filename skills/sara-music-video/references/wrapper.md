# The wrapper: how Out of Office stayed consistent without a map

The one rule that made the benchmark work, taken from its job files (`out-of-office/jobs_stills.json` and `out-of-office/jobs_clips.json`, built from `out-of-office/storyboard.json` by `out-of-office/tools/build_jobs.py`; paths from the repo root). Every one of its 74 stills was made four at a time with no reference to any other still, and the office kept its light because every prompt described it in the same words.

## §1 The template

**Every still prompt** = identity line + the shot + style line, with the references for that act attached.

- **Identity line** (fixed for the video, word for word; this one is Sara's, so write your own artist's): *"NOVA is the female android from the reference images: keep her face identical, platinum-silver blunt bob with a sharp fringe, glowing electric-cyan eyes, fine chrome seams on her jaw and collarbones."* (NOVA was Sara's name when Out of Office was made.) Today the marks that drift are named exactly: two thin chrome seam lines, one each side of the chin, from the corner of the mouth to the jawline, none on the cheeks; no coloured eyeshadow. Kevin gets his own line (comb-over, moustache, round glasses, beige short-sleeve shirt, mustard tie). Any other recurring character gets one too.
- **Check the identity line against the reference image before the first still.** It reproduces its mistakes as faithfully as its virtues: a later video's Kevin line said "a plain thick moustache" while his reference has a small neat one, so every still drifted the same way and the expressive ones became a cartoon. Name the marks as they are in the picture, and say what they are not ("never curled").
- **The shot**: the picture, in one camera, naming the world by its nouns every time (the beige cubicles, the fluorescent tubes, the server hall). Repeating the nouns is what keeps the place the same.
- **Style line** (fixed for the video, or per section when the song flips style): *"Cinematic music-video still, glossy high-fashion dystopian corporate satire, saturated neon magenta and electric cyan accents against sickly beige office tones, anamorphic lens flare, shallow depth of field, crisp hyperreal detail, no captions, no watermark."* It carries the palette, the world's tones, the lens and the finish. Write a new one per video; change it deliberately for a section (another video's deliberate style flips were the director's favourite thing about it), never by accident.

**Every clip prompt** = the action + a fixed suffix: *"Dynamic cinematic music-video camera work, energetic, smooth motion, keep the characters' faces consistent."* Add "locked-off camera: the camera does not move" only when the shot needs it (text in frame, a hit that must land, a chained shot).

**Photoreal is part of the style line.** A later video's stills drifted towards cartoon next to everything else; the cause isn't established (the way its stills were made changed around the same time, which is a correlation, not a finding). "Crisp hyperreal detail" in the style line and a check against a live-action-quality frame are cheaper than fixing it after. Judge a new still against an approved Out of Office-quality frame, and each recurring face against its own reference image at full size: Kevin's moustache and glasses drift toward a cartoon in expressive shots (a face pressed on glass, a hop), and a still that has drifted a little passes it on to every clip chained through it.

## §2 References: one look per act

Out of Office used five images for 74 shots: Sara's portrait (47 shots), her club look (24), Kevin (18), her space look (12), her office look (11). One look per act, pinned to one image, gives variety between acts and no drift within one; the director asked for both.

- **Per video:** Sara's portrait; one full-length image per look, from your artist's wardrobe references or made for the song and signed off; Kevin; any other recurring character. That is usually the whole set for a montage video.
- **Add a reference only when something recurs:** an empty set image for a place seen more than a few times (a home set for the chorus), a sheet for a prop or creature seen twice, a design image for a character version. A reference with people in it copies the people; make set images empty.
- **Face references only** on shots that are about a new outfit; never a face image that also shows clothing on an outfit shot (Sara's carries a white jacket). No face reference on from-behind shots or on small photos of her inside the frame; describe those in words.
- **Continuous scenes** add one thing: the previous shot's played frame as the continuity reference ("the SAME place and camera side: keep every position and the sides; only the action changes"). See `storyboard-spec.md` §1c.

## §3 Wording that works, and what fails without it

Each line cost a re-roll. Use the "Write" wording when the intent comes up; the "Not" column is what produced the failure.

| Intent | Write | Not | Why |
|---|---|---|---|
| someone walks | "takes two slow steps and stops right under the arch; stays full length in the frame, far from the camera; locked-off camera: the camera does not move" | "walks toward the camera" | the walker reaches the lens, the head is cut off |
| a clear path | "the aisle stays clear and empty: no object ever appears in it" | nothing | Kling grew a desk in the aisle |
| someone leaves in a chair | "glides away slowly and smoothly, upright, the chair flat on its wheels, nobody falls" | "rolls away waving both arms" | two takes crashed the chair |
| an action that must land | start the still with it under way (the crown already over his eyes; the clip only lifts it) | the whole action in one line | it failed twice |
| a hit | put the target where the swing naturally lands (a bell at head height beside her); make the end frame the moment of contact | a target above her head | the mallet passed under it |
| something absent | "no aeroplane anywhere" | silence | Kling drew a real airliner where the aircraft was meant to be invisible |
| fabric near a head | "his head stays bare and uncovered the whole time"; keep the fabric on the far side | nothing | the gown hooded Kevin |
| a vehicle or lift moving | draw it where the move starts | the lift at the top of the tower | it went down |
| a crowd moving | "All together, as one: every one raises an arm and twirls"; room between bodies | a small gesture, a packed group swinging arms | only the front row moved; arms passed through each other |
| a group dance | a closer medium-wide still, everyone mid-move, one repeating move, **no end frame** | a big pose change with start + end frames | vortex morphs |
| a dance | "one slow step-touch to a steady beat, over and over, never speeding up", from a relaxed pose | a routine of several moves; "dances throughout" on every shot | too fast and uncoordinated: it looks odd |
| guitar | strap over the shoulder, pick over the strings, fingertips on the frets in the still; "big, clearly visible down-strokes … the hands never leave the guitar" | "hits the first chord"; "short, quick strokes" | one strum then a pose; floating guitars |
| a costume change | start + end frames on the same set, a whirlwind or whoosh between | a hard cut between two colours | with no visible reason it looks like a continuity error |
| a jacket coming off ("slips the blazer off") | let it happen in the clip, from a chained frame | writing it in a still prompt | image models refuse the action in a still |
| a sexy look | name the garment and the cut (a gold latex corset bodice, lamé with a V neckline) | "sexy", "bustier", "plunging", "midriff", "low-rise", "body chain" | ChatGPT's output filter |
| a pose near furniture | "stands upright beside the desk", "sits on a wooden chair beside the bed" | "hip against the desk", "sits on the edge of the bed" | blocked as sexual |
| stockings | "plain sheer black stockings with no seam lines" | "seamed stockings" | a seam down the front of the leg |
| a city | "plain flat-roofed rectangular glass towers: no domes, no spires, no bridges, no landmark buildings" | "a skyline" | real landmarks appeared |
| captions, flashes, titles | in the edit notes, never in the motion line | "the title slams on the hit (white flash)" | Kling drew a white title card |
| a man in Sara's role | "she" | "he" | Kling added a second, male person |
| a reflection | frame straight on | a mirror shot | Kling confuses reflections |
| a designed end frame | new poses from the same camera | an end frame identical to the start | the shot freezes for 4 seconds; identical start and end only for a blink-and-reopen gag |
| a security-camera shot | desaturate it in the edit | trusting the prompt | Kling adds colour |
| someone already gone | "he has already rolled out of the frame and is NOT in this picture" | a reference that shows him | ChatGPT copied him from the reference |
| a small photo of Sara in frame | describe it in words | attaching her face | the robot turned into Sara |
| slow motion | ask for it in the prompt | slowing below about 0.5× in the edit | it reads as a freeze |

**What image filters refuse (ChatGPT's and other image services'):** the word "sexy"; "bustier", "plunging", "low-rise", "body chain", "midriff"; pose words ("hip against the desk", "sits on the edge of the bed"); undressing actions; one character touching another in a bedroom. Passed: named garments and cuts (a gold latex corset bodice with clear PVC panniers; metallic lamé with a V neckline), upright poses, "short cocktail dress and knee-high boots". When a look is refused, rewrite the row rather than fight the filter: name the garment and the cut, keep the pose upright, and keep a more covered variant of each costume ready.
