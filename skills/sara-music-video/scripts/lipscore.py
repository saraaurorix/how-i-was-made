"""Lip-sync score from face landmarks: how open the lips are (MediaPipe) vs how loud the vocal is, frame by frame.

score(clip, wav, seconds) -> {"corr", "lag_ms", "face"}: corr > 0.5 good, 0.3-0.5 loose, < 0.3 poor.
lag_ms > 0 means the mouth trails the voice. Works for held sung notes (unlike motion-based checks).
Usage: python tools/lipscore.py clip.mp4 driving.wav [seconds]
"""
import os
import subprocess
import sys

import cv2
import imageio_ffmpeg
import mediapipe as mp
import numpy as np
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.core.base_options import BaseOptions

FF = imageio_ffmpeg.get_ffmpeg_exe()
MODEL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models", "face_landmarker.task")


def apertures(clip, seconds=None):
    lm = vision.FaceLandmarker.create_from_options(vision.FaceLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=MODEL), running_mode=vision.RunningMode.VIDEO, num_faces=1))
    cap = cv2.VideoCapture(clip)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    out, i = [], 0
    while True:
        ok, f = cap.read()
        if not ok or (seconds and i >= seconds * fps):
            break
        r = lm.detect_for_video(mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(f, cv2.COLOR_BGR2RGB)), int(i * 1000 / fps))
        if r.face_landmarks:
            p = r.face_landmarks[0]
            face_h = np.hypot(p[10].x - p[152].x, p[10].y - p[152].y) + 1e-6
            out.append(np.hypot(p[13].x - p[14].x, p[13].y - p[14].y) / face_h)
        else:
            out.append(np.nan)
        i += 1
    lm.close()
    return np.array(out), fps


def envelope(wav, fps, n):
    p = subprocess.run([FF, "-v", "error", "-i", wav, "-ac", "1", "-ar", "16000", "-f", "f32le", "-"], capture_output=True)
    a = np.frombuffer(p.stdout, dtype=np.float32)
    hop = 16000 / fps
    env = np.array([np.sqrt((a[int(k * hop):int((k + 1) * hop)] ** 2).mean()) if int(k * hop) < len(a) else 0 for k in range(n)])
    return np.convolve(env, np.ones(3) / 3, mode="same")


def score(clip, wav, seconds=None):
    ap, fps = apertures(clip, seconds)
    face = float(np.mean(~np.isnan(ap))) if len(ap) else 0.0
    if face < 0.5:
        return {"corr": float("nan"), "lag_ms": 0, "face": round(face, 2)}
    ap = np.where(np.isnan(ap), np.nanmean(ap), ap)
    env = envelope(wav, fps, len(ap))
    best = (-2.0, 0)
    for lag in range(-6, 7):  # lag > 0: mouth trails voice
        a, e = (ap[lag:], env[:len(env) - lag]) if lag >= 0 else (ap[:lag], env[-lag:])
        if len(a) > 10 and a.std() > 0 and e.std() > 0:
            c = float(np.corrcoef(a, e)[0, 1])
            if c > best[0]:
                best = (c, lag)
    return {"corr": round(best[0], 2), "lag_ms": round(best[1] * 1000 / fps), "face": round(face, 2)}


if __name__ == "__main__":
    if len(sys.argv) < 3 or sys.argv[1] in ("-h", "--help"):
        sys.exit(__doc__)
    print(score(sys.argv[1], sys.argv[2], float(sys.argv[3]) if len(sys.argv) > 3 else None))
