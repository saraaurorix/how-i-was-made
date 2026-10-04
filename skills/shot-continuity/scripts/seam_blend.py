"""Smooth a chained cut: Kling's first frames step a little further than normal and shift the brightness a few levels, so a chained
cut still shows a small hitch. Blends the first N used frames of B's clip with A's continuation frames (the ones just after A's last used
frame), fading from A to B. B's clip is rewritten; the original is kept as <B>_raw.mp4. The encode uses the machine's GPU encoder
where there is one and x264 otherwise (venc.py).
Usage: python seam_blend.py A B [--n 3] [--sb storyboard.json] [--clips gen/clips] [--window windows.json]
Run it from the project folder. A's clip needs N frames after its last used frame: when the cut plays A to the very end of its clip
there are none to blend with: the script then stops before changing anything and says which --n would work. A's and B's
clips must have the same size and frame rate. Both clips are decoded into memory, so keep to clips of a few seconds.
--sb, --clips and --window (a JSON file {shot id: seconds into the clip where the cut starts playing it}) are described in chainlib.py."""
import argparse, os, subprocess, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import chainlib as C
import venc
ap = argparse.ArgumentParser(); ap.add_argument("a"); ap.add_argument("b"); ap.add_argument("--n", type=int, default=3); C.add_common(ap)
a = ap.parse_args()
sb, win = C.load(a)
raw = os.path.join(a.clips, a.b + "_raw.mp4"); out = os.path.join(a.clips, a.b + ".mp4")
src = raw if os.path.exists(raw) else out  # B as it was before any blend
W, H, fps = C.probe(src)


def frames(p):
    r = subprocess.run([C.FF, "-v", "error", "-i", p, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True)
    return np.frombuffer(r.stdout, np.uint8).reshape(-1, H, W, 3)


A = frames(os.path.join(a.clips, a.a + ".mp4")); B = frames(src).copy()
last = C.last_used_index(sb[a.a], C.window(win, a.a, a.default_window), fps)
b0 = round(C.window(win, a.b, C.CHAIN_WINDOW) * fps)
spare = len(A) - 1 - last  # frames of A after the last one the cut plays
if spare < a.n or b0 + a.n > len(B):
    sys.exit(f"{a.a} has {max(spare, 0)} frame(s) after its last used frame and --n is {a.n}: nothing was changed. "
             f"Use --n {max(spare, 0)} or less" + ("" if spare > 0 else " (here there is nothing to blend with: leave this cut as it is)") + ".")
if src == out:
    os.rename(out, raw)
for k in range(a.n):
    wa = 1 - (k + 1) / (a.n + 1)
    B[b0 + k] = np.clip(wa * A[last + 1 + k].astype(float) + (1 - wa) * B[b0 + k].astype(float), 0, 255).astype(np.uint8)
p = subprocess.Popen([*C.NICE, C.FF, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", f"{fps:g}", "-i", "-",
                      *venc.h264(85, gop=24), "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
p.stdin.write(B.tobytes()); p.stdin.close(); p.wait()
print(f"{a.b}: frames {b0}..{b0 + a.n - 1} blended with {a.a} frames {last + 1}..{last + a.n} -> {out} (original kept as {raw})")
