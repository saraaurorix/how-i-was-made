# Generation playbook

This is everything learned about making the pictures, the clips and the lip-syncs, and about getting them into the cut, on Out of Office and the videos made after it. **What the later videos learned is in `field-lessons.md`; where the two disagree, that file wins.**
- **How to read it:** work out the free/paid route first. Then, for each asset type, it gives the recipe, then every known failure as *symptom → how to detect → fix*.
- **Evidence:** "(OOO)" marks a lesson from Out of Office. The rest come from later videos.
- **The director** is the human who makes the calls.
- **House rules:** Sara's look, her cast, her caption styles and her ending are her house rules. Swap in your own artist's.
- **Scripts:** `scripts/<name>.py` is in this skill's folder. `out-of-office/tools/…` is Out of Office's own tooling in the public repo.

Contents
- §0 Free or paid? (decide first, every time)
- §1 Audio: casting, analysis, timing
- §2 Storyboarding for generation
- §3 Stills (ChatGPT via Codex first; Nano Banana Pro and Grok as fallbacks)
- §4 B-roll clips (Kling 3.0; Veo/Wan/Seedance when needed)
- §5 Lip-sync (a Kling singing take first; OmniHuman as the fix)
- §6 The second vocalist, Kevin, clones and crowds
- §7 AI upscaling (Apple super-resolution)
- §8 The edit and deliverables
- §9 End-to-end checks before anything reaches the director

---

## §0 Free or paid? (decide first, every time)

| Asset | First choice | Fallback or upgrade (paid: quote first, wait for a yes) |
|---|---|---|
| Stills | **ChatGPT image generation through the Codex CLI**; Grok CLI `image_edit` for small edits | Nano Banana Pro at 2K, the fallback when ChatGPT refuses |
| B-roll video | Kling 3.0, **720p, 5 s** | Kling 3.0 pro (1080p); Veo 3.1; Wan 3.0 |
| Mouth shots | **A Kling singing take, sound on** (the default) | OmniHuman 1.5, **only for the takes that fail**, stills shown first; Kling AI Avatar v2 Pro; sync-3 and lipsync-2-pro retired |
| Motion graphics, captions, grids, reverse, window, band-reverse, upscale, lip nudges, prop composites | **Always free** (local, on the GPU) | none |

- **Ask before any paid generation.** Quote the cost first and wait for a yes, whichever column the route is in.
- **Approval is per batch.** Quote the model, the number of jobs and the cost; after the job, report what it actually cost.
- **The director prefers the cheaper route even when it's slow.** Cheap beats fast.

## §1 Audio: casting, analysis, timing

**Casting is a hard gate before any lip-sync spend.** Suno ignores the singer tags in the lyrics.
- **What went wrong:**
  - On one video a man's voice sang one of Sara's lines.
  - On another the second vocalist sang most of verse 2, so three paid Sara lip-syncs were on his lines.
- **The rule:** the storyboard's `voice` comes from the take **as sung**.
- **The check (the standard method).** The director made it the standard because it saves a lot of time. On its first use it found Suno's swap on the first pass (the second vocalist on verse 2, part of a chorus, a spoken section and the outro; Sara on bridge lines), and the director answered 7 cards in one message.
  1. **Stems and words:** Demucs vocals; `scripts/transcribe.py`; then `scripts/transcribe_gaps.py` on every stretch the full pass dropped (dense choruses and bridges: set `GAP_PROMPT` to a few lyric words); `scripts/align_lines.py`, then paste the gap times into `lines_timed.json` for the GUESS lines.
  2. **`scripts/casting_scan.py --vocals <stem> --sara <t0-t1>`:** per line, the **timbre** call (MFCC nearest-centroid; the references are lines from an earlier song that are certainly Sara *and* certainly the second vocalist, plus a stretch of this song you're sure is Sara), and the **pitch** (pyin) as a hint. Writes `casting.json`.
     - **Trust timbre, not pitch.** Against the director's ear: timbre was right on 35/40 lines, pitch on 22/36. The second vocalist raps in a female pitch range (~165–190 Hz), and Sara's pitch-shifted backing copies read ~87 Hz. Timbre margins of 1.0 or more were right 18/20 times.
     - Cross-song references beat same-song ones: you don't need to know any of the second vocalist's lines in the new take.
  3. **Group the flagged lines into PASSAGES** (whole sections, not single lines), **card 1 a control** you're sure of. Build `scripts/casting_clip.py --wav … "label|n0|n1|sheet|detector" …`: one labelled card per passage ("Sheet: X · Detector: Y · Who sings it: Sara or the second vocalist?"), then the passage. About 2 minutes for a whole song.
  4. **The director answers per card**, naming odd lines inside (one line in a passage can belong to the other voice; echoes in brackets can be the other voice). Write the answers into `casting.json` as `ear` (S/B) and into `casting.md`. **Then a short part-2 clip** of flagged lines that weren't on any card.
  5. The storyboard's `voice` comes from `ear`, never from the sheet.
- **Older tool:** `scripts/voice_id.py` (same-song REFS, per storyboard shot) still works once a storyboard exists, but the scan above replaces it for the first pass.
- **Pitch alone misleads** (see step 2).
- **A male line the director wants left alone:** let it play and don't lip-sync it. Put it over a non-singing gag shot or a second-vocalist shot with gold rap captions.
- **Keep Suno to two voices:** Sara (lead and choir) and the second vocalist (male announcer and rapper). **Kevin never has a voice;** he types.

**Analysis (run on the WAV, never the MP3):**
```
python scripts/analyze.py song.wav timing.json                    # tempo, bar grid, sections
python -m demucs --two-stems vocals -n htdemucs -o sep_wav song.wav
python scripts/transcribe.py sep_wav/htdemucs/<name>/vocals.wav words.json   # word times (faster-whisper)
python scripts/align_lines.py                                      # lyric lines -> timed lines
```
- **Whisper is not ground truth.**
  - Word starts can be 0.3–0.4 s off.
  - Medium hallucinates on crops ("Thank you for watching").
  - It can drop a dense chorus. Copy the words from an identical chorus, shifted by the onset cross-correlation.
- **Check every lip cut against the vocal stem's actual onset** (energy plus pyin per 50 ms). `scripts/lip_slices.py` does energy-gated slices; prefer it to Whisper word masks when timings are doubtful.
- **Import `cv2` and `faster_whisper` in separate processes on macOS.** Both bundle libavdevice; there are objc warnings.

## §2 Storyboarding for generation

**The board's rules live in one place, `storyboard-spec.md`.** It holds the fields every shot row needs, how to judge each section's form against the song, how to direct a continuous scene, the writing order, the board gate with `scripts/board_lint.py`, the wording library (now `wrapper.md` §3), and the rules that used to be here (§4b: usable seconds of a clip, a location per montage shot, onboard cameras, chanted lines, text beats, silhouettes, logic gags, closed-mouth tails). Mouth-shot framing is in its step 9 and in §5 below.

## §3 Stills (ChatGPT via Codex first; Nano Banana Pro and Grok as fallbacks)

*Newer lessons (filters, refusals, reference traps, Grok compositing): `field-lessons.md` §3.*

**Route: ChatGPT image generation through the Codex CLI** (the director made it the standing rule for stills; the runner is `out-of-office/tools/more/gpt_edit.py` in the repo). About 90 s a still, 3 in parallel, 16:9 at 1672×941, face refs attached. **Fallback, for a still ChatGPT won't make:** Nano Banana Pro at 2K (`scripts/gen.py jobs.json 4`), paid and **asked for every time**. Start the Kling clips as soon as the first stills land.

**References per character.**
- **Sara:** a face ref plus a portrait (face only, for new outfits), plus the outfit ref for the act from your artist's wardrobe references.
- **The second vocalist:** one design ref.
- **Kevin:** put his ref **first** and turn him three-quarters to camera; side-on he drifts to another face.

**Prompt construction.**
- **Put mood and lighting words at the start** of the prompt.
- **Quote every piece of in-scene text** and say "and nothing else": `a sign that says "BE NICE TO HER" and nothing else`.
  - "Moody." after the sign text got painted onto the sign.
  - A "1998 printer" printed "1998". Don't put years or numbers in object descriptions unless they should appear.
- **Name the signature features every time.**
  - The second vocalist: "wearing his black sunglasses, gold USB chains clearly visible, small as a football". He was once drawn human-sized, without them.
  - Sara: platinum-silver bob, glowing cyan eyes, chrome jaw seams.
- **Clones:** pass the outfit ref and say "every copy is identical to SARA in the exact same outfit; no robots, no other people, no other outfits". Or, for varied clones, give each a different outfit from the approved range while staying unmistakably Sara.
- **Motorsport.**
  - "Formula 1 broadcast style" pulled in real F1, Pirelli, Rolex, DHL and Red Bull branding. Dropping "Formula 1" gave GT cars.
  - What works: "glossy motorsport cinematography" plus "modern open-wheel single-seater formula race cars with a halo".
  - Listing the made-up sponsors plastered them over offices and suburbs. Scope them to trackside shots, "small and in the background", and add "no advertising boards" off-track.
- **Drop "faces sharp"** for shots with no people: it spawns strangers.
- **Content filter:** a tux over a camisole and a space-gown reference were blocked on 5 shots. Covered-up variants passed: a buttoned-up blouse and bow tie, and a fully covered gown described in words. Keep a safe variant of each costume ready.
- **Close-ups of hands, feet or props:** don't attach Sara's face refs, or the model paints a floating Sara head into the frame.

**QA before the director sees them.**
1. **Spot-check the first ~20 of a big batch** before letting it run. Systematic prompt flaws show early.
2. **Contact sheet** (`scripts/contact.py`, or a story-order sheet labelled with each line). Check:
   - identity (face, bob, eyes, seams) and outfit, including background clones;
   - the right character (Kevin stays Kevin; no random strangers);
   - text legible and spelled right;
   - anatomy (extra arms), head proportions (a head too big for the body), continuity with neighbouring shots;
   - anyone who looks like a real celebrity (make them Sara copies);
   - real logos. **Check every edited still at full size:** image edits can re-introduce real logos.
3. **Lip-sync stills:** measure Sara's face height with MediaPipe; crop in (free) wherever it's under about 30%.
4. **Continuity props:** the same pods, cars and set across consecutive shots (OOO pods).
5. **Outfit drift.** A look repeated across shots drifts when each still is made from words alone (on a later video a red dress changed between shots, and three more looks drifted). Pin each repeated look to its first approved still as an image ref (an `OUTFIT_REF` entry per look), reuse stills where the framing allows, spell out the coverage, then run `scripts/outfit_audit.py` (one row per look, anchor first; `--clips` adds each clip's last frame) after every round and before the animatic. Keep the drifted file as `_<ID>_old_drift.png` for the before/after.

## §4 B-roll clips (Kling 3.0; Veo, Wan and Seedance when needed)

**Route.** Kling 3.0, 720p, 5 s a clip, each from its shot's still.
- **Start a tracked watcher after every submit;** an untracked job once sat finished for an hour while nothing else ran.
- **Speed:** about 1.5–4 minutes a clip.

**Prompt shape** (keep the first 80 characters unique if your collector matches clips back to shots by them, as ours did):
```
<one short motion line, specific to this shot>. Scene: <what is in frame>. <continuity clauses>. Cinematic music video, energetic, smooth natural motion. No dialogue, no subtitles.
```
**Continuity clauses:**
- "Every Sara keeps the identical face, platinum-silver bob, glowing cyan eyes and costume throughout; no morphing."
- For non-singing Sara: "Sara's mouth stays closed or smiling; she does not talk or sing in this shot." Add the same for Kevin and the others.
- When Sara plays a man, write **"she"** in the motion line. "He" makes Kling add a man.
- **Vehicles:** read each car's nose direction in the still at full size (the front wing is the wide, low, multi-element wing). Write "toward the camera, nose first" or "to the right, nose first", plus "Every car drives forward in the direction its nose points; no car ever moves backwards or tail-first". Ask for background cars to move, or they stay parked. **This includes background packs in non-car gags.**
- **Camera:** "steady camera, never tilts, rolls or flips, horizon stays level" when Kling rolled the camera. Don't write "locked-off camera" on a shot whose motion asks for a pan.
- **A singing base for lip-sync:** "Singing to camera: … She sings the words expressively, her lips clearly moving and opening on every vowel, her face toward the camera and her head fairly steady." (See §5.)

**Longer than 5 s:** take clip A's last frame (`ffmpeg -sseof -0.05 -i A.mp4 -frames:v 1 A_last.jpg`), make clip B from it, and join them dropping B's first frame (`JOIN` in the editor).

**Known Kling failures: symptom → detect → fix**

| Symptom | Detect | Fix |
|---|---|---|
| Cars drive tail-first (head-on cars recede while the camera pushes in) | Strips at 0.25–0.5 s against static boards (2.5 s spacing hides it); `scripts/carflow.py CLIP x0 x1 y0 y1` gives a signed flow | `REVERSE` if the whole clip is backwards; `BAND_REVERSE` if only the track is (a homography-warped band, SIFT on static boards, 0.3 px error); else re-roll with the direction written in |
| Motion flips near the clip's end | measure the flow of the moving pixels across the seconds the cut plays (`scripts/carflow.py` gives a signed number for a region), then a 0.1 s strip | `WINDOW` ending before the flip (on one clip, 0.6–3.4 s) |
| On-screen text garbles after a few seconds | Clipsheet start/mid/end (`scripts/clipsheet.py`) | `WINDOW` the good part, or make the text a motion graphic |
| The key action only happens in the first or last second | Clipsheet | `WINDOW` (slowed or sped to fit the shot) |
| A character mouths along to someone else's line | Mouth-movement measure on a face crop (`scripts/lipsync_audit.py` flags it) | Re-render with "lips pressed together in a tight closed-mouth smirk, never opens her mouth"; else a slow push-in on the still |
| Identity drift (hair, face) or morphing crowds | Clipsheet start/mid/end against the still | `WINDOW`; re-roll |
| Camera tilts, rolls or flips | Strips | Re-roll with the steady-camera clause |
| Logic breaks (head floats after she ducks into a hatch) | Watch the used window | `WINDOW` before it (on that clip, 0–3.0 s) |

**Other models (paid, quote first).**
- **Veo 3.1:** legible on-screen text, crowds, big effects, with a locked-off camera. Its content checker is strict about glamour poses: don't retry, plan those shots on Wan 3.0 or Kling.
- **Wan 3.0:** cheap B-roll. It can't take a start image plus audio.
- **Seedance 2.5:** gorgeous but expensive; poor for lip-sync.
- **MiniMax H3:** was used for the second vocalist's *old* design; not needed with the waveform mouth.

**Added on a later video:**
- **A collector that matches finished clips to shots by the first 80 characters of the prompt files clips under the wrong shot when shots share an opening.** A long shared opening (a full costume description, say) made four shots identical. Open with a short look tag ("In her dress uniform, …") or with the action, and check `Counter(prompt[:80])` across the whole job list before starting.
- **"Theme park" prompts can produce a pink fairy-tale castle on a Main Street axis**, which reads as a real park. Write "no castle" into wide park scenes; if it lands anyway, crop it out in the edit and say the crop is soft. Scan the lower third of every wide park still, not just the one you spotted.
- **Kling drops a character's "solid black sunglasses" when the action says "wink".** Write "tips his head" instead of "winks" for him.
- **Check each gag's payoff time in the clip** (fine strip every 0.3–0.5 s) and set `WINDOW` so a 1.5–3 s shot plays the payoff: a prop dropping, something landing, doors opening (Kling sometimes closes them first).

## §5 Lip-sync

**Casting first (§1). Framing (`storyboard-spec.md`, step 9): head-and-shoulders, face ≥ 1/3, props clear of the mouth box.**

**THE DEFAULT: a Kling singing take IS the lip shot.** The director's rule: lip-sync is for where Kling fails, not for every mouth shot; sometimes Kling works. Sound ON, the lyric quoted in the prompt, start frame = the lip still, 2 takes; fit each take against the vocal (the measure in `field-lessons.md` §1: PASS ≥ 0.40, CHECK 0.25–0.40, FAIL < 0.25) and judge by eye. **OmniHuman, below, is the fix for the takes that fail,** after the director has seen the still at full size with the cost quoted. Never plan a video's lip shots as an OmniHuman batch. Details: `field-lessons.md` §1.

**Audio-swap step:** generate the singing performance with **audio ON**, keep the original take for reference, then **mute/strip its generated audio and use the existing approved master soundtrack**. Check the mouth against the same lyric passage in that master, not only against Kling's own generated sound. Preserve the master; fit the picture only if needed. The full method is in `field-lessons.md` §1.

**The fix engine: OmniHuman 1.5 (`fal-ai/bytedance/omnihuman/v1.5`),** judged the best of the lip-sync engines tried. Input: the shot's head-and-shoulders still + the loudness-gated vocal slice with a 0.3 s run-up, run through `scripts/falgen.py`. No Kling singing base. Output is 25 fps and its audio starts at 0 ms; the edit skips the run-up. **Why not sync-3 (now retired):** on a Kling singing base it keeps the base's mouth rhythm (output vs base r = +0.41, vs audio +0.02), so every line started right and had drifted by its end. Test for it: correlate the output mouth with the base mouth and with the vocal (mouth apertures per frame); a lip engine must track the vocal, not the input video. Fallback: Kling AI Avatar v2 Pro (image + audio). **Prompt it.** The `prompt` arg steers expression and body motion; "she dances throughout" worked (head bobs and shoulder shimmies in close-ups, full choreography in MCU, lips still closing on the m's). Without a camera lock, action lines made it move the camera and the body: one shot pulled back to a full-body wide (the mouth became unreadable), and another stood up from a lounge pose and lost her hat. Every lip prompt now ends with the locked-off rule: the framing is held, with no zoom or pull-back; she stays in the still's pose and never leaves frame; every accessory stays on. Big actions get rewritten as in-frame versions. Close-ups also keep her hands below her chin. QA each landing clip at 2 fps for framing, pose and outfit before the rest of the batch runs; with `scripts/falgen.py`, unstarted jobs can be held at no cost by moving their audio aside. Still true for any engine: gate the vocal by loudness (Whisper misses held notes), keep casting (never drive her mouth with the second vocalist's words unless the shot is his line on purpose), and start/end lip shots on the sung notes.

(Retired) sync-3 on a Kling singing base was the earlier route.
- Frame: head-and-shoulders. Crop the shot's own 2K still or make a new 1K still (refs: Sara's face ref + the shot's still).
- Base: a Kling clip of her SINGING.
- Then `scripts/lip_v2v.py`, then `fal-ai/sync-lipsync/v3`.
- Casting check per line first: never lip-sync Sara on the male voice. On one video two lines were his; the director caught both.

The routes below remain as fallbacks.

**Choose a route (both proven; quote costs before either).**

| Route | How | Proven on | Watch for |
|---|---|---|---|
| **A. Wan 2.7 image+audio** | Higgsfield `wan2_7` (start image + audio, `--duration` 3–10 s) or fal `wan/v2.7/image-to-video` + `audio_url`. Drive it with an energy-gated vocal slice (`scripts/lip_slices.py`) that starts on the shot's first frame (round(t0·30)/30), at least 3 s long. Prompt "she sings the words with clear articulated mouth shapes, mouth closes between phrases, head fairly steady". **Two takes per shot at 1080p,** then `scripts/pick_lip_takes.py` scores them and keeps the better one | Out of Office and three later videos | Mouths drift 0.2–0.5 s even when the embedded audio aligns; mouths move through silences (use `LIPTAIL`); ignores gestures (use `INSERT`); big laughs or cries swamp the words |
| **B. Kling singing base + sync.so lipsync-2-pro** | Make a **singing** Kling base: a closed-mouth base failed, because sync.so copies the input's speaking style. `scripts/lip_v2v.py ID [--start 0.5] [--pre 0.3]` writes a word-masked slice with a 0.3 s run-up, plus the trimmed 30 fps base window (VideoToolbox) and the fal job. Run with `scripts/falgen.py jobs_lipsync.json 4 IDs` | A later video (16 shots) | **Colour-check every input and output** (six came back green from a bad encode and had to be re-run). Mouths trail the voice by about +43 ms (nudge +1 frame by default, then measure). **Props through the mouth box vanish** (`scripts/glassfix.py`). The upload cache is keyed on path + mtime |
| **C. sync.so on a flagged Wan shot** | lipsync-2-pro (or sync-3) on the Wan clip's exact shot window with the word-masked audio; the output goes to `gen/lipsync_v2v/`, which the editor prefers | A later video's opening lines, after Wan re-takes and re-timing failed | Offer the two models side by side; fix only flagged lines |

**Before any batch, run a 2-shot pilot.** Show it as a before/after sheet, then ask for the rest (the director: "just do 1 first so we can check style"). A pilot costs little and catches a wrong route before the whole spend.

**Route B details:**
- **Lines longer than about 4.9 s don't fit one 5 s base.** Chain two bases (`JOIN`) before `scripts/lip_v2v.py`, or split the line across two shots.
- **`scripts/lip_v2v.py` masks the audio by Whisper words** (with a 0.06 s lead and 0.10 s tail). Where Whisper is doubtful (§1), check the mask against the vocal onsets, or feed it `scripts/lip_slices.py`'s energy-gated slice instead.
- **fal has no balance command.** Report fal spend from `fal_log.jsonl` (one line per job) times the price, and ask the director to check the fal dashboard if a job fails with "User is locked" or a 403 on upload.

**Measuring sync (before the director sees it):**
- **`scripts/lip_lag.py`:** measure on the **rendered segments** against the vocal stem at the same song time. It gives sub-frame lag; lag > 0 means the mouth trails. Audio ahead of the lips is noticeable from about 45 ms; lips ahead are tolerated to about 125 ms.
- **Trust only correlation ≥ 0.3.** Short lines, choir-heavy chorus lines and shots where a prop covers the lips score unreliably, so judge those by eye.
- **Measure only over the words the on-screen singer sings.** One shot mixed in the second vocalist's ad-libs: the whole shot showed no offset, while Sara's words alone showed 0.2 s late.
- **Wan:** `scripts/lipsync_audit.py --write` measures visual lag over ±600 ms and writes confident offsets to `gen/lip_offsets.json`. The embedded audio is always 0 ms and proves nothing.

**Fix menu, cheapest first:**
1. **A whole-frame shift:** `LIP_NUDGE` in the editor (+ = the mouth earlier, i.e. skip further into the clip).
   - Rule: the shot's own estimate, rounded, where its correlation is ≥ 0.3; otherwise +1. Clamp to −1..+2 unless two measurements agree. Re-measure: one video went from +43 ms to +3 ms median.
   - `gen/lip_offsets.json` is written by tools (`scripts/lip_v2v.py` puts its run-up there; `scripts/lipsync_audit.py --write` puts its measured Wan offsets there), so keep manual corrections in `LIP_NUDGE`, where no tool will overwrite them.
2. **A smooth re-time,** `scripts/lip_retime.py` (0.75–1.25× warp, blended frames). **Never frame holds or skips:** DTW stutters that scored 0.95 were seen by the director at once. Per shot, pick the best of the original, the original plus an offset, and the smooth re-time, by eye.
3. **`LIPTAIL`:** the sung part, then a closed-mouth Kling tail for the silence.
   - Keep the tail **neutral** (a closed-mouth smile or a look).
   - A crossfade into an *expression* tail was rejected (fading into a pout reads wrong). If the line needs an expression after it, regenerate the whole lip take in one generation rather than splicing one on.
   - Kling reads "pout" as a pucker or kiss face even with "NOT puckered": describe it as "lips pressed flat, corners down, sheepish frown".
4. **`INSERT`:** a Kling close-up for a gesture Wan ignored, cropped so no mouth shows.
5. **Editorial:** cut away before a stubborn line and play it over a shot with no visible mouth.
6. **Paid:** sync.so on that shot's window (route C). Paid re-takes on two shots did *not* beat the original: check the real cause (silence, casting, a prop) first.
7. **A prop erased by sync.so:** `scripts/glassfix.py base.mp4 fal.mp4 out.mp4` composites the prop back from the base (colour mask inside the repainted box, gaps closed, rim loops filled, lenses as convex shapes, specks dropped). The mouth stays synced. Diff fal's output against its input to see the box.

**Show the fix next to the original.** On one shot the director found the "fixed" pout odd and the original clip far better.

**Lip-sync root cause, found on a later video where most lines were off and her mouth sang longer than the audio:**
- **Word masks mute real singing.** Whisper misses held notes and repeats; the word mask in `scripts/lip_v2v.py` then silences real vocals and sync-3 falls back to the base's random singing. Mask by the stem's loudness instead, with the second vocalist's words excluded. Check first: loud-but-muted % per shot (0% after gating).
- **sync-3 keeps the mouth singing through real pauses** and before the first note. End or start the lip shot at the sung notes (extend the neighbour b-roll) and seek into the existing clip in the edit; no new sync-3 needed.
- **Audit per frame:** mouth open (MediaPipe) vs the stem's loudness. Flag QUIET (mouth moving in silence), TAIL (after the last note) and SING (b-roll mouthing). Define "singing" by the stem, not Whisper words.

**Added on a later video:** `scripts/lip_lag.py` has **no usable signal on sync-3 singing close-ups** (per-shot peaks scatter ±200 ms; pooled against sync-3's own driving audio r ≈ 0). The reliable check is the pipeline offset: cross-correlate the returned audio with the input slice (0.0 ms on all 14). Keep `LIP_NUDGE` at the default and judge sync by eye.

## §6 The second vocalist, Kevin, clones and crowds

*Sara's house rules for her cast. Swap in your own.*

- **The second vocalist's mouth is a waveform LED.** Prompt Kling with "his LED waveform mouth pulsing as he speaks".
  - For his first or featured shot, re-render in Kling with a live waveform screen.
  - **A redrawn mouth driven by his vocal stem was tried and the director dropped it.** Kling's own pulse is the default. Never paste a mouth panel onto a design: a black panel over his mouth looks wrong.
- **The second vocalist's screen time is low** (about 3–5 shots) except in songs he leads. His lines usually play as voice-over while Sara acts them out with Kevin, lips closed (the director's note: too much of him on screen). His rap gets gold captions.
- **Kevin types** (blue bubbles, a ding), never sings. Stills: his ref first, three-quarters to camera; check he doesn't turn cartoonish or grow an oversized head.
- **Sara is peppered through nearly every scene in a role** (rep, hostess, cashier, CEO…), even in songs she doesn't lead. She sings the chorus on camera.
- **Clones:** identical in outfit when the gag needs it, otherwise each in a different outfit from the approved range, but unmistakably Sara. Background clones in the wrong outfit were flagged.
- **Crowds:** fewer generic people (OOO). Show real social situations.

## §7 AI upscaling (Apple super-resolution, free)

**Two super-resolution traps:**
- **Timing.** A window's frame 0 is the source frame *covering* the requested start, but AVFoundation stamps it with the start time. So the window's first timestamp is not a frame time, the next frames sit off the grid (duplicate or half-frame timestamps), and a time seek into the copy lands a frame out on some shots (Kling is 24 fps).
  - **Fix:** enter the copy by frame index. The source frame is the first with pts ≥ the 2-decimal seek. The window's frame 0 is the last source frame with pts ≤ the window's first timestamp. Use `trim=start_frame=j`, then rebuild pts with `setpts=N/(rate*TB)`.
  - **Check:** render every upscaled shot with and without the upscale at 64×36; the best shift should be 0 on every shot.
- **Grade.** The copy has about 3.5% less contrast and saturation than its source (Y ×1.0354 through 0, chroma ×1.0363 about 128, the same on every clip). A `lutyuv` correction in the edit undoes it, so the upscaled cut keeps the approved grade.

**RULE: upscale only the parts that need upscaling.**
- Only 720p sources, meaning Kling clips and the 720p sync-3 lip-sync clips.
- Only the window of each clip the cut actually plays, plus a 0.15 s margin.
- Never whole clips. Never sources that are already 1080p or better: 2K-still push-ins, PIL cards and graphics, 1080p lip-syncs.
- After a WINDOW, INSERT or lip-sync change, re-run the batch for that ID only.
- **Verify frame-exactness against the approved WIP by frame index** (select n), not time seeks. On one video, offset 0 was identical and ±1 frame clearly worse.
- **Lip clips seek with 2 decimals in the editor.** Pin the frame the 2-decimal seek landed on (`k = ceil(round(off, 2)·30)`) and seek the upscaled window to `(k − first_frame − 0.25)/30`, so the upscale can't move a lip frame the director approved.

- **The tool:** a small Swift command-line program around VideoToolbox's `VTSuperResolutionScalerConfiguration` (macOS 26). It supports only **4×**, with video input up to 1920×1080; by default it halves the 4× result, so 720p becomes about 1440p.
  - It runs on the Neural Engine and GPU at about 1–3 fps, with about 2 CPU-seconds per clip.
  - It needs a one-time model download, and it can take a start and a duration to upscale just a window.
- **The batch:** upscale only the part of each clip the cut plays (± 0.15 s), record each window's real first frame, and keep copies that already cover the need.
  - Joined, reversed and band-reversed shots get whole clips.
  - A whole film is about 7,000 frames, roughly 1.5–2 h at nice 19.
- **In the edit:** map each shot into its window (checked frame-exact) and skip `unsharp` on upscaled sources. A window that doesn't cover the shot falls back to 720p with a printed warning.
- **The director chose a sharper 1080p** (upscale the sources, edit at 1080p). A 4K master is possible later but needs captions re-laid out. The result is clearly crisper (lashes, eyebrows, crowd faces, car edges) and not painted.
- **After any source change** (a prop composite, a new lip-sync), re-run the batch for that ID before rendering.

## §8 The edit and deliverables

**The editor** (one `edit.py` per video; Out of Office's is `out-of-office/tools/edit.py`; see `tool-map.md` for what lives where). The per-shot dicts across the editors, each with a comment giving the reason. Out of Office's own editor and captions have only `DROPS`, `HOOK` and `SYSTEM` of these; the rest were added in later videos' editors:
- `DROPS`: a white flash.
- `WINDOW`: use part of a clip, sped or slowed.
- `REVERSE` and `BAND_REVERSE`.
- `JOIN`: chain 5 s clips.
- `OVERRIDE`: an alternative clip.
- `SPLIT`: a non-singing clip that cuts into the lip-sync at her words.
- `INSERT` and `LIPTAIL`.
- `LIP_NUDGE`: whole frames. Keep nudges in the editor, never in `gen/lip_offsets.json`, which `scripts/lip_v2v.py` rewrites.
- `DOCGRADE` and `GLITCH_OUT`.
- The caption sets: `HOOK`, `WHISPER`, `SKIP`, `TOPCAP`, `SYSTEM`, `BUBBLES`, `RAP`, `ASIDE`, `STAMP`.

**Frame-exact rules (each one cost a WIP):**
- **Segment length** is `nf = round(t1·30) − round(t0·30)`, never `-t dur` (which drifted about 100 ms over 100 cuts).
- **Trim to `nf` frames plus half a frame,** not to `dur`. When both edges fall on half-frames, `nf` is one more than `dur·30`.
- **Put `tpad=stop_mode=clone` right after decode,** before any `trim`, so a clip that runs out is padded at the real end of its input. A tpad after the trim didn't pad (seen on two shots and in a minimal ffmpeg test), though in some caption-overlay chains the shot happened to come out full length anyway. Don't rely on it.
- **Lip clips are 30 fps and nudged by whole frames,** so seek a quarter frame before the target frame. Two-decimal seeks round 8 frames (0.2667 s) to 0.27 and start a frame late.
- **Still inputs need `-framerate 30`,** or ffmpeg reads them at 25 fps and every still segment runs 17% short (one animatic was 5 s short).
- **Segments are joined with `-c copy`,** so they must all come from one encoder: record the encoder used and force a full re-render when it changes; otherwise re-render just the changed shots.
- **The drift check at the end** must be within one frame of the song plus the end card.

**Encoding:** `h264_videotoolbox -allow_sw 0 -profile:v high -g 60 -q:v 70` for masters (without `-g`, VideoToolbox keyframes every 12 frames and bloats the file). q 65 starved grainy footage (a documentary grade got 4.5 Mbps). Decode is `-hwaccel videotoolbox`. A self-test decodes with `-hwaccel_output_format videotoolbox_vld` so a software fall-back errors instead of silently running on the CPU.

**Captions** (Out of Office's are in `out-of-office/tools/captions.py`; the styles are Sara's house styles):
- Sara: neon word-pops.
- Hooks: chromatic slams.
- The second vocalist: system panels, or gold rap words.
- Kevin: blue bubbles with Delivered/Read.
- Whispered asides: small italics.
- Documentary sections: lower thirds plus subtitles with the [BLEEP] bar, at most about 3 words per second.
- Skip a caption when the frame already shows the words (OOO S57).
- Substitute fonts (on a Mac: DIN Condensed, Helvetica Neue, Menlo) carry a per-font vertical nudge, so captions land within 2 px of the original renders.

**Sound design:** effects mixed under the song (a 1 kHz bleep, stamp thunks, dings, survey blips).

**Signature ending, every video (Sara's house rule):** the "HOW WOULD YOU RATE YOUR EXPERIENCE TODAY?" survey card, then the end card.

**Deliverables:**
- **WIP cuts:** `NAME_wipN.mp4`, never overwriting a sent one.
- **The full 1080p master.**
- **A compact version of about 130 MB:** a VideoToolbox bitrate target = MB × 8 / duration − audio. Use a 2-pass x264 only if the director asks and nothing else is running on the machine.
- **The 9:16 shorts (they replace the ~90–100 s medley reel):** at least 6 separate clips, each ONE continuous stretch of the song with one reason to care: the chorus (the sound), a punchline run (the send), the dark turn (the comment). Open on the hook or payoff in the first second; a chorus runs 15–25 s, a joke as long as the joke (8–15 s), a setup and payoff up to 30 s. Never a stitched medley: Out of Office's 1:47 medley reel didn't flow.
  - **How:** a shorts script maps each clip's name to its stretch of the song, takes the film's exact picture without captions (upscaled windows included), and adds the crops, fits, pans and the vertical captions (`captions.configure(W, H, True)`). Out of Office's `out-of-office/tools/more/shorts.py` is the frame-by-frame original; a later video rebuilt it on top of its reels script, which is the preferred way. Outputs go to a `shorts/` folder, plus 720×1280 phone copies for review.
  - **Edges in the vocal stem's gaps.** Print the stem's level at 40 ms steps ±0.3 s around each edge and cut where it dips. Whisper's word ends run early or late by up to 0.7 s (on a later video a choir held its last word 0.7 s past Whisper's end, and another line ended 0.15 s before it). Mute the stem past an edge where the next line's consonant would leak, and hold the last frame rather than flash the next shot.
  - **Frame the wide gags by hand.** MediaPipe's face finder only catches close-ups, so every wide shot falls back to the small "fit" band. On gridded caption-free frames, pick a crop x or a pan (start x, end x, eased) that follows the line to its punchline. FIT only for text tableaux and crowds.
  - **Open on the picture, not a white flash:** a short that starts on one of the film's flash shots (`DROPS`) gets that first shot rendered without the flash. The first frame is the default cover on TikTok and Reels.
  - **Check each clip:** frame count = span × 25 (at 25 fps) and audio = video; a strip every ~0.75 s judged against the lyric (is the thing the line names in frame when it's sung, and clear of the captions?).
- **Compact and phone copies: an all-GPU transcode, about 0.1 of a core.**
  - `-hwaccel videotoolbox -hwaccel_output_format videotoolbox_vld -i IN -c:v h264_videotoolbox -allow_sw 0 -b:v … -c:a copy`, plus `-vf scale_vt=w=720:h=1280` for a phone copy under 30 MB.
  - **Measure once, then aim:** one run came out about 15% under its bitrate target (3400k gave 2.9 Mbps, 112 MB for 4:44); another landed within 1% (3450k gave 3.44 Mbps; 2920k gave 129.4 MB for 5:26), with `-hwaccel_output_format videotoolbox_vld` and `-c:a copy`. Encode once at the computed target, check the size, adjust.

## §9 End-to-end checks before anything reaches the director

Run these on the cut you are about to send, not just on its parts (`qa-gates.md` §6):
1. **Every segment's frame count** equals the storyboard's; the drift is within a frame.
2. **A full GPU decode is clean.** Packet sizes match slot by slot: concat adds in-band SPS/PPS, +24 or +28 bytes per keyframe. Don't compare decoded-frame hashes across VideoToolbox decodes.
3. **A whole-film colour scan:** no green-dominated samples.
4. **Motion:** no unexplained flips (a strip every 0.1 s of any shot that moves oddly; `scripts/carflow.py` for a signed number), and every vehicle flip checked by eye.
5. **`scripts/lip_lag.py`:** a median near 0 over the shots with correlation ≥ 0.3.
6. **Props checked** on every sync.so shot (diff against `gen/v2v_in`).
7. **The final's audio cross-correlated with the song:** a 0 ms offset (no AAC priming delay).
8. **Evidence sent** with the cut: a contact or before/after sheet under 30 MB, what changed, and what to watch at which m:ss.
