# The generation flow (agreed with the director)

*The full order of work for a video is the `sara-music-video` skill's SKILL.md (principles, the flow, a toolbox), with the continuous-scene toolbox in `../sara-music-video/references/storyboard-spec.md` (install both skills). This file is the continuity half of that order; where they differ, that skill wins.*

The director's diagnosis, after the continuity reviews: the set reference was the missing step, and the next clip should be prompted with the previous clip's end as its reference. This is the order of work for a video; the old pipeline was concept → wardrobe → storyboard → stills in parallel, with nothing connecting the shots.

1. **Concept and lyrics.**
2. **Wardrobe references:** the outfits, and **one fixed identity line per character** with exact words for the marks that drift (seams, make-up, hair colour, lanyard). The line never varies between prompts.
3. **Set pack.** Per location used in more than one shot: an EMPTY establishing wide **per lighting state it is seen in** (day, dusk, night, lit), one layout line (what is where, which side the camera lives on, where the exits are), and every recurring thing on a fixed sheet: props (a chair, a portal, a billboard), creatures (a monster, a robot dog), and **each character generation** (a robot version, a costume variant) as a design, never a description.
4. **The director signs off the set pack**, as they sign off the wardrobe references.
5. **The storyboard is written in scenes.** Each scene has a staging line (geography, camera side, who is screen-left, direction of travel, light and time). Every cut has a type: FLOW, SAME, JUMP, TRANSITION or MONTAGE. Every shot has a start state and an end state, including every running prop. (SKILL.md Part 1.)
6. **Stills, scene by scene, in order.** Each still is made from the set reference + the identity references + **the previous shot's still** as the continuity reference (at this stage, before any clip exists; once the clips are made, the next shot's start frame is taken from the previous clip's cut frame instead, step 9) ("the SAME place and camera side: keep every position and the sides; only the action changes"). Only a scene's first still starts from the anchors alone.
7. **The join check on the stills** (`scripts/join_check.py --stills`), the character face sheet and the thread ledger, all before any video is paid for. A flipped still is cheap to redo.
8. **The animatic** (stills + song + captions) for the director's notes. Timing and pacing notes are cheapest here.
9. **Clips, scene by scene, produced from each other.** Where the camera holds: generate A with **B's still as the end frame** (`scripts/gen.py` job key `end`), so A lands on a reviewed still and a scene's clips run in parallel. Where the action is unpredictable: **chain** B's start from A's last used frame (`scripts/chain_frame.py`), cleaned through the image model, re-anchored from the character references every two or three hops. Check every clip's cut frame before building the next on it. Lip shots are in the chain (their still comes from the previous cut frame; the next shot chains from the lip clip). **A lip shot is a Kling singing take first** (sound on, the lyric in the prompt, fitted against the vocal); OmniHuman only for a take that fails, stills shown to the director with the quote first.
10. **Post** (below), then `scripts/join_check.py --cut`, the intent screen, and **the end-to-end pass (SKILL.md Part 3c): every shot in motion, looks at full size, placeholders labelled**, then the director's notes. Build and send **minute by minute** or section by section on a long video; nothing already approved is exempt from the next read.
11. **When a section's fixes go in circles,** stop and restage it (SKILL.md Part 3d): the plan and a section animatic for the director's yes before any clip.

## Post-processing, in order
1. **Windows:** each clip's used seconds from the frame strips; the played part ends where the next shot starts. Chained shots are windowed at 0.04 s.
2. **Seam blend** 3–6 frames at every chained cut (`scripts/seam_blend.py`).
3. **Grade match at joins:** small luma or warmth steps inside a scene get a curve in the editor; big ones are a regenerate.
4. **Speed by frame blending only** (ffmpeg's `framerate` for a speed change, `minterpolate` for a fit to the beat); never slow a clip much in the edit (ask the prompt for slow motion): below about 0.5× it reads as frozen.
5. **Free fixes:** paint-outs from the clip's own plate, a mirror for a flipped side (only with no text, clocks or one-sided marks in frame), crops, prop composites, hair recolour on a finished lip clip.
6. **Upscale** only the 720p sources that survive (Kling std, older clips), windowed and frame-exact.
7. **Captions and graphics.**
8. **Gates on the cut:** frame counts and drift, the audio offset, the colour scan, the mouth scan on non-lip shots, `scripts/join_check.py --cut`, the cut sheet read in order, a scan for freezes and looks, and the end-to-end pass (`scripts/story_sheets.py` + ledger + `scripts/join_judge.py` → `review/E2E_cutN.md`).
9. **Deliverables:** the master, the compact, the 9:16.
