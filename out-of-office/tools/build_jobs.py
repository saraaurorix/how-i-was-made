"""Turn storyboard.json into keyframe-still jobs and clip jobs for gen.py."""
import json
import os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sb = json.load(open(os.path.join(ROOT, "storyboard.json")))

REFS = {
    "o": ["gen/char/nova_portrait.png", "gen/char/nova_office.png"],
    "c": ["gen/char/nova_portrait.png", "gen/char/nova_club.png"],
    "s": ["gen/char/nova_portrait.png", "gen/char/nova_space.png"],
    "k": ["gen/char/kevin.png"],
}
NOVA = ("NOVA is the female android from the reference images: keep her face identical, platinum-silver blunt bob with a sharp fringe, "
        "glowing electric-cyan eyes, fine chrome seams on her jaw and collarbones. ")
KEVIN = ("KEVIN is the man from the reference image: keep him identical, balding comb-over, thick mustache, round wire glasses, "
         "beige short-sleeve shirt, mustard tie. ")
STYLE = (" Cinematic music-video still, glossy high-fashion dystopian corporate satire, saturated neon magenta and electric cyan "
         "accents against sickly beige office tones, anamorphic lens flare, shallow depth of field, crisp hyperreal detail, no captions, no watermark.")

stills, clips = [], []
for s in sb:
    refs = []
    for ch in s["refs"]:
        refs += [r for r in REFS[ch] if r not in refs]
    prefix = (NOVA if any(c in s["refs"] for c in "ocs") else "") + (KEVIN if "k" in s["refs"] else "")
    stills.append({"id": s["id"], "model": "nano_banana_pro",
                   "params": {"aspect_ratio": "16:9", "resolution": "2k", "prompt": prefix + s["still"] + STYLE},
                   "refs": refs, "out": f"gen/stills/{s['id']}.png"})
    clips.append({"id": s["id"], "model": "kling3_0",
                  "params": {"mode": "pro", "duration": 5, "sound": "off", "aspect_ratio": "16:9",
                             "prompt": s["motion"] + " Dynamic cinematic music-video camera work, energetic, smooth motion, keep the characters' faces consistent."},
                  "start": f"gen/stills/{s['id']}.png", "out": f"gen/clips/{s['id']}.mp4"})

json.dump(stills, open(os.path.join(ROOT, "jobs_stills.json"), "w"), indent=1)
json.dump(clips, open(os.path.join(ROOT, "jobs_clips.json"), "w"), indent=1)
print(len(stills), "stills,", len(clips), "clips")
