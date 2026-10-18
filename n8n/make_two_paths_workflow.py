import json, uuid

IDEAS = [
 dict(L="STEADY", R="SPRINTER", light="bright indoor pool light", scene="an indoor swimming pool, one lane on each half, a glowing finish wall at the far end",
      left="standing at the edge of his lane in a swim cap, calm", right="crouched at the edge of his lane, flexing, ready to explode off the block",
      beats="The grey figure on the RIGHT dives in and sprints wildly, splashing hard, then runs out of breath halfway and clings to the lane rope, stuck. The ivory figure on the LEFT dives in and swims calm, even strokes the whole way and touches the glowing finish wall, which lights up warm gold.",
      nots="The grey figure never reaches the wall. Only the wall on the LEFT lights up.", s1="Fast starts fade.", s2="Steady finishes.",
      cap="He started fast. I finished.", tags="#consistency #mindset #discipline"),
 dict(L="INNOVATOR", R="STUBBORN", light="warm desert sunlight", scene="sand dunes on both halves, each figure holding the rope of a heavy wooden sled stacked with crates",
      left="standing next to his sled, looking at it thoughtfully, two wooden wheels lying beside it", right="leaning into the rope, pulling his sled hard",
      beats="The grey figure on the RIGHT pulls harder and harder; his sled digs deeper into the sand and stops completely. The ivory figure on the LEFT fits the two wooden wheels under his sled, then rolls it easily across the sand and out of frame toward a glowing oasis.",
      nots="The grey sled never moves forward. The grey figure himself never changes.", s1="Work harder?", s2="Work different.",
      cap="Same load. Different idea.", tags="#innovation #worksmart #mindset"),
 dict(L="DOER", R="OVERTHINKER", light="golden late-afternoon light", scene="a beach on both halves with big glowing waves rolling in",
      left="standing at the water's edge holding a simple surfboard", right="sitting on the sand surrounded by unused surfboards, reading a thick surfing manual",
      beats="The ivory figure on the LEFT paddles out on his simple board, stands up and rides a glowing wave across the LEFT half. The grey figure on the RIGHT keeps reading his manual, turning page after page, and never touches the water.",
      nots="The grey figure never stands up and never enters the water.", s1="Reading isn't riding.", s2="Start.",
      cap="He studied the wave. I caught it.", tags="#action #mindset #motivation"),
 dict(L="ADAPT", R="REPEAT", light="soft overcast light", scene="a tall heavy wooden gate in a stone wall on each half, bright garden light behind each gate",
      left="standing in front of his gate, looking at its handle", right="ramming his shoulder into his gate",
      beats="The grey figure on the RIGHT rams his shoulder into the gate again and again; it never moves and he staggers back each time. The ivory figure on the LEFT notices the gate is a sliding door, slides it sideways with one hand and walks through into warm garden light.",
      nots="The gate on the RIGHT never opens. The grey figure himself never changes.", s1="Same move, same wall.", s2="Change the move.",
      cap="He pushed harder. I looked closer.", tags="#adapt #growthmindset #mindset"),
 dict(L="INVESTOR", R="SPENDER", light="bright clean studio light", scene="a calm light-grey studio with soft clouds high above both halves",
      left="kneeling beside a small stack of gold bricks", right="standing surrounded by colorful shopping bags and boxes",
      beats="The ivory figure on the LEFT stacks gold bricks one by one into a staircase that rises into the clouds, then climbs up toward a glowing platform. On the RIGHT the pile of shopping bags around the grey figure grows, wobbles and topples over him, and he stays on the ground.",
      nots="The grey figure never rises. Only the LEFT staircase grows.", s1="Stack, don't spend.", s2="Rise.",
      cap="He bought things. I built steps.", tags="#money #investing #mindset"),
 dict(L="COURAGE", R="FEAR", light="dramatic canyon sunset light", scene="the edge of a deep canyon on both halves, a narrow wooden rope bridge leading across to a glowing platform on the far side",
      left="standing at the start of the rope bridge, one hand on the rope", right="crouched at the canyon edge clutching the railing, maps in his hands",
      beats="The ivory figure on the LEFT walks across the bridge plank by plank and reaches the glowing platform, which brightens. The grey figure on the RIGHT stays crouched at the edge; the wind blows his maps out of his hands and away into the canyon.",
      nots="The grey figure never steps onto the bridge.", s1="Fear plans.", s2="Courage crosses.",
      cap="He planned the crossing. I crossed.", tags="#courage #mindset #selfgrowth"),
 dict(L="FOCUSED", R="DISTRACTED", light="crisp morning light", scene="an outdoor archery range on both halves, a round target at the back of each half",
      left="standing with a bow, drawing an arrow calmly", right="holding a bow while glancing at a phone in his other hand",
      beats="Colorful notification bubbles keep popping up around the grey figure on the RIGHT; he shoots while looking at his phone and his arrows fly wide, missing the target. The ivory figure on the LEFT breathes, aims and hits the center of his target, which flashes gold.",
      nots="No notification bubbles appear on the LEFT. The grey figure never hits the target.", s1="Notifications or goals.", s2="Pick one.",
      cap="He checked his phone. I checked my aim.", tags="#focus #discipline #productivity"),
 dict(L="LEARNING", R="SCROLLING", light="warm evening lamp light", scene="a cozy room on both halves at night",
      left="sitting at a desk with a stack of books and a glowing lamp", right="slouched on a sofa holding a phone with a blue glowing screen",
      beats="The ivory figure on the LEFT reads book after book; with each closed book a step of light appears and the room on the LEFT grows warmer and brighter, ending with a glowing doorway opening behind him. On the RIGHT the grey figure keeps scrolling; the room around him slowly gets darker until only the phone glow lights his blank face.",
      nots="No doorway appears on the RIGHT. The grey figure never puts down the phone.", s1="One scroll at a time,", s2="or one page at a time.",
      cap="Same hours. Different future.", tags="#selfimprovement #reading #mindset"),
 dict(L="RESPONSIBLE", R="EXCUSES", light="cloudy lake light", scene="a calm lake on both halves, each figure sitting in a small wooden rowboat that has a small leak with water bubbling in",
      left="looking down at the leak, a bucket and a patch in his hands", right="pointing angrily at the leak and then out at the lake as if blaming it",
      beats="The ivory figure on the LEFT bails the water out with his bucket, presses the patch over the leak and rows calmly toward a sunny shore. The grey figure on the RIGHT keeps pointing and complaining while water rises in his boat until it sits low in the water, stuck.",
      nots="The grey figure never picks up a bucket. Only the LEFT boat moves.", s1="Blame keeps you sinking.", s2="Fix it.",
      cap="He blamed the water. I fixed the hole.", tags="#responsibility #mindset #growth"),
 dict(L="PREPARED", R="CARELESS", light="calm sunny light turning stormy", scene="a small hilltop on both halves under a clear sky, dark storm clouds approaching in the distance",
      left="hammering wooden boards onto a small shelter frame", right="lying in a hammock with sunglasses, relaxed",
      beats="The ivory figure on the LEFT finishes the roof of his small shelter and steps inside just as the storm arrives. Heavy rain pours on both halves; the grey figure on the RIGHT jumps out of his soaked hammock with nowhere to go, standing in the rain.",
      nots="The grey figure never builds anything. The ivory figure stays dry under his roof.", s1="Build the roof", s2="before the rain.",
      cap="He waited for the storm. I got ready for it.", tags="#prepared #discipline #mindset"),
 dict(L="BUILDER", R="GAMBLER", light="warm golden studio light", scene="a clean beige studio on both halves",
      left="laying bricks for a low wall, a stack of bricks beside him", right="standing at a flashy glowing slot machine with a handful of gold coins",
      beats="The ivory figure on the LEFT lays brick after brick; the wall rises steadily into a small solid house with a warm lit window. The grey figure on the RIGHT feeds coins into the slot machine and pulls the lever again and again; his coin pile shrinks to nothing and the machine's lights go dark.",
      nots="The grey figure never wins anything. Only the LEFT house grows.", s1="Luck is a lever.", s2="Work is a wall.",
      cap="He pulled a lever. I laid a brick.", tags="#discipline #money #mindset"),
 dict(L="EARLY", R="LATE", light="soft sunrise light", scene="a small farm field on both halves at sunrise, ripe golden wheat",
      left="already standing in the field with a sickle and a basket", right="asleep in a hammock under a tree at the edge of the field",
      beats="The ivory figure on the LEFT harvests the wheat steadily and fills his basket to the top as the sun rises. As the light turns grey, rain begins on the RIGHT; the grey figure wakes up, sits up in the hammock and looks at his field, flattened by the rain.",
      nots="The grey figure never harvests anything. The LEFT field stays sunny.", s1="The day rewards", s2="who shows up first.",
      cap="He slept in. I showed up.", tags="#discipline #morningroutine #mindset"),
]

IVORY = "a faceless male mannequin with warm ivory satin ceramic skin, featureless egg-shaped head, wearing a fitted cream long-sleeve sweater, sand-colored trousers, gold belt buckle and tan shoes"
GREY = "a faceless male mannequin with flat matte slate-grey skin, featureless head, wearing a loose grey sweatshirt, charcoal trousers and dark shoes"

pick_code = r"""// Picks the next 2 ideas, builds the prompts and the US post times for TOMORROW (New York).
const cfg = $('Config').first().json;
const IDEAS = __IDEAS__;
const IVORY = __IVORY__;
const GREY = __GREY__;
const st = $getWorkflowStaticData('global');
let next = Number(st.next ?? cfg.START_AT_IDEA ?? 0);
if (next + 2 > IDEAS.length) throw new Error('Two Paths: idea list is used up. Add more ideas to the "Pick 2 ideas" node (IDEAS list) or set START_AT_IDEA.');

// tomorrow's date in New York, and that day's UTC offset (handles the clock change)
const now = new Date();
const nyDate = d => new Intl.DateTimeFormat('en-CA', {timeZone: 'America/New_York', year: 'numeric', month: '2-digit', day: '2-digit'}).format(d);
const tomorrow = nyDate(new Date(now.getTime() + 24 * 3600 * 1000));
function nyOffset(dateStr, hh) {
  const probe = new Date(`${dateStr}T${hh}:00:00Z`);
  const part = new Intl.DateTimeFormat('en-US', {timeZone: 'America/New_York', timeZoneName: 'shortOffset'}).formatToParts(probe).find(p => p.type === 'timeZoneName').value; // e.g. GMT-4
  const h = Number(part.replace('GMT', '')) || -5;
  return (h < 0 ? '-' : '+') + String(Math.abs(h)).padStart(2, '0') + ':00';
}
const times = [cfg.POST_TIME_1 || '12', cfg.POST_TIME_2 || '19'];
const out = [];
for (let k = 0; k < 2; k++) {
  const i = IDEAS[next + k];
  const hh = String(times[k]).padStart(2, '0');
  const image_prompt = `Vertical 9:16 split screen divided by a thin vertical line down the middle, clean stylized 3D render, ${i.light}, ${i.scene}. LEFT half: ${IVORY}, ${i.left}. At the top of the left half the word ${i.L} in clean bold white letters inside a thin glowing white halo ring. RIGHT half: ${GREY}, ${i.right}. At the top of the right half the word ${i.R} in clean bold white letters. Both figures large and fully visible, static eye-level camera, no other text, no logos.`;
  const motion_prompt = `Static locked-off camera, one continuous shot, no cuts, the split screen stays exactly as is. ${i.beats} ${i.nots} Nothing covers the figures' heads. The words ${i.L} and ${i.R} stay exactly as they are at the top, sharp and single, no extra text. Both figures keep their exact shape, clothing, color and material. Ambient sound only, no speech, no music.`;
  out.push({json: {
    n: k + 1, idea_index: next + k, labels: `${i.L} vs ${i.R}`, date: tomorrow,
    post_key: `tp-${tomorrow}-${k + 1}`,
    publish_at: `${tomorrow}T${hh}:00:00${nyOffset(tomorrow, hh)}`,
    image_prompt, motion_prompt, summary1: i.s1, summary2: i.s2,
    caption: `${i.cap}\n\n${i.tags}`,
  }});
}
st.next = next + 2;
return out;
"""
pick_code = (pick_code.replace("__IDEAS__", json.dumps(IDEAS, indent=1))
             .replace("__IVORY__", json.dumps(IVORY)).replace("__GREY__", json.dumps(GREY)))

image_code = r"""// Start image with Google's image model (Nano Banana), 9:16.
const cfg = $('Config').first().json;
const j = $json;
const res = await this.helpers.httpRequest({
  method: 'POST',
  url: `https://generativelanguage.googleapis.com/v1beta/models/${cfg.IMAGE_MODEL}:generateContent`,
  headers: {'x-goog-api-key': cfg.GEMINI_API_KEY, 'Content-Type': 'application/json'},
  body: {contents: [{parts: [{text: j.image_prompt}]}],
         generationConfig: {responseModalities: ['IMAGE'], imageConfig: {aspectRatio: '9:16'}}},
  json: true,
});
const parts = res?.candidates?.[0]?.content?.parts || [];
const img = parts.find(p => p.inlineData || p.inline_data);
if (!img) throw new Error('No image returned: ' + JSON.stringify(res).slice(0, 400));
const d = img.inlineData || img.inline_data;
return {json: {...j, image_b64: d.data, image_mime: d.mimeType || d.mime_type || 'image/png'}};
"""

veo_start_code = r"""// Start the 8 s Veo video from the start image.
const cfg = $('Config').first().json;
const j = $json;
const res = await this.helpers.httpRequest({
  method: 'POST',
  url: `https://generativelanguage.googleapis.com/v1beta/models/${cfg.VEO_MODEL}:predictLongRunning`,
  headers: {'x-goog-api-key': cfg.GEMINI_API_KEY, 'Content-Type': 'application/json'},
  body: {instances: [{prompt: j.motion_prompt, image: {inlineData: {mimeType: j.image_mime, data: j.image_b64}}}],
         parameters: {aspectRatio: '9:16', durationSeconds: 8, resolution: '720p', personGeneration: 'allow_adult'}},
  json: true,
});
if (!res.name) throw new Error('Veo did not start: ' + JSON.stringify(res).slice(0, 400));
const {image_b64, ...rest} = j;   // drop the big image, keep the rest
return {json: {...rest, operation: res.name, checks: 0}};
"""

veo_check_code = r"""// Check the Veo job once.
const cfg = $('Config').first().json;
const j = $json;
const res = await this.helpers.httpRequest({
  method: 'GET',
  url: `https://generativelanguage.googleapis.com/v1beta/${j.operation}`,
  headers: {'x-goog-api-key': cfg.GEMINI_API_KEY},
  json: true,
});
if (res.error) throw new Error('Veo error: ' + JSON.stringify(res.error).slice(0, 400));
const checks = (j.checks || 0) + 1;
if (checks > 40) throw new Error('Veo took more than 20 minutes for ' + j.post_key);
let video_uri = '';
if (res.done) {
  video_uri = res?.response?.generateVideoResponse?.generatedSamples?.[0]?.video?.uri || '';
  if (!video_uri) throw new Error('Veo finished without a video (maybe blocked by safety filters): ' + JSON.stringify(res).slice(0, 500));
}
return {json: {...j, checks, done: !!res.done, video_uri}};
"""

upload_code = r"""// Download the clip and store it on the reel-files branch so GitHub can fetch it.
const cfg = $('Config').first().json;
const j = $json;
const buf = await this.helpers.httpRequest({
  method: 'GET', url: j.video_uri, headers: {'x-goog-api-key': cfg.GEMINI_API_KEY},
  encoding: 'arraybuffer', returnFullResponse: false,
});
const b64 = Buffer.from(buf).toString('base64');
const path = `tp-raw/${j.post_key}.mp4`;
const gh = {Authorization: `Bearer ${cfg.GITHUB_TOKEN}`, Accept: 'application/vnd.github+json', 'User-Agent': 'n8n-two-paths'};
let sha;
try {
  const old = await this.helpers.httpRequest({method: 'GET', url: `https://api.github.com/repos/${cfg.GITHUB_REPO}/contents/${path}?ref=reel-files`, headers: gh, json: true});
  sha = old.sha;
} catch (e) { /* new file */ }
await this.helpers.httpRequest({
  method: 'PUT', url: `https://api.github.com/repos/${cfg.GITHUB_REPO}/contents/${path}`, headers: gh, json: true,
  body: {message: `raw clip ${j.post_key}`, content: b64, branch: 'reel-files', ...(sha ? {sha} : {})},
});
return {json: {...j, raw_url: `https://raw.githubusercontent.com/${cfg.GITHUB_REPO}/reel-files/${path}`, raw_bytes: buf.byteLength}};
"""

dispatch_code = r"""// Ask GitHub to add the outro and schedule the Reel on Facebook.
const cfg = $('Config').first().json;
const j = $json;
await new Promise(r => setTimeout(r, 15000)); // let the raw link become available
await this.helpers.httpRequest({
  method: 'POST',
  url: `https://api.github.com/repos/${cfg.GITHUB_REPO}/actions/workflows/two-paths-reel.yml/dispatches`,
  headers: {Authorization: `Bearer ${cfg.GITHUB_TOKEN}`, Accept: 'application/vnd.github+json', 'User-Agent': 'n8n-two-paths'},
  body: {ref: 'main', inputs: {raw_url: j.raw_url, summary1: j.summary1, summary2: j.summary2,
         caption: j.caption, publish_at: j.publish_at, post_key: j.post_key, dry_run: String(cfg.DRY_RUN === true || cfg.DRY_RUN === 'true')}},
  json: true,
});
return {json: {post_key: j.post_key, labels: j.labels, publish_at: j.publish_at, caption: j.caption,
  check_here: `https://github.com/${cfg.GITHUB_REPO}/actions/workflows/two-paths-reel.yml`}};
"""

def node(name, typ, ver, pos, params, **kw):
    d = {"parameters": params, "id": str(uuid.uuid4()), "name": name, "type": typ, "typeVersion": ver, "position": pos}
    d.update(kw); return d

def code(name, js, pos):
    return node(name, "n8n-nodes-base.code", 2, pos, {"mode": "runOnceForEachItem", "jsCode": js}) if "first().json;\nconst IDEAS" not in js else \
           node(name, "n8n-nodes-base.code", 2, pos, {"mode": "runOnceForAllItems", "jsCode": js})

nodes = [
 node("Every day 18:49", "n8n-nodes-base.scheduleTrigger", 1.2, [0, 300],
      {"rule": {"interval": [{"field": "cronExpression", "expression": "49 18 * * *"}]}}),
 node("Config", "n8n-nodes-base.set", 3.4, [220, 300], {
   "mode": "manual", "includeOtherFields": False,
   "assignments": {"assignments": [
     {"id": str(uuid.uuid4()), "name": "GEMINI_API_KEY", "value": "PASTE_YOUR_GEMINI_API_KEY", "type": "string"},
     {"id": str(uuid.uuid4()), "name": "GITHUB_TOKEN", "value": "PASTE_YOUR_GITHUB_TOKEN", "type": "string"},
     {"id": str(uuid.uuid4()), "name": "GITHUB_REPO", "value": "adinhadza/unpop-truths", "type": "string"},
     {"id": str(uuid.uuid4()), "name": "IMAGE_MODEL", "value": "gemini-2.5-flash-image", "type": "string"},
     {"id": str(uuid.uuid4()), "name": "VEO_MODEL", "value": "veo-3.1-fast-generate-preview", "type": "string"},
     {"id": str(uuid.uuid4()), "name": "POST_TIME_1", "value": "12", "type": "string"},
     {"id": str(uuid.uuid4()), "name": "POST_TIME_2", "value": "19", "type": "string"},
     {"id": str(uuid.uuid4()), "name": "START_AT_IDEA", "value": 0, "type": "number"},
     {"id": str(uuid.uuid4()), "name": "DRY_RUN", "value": True, "type": "boolean"},
   ]}}),
 code("Pick 2 ideas", pick_code, [440, 300]),
 code("Make start image", image_code, [660, 300]),
 code("Start video (Veo)", veo_start_code, [880, 300]),
 node("Wait 30s", "n8n-nodes-base.wait", 1.1, [1100, 300], {"amount": 30}, webhookId=str(uuid.uuid4())),
 code("Check video", veo_check_code, [1320, 300]),
 node("Video ready?", "n8n-nodes-base.if", 2.2, [1540, 300], {
   "conditions": {"options": {"caseSensitive": True, "leftValue": "", "typeValidation": "loose", "version": 2},
                  "conditions": [{"id": str(uuid.uuid4()), "leftValue": "={{ $json.done }}", "rightValue": True,
                                  "operator": {"type": "boolean", "operation": "true", "singleValue": True}}],
                  "combinator": "and"}, "options": {}}),
 code("Save clip to GitHub", upload_code, [1760, 200]),
 code("Build + schedule on Facebook", dispatch_code, [1980, 200]),
 node("How to use", "n8n-nodes-base.stickyNote", 1, [180, 20], {
   "content": "## Two Paths Mindset - daily reels\n1. Open **Config**: paste your Gemini API key and GitHub token.\n2. Leave **DRY_RUN = true** for the first test (builds the reel but does not post). Run with **Test workflow**, then check GitHub > Actions > 'Two Paths Mindset - build and post one Reel'.\n3. Set **DRY_RUN = false** and switch the workflow **Active**.\nEach run makes 2 reels for tomorrow (New York 12:00 and 19:00).",
   "height": 220, "width": 520}),
]
N = {n["name"]: n for n in nodes}
def link(a, b, out=0): return {a: {"main": [[{"node": b, "type": "main", "index": 0}]]}} if out == 0 else None
connections = {
 "Every day 18:49": {"main": [[{"node": "Config", "type": "main", "index": 0}]]},
 "Config": {"main": [[{"node": "Pick 2 ideas", "type": "main", "index": 0}]]},
 "Pick 2 ideas": {"main": [[{"node": "Make start image", "type": "main", "index": 0}]]},
 "Make start image": {"main": [[{"node": "Start video (Veo)", "type": "main", "index": 0}]]},
 "Start video (Veo)": {"main": [[{"node": "Wait 30s", "type": "main", "index": 0}]]},
 "Wait 30s": {"main": [[{"node": "Check video", "type": "main", "index": 0}]]},
 "Check video": {"main": [[{"node": "Video ready?", "type": "main", "index": 0}]]},
 "Video ready?": {"main": [[{"node": "Save clip to GitHub", "type": "main", "index": 0}],
                           [{"node": "Wait 30s", "type": "main", "index": 0}]]},
 "Save clip to GitHub": {"main": [[{"node": "Build + schedule on Facebook", "type": "main", "index": 0}]]},
}
wf = {"name": "Two Paths Mindset - daily reels", "nodes": nodes, "connections": connections,
      "settings": {"executionOrder": "v1", "timezone": "Europe/Belgrade", "saveManualExecutions": True},
      "pinData": {}, "active": False}
import sys
json.dump(wf, open(sys.argv[1], "w"), indent=2)
print(len(IDEAS), "ideas")
