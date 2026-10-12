#!/usr/bin/env python3
"""Schedule one Unpopular Truths voice Reel through post-reel.yml and wait for the result.
usage: schedule_ut_reel.py <n> <publish_at e.g. 2026-10-13T07:00:00-05:00> <caption> <date>
The MP4 must already be on branch reel-files as ut-<date>-<n>.mp4. Uses the session proxy for GitHub auth."""
import json, subprocess, sys, time
n, when, caption = sys.argv[1], sys.argv[2], sys.argv[3]
date = sys.argv[4]
body = {"ref": "main", "inputs": {
    "page": "main",
    "video_url": f"https://raw.githubusercontent.com/adinhadza/unpop-truths/reel-files/ut-{date}-{n}.mp4",
    "caption": caption, "mode": "upload", "music": "none",
    "publish_at": when, "post_key": f"ut-{date}-{n}"}}
r = subprocess.run(["curl", "-s", "-w", "%{http_code}", "-X", "POST", "-H", "Content-Type: application/json",
    "https://api.github.com/repos/adinhadza/unpop-truths/actions/workflows/post-reel.yml/dispatches",
    "-d", json.dumps(body)], capture_output=True, text=True)
print("dispatch", r.stdout)
time.sleep(8)
def get(u):
    return json.loads(subprocess.run(["curl", "-s", u], capture_output=True, text=True).stdout)
run = None
for _ in range(60):
    runs = get("https://api.github.com/repos/adinhadza/unpop-truths/actions/workflows/post-reel.yml/runs?per_page=5")["workflow_runs"]
    mine = [x for x in runs if x["display_title"] == f"Post Reel ut-{date}-{n}"]
    if mine:
        run = mine[0]
        if run["status"] == "completed":
            break
    time.sleep(15)
print(run["id"], run["status"], run["conclusion"])
jobs = get(f"https://api.github.com/repos/adinhadza/unpop-truths/actions/runs/{run['id']}/jobs")["jobs"]
for j in jobs:
    for a in get(f"https://api.github.com/repos/adinhadza/unpop-truths/check-runs/{j['id']}/annotations"):
        if "Node.js" not in a["message"] and "ubuntu-latest" not in a["message"]:
            print(a["annotation_level"], a["message"][:300])
