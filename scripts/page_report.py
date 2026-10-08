#!/usr/bin/env python3
"""Report what a Facebook Page has posted and how each post is doing.

Env: PAGE_ID, PAGE_TOKEN, KIND (reels | posts), LABEL, GRAPH_VERSION.
Prints the report as ::notice:: annotations (compact JSON, split into chunks)
so it can be read without opening the run log. Missing permissions are
reported per metric instead of failing the run.
"""
import json, os, sys, urllib.parse, urllib.request, urllib.error

VER = os.environ.get("GRAPH_VERSION", "v23.0")
GRAPH = f"https://graph.facebook.com/{VER}"
PAGE = os.environ.get("PAGE_ID", "")
TOKEN = os.environ.get("PAGE_TOKEN", "")
KIND = os.environ.get("KIND", "posts")
LABEL = os.environ.get("LABEL", "page")


def get(path, **params):
    params["access_token"] = TOKEN
    url = f"{GRAPH}/{path}?{urllib.parse.urlencode(params)}"
    try:
        with urllib.request.urlopen(url, timeout=40) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        try:
            err = json.load(e).get("error", {})
        except Exception:
            err = {}
        return {"_error": f"{err.get('code')}: {err.get('message', str(e))}"[:160]}
    except Exception as e:  # network problems
        return {"_error": str(e)[:160]}


def insights(obj_id, metrics, endpoint="insights"):
    out = {}
    for m in metrics:
        r = get(f"{obj_id}/{endpoint}", metric=m)
        if "_error" in r:
            out[m] = "ERR " + r["_error"]
            continue
        data = r.get("data", [])
        if not data:
            out[m] = None
            continue
        vals = data[0].get("values", [])
        out[m] = vals[-1].get("value") if vals else None
    return out


def summary(obj, key):
    return (obj.get(key) or {}).get("summary", {}).get("total_count")


report = {"page": LABEL}
if not PAGE or not TOKEN:
    print(f"::error::{LABEL}: page id or token secret is missing")
    sys.exit(0)

info = get(PAGE, fields="name,fan_count,followers_count,link")
report["info"] = info

items = []
if KIND == "reels":
    lst = get(f"{PAGE}/video_reels",
              fields="id,description,created_time,updated_time,length,permalink_url,published,status",
              limit=50)
    if "_error" in lst:
        report["list_error"] = lst["_error"]
    for v in lst.get("data", []):
        vid = v["id"]
        extra = get(vid, fields="likes.summary(true).limit(0),comments.summary(true).limit(0),scheduled_publish_time,views")
        status = v.get("status") or {}
        item = {
            "id": vid,
            "created": v.get("created_time"),
            "text": (v.get("description") or "")[:70],
            "published": v.get("published"),
            "state": status.get("video_status"),
            "scheduled_for": extra.get("scheduled_publish_time"),
            "likes": summary(extra, "likes"),
            "comments": summary(extra, "comments"),
            "views_field": extra.get("views"),
            "link": v.get("permalink_url"),
        }
        if "_error" in extra:
            item["detail_error"] = extra["_error"]
        if v.get("published"):
            item["insights"] = insights(vid, [
                "blue_reels_play_count",
                "fb_reels_total_plays",
                "post_impressions_unique",
                "post_video_avg_time_watched",
                "post_video_social_actions",
            ], endpoint="video_insights")
        items.append(item)
else:
    lst = get(f"{PAGE}/posts",
              fields="id,created_time,message,permalink_url,is_published,"
                     "reactions.summary(true).limit(0),comments.summary(true).limit(0),shares",
              limit=50)
    if "_error" in lst:
        report["list_error"] = lst["_error"]
    for p in lst.get("data", []):
        item = {
            "id": p["id"],
            "created": p.get("created_time"),
            "text": (p.get("message") or "")[:70],
            "reactions": summary(p, "reactions"),
            "comments": summary(p, "comments"),
            "shares": (p.get("shares") or {}).get("count", 0),
            "insights": insights(p["id"], ["post_impressions", "post_impressions_unique", "post_clicks"]),
        }
        items.append(item)
    sch = get(f"{PAGE}/scheduled_posts", fields="id,scheduled_publish_time,message", limit=50)
    report["scheduled"] = sch.get("data", sch.get("_error"))

report["items"] = items
report["page_insights"] = insights(PAGE, ["page_impressions_unique", "page_post_engagements", "page_video_views"])

text = json.dumps(report, separators=(",", ":"), ensure_ascii=True)
text = text.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
size = 3500
chunks = [text[i:i + size] for i in range(0, len(text), size)]
if len(chunks) > 9:
    print(f"::warning::{LABEL}: report has {len(chunks)} parts, only the first 9 are shown")
for n, c in enumerate(chunks[:9], 1):
    print(f"::notice title={LABEL} {n}/{min(len(chunks), 9)}::{c}")
