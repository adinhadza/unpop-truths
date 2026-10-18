#!/usr/bin/env python3
"""Schedule one Two Paths Mindset Reel through post-reel.yml (page twopaths) and wait for the result.
usage: schedule_tp_reel.py <file on branch reel-files> <publish_at e.g. 2026-10-18T11:00:00-04:00> <caption> <post_key>
Uses the session proxy for GitHub auth."""
import json, subprocess, sys, time
fname, when, caption, key = sys.argv[1:5]
API = "https://api.github.com/repos/adinhadza/unpop-truths"
body = {"ref": "main", "inputs": {
    "page": "twopaths",
    "video_url": f"https://raw.githubusercontent.com/adinhadza/unpop-truths/reel-files/{fname}",
    "caption": caption, "mode": "upload", "music": "none",
    "publish_at": when, "post_key": key}}
r = subprocess.run(["curl", "-s", "-w", "%{http_code}", "-X", "POST", "-H", "Content-Type: application/json",
                    f"{API}/actions/workflows/post-reel.yml/dispatches", "-d", json.dumps(body)],
                   capture_output=True, text=True)
print("dispatch", r.stdout)
time.sleep(8)
def get(u):
    return json.loads(subprocess.run(["curl", "-s", u], capture_output=True, text=True).stdout)
run = None
for _ in range(60):
    runs = get(f"{API}/actions/workflows/post-reel.yml/runs?per_page=10")["workflow_runs"]
    mine = [x for x in runs if x["display_title"] == f"Post Reel {key}"]
    if mine:
        run = mine[0]
        if run["status"] == "completed":
            break
    time.sleep(15)
print(run["id"], run["status"], run["conclusion"])
for j in get(f"{API}/actions/runs/{run['id']}/jobs")["jobs"]:
    for a in get(f"{API}/check-runs/{j['id']}/annotations"):
        if "Node.js" not in a["message"] and "ubuntu-latest" not in a["message"]:
            print(a["annotation_level"], a["message"][:300])
