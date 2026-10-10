// Google Apps Script web app that saves a video (or text) from a link into Google Drive.
// Paste into https://script.new, change KEY, then Deploy > New deployment > Web app,
// Execute as: Me, Who has access: Anyone. Put the web app URL and the same KEY in GitHub secrets
// DRIVE_SCRIPT_URL and DRIVE_KEY.
const KEY = 'CHANGE-ME-to-a-long-random-phrase';
const ROOT_ID = '1sBCYH7oQr1qEsOUUrYosp8HsS6CliG6x'; // "Unpopular Truths Reels" folder

function doPost(e) {
  try {
    const p = JSON.parse(e.postData.contents);
    if (p.key !== KEY) return out({ ok: false, error: 'wrong key' });
    const root = DriveApp.getFolderById(p.rootId || ROOT_ID);
    const day = folder(root, p.folder);
    if (!p.name) return out({ ok: true, folderId: day.getId() });
    const existing = day.getFilesByName(p.name);
    if (existing.hasNext()) {
      const f = existing.next();
      return out({ ok: true, id: f.getId(), size: f.getSize(), skipped: 'already there' });
    }
    let file;
    if (p.url) {
      const res = UrlFetchApp.fetch(p.url, { muteHttpExceptions: true, followRedirects: true });
      if (res.getResponseCode() !== 200) return out({ ok: false, error: 'download failed: HTTP ' + res.getResponseCode() });
      file = day.createFile(res.getBlob().setName(p.name));
    } else {
      file = day.createFile(p.name, p.text || '', MimeType.PLAIN_TEXT);
    }
    return out({ ok: true, id: file.getId(), size: file.getSize(), folderId: day.getId() });
  } catch (err) {
    return out({ ok: false, error: String(err) });
  }
}

function folder(parent, name) {
  const it = parent.getFoldersByName(name);
  return it.hasNext() ? it.next() : parent.createFolder(name);
}

function out(o) {
  return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON);
}
