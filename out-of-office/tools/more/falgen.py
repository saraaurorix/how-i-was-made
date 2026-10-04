"""Run fal.ai jobs in parallel from a JSON job list, download results, resume-safe.

Job: {"id", "endpoint", "args": {...}, "out": path}
Any string arg starting with "@" is a local file (relative to the jobs file) that gets uploaded; lists are handled too.
Usage: python falgen.py jobs.json [workers] [ID,ID]
"""
import json
import os
import sys
import threading
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

import fal_env  # noqa: F401  (loads FAL_KEY)
import fal_client

ROOT = os.path.dirname(os.path.abspath(sys.argv[1]))
UPLOADS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fal_uploads.json")
LOG = os.path.join(ROOT, "fal_log.jsonl")
lock = threading.Lock()


def upload(path):
    path = os.path.abspath(os.path.join(ROOT, path))
    key = f"{path}|{os.path.getmtime(path)}"
    with lock:
        cache = json.load(open(UPLOADS)) if os.path.exists(UPLOADS) else {}
        if key in cache:
            return cache[key]
    for attempt in range(6):
        try:
            url = fal_client.upload_file(path)
            break
        except Exception as e:
            if "403" in str(e) and os.path.getsize(path) < 12_000_000:
                return fal_client.encode_file(path)  # storage upload refused: send inline as a data URI (not cached)
            if attempt == 5:
                raise
            time.sleep(10)
    with lock:
        cache = json.load(open(UPLOADS)) if os.path.exists(UPLOADS) else {}
        cache[key] = url
        json.dump(cache, open(UPLOADS, "w"), indent=1)
    return url


def resolve(v):
    if isinstance(v, str) and v.startswith("@"):
        return upload(v[1:])
    if isinstance(v, list):
        return [resolve(x) for x in v]
    return v


def media_url(res):
    for k in ("video", "image"):
        if isinstance(res.get(k), dict) and res[k].get("url"):
            return res[k]["url"]
    for k in ("images", "videos"):
        if res.get(k):
            return res[k][0]["url"]
    raise RuntimeError(f"no media in result: {json.dumps(res)[:300]}")


def do(job):
    out = os.path.join(ROOT, job["out"])
    if os.path.exists(out) and os.path.getsize(out) > 1000:
        return job["id"], "skip"
    os.makedirs(os.path.dirname(out), exist_ok=True)
    args = {k: resolve(v) for k, v in job["args"].items()}
    last = ""
    for attempt in range(3):
        t0 = time.time()
        try:
            res = fal_client.subscribe(job["endpoint"], arguments=args, client_timeout=1800)
            url = media_url(res)
            urllib.request.urlretrieve(url, out + ".part")
            os.replace(out + ".part", out)
            with lock:
                open(LOG, "a").write(json.dumps({"id": job["id"], "endpoint": job["endpoint"], "url": url,
                                                 "secs": round(time.time() - t0)}) + "\n")
            return job["id"], f"ok {round(time.time() - t0)}s"
        except Exception as e:
            last = str(e)[:400]
            if "rate" in last.lower() or "429" in last:
                time.sleep(30)
            elif any(w in last.lower() for w in ("content", "safety", "nsfw", "policy", "422", "validation")):
                break
    with lock:
        open(LOG, "a").write(json.dumps({"id": job["id"], "endpoint": job["endpoint"], "error": last}) + "\n")
    return job["id"], "FAIL " + last


def safe(job):
    try:
        return do(job)
    except Exception as e:
        return job["id"], "FAIL " + str(e)[:400]


if __name__ == "__main__":
    jobs = json.load(open(sys.argv[1]))
    workers = int(sys.argv[2]) if len(sys.argv) > 2 else 6
    if len(sys.argv) > 3:
        want = set(sys.argv[3].split(","))
        jobs = [j for j in jobs if j["id"] in want]
    with ThreadPoolExecutor(workers) as ex:
        for jid, status in ex.map(safe, jobs):
            print(f"{jid}: {status}", flush=True)
