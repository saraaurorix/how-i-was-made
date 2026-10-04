# Field lessons

Lessons from the videos made after Out of Office, collected by stage. Where this file disagrees with `generation-playbook.md`, this file is newer.

---

## §1 Mouth shots: a Kling singing take first, OmniHuman only as a fix

**The rule.** Lip-sync is for where Kling fails, not for every mouth shot. A Kling singing take sometimes works as it comes, and on the earlier videos OmniHuman was only ever used for fixes. For a stretch after that, every lip shot went straight to OmniHuman. That is the mistake this rule corrects.

**Audio ON during generation, the master soundtrack in the edit.** The director's observation: Kling lip-syncs well when the take is generated with its audio on. Make this the first route for a Kling singing performance: generate with sound ON and the intended lyric, keep the original take with its generated audio as a reference, then mute or strip that audio in the edit and place the picture over the matching passage of the approved master song. Keep the master soundtrack unchanged. Watch the result with the master playing; check words, phrase starts and ends, and pauses. Alignment with Kling's own audio does not by itself establish alignment with the separate master, so adjust the picture only where needed before considering paid lip-sync. This records one successful observation, not a tested universal guarantee. Before any paid generation, quote the cost and get a yes.

**Per mouth shot:**
1. **The still.** Face at least about 30% of the frame height (punch in and upscale small crops). Nothing in front of the mouth: remove microphones with a Grok image edit. Her eyes on the lens: OmniHuman returns to the still's gaze (in one shot she sang to her lap twice), and the still is also its fallback input. **Anyone else in frame has their mouth shut in the still itself** (a ChatGPT edit, "his mouth closed in a tight-lipped smile"): with that, neither Kling take of a two-person shot moved his mouth (measured 0.001); a prompt line alone had not stopped it.
2. **A Kling singing take:** sound **ON**, the lyric quoted in the prompt, start frame = the lip still. Make 2 takes.
3. **Fit it.** Slide the shot's vocal window along the take and correlate her mouth opening (face landmarks, face-cropped) with the vocal stem's loudness (`scripts/lipscore.py` gives the correlation and lag for one clip against one slice; the sliding fit itself is not shipped as a script).
   - On that measure: **PASS ≥ 0.40** (the OmniHuman takes kept by eye scored 0.36–0.72); **CHECK 0.25–0.40**: watch it with the sound; **FAIL < 0.25**: an OmniHuman candidate. A closed-mouth Kling clip scored 0.16.
   - Dense staccato lines score about 0 even when they look fine. **A smiling singer scores low too:** the measure reads teeth as an open mouth (one take scored 0.13 against the song and 0.02 against Kling's own soundtrack). A low score is a reason to look, not a verdict. The eye decides.
   - **Kling sings the right line at its own pace** (in one take every word was right, but about 14% slower and with a long pause mid-line), so one offset can't fit both phrases. The fix that needs no new generation is a word-anchored retime: play the take along straight lines between the take's own Whisper word times and the song's word times, frame-blended; then check frame by frame that the closed, round and open mouth shapes land on their words (within 1–2 frames on that take). Keep stretches at about 0.8–1.3×, pauses excepted.
4. **Only a failed take goes to OmniHuman,** and only after the director has seen the still at full size with the cost quoted. Review the actual stills before paying for lip-sync: if they are wrong, the money is wasted. In a later video two paid lip-syncs were built on cartoonish stills with the wrong Kevin costume.
5. **Flow first.** Get the scene flowing before tuning the lip-sync. While a scene is being restaged, a lip shot can be a Kling take or a labelled still; the paid fix comes last.

**First result:** a shot planned for OmniHuman got a photoreal still and a Kling singing take instead (correlation 0.30, CHECK, installed in the cut); the paid job was never run.

**OmniHuman habits, for when it is the fix:**
- It **drops props held in the hands** unless the prompt pins them: "both of her hands stay exactly where they are in the image the whole time, holding what they hold; only her head and face move".
- It **starts moving the mouth about 0.5 s in** whatever the audio does: open the shot no more than 0.4 s before her first word, measured on the vocal stem (not Whisper's word times).
- Its **mouth leads the sound by 80–160 ms.** That is the tolerated direction; don't nudge it.
- It **rewrites on-screen text and numbers** (a percentage on a screen came back as a different number). On a locked camera, lay the still's screen region back over the clip in the edit.
- It **moves everyone's mouth:** in one two-person shot the man sang the lyrics as well as her. Say only she sings, and keep the other person still in the still.
- Without a camera lock, action lines make it pull back or stand up. Keep the locked-off rule at the end of every lip prompt (`generation-playbook.md` §5).
- **Finished lip-sync, redesigned set:** swap the background instead of redoing the lip-sync (a person matte over an empty set plate; check full frames for leaks). Wrong hair colour on a finished lip clip: recolour it in post.

---

## §2 Video clips: Kling settings and chaining a continuous scene

**Settings used:** Kling 3.0, 720p standard, 5 s, multi-shot off, enhance off; sound off for b-roll and ON for mouth shots (§1). Paid generation needs a fresh, explicit yes from the director, with the cost quoted first.

- **A 5 s Kling clip is 121 frames = 4.84 s at 25 fps:** plan no shot over 4.7 s on one clip.
- **Kling pro returns 1916×1080** against standard's 1280×720, which saves the upscale pass.
- **Flux 3 on fal** was run head to head with Kling on one video's first minute (25 clips). The director's verdict was that Kling is better. Kling stays the b-roll engine.
- **Chaining:** a continuous scene is made in order, each clip from the frame the cut actually plays last in the one before (`../shot-continuity/scripts/chain_frame.py`), never from the shot's still: in another video a shot made from the previous shot's still put Kevin in the aisle before he had moved. Window a chained shot at 0.04 s (0.042 skips frame 1 at 24 fps) and blend the seam over 3–6 frames (`../shot-continuity/scripts/seam_blend.py`).

---

## §3 Stills: routes, refusals and wording

**Route, in order** (the director made the first one a standing rule):
1. **ChatGPT images through the Codex CLI:** about 90 s a still, 3 in parallel, 1672×941 (16:9). Edits of an existing picture go the same way. The runner is `out-of-office/tools/more/gpt_edit.py` in the repo.
2. **When it refuses a look:** rewrite the row (the wording below) rather than fight the filter, and keep a more covered variant of each costume ready.
3. **Nano Banana Pro 2K** is the other stills route; where it is paid, only on a yes, every time. **Grok image edit** for small edits: microphone removal, a stamp printed on a costume. Grok's CLI outputs about 1280×720 and full-frame edits move things (in one still Sara was redrawn taller and Kevin moved), so crop the edit and composite it back. Tell it the size and placement ("the size of a hand, printed into the fabric, not a sticker"), and check skin for stray red marks.

**What image filters refuse, and the wording that passed** (ChatGPT's unless noted):
- The word "sexy"; "bustier", "plunging", "low-rise", "body chain", "midriff"; vinyl with mesh gloves and knee-high boots.
- **Pose words, not only clothes:** "hip against the desk", "sits on the edge of the bed", "mini dress… matching boots". Passed: "stands upright beside the desk", "sits on a wooden chair beside the bed", "short cocktail dress and knee-high boots".
- **Contact:** Sara touching Kevin in a bedroom set was refused twice; the shot was rewritten without contact, with a prop doing the job.
- Passed: a gold latex corset bodice with clear PVC panniers; metallic lamé with a V neckline and a wide belt; a satin corset-style top under an open moto jacket; a glossy neoprene blazer with a deep V, waist cut-outs and sheer sleeves.
- **Don't add a modest-neckline retry to a pinned look.** It is what made one video's looks drift. Plain retry, then (with the director's yes) Nano Banana Pro 2K.
- One video platform's own filter flagged "sweetheart neckline and thin straps"; "halter mini dress with a structured corset waist" passed.

**References and wording:**
- **Never attach a face reference that shows clothing to an outfit shot:** ours carried a white jacket that Nano Banana copied onto her.
- **A reference with people in it copies the people.** In another video a set reference put an earlier cut's contestants into every still; ChatGPT copied Kevin from a group reference into a doorway shot he had already left. Say so: "he has already rolled out of the frame and is NOT in this picture".
- **Small photos of Sara in the frame** (a badge): describe them in words. Attaching her face turned a robot character into Sara.
- **A row that doesn't name SARA gets no face or outfit reference** in a builder that attaches references by name ("Her gloved finger…" came back unreferenced). Name her.
- **"Seamed stockings"** draws a seam down the front of the leg: "plain sheer black stockings with no seam lines".
- **Set references can contain real skylines:** "plain flat-roofed rectangular glass towers: no domes, no spires, no bridges, no landmark buildings".
- **ChatGPT can flip the camera** on a chained still (one came back looking the other way). Check the sides against the previous shot.
- **ChatGPT's edit mode got the dead letters wrong on a neon sign.** OpenCV inpainting of the tubes was exact.
- **Tiny figures lose their identity:** name her hair (for Sara, the platinum bob) even at thumbnail size.
- **Photoreal:** some stills come back CGI or cartoonish. Judge each still against an approved frame at full size before animating it (§4).
- **Claude Code's Read tool caches images by path.** After regenerating a still at the same path, view a copy under a new name before judging it.

---

## §4 The checks the later videos added

| Check | What it catches | How |
|---|---|---|
| **Intent screen** | a clip that joins fine but doesn't do what its row says (a gag that never happens, an object that contradicts the joke) | `../shot-continuity/scripts/clip_screen.py --judge --workers 3` (add `--lips` for sung shots) |
| **End-to-end read** | a film whose shots and joins all pass but tell no story | `../shot-continuity/scripts/story_sheets.py`, the state ledger, `../shot-continuity/scripts/join_judge.py`, written up as an end-to-end read that goes with the cut (shot-continuity Part 3c) |
| **In motion, every shot** | hands rising mid-shot, a backwards slide: invisible in three frames | a strip per shot with a frame every 0.25 s; 0.1 s steps where anything moves oddly |
| **Freeze + look** | placeholder stills, clips that barely move, CGI/cartoon looks, melted faces, ugly expressions | optical-flow residual after a global zoom/pan fit (placeholders 0.013–0.038, the stillest real clip 0.064, threshold 0.05; no script shipped), plus ChatGPT asked relative to an approved frame (asked absolutely, it calls every AI frame "CGI") |
| **Placeholder label** | an unanimated still sent as if finished | the editor burns a red "STILL <id> - NOT ANIMATED YET" bar and warns. It also caught a chained shot whose window ran 4 frames past its clip |
| **Pace** | a dance that is too fast and looks odd, which strips can't show | measure the pace against approved clips (chained shots are their own class) |
| **Beat fit** | dancing or strumming off the beat | fit the dance steps or the guitar strokes to the beats |
| **Mouth sync of a Kling take** | a take that doesn't follow the vocal | the fit in §1 |
| **Mouths on non-lip shots** | Sara (or anyone) mouthing where nobody sings | scan the b-roll for mouth movement |
| **World-change ledger** | a character who leaves through one portal and, in the same scene, another | a ledger of every world change |
| **First frame = the new still** | a stale start frame sent to Kling | compare the clip's frame 0 with the still (mean abs diff < about 12, or brightness) |
| **The gate** | frame counts, drift, strict decode, colour, audio offset, same-source neighbours | one gate script run on the work-in-progress cut (the checks are listed in `qa-gates.md` §6; no script shipped) |
| **A 10-clip pilot** | systematic prompt faults before the full run | one clip per set and look, plus a text gag (on one video it caught two faults) |

**How to read the checks:**
- **A flag that something moves the wrong way stands** unless you can show it in motion. On one video a backwards slide was measured away as a camera move, and the director saw it at once.
- **Nothing is exempt because it was approved earlier.** One shot sat in an approved minute and was never re-checked; an ending was skipped because the director had liked it, and a pose snap went through.
- **The director's timestamp is relative to the file they watched.** A minute file starts at 0:00, not 2:00. Check which file was last sent before diagnosing.
- **Numbers flag; only the eye clears.** Look at full size before calling anything fine or broken.

---

## §5 Kling prompts: habits to write around

The wording that works and what fails without it (walkers, chairs, crowds, group dances, end frames, guitar, dance, editing notes, actions that must land, mirrors, security cameras) is the wording library in `wrapper.md` §3, because it is decided when the row is written. The shot-continuity skill's Part 2, "Kling habits", has the continuity reasons.

---

## §6 The edit

- **Edit at 25 fps.** A 30 fps edit repeated every 5th–6th frame of 24/25 fps sources and made every move judder.
- **Change speed by blending, never by dropping frames:** ffmpeg `framerate` blending for a plain speed change; straight-line speed ramps between knots (one shot ran 0.75× on the wind-up so the hit landed on its word, then 1.15× so the reaction landed on the next); `minterpolate` for fitting a dance to the beat. The chaining tools assume plain playback, so work out a ramped shot's last played frame by hand.
- **A clip slowed below about 0.5× reads as frozen** (one at 0.44× did). Re-roll with motion instead. **And never speed a gesture up to land on the beat:** a guitar riff at 1.67× read as far too fast and cartoonish. Fit the music by where the action starts and stops, at 1.0×.
- **The end still drives the motion as much as the prompt:** a playing-pose end still made her keep playing through a dead stop in the music. Design the end still for the state the music wants at the cut.
- **Check the whole frame, not just the subject:** a beam in the background morphed into a staircase behind the riff and nearly went out.
- **Chaining:** see §2.
- **Cut on the action** when the move leaves the frame; open the next shot on its completion.
- **Devices for a place change:** a whip out and a whip in, a dip out and a dip in, white flashes on look changes, a colour flash fading in for a match-cut between worlds.
- **Mirroring** fixes a flipped shot without a re-roll, but not when anything in frame reads, and check one-sided marks (an earpiece changed ear in one shot).
- **Paint out** a wrong moving object in a locked-off clip with a clean plate from the clip's own first and last frames.
- **Grading:** to recolour, go to grey first and then tint. A `hue=h=55` rotation turned a robot character's eyes purple. Our super-resolution upscale came back with a grade 3.5% flatter; the edit undoes it.
- **ffmpeg `pad` can't follow a per-frame scale** (it leaves green edges): overlay on a black colour source.
- **A caption's minimum hold can spill onto the next shot** (one line ran 0.4 s into the next scene). Check the first frames after every short line.
- **Words in the picture** sit on things that don't move, in locked-off shots.

---

## §7 How the builds ran

- **Minute by minute, with the director's OK on each.** Craft the video a minute at a time, reviewing each minute's output carefully before rendering the next, and render the first minute first. Each minute: stills (riskiest first), clips, strips, windows, render, gate, the sequence read, then send.
- **Ideate the board with the director before generating anything.** Jumping straight into generation is how the creative drifts.
- **One frame for the whole video** helps: one later video was a single event carried through three escalating settings, and the director liked that board.
- **A second version is rebuilt as one world, not bolted on.** A cut that spliced two concepts came out disjointed. Count world switches on every board before showing it.
- **A continuous event is one scene with a ledger,** never a list of pictures. A chorus in one video and an intro in another broke the same way and were restaged the same way (shot-continuity Parts 3c and 3d).
- **Keep the rejected takes** with the reason in the file name, in a `rejected/` folder, and move the old cut's stills and clips into a `_cutN/` folder before remaking.
