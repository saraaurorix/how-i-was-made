"""Run Higgsfield jobs (stills or clips) in parallel from a JSON job list, download the results, resume-safe.

Usage: python gen.py jobs.json [workers] [ID,ID]      (workers: 4 by default; ID,ID: only these jobs)

Needs the Higgsfield CLI (`higgsfield`, npm package @higgsfield/cli) installed and signed in; each job uses that account's
credits. jobs.json is a list of jobs:
  {"id", "model", "params": {...}, "refs": [paths], "start": path|null, "end": path|null, "audio": path|null, "out": path}
  model, params   passed on as `higgsfield generate create MODEL --key value ...`
  refs            reference images; start and end are the clip's first and last frame (start = the previous shot's last used
                  frame from chain_frame.py is how a shot is chained); audio is an audio reference
  out             where the result is saved. A job whose out file already exists is skipped, so a stopped batch can be run again.
Paths are relative to the job file's folder. Uploads are cached in uploads.json beside this script (keyed on path, content and
account); results and errors are logged to gen_log.jsonl beside the job file. GEN_ATTEMPTS (default 3) is the number of tries per job.
"""
import hashlib, json
import os
import subprocess
import sys
import threading
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

HF = "higgsfield.cmd" if os.name == "nt" else "higgsfield"
if len(sys.argv) < 2:
    sys.exit(__doc__)
ROOT = os.path.dirname(os.path.abspath(sys.argv[1]))
UPLOADS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads.json")
# the CLI can be signed in to a different Higgsfield account between runs, and an upload id from one account is
# "Media input not found" on the other, so the cache key carries the account
ACCOUNT = (subprocess.run([HF, "account", "status"], capture_output=True, text=True).stdout.split() or ["?"])[0]
LOG = os.path.join(ROOT, "gen_log.jsonl")
lock = threading.Lock()


def run(args, timeout):
    p = subprocess.run([HF, *args], capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    return p.returncode, p.stdout, p.stderr


def upload_id(path):
    # keyed on path + content hash: a regenerated still at the same path must be uploaded again (with a path-only key the
    # old frames went to the video model and the clips had to be made again)
    path = os.path.abspath(path)
    path = path + "#" + hashlib.sha1(open(path, "rb").read()).hexdigest()[:12] + "#" + ACCOUNT  # upload ids are per account
    with lock:
        cache = json.load(open(UPLOADS)) if os.path.exists(UPLOADS) else {}
        if path in cache:
            return cache[path]
    for _ in range(8):
        code, out, err = run(["upload", "create", path.split("#")[0], "--json"], 600)
        if not code:
            break
        time.sleep(30)
    if code:
        raise RuntimeError(f"upload failed {path.split('#')[0]}: {err[-300:]}")
    d = json.loads(out)
    d = d[0] if isinstance(d, list) else d
    uid = d.get("id") or d.get("upload_id") or d.get("media_id")
    if not uid:
        raise RuntimeError(f"no upload id in {out[:300]}")
    with lock:
        cache = json.load(open(UPLOADS)) if os.path.exists(UPLOADS) else {}
        cache[path] = uid
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
    if job.get("end"):  # Kling 3.0 end frame (pins where the clip must land, e.g. the costume after a quick-change)
        args += ["--end-image", upload_id(os.path.join(ROOT, job["end"]))]
    if job.get("audio"):
        args += ["--audio-references", upload_id(os.path.join(ROOT, job["audio"]))]
    args += ["--wait", "--wait-timeout", "25m", "--wait-interval", "6s", "--json"]
    last = ""
    attempt = 0
    while attempt < int(os.environ.get("GEN_ATTEMPTS", "3")):  # set GEN_ATTEMPTS=1 where a resubmit after a timeout would be charged twice
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
