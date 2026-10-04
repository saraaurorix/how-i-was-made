"""ffmpeg H.264 arguments: the machine's GPU encoder where there is one, x264 otherwise.

These scripts were written on a Mac and encoded with Apple VideoToolbox. So that they run anywhere:

    import venc
    cmd = [FF, "-i", src, *venc.h264(80, gop=24), "-pix_fmt", "yuv420p", out]   # 80 = quality, 0-100, higher is better
    cmd = [FF, *venc.hwdec(), "-i", src, ...]                                    # GPU decode on a Mac, nothing elsewhere

The first call tries, in order, VideoToolbox (macOS), NVENC (NVIDIA), Quick Sync (Intel), then libx264, with a one-frame
test encode, and remembers the answer. Force one with the environment variable VENC, for example VENC=libx264.
"""
import os
import subprocess
import sys

_picked = None


def _ffmpeg():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"


def _works(codec):
    test = [_ffmpeg(), "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i", "color=c=black:s=320x180:r=24:d=0.2",
            "-c:v", codec, *(["-allow_sw", "0"] if codec == "h264_videotoolbox" else []), "-pix_fmt", "yuv420p", "-f", "null", "-"]
    try:
        return subprocess.run(test, capture_output=True, timeout=30).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def encoder():
    """The H.264 encoder ffmpeg will be asked for on this machine."""
    global _picked
    if _picked is None:
        forced = os.environ.get("VENC")
        order = [forced] if forced else (["h264_videotoolbox"] if sys.platform == "darwin" else []) + ["h264_nvenc", "h264_qsv", "libx264"]
        _picked = next((c for c in order if c == "libx264" or _works(c)), "libx264")
    return _picked


def h264(q=70, gop=None):
    """ffmpeg arguments for an H.264 encode at quality q (0-100, as VideoToolbox's -q:v; about 55 draft, 70 final, 80 master)."""
    enc = encoder()
    crf = str(max(12, min(30, round(34 - q * 0.22))))  # 55 -> 22, 70 -> 19, 80 -> 16
    args = {"h264_videotoolbox": ["-c:v", "h264_videotoolbox", "-allow_sw", "0", "-profile:v", "high", "-q:v", str(q)],
            "h264_nvenc": ["-c:v", "h264_nvenc", "-profile:v", "high", "-rc", "vbr", "-cq", crf, "-b:v", "0"],
            "h264_qsv": ["-c:v", "h264_qsv", "-profile:v", "high", "-global_quality", crf],
            }.get(enc, ["-c:v", "libx264", "-profile:v", "high", "-preset", "medium", "-crf", crf])
    return args + (["-g", str(gop)] if gop else [])


def hwdec():
    """ffmpeg input arguments for GPU decoding: VideoToolbox on a Mac, none elsewhere."""
    return ["-hwaccel", "videotoolbox"] if encoder() == "h264_videotoolbox" else []


if __name__ == "__main__":
    print("encoder:", encoder(), "| h264(70):", " ".join(h264(70)), "| hwdec:", " ".join(hwdec()) or "(none)")
