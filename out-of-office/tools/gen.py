"""Run Higgsfield jobs in parallel from a JSON job list, download results, resume-safe.

Job: {"id", "model", "params": {...}, "refs": [paths], "start": path|null, "out": path}
Usage: python gen.py jobs.json [workers]
"""
import json
import os
import subprocess
import sys
import threading
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

HF = "higgsfield.cmd" if os.name == "nt" else "higgsfield"
ROOT = os.path.dirname(os.path.abspath(sys.argv[1]))
UPLOADS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads.json")
LOG = os.path.join(ROOT, "gen_log.jsonl")
lock = threading.Lock()


def run(args, timeout):
    p = subprocess.run([HF, *args], capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    return p.returncode, p.stdout, p.stderr


def upload_id(path):
    path = os.path.abspath(path)
    key = f"{path}|{os.path.getmtime(path)}"  # re-upload when the file changes (a regenerated still keeps its name)
    with lock:
        cache = json.load(open(UPLOADS)) if os.path.exists(UPLOADS) else {}
        if key in cache:
            return cache[key]
    for _ in range(8):
        code, out, err = run(["upload", "create", path, "--json"], 600)
        if not code:
            break
        time.sleep(30)
    if code:
        raise RuntimeError(f"upload failed {path}: {err[-300:]}")
    d = json.loads(out)
    d = d[0] if isinstance(d, list) else d
    uid = d.get("id") or d.get("upload_id") or d.get("media_id")
    if not uid:
        raise RuntimeError(f"no upload id in {out[:300]}")
    with lock:
        cache = json.load(open(UPLOADS)) if os.path.exists(UPLOADS) else {}
        cache[key] = uid
        json.dump(cache, open(UPLOADS, "w"), indent=1)
    return uid


def do(job):
    out = os.path.join(ROOT, job["out"])
    if os.path.exists(out) and os.path.getsize(out) > 1000:
        return job["id"], "skip"
    os.makedirs(os.path.dirname(out), exist_ok=True)
    args = ["generate", "create", job["model"]]
    for k, v in job.get("params", {}).items():
        args += [f"--{k}", str(v)]
    for r in job.get("refs", []):
        args += ["--image-references", upload_id(os.path.join(ROOT, r))]
    if job.get("start"):
        args += ["--start-image", upload_id(os.path.join(ROOT, job["start"]))]
    if job.get("audio"):
        args += ["--audio-references", upload_id(os.path.join(ROOT, job["audio"]))]
    args += ["--wait", "--wait-timeout", "25m", "--wait-interval", "6s", "--json"]
    last = ""
    attempt = 0
    while attempt < 3:
        attempt += 1
        t0 = time.time()
        try:
            code, so, se = run(args, 1800)
        except subprocess.TimeoutExpired:
            last = "timeout"
            continue
        if code == 0:
            try:
                d = json.loads(so)
                d = d[0] if isinstance(d, list) else d
                url = d.get("result_url")
                if d.get("status") == "completed" and url:
                    urllib.request.urlretrieve(url, out)
                    with lock:
                        with open(LOG, "a") as f:
                            f.write(json.dumps({"id": job["id"], "job": d.get("id"), "model": job["model"], "url": url,
                                                "secs": round(time.time() - t0)}) + "\n")
                    return job["id"], f"ok {round(time.time() - t0)}s"
                last = f"status {d.get('status')}"
            except Exception as e:  # noqa: BLE001
                last = f"parse {e}: {so[:200]}"
        else:
            last = (se or so)[-300:]
            if "rate_limit_reached" in last:  # account-wide concurrency cap: wait for a slot, don't burn a retry
                attempt -= 1
                time.sleep(45)
                continue
        time.sleep(5)
    with lock:
        with open(LOG, "a") as f:
            f.write(json.dumps({"id": job["id"], "error": last}) + "\n")
    return job["id"], f"FAILED {last}"


if __name__ == "__main__":
    jobs = json.load(open(sys.argv[1]))
    only = set(sys.argv[3].split(",")) if len(sys.argv) > 3 else None
    if only:
        jobs = [j for j in jobs if j["id"] in only]
    workers = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    def safe(job):
        try:
            return do(job)
        except Exception as e:  # noqa: BLE001 - one bad job must not stop the batch
            return job["id"], f"FAILED {e}"
    with ThreadPoolExecutor(workers) as ex:
        for jid, status in ex.map(safe, jobs):
            print(f"{jid}: {status}", flush=True)
