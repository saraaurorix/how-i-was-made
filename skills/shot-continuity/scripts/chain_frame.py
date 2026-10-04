"""Save the LAST frame the cut uses from shot A's clip, as shot B's start frame (or as a reference for B's still), so B begins exactly
where A ends. Then set B's WINDOW to 0.04.
Usage: python chain_frame.py A B OUT.png [--sb storyboard.json] [--clips gen/clips] [--window windows.json]
Run it from the project folder. --window is a JSON file {shot id: seconds into the clip where the cut starts playing it}, or one that
holds that map under a "WINDOW" key; shots not in it use --default-window (0.15). The formats and the frame arithmetic: chainlib.py."""
import argparse, os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import chainlib as C
ap = argparse.ArgumentParser(); ap.add_argument("a"); ap.add_argument("b"); ap.add_argument("out"); C.add_common(ap)
a = ap.parse_args()
sb, win = C.load(a)
src = os.path.join(a.clips, a.a + ".mp4")
_, _, fps = C.probe(src)
w0 = C.window(win, a.a, a.default_window)
idx = C.last_used_index(sb[a.a], w0, fps)
have = C.count_frames(src)
if idx >= have:
    sys.exit(f"{a.a}: the cut plays its clip up to frame {idx} ({idx / fps:.2f} s) but the clip has {have} frames "
             f"({have / fps:.2f} s): nothing written. Shorten the shot, lower its WINDOW, or re-roll a longer clip.")
if os.path.exists(a.out):
    os.remove(a.out)
subprocess.run([C.FF, "-v", "error", "-y", "-i", src, "-vf", f"select=eq(n\\,{idx})", "-vframes", "1", a.out], check=True)
if not os.path.exists(a.out) or os.path.getsize(a.out) == 0:
    sys.exit(f"{a.a}: ffmpeg found no frame {idx} in {src}: nothing written.")
print(f"{a.a}: window {w0} s, {C.nframes(sb[a.a])} edit frames, clip {fps:g} fps -> last used source frame {idx} ({idx / fps:.3f} s) -> {a.out}; set WINDOW[{a.b}] = {C.CHAIN_WINDOW}")
