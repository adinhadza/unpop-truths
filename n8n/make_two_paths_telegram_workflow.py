import json, uuid, sys, importlib.util, os
spec = importlib.util.spec_from_file_location("base", os.path.join(os.path.dirname(__file__), "make_workflow.py"))
# make_workflow.py writes a file when run; load only its IDEAS/IVORY/GREY by exec of the top part
src = open(os.path.join(os.path.dirname(__file__), "make_workflow.py")).read()
top = src.split("pick_code = r")[0]
ns = {}; exec(top, ns)
IDEAS, IVORY, GREY = ns["IDEAS"], ns["IVORY"], ns["GREY"]

LIB = r"""
// ---------- shared helpers (same in both code nodes) ----------
const cfg = $('Config').first().json;
const st = $getWorkflowStaticData('global');
st.pending = st.pending || {};          // post_key -> idea + telegram message id
const IDEAS = __IDEAS__;
const IVORY = __IVORY__;
const GREY = __GREY__;
const TG = `https://api.telegram.org/bot${cfg.TELEGRAM_BOT_TOKEN}`;
const http = this.helpers.httpRequest.bind(this.helpers);
const esc = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
async function tg(method, body) {
  return http({method: 'POST', url: `${TG}/${method}`, body, json: true});
}
function nyDate(d) {
  return new Intl.DateTimeFormat('en-CA', {timeZone: 'America/New_York', year: 'numeric', month: '2-digit', day: '2-digit'}).format(d);
}
function nyOffset(dateStr, hh) {
  const probe = new Date(`${dateStr}T${hh}:00:00Z`);
  const p = new Intl.DateTimeFormat('en-US', {timeZone: 'America/New_York', timeZoneName: 'shortOffset'}).formatToParts(probe).find(x => x.type === 'timeZoneName').value;
  const h = Number(p.replace('GMT', '')) || -5;
  return (h < 0 ? '-' : '+') + String(Math.abs(h)).padStart(2, '0') + ':00';
}
function slotTime(dateStr, hh) {
  hh = String(hh).padStart(2, '0');
  const iso = `${dateStr}T${hh}:00:00${nyOffset(dateStr, hh)}`;
  return {iso, ms: Date.parse(iso)};
}
function serbiaTime(ms) {
  return new Intl.DateTimeFormat('en-GB', {timeZone: 'Europe/Belgrade', weekday: 'short', hour: '2-digit', minute: '2-digit'}).format(new Date(ms));
}
function buildPrompts(i) {
  const image_prompt = `Vertical 9:16 split screen divided by a thin vertical line down the middle, clean stylized 3D render, ${i.light}, ${i.scene}. LEFT half: ${IVORY}, ${i.left}. At the top of the left half the word ${i.L} in clean bold white letters inside a thin glowing white halo ring. RIGHT half: ${GREY}, ${i.right}. At the top of the right half the word ${i.R} in clean bold white letters. Both figures large and fully visible, static eye-level camera, no other text, no logos.`;
  const video_prompt = `Static locked-off camera, one continuous shot, no cuts, the split screen stays exactly as is. ${i.beats} ${i.nots} Nothing covers the figures' heads. The words ${i.L} and ${i.R} stay exactly as they are at the top, sharp and single, no extra text. Both figures keep their exact shape, clothing, color and material. Ambient sound only, no speech, no music.`;
  return {image_prompt, video_prompt};
}
// Sends the next 2 ideas as two Telegram messages and remembers them.
async function sendNextPrompts(chatId) {
  let next = Number(st.next ?? cfg.START_AT_IDEA ?? 0);
  if (next >= IDEAS.length) {
    await tg('sendMessage', {chat_id: chatId, text: 'Two Paths: the idea list is used up. Add more ideas to the IDEAS list in both code nodes (or reset START_AT_IDEA).'});
    return [];
  }
  const date = nyDate(new Date());
  const sent = [];
  for (let k = 0; k < 2 && next < IDEAS.length; k++, next++) {
    const i = IDEAS[next];
    const {image_prompt, video_prompt} = buildPrompts(i);
    const post_key = `tp-${date}-${k + 1}-${next}`;
    const hh = k === 0 ? cfg.POST_TIME_1 : cfg.POST_TIME_2;
    let slot = slotTime(date, hh), sdate = date;
    if (slot.ms < Date.now() + 2 * 3600 * 1000) { sdate = nyDate(new Date(Date.now() + 24 * 3600 * 1000)); slot = slotTime(sdate, hh); }
    const text =
      `<b>Reel ${k + 1}: ${esc(i.L)} vs ${esc(i.R)}</b>  (${esc(post_key)})\n` +
      `Posts ${hh}:00 New York (${esc(serbiaTime(slot.ms))} Serbia)\n\n` +
      `<b>1. Start image</b> (Flow: Image, Nano Banana, 9:16)\n<pre>${esc(image_prompt)}</pre>\n\n` +
      `<b>2. Video</b> (Flow: Video, Frames, 9:16, 8s, start = that image)\n<pre>${esc(video_prompt)}</pre>\n\n` +
      `Summary: ${esc(i.s1)} / ${esc(i.s2)}\n` +
      `👉 <b>Reply to this message with the finished video</b> (send it as a File if Telegram compresses it).`;
    const r = await tg('sendMessage', {chat_id: chatId, text, parse_mode: 'HTML'});
    st.pending[post_key] = {post_key, slot_hour: String(hh), date: sdate, msg_id: r.result.message_id,
      labels: `${i.L} vs ${i.R}`, summary1: i.s1, summary2: i.s2, caption: `${i.cap}\n\n${i.tags}`, sent_at: Date.now()};
    sent.push(post_key);
  }
  st.next = next;
  return sent;
}
// ---------- end of shared helpers ----------
"""

DAILY = LIB + r"""
// Daily: send today's two prompt messages.
const chatId = cfg.TELEGRAM_CHAT_ID || st.owner_chat;
if (!chatId) throw new Error('No Telegram chat linked yet: send any message to your bot first (the minute check links it), or fill TELEGRAM_CHAT_ID in Config.');
const sent = await sendNextPrompts(chatId);
return [{json: {sent, next_idea: st.next}}];
"""

POLL = LIB + r"""
// Every minute: read new Telegram messages; videos replying to a prompt message are built and scheduled.
const res = await http({method: 'GET', url: `${TG}/getUpdates`, qs: {offset: (st.offset || 0), timeout: 0, allowed_updates: JSON.stringify(['message'])}, json: true});
const updates = res.result || [];
const log = [];
if (updates.length) {   // confirm them right away so an overlapping run never processes the same video twice
  st.offset = updates[updates.length - 1].update_id + 1;
  await http({method: 'GET', url: `${TG}/getUpdates`, qs: {offset: st.offset, limit: 1, timeout: 0}, json: true});
}
for (const u of updates) {
  st.offset = u.update_id + 1;
  const m = u.message;
  if (!m) continue;
  const chatId = m.chat.id;
  // link the owner: the first chat that writes to the bot (or the one in Config)
  if (!cfg.TELEGRAM_CHAT_ID && !st.owner_chat) {
    st.owner_chat = chatId;
    await tg('sendMessage', {chat_id: chatId, text: 'Linked ✅ This chat will get the daily Two Paths prompts. Send /prompts to get the next 2 now.'});
    continue;
  }
  const owner = String(cfg.TELEGRAM_CHAT_ID || st.owner_chat);
  if (String(chatId) !== owner) continue;              // ignore strangers

  const text = (m.text || '').trim().toLowerCase();
  if (text === '/prompts' || text === 'prompts') { await sendNextPrompts(chatId); log.push('prompts sent'); continue; }
  if (text === '/status' || text === 'status') {
    const p = Object.values(st.pending);
    await tg('sendMessage', {chat_id: chatId, text: p.length ? 'Waiting for videos:\n' + p.map(x => `• ${x.labels} (${x.post_key})`).join('\n') : 'Nothing waiting. Send /prompts for the next 2.'});
    continue;
  }

  const file = m.video || m.document || m.animation;
  if (!file) continue;
  // which prompt does this video belong to? 1) the message it replies to, 2) otherwise the oldest waiting one
  let item = null;
  if (m.reply_to_message) item = Object.values(st.pending).find(x => x.msg_id === m.reply_to_message.message_id);
  if (!item) item = Object.values(st.pending).sort((a, b) => a.sent_at - b.sent_at)[0];
  if (!item) { await tg('sendMessage', {chat_id: chatId, reply_to_message_id: m.message_id, text: 'I have no prompt waiting for a video. Send /prompts first.'}); continue; }

  try {
    if (file.file_size && file.file_size > 20 * 1024 * 1024) throw new Error('video is over 20 MB (Telegram bot limit). Export 720p or trim it.');
    const f = await tg('getFile', {file_id: file.file_id});
    const buf = await http({method: 'GET', url: `https://api.telegram.org/file/bot${cfg.TELEGRAM_BOT_TOKEN}/${f.result.file_path}`, encoding: 'arraybuffer'});
    // store the raw clip on the reel-files branch
    const gh = {Authorization: `Bearer ${cfg.GITHUB_TOKEN}`, Accept: 'application/vnd.github+json', 'User-Agent': 'n8n-two-paths'};
    const path = `tp-raw/${item.post_key}.mp4`;
    let sha;
    try { sha = (await http({method: 'GET', url: `https://api.github.com/repos/${cfg.GITHUB_REPO}/contents/${path}?ref=reel-files`, headers: gh, json: true})).sha; } catch (e) {}
    await http({method: 'PUT', url: `https://api.github.com/repos/${cfg.GITHUB_REPO}/contents/${path}`, headers: gh, json: true,
      body: {message: `raw clip ${item.post_key}`, content: Buffer.from(buf).toString('base64'), branch: 'reel-files', ...(sha ? {sha} : {})}});
    // publish time: this slot today, or the same slot tomorrow if it is less than 30 min away
    let slot = slotTime(item.date, item.slot_hour);
    if (slot.ms < Date.now() + 30 * 60 * 1000) {
      let d = nyDate(new Date());
      slot = slotTime(d, item.slot_hour);
      if (slot.ms < Date.now() + 30 * 60 * 1000) { d = nyDate(new Date(Date.now() + 24 * 3600 * 1000)); slot = slotTime(d, item.slot_hour); }
    }
    await new Promise(r => setTimeout(r, 10000));   // let the raw link appear
    const dry = cfg.DRY_RUN === true || cfg.DRY_RUN === 'true';
    await http({method: 'POST', url: `https://api.github.com/repos/${cfg.GITHUB_REPO}/actions/workflows/two-paths-reel.yml/dispatches`, headers: gh, json: true,
      body: {ref: 'main', inputs: {raw_url: `https://raw.githubusercontent.com/${cfg.GITHUB_REPO}/reel-files/${path}`,
        summary1: item.summary1, summary2: item.summary2, caption: item.caption, publish_at: slot.iso,
        post_key: item.post_key, dry_run: String(dry)}}});
    delete st.pending[item.post_key];
    await tg('sendMessage', {chat_id: chatId, reply_to_message_id: m.message_id, parse_mode: 'HTML',
      text: `✅ <b>${esc(item.labels)}</b> received.\n${dry ? 'TEST MODE: built only, not posted.' : `Scheduled for ${esc(slot.iso.slice(11, 16))} New York (${esc(serbiaTime(slot.ms))} Serbia).`}\nThe outro is added on GitHub in ~2 min: https://github.com/${esc(cfg.GITHUB_REPO)}/actions/workflows/two-paths-reel.yml`});
    log.push(`${item.post_key} -> ${slot.iso}`);
  } catch (e) {
    await tg('sendMessage', {chat_id: chatId, reply_to_message_id: m.message_id, text: `❌ Couldn't schedule ${item.labels}: ${String(e.message || e).slice(0, 300)}\nSend the video again to retry.`});
    log.push(`error ${item.post_key}: ${e.message}`);
  }
}
return [{json: {updates: updates.length, log}}];
"""

def sub(s):
    return s.replace("__IDEAS__", json.dumps(IDEAS, indent=1)).replace("__IVORY__", json.dumps(IVORY)).replace("__GREY__", json.dumps(GREY))

def node(name, typ, ver, pos, params, **kw):
    d = {"parameters": params, "id": str(uuid.uuid4()), "name": name, "type": typ, "typeVersion": ver, "position": pos}
    d.update(kw); return d
def A(name, value, typ="string"):
    return {"id": str(uuid.uuid4()), "name": name, "value": value, "type": typ}

nodes = [
 node("Daily prompts 10:00", "n8n-nodes-base.scheduleTrigger", 1.2, [0, 160],
      {"rule": {"interval": [{"field": "cronExpression", "expression": "0 10 * * *"}]}}),
 node("Check Telegram every minute", "n8n-nodes-base.scheduleTrigger", 1.2, [0, 420],
      {"rule": {"interval": [{"field": "cronExpression", "expression": "* * * * *"}]}}),
 node("Config", "n8n-nodes-base.set", 3.4, [240, 300], {
   "mode": "manual", "includeOtherFields": False,
   "assignments": {"assignments": [
     A("TELEGRAM_BOT_TOKEN", "PASTE_BOT_TOKEN_FROM_BOTFATHER"),
     A("TELEGRAM_CHAT_ID", ""),
     A("GITHUB_TOKEN", "PASTE_YOUR_GITHUB_TOKEN"),
     A("GITHUB_REPO", "adinhadza/unpop-truths"),
     A("POST_TIME_1", "12"),
     A("POST_TIME_2", "19"),
     A("START_AT_IDEA", 0, "number"),
     A("DRY_RUN", True, "boolean"),
   ]}}),
 node("Daily or minute?", "n8n-nodes-base.if", 2.2, [460, 300], {
   "conditions": {"options": {"caseSensitive": True, "leftValue": "", "typeValidation": "loose", "version": 2},
     "conditions": [{"id": str(uuid.uuid4()), "leftValue": "={{ $('Daily prompts 10:00').isExecuted }}", "rightValue": True,
                     "operator": {"type": "boolean", "operation": "true", "singleValue": True}}],
     "combinator": "and"}, "options": {}}),
 node("Send today's prompts", "n8n-nodes-base.code", 2, [700, 160], {"mode": "runOnceForAllItems", "jsCode": sub(DAILY)}),
 node("Process new videos", "n8n-nodes-base.code", 2, [700, 420], {"mode": "runOnceForAllItems", "jsCode": sub(POLL)}),
 node("How to use", "n8n-nodes-base.stickyNote", 1, [180, -160], {
   "content": "## Two Paths Mindset via Telegram\n1. **Config**: paste the bot token (from @BotFather) and the GitHub token. Keep DRY_RUN = true for the first test.\n2. Switch the workflow **Active**, then send any message to your bot: it replies *Linked*.\n3. Send **/prompts** to get 2 reels now (or wait for 10:00). Make them in Flow, then **reply to each message with its video**.\n4. When the test reel looks right on GitHub, set DRY_RUN = false.\nCommands: /prompts, /status",
   "height": 260, "width": 560}),
]
connections = {
 "Daily prompts 10:00": {"main": [[{"node": "Config", "type": "main", "index": 0}]]},
 "Check Telegram every minute": {"main": [[{"node": "Config", "type": "main", "index": 0}]]},
 "Config": {"main": [[{"node": "Daily or minute?", "type": "main", "index": 0}]]},
 "Daily or minute?": {"main": [[{"node": "Send today's prompts", "type": "main", "index": 0}],
                               [{"node": "Process new videos", "type": "main", "index": 0}]]},
}
wf = {"name": "Two Paths Mindset - Telegram + Flow", "nodes": nodes, "connections": connections,
      "settings": {"executionOrder": "v1", "timezone": "Europe/Belgrade", "saveManualExecutions": True,
                   "saveDataSuccessExecution": "none", "saveDataErrorExecution": "all"},
      "pinData": {}, "active": False}
json.dump(wf, open(sys.argv[1], "w"), indent=2, ensure_ascii=False)
print("ok", len(IDEAS))
