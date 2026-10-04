#!/usr/bin/env python3
"""Board lint: the mechanical half of the board gate (references/storyboard-spec.md §3).

Reads a storyboard (and optionally bible.json) and reports every rule that can be checked from the text, BEFORE any still
is made. Deterministic, stdlib only, no vision model, free. It finds the known mistakes that later cost remakes: adjacent
shots from one still, editing notes in a motion line, walkers with no stop, filter words, shots too long for one clip,
mouth shots with no singer or framing, labelled joins with no reason, FLOW joins whose states don't match, missing
camera setups and scale anchors, risky verbs, several actions in one shot, and the counts against Out of Office.

Boards from different videos used different field names; ALIASES maps them. A new board should use the names in the spec.
Its word lists are heuristics: a LOOK is a row to read, not a verdict. Fix the board, not the lint.

Usage: python board_lint.py storyboard.json [--bible bible.json] [--out BOARD_LINT.md]
Levels: FIX = a known cause of a re-roll, worth fixing on the board. LOOK = a row worth a glance. GAP = an optional field this board doesn't use.
It is a list of things to look at, not a gate; decide for yourself.
"""
import argparse, json, re, statistics, sys
from collections import OrderedDict, defaultdict

ALIASES = {
    "lyric": ["cap", "lyric", "lines"],
    "picture": ["picture", "pic", "still_prompt"],  # plus "scene" when it is long text
    "action": ["motion", "action"],
    "place": ["set", "place", "fmt"],
    "voice": ["voice", "sings"],
    "still": ["still", "still_file"],
    "extra": ["expr", "text", "omni_prompt"],
}
OOO = {"shots": 74, "mean": 3.2, "lip": 14}  # Out of Office, the benchmark (creative-playbook §5)
MAX_CLIP = 4.7  # a 5 s Kling clip is 4.84 s at 25 fps


def get(s, key):
    for k in ALIASES.get(key, [key]):
        v = s.get(k)
        if v not in (None, "", "None", [], "[]"):
            return str(v)
    if key == "picture" and len(str(s.get("scene", ""))) > 40:
        return str(s["scene"])
    return ""


def scene_id(s):
    if s.get("scene_id"):
        return str(s["scene_id"])
    v = str(s.get("scene", ""))
    return v if 0 < len(v) <= 24 else ""


def f(x, d=0.0):
    try:
        return float(x)
    except (TypeError, ValueError):
        return d


def is_lip(s):
    t = str(s.get("type", s.get("kind", ""))).lower()
    return t == "lip" or str(s.get("lip", "")).lower() == "true"


def is_clip(s):
    t = str(s.get("type", s.get("kind", ""))).lower()
    return t in ("gen", "clip", "lip", "kling", "") or is_lip(s)


def has(rx, text):
    return re.search(rx, text, re.I) is not None


R = {
    "edit_note": r"\b(caption|subtitle|title card|title slams?|white flash|flash(es)? (to|into)|cuts? to|whip[- ]pan to|dissolves?|fades? (in|out|to)|overlay|lower third|on-screen text|slams? on the (hit|beat))\b",
    "walker": r"\b(walks?|walking|strides?|striding|struts?|strutting|runs?|running|march(es|ing)?|charges?|steps? forward)\b[^.;]{0,80}?\b(toward|towards|at|into) (the )?(camera|lens|viewer)",
    "walker_ok": r"\b(stops?|halts?|stays? full[- ]length|freezes)\b",
    "filter": r"\b(sexy|sexily|bustier|plung(e|ing)|low-rise|body chain|midriff|straddl\w*|bend(s|ing)? over|hip against|edge of the bed|seamed stockings?|lingerie)\b",
    "undress": r"\b(takes? off|taking off|slips? (off|out of)|slipping off|removes? (her|his) (blazer|jacket|dress|top|shirt|coat)|undress\w*|strips? off)\b",
    "risky": r"\b(rolls? away|crash(es|ing)?|falls? (over|down|off)|tips? over|topples?|collaps(es|ing))\b",
    "mirror": r"\b(in (a|the|her|his) mirror|mirror (image|selfie)|(her|his|their) reflection|reflected in)\b",
    "seq": r"\b(then|and then|after that|finally)\b|->|→",
    "dance": r"\b(danc\w*|choreograph\w*|groov\w*)\b",
    "dance_one": r"\b(one|single|step-touch|sway\w*|same (step|move)|over and over|repeat\w*)\b",
    "dance_moves": r"\b(spins?|twirls?|kicks?|shimm(y|ies)|hip (roll|thrust)|jumps?|points?|claps?|slides?|turns?|drops?|splits?)\b",
    "guitar": r"\b(guitar|riff|bass guitar)\b",
    "guitar_ok": r"\bstrap\b.*\b(pick|fret|strings?)\b|\b(pick|fret|strings?)\b.*\bstrap\b",
    "lip_frame": r"close-?up|close up|head-and-shoulders|head and shoulders|\bmcu\b|medium close|\bcu\b|face fills|portrait|punched in",
    "others": r"\b(kevin|crowd|audience|the man|guy|courtiers?|front row|passengers?|the groom|the bride)\b",
    "others_ok": r"mouths? (closed|shut)|lips (closed|sealed|together)|silent|not (singing|talking|speaking)|keeps? (his|their|her) mouth",
    "she": r"\b(she|her)\b",
    "sara": r"\b(sara|nova|saras)\b",
    "other_woman": r"\b(mum|mother|woman|women|girl|bride|lady|grandma|granny|queen|nurse|she-\w+)\b",
    "big": r"\b(crowd|audience|stadium|arena|elephant|giant|huge|tower|skyscraper|ship|plane|airliner|jet|car|truck|lift|elevator|monster|building|dragon|kaiju)\b",
    "scale_ok": r"same height|size of|as tall as|towers? (over|behind)|tiny|small in (the )?frame|far|distant|dwarf|scale|(head|shoulder|waist|hip|knee) height",
    "cam_locked": r"\b(locked|locked-off|camera does not move|static camera|camera holds)\b",
    "cam_moves": r"\b(pans?|tracks?|tracking|dolly|push(es)? in|zooms?|orbits?|crane|pulls? back)\b",
    "quoted": r"[\"“][^\"”]{2,}[\"”]",
    "landmark": r"\b(skyline|cityscape|downtown|cathedral|bridge|landmark|eiffel|big ben)\b",
    "landmark_ok": r"no (domes|landmark|spires|bridges)",
    "move": r"\b(walks?|strides?|struts?|runs?|leaps?|jumps?|slides?|rides?|climbs?|carr(y|ies|ied)|enters?|exits?|pivots?|turns? (round|around|back)|sits? down|stands? up|kneels?|falls?|dives?|steps? (off|out|through|in)|rolls? (out|in|away)|glides?|march(es)?|arrives?|leaves?)\b",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("board")
    ap.add_argument("--bible", default="")
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    d = json.load(open(a.board))
    sb = d if isinstance(d, list) else d.get("shots", [])
    bible = json.load(open(a.bible)) if a.bible else {}
    scenes_b = {str(sc.get("id")): sc for sc in bible.get("scenes", [])}
    props_b = bible.get("props", {})

    fix, look = defaultdict(list), defaultdict(list)
    gaps = OrderedDict((k, []) for k in ["cam", "scale", "start", "end", "route", "read", "join", "join_why", "voice", "lip_route"])

    def note(level, rule, s, why):
        (fix if level == "FIX" else look)[rule].append((s.get("id", "?"), f(s.get("t0")), why))

    has_voice = any(get(s, "voice") for s in sb)
    has_lipfield = any(("type" in s) or ("kind" in s) or ("lip" in s) for s in sb)
    has_place = any(get(s, "place") for s in sb)
    prev = None
    for i, s in enumerate(sb):
        t0, t1 = f(s.get("t0")), f(s.get("t1"))
        dur = t1 - t0
        pic, act, extra = get(s, "picture"), get(s, "action"), get(s, "extra")
        lip, clip = is_lip(s), is_clip(s)
        text = " ".join([pic, act, extra])
        chained = "chained" in pic.lower() or str(s.get("route", "")).lower() == "chain"

        # length
        if clip and dur > MAX_CLIP and not s.get("long"):
            note("LOOK" if lip else "FIX", "longer than one clip", s, f"{dur:.2f} s > {MAX_CLIP} s: split, chain a second clip, or mark long (10 s)")
        if clip and 0 < dur < 0.4:
            note("LOOK", "very short shot", s, f"{dur:.2f} s reads as a flash")
        # adjacency
        st = get(s, "still")
        if prev is not None and st and st == get(prev, "still") and not chained:
            note("FIX", "adjacent shots from one still", s, f"same still as {prev.get('id')}: poses and props reset at the cut")
        # motion line
        if act and has(R["edit_note"], act):
            note("FIX", "editing note in the motion line", s, re.search(R["edit_note"], act, re.I).group(0) + " (Kling draws it; keep it in the edit notes)")
        if act and has(R["walker"], act) and not has(R["walker_ok"], act):
            note("FIX", "walker with no stop", s, "say where they stop, 'stays full length in the frame', 'locked-off camera'")
        n_seq = len(re.findall(R["seq"], act, re.I))
        if n_seq >= 2:
            note("FIX", "several actions in one shot", s, f"{n_seq + 1} steps in sequence: one action per shot")
        elif n_seq == 1:
            note("LOOK", "two actions in one shot", s, "'then': can Kling do both inside the played seconds?")
        if act and has(R["risky"], act):
            note("LOOK", "risky verb", s, re.search(R["risky"], act, re.I).group(0) + ": Kling tends to make an accident of it (spec §4)")
        if act and has(R["cam_locked"], act) and has(R["cam_moves"], act):
            note("FIX", "camera locked and moving", s, "the motion line asks for both a locked camera and a move")
        if act and has(R["dance"], act):
            if not has(R["dance_one"], act):
                note("LOOK", "dance with no single step", s, "name one repeated step, fitted to the beat in the edit")
            if len(set(m.group(0).lower() for m in re.finditer(R["dance_moves"], act, re.I))) >= 3:
                note("LOOK", "dance routine in one clip", s, "several moves in 5 s come back too fast: one move per clip")
        # filters and undressing
        if has(R["filter"], text):
            note("FIX", "filter word", s, re.search(R["filter"], text, re.I).group(0) + ": describe the garment and the cut (spec §4)")
        if pic and has(R["undress"], pic):
            note("FIX", "undressing in a still", s, "every image filter refuses it: animate it from a chained frame")
        elif act and has(R["undress"], act):
            note("LOOK", "undressing in the motion line", s, "check the clip; stills of it are refused")
        if pic and has(R["mirror"], pic):
            note("LOOK", "mirror or reflection", s, "Kling confuses reflections: frame straight on")
        # performance
        if clip and has(R["guitar"], text) and has(R["sara"], text) and not has(R["guitar_ok"], text):
            note("LOOK", "guitar without the playing spec", s, "strap, pick over the strings, fingertips on the frets in the still")
        # mouth shots
        if lip:
            v = get(s, "voice").strip()
            if not v and not has_voice:
                gaps["voice"].append(s.get("id"))
            elif not v:
                note("FIX", "mouth shot with no singer", s, "who sings this line, as sung (the casting check)?")
            elif v.upper() not in ("S", "SARA"):
                note("LOOK", "mouth shot on another voice", s, f"voice {v}: deliberate?")
            if pic and not has(R["lip_frame"], pic) and not chained:
                note("LOOK", "mouth shot not framed for a mouth", s, "head-and-shoulders, face about a third of the height")
            if pic and has(R["others"], pic) and not has(R["others_ok"], text):
                note("LOOK", "others in a mouth shot", s, "say everyone else's mouth stays shut")
            if not s.get("lip_route"):
                gaps["lip_route"].append(s.get("id"))
        # references, scale, text, landmarks
        cast = str(s.get("cast", "")) + str(s.get("refs", ""))
        if pic and has(R["she"], pic) and not has(R["sara"], pic) and not has(R["other_woman"], pic) and "sara" not in cast.lower():
            note("LOOK", "her with no SARA", s, "a row that doesn't name her may get no face or outfit reference")
        if pic and has(R["big"], pic) and has(r"\b(sara|kevin|nova)\b", pic) and not s.get("scale") and not has(R["scale_ok"], pic):
            note("LOOK", "no scale anchor", s, "people next to something big: write a scale anchor")
        if pic and has(R["quoted"], pic):
            note("LOOK", "text in frame", s, "locked camera; plan a WINDOW, a patch or a graphic if Kling garbles it")
        if pic and has(R["landmark"], pic) and not has(R["landmark_ok"], pic):
            note("LOOK", "possible real landmark", s, "add 'no domes, no spires, no bridges, no landmark buildings'")
        if f(s.get("speed"), 1.0) < 0.5:
            note("FIX", "slowed below 0.5x", s, "reads as a freeze: ask the prompt for slow motion instead")
        if str(s.get("reused", "")).lower() == "true" or str(s.get("src", "")).upper().startswith("REUSE"):
            note("LOOK", "reused clip", s, "a reused clip is a break by default until the join check clears it")
        for p in props_b:
            if has(r"\b" + re.escape(p) + r"\b", pic) and p not in str(s.get("props", "")) + cast:
                note("LOOK", "prop without its sheet", s, f"'{p}' has a sheet in the bible: attach it")
        # joins and states
        j = str(s.get("join", "")).upper()
        if not j:
            gaps["join"].append(s.get("id"))
        elif j in ("JUMP", "TRANSITION", "MONTAGE") and not s.get("join_why"):
            gaps["join_why"].append(s.get("id"))
        if j == "FLOW" and prev is not None and s.get("start") and prev.get("end"):
            if json.dumps(s["start"], sort_keys=True).lower() != json.dumps(prev["end"], sort_keys=True).lower():
                note("FIX", "FLOW join whose states differ", s, f"start differs from {prev.get('id')}'s end")
        for k in ("cam", "scale", "start", "end", "route", "read"):
            if not s.get(k):
                gaps[k].append(s.get("id"))
        sc = scenes_b.get(scene_id(s))
        if sc and s.get("cam") and sc.get("cams") and s["cam"] not in sc["cams"]:
            note("FIX", "camera setup not in the scene", s, f"{s['cam']} is not one of {sc['cams']}")
        prev = s

    # scenes: moves, places and looks inside a scene
    groups = OrderedDict()
    for s in sb:
        groups.setdefault(scene_id(s) or "(none)", []).append(s)
    scene_rows = []
    for sid, rows in groups.items():
        if sid == "(none)":
            continue
        span = max(f(r.get("t1")) for r in rows) - min(f(r.get("t0")) for r in rows)
        moves = sum(1 for r in rows if has(R["move"], get(r, "action")))
        rate = moves / max(span / 30.0, 0.5)
        places = sorted(set(get(r, "place") for r in rows if get(r, "place")))
        looks = [get(r, "look") for r in rows if get(r, "look") and get(r, "look").upper() not in ("NONE", "")]
        look_changes = sum(1 for x, y in zip(looks, looks[1:]) if x != y)
        sc = scenes_b.get(sid, {})
        kind = sc.get("kind", "?")
        scene_rows.append((sid, len(rows), span, moves, rate, places, look_changes, kind))
        if bible:
            if not sc:
                look["scene not in the bible"].append((sid, f(rows[0].get("t0")), "no kind, story or setups for this scene"))
            else:
                if not sc.get("kind") or not sc.get("why"):
                    fix["scene form not judged"].append((sid, f(rows[0].get("t0")), "kind and why (spec §1b)"))
                if sc.get("kind") == "continuous":
                    miss = [k for k in ("story", "axis", "cams", "relations", "direction", "moves") if not sc.get(k)]
                    if miss:
                        fix["continuous scene not directed"].append((sid, f(rows[0].get("t0")), "missing " + ", ".join(miss) + " (spec §1c)"))
                    if any(not r.get("start") or not r.get("end") for r in rows):
                        fix["continuous scene without a ledger"].append((sid, f(rows[0].get("t0")), "every row needs start and end states"))
        if (kind == "continuous" or (not bible and len(rows) >= 4)) and rate > 4:
            (fix if kind == "continuous" else look)["move budget"].append(
                (sid, f(rows[0].get("t0")), f"{moves} physical moves in {span:.0f} s ({rate:.1f} per 30 s; budget about 4)" + ("" if kind == "continuous" else ", if this scene is continuous")))
        unmarked = [r2.get("id") for r1, r2 in zip(rows, rows[1:])
                    if get(r1, "place") and get(r2, "place") and get(r1, "place") != get(r2, "place")
                    and str(r2.get("join", "")).upper() not in ("TRANSITION", "MONTAGE", "JUMP")]
        if unmarked and kind != "montage":
            look["place change with no transition"].append((sid, f(rows[0].get("t0")), ", ".join(places) + f": the place changes into {', '.join(unmarked)} without a TRANSITION"))

    # counts
    durs = [f(s.get("t1")) - f(s.get("t0")) for s in sb]
    runtime = sum(durs)
    lips = [s for s in sb if is_lip(s)]
    lip_time = sum(f(s.get("t1")) - f(s.get("t0")) for s in lips)
    places_all = [get(s, "place") for s in sb]
    switches = sum(1 for x, y in zip(places_all, places_all[1:]) if x and y and x != y)

    out = []
    w = out.append
    w(f"# Board lint: `{a.board}`" + (f" with `{a.bible}`" if a.bible else ""))
    w("")
    w(f"**{sum(len(v) for v in fix.values())} FIX** in {len(fix)} rules, **{sum(len(v) for v in look.values())} LOOK** in {len(look)} rules. "
      "FIX = a known cause of a re-roll; LOOK = worth a glance. A list to look at, not a gate.")
    w("")
    w("## Counts against Out of Office")
    w("| | This board | Out of Office |")
    w("|---|---|---|")
    w(f"| shots | {len(sb)} | {OOO['shots']} |")
    w(f"| mean shot | {statistics.mean(durs):.1f} s | {OOO['mean']} s |" if durs else "| mean shot | - | 3.2 s |")
    w(f"| mouth shots | {len(lips)} ({100 * lip_time / runtime:.0f}% of the runtime) | {OOO['lip']} |" if runtime and has_lipfield else f"| mouth shots | no type field | {OOO['lip']} |")
    w(f"| places | {len(set(p for p in places_all if p))} | |" if has_place else "| places | no place field | |")
    w(f"| place changes across cuts | {switches} | |" if has_place else "| place changes across cuts | no place field | |")
    w(f"| shots over {MAX_CLIP} s | {sum(1 for s, dd in zip(sb, durs) if is_clip(s) and dd > MAX_CLIP)} | |")
    w("")
    for title, bag in (("FIX", fix), ("LOOK", look)):
        if not bag:
            continue
        w(f"## {title}")
        for rule, items in sorted(bag.items(), key=lambda kv: -len(kv[1])):
            w(f"### {rule} ({len(items)})")
            for sid, t0, why in items[:40]:
                w(f"- `{sid}` {int(t0 // 60)}:{t0 % 60:04.1f}: {why}")
            if len(items) > 40:
                w(f"- … and {len(items) - 40} more")
        w("")
    w("## Scenes")
    w("| scene | shots | seconds | shots with a move | moves per 30 s | places | look changes | kind |")
    w("|---|---|---|---|---|---|---|---|")
    for sid, n, span, moves, rate, places, lc, kind in scene_rows:
        w(f"| {sid} | {n} | {span:.0f} | {moves} | {rate:.1f} | {', '.join(places)[:40]} | {lc} | {kind} |")
    w("")
    w("## GAP: optional spec fields this board doesn't use")
    w("| field | missing on | of |")
    w("|---|---|---|")
    for k, ids in gaps.items():
        total = len(lips) if k in ("lip_route", "voice") else (sum(1 for s in sb if str(s.get('join', '')).upper() in ('JUMP', 'TRANSITION', 'MONTAGE')) if k == "join_why" else len(sb))
        w(f"| `{k}` | {len(ids)} | {total} |")
    text = "\n".join(x for x in out if x is not None)
    if a.out:
        open(a.out, "w").write(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
