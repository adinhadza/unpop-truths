# Delivering the day's videos to Google Drive

Drive layout: My Drive / "Unpopular Truths Reels" (folder id 1sBCYH7oQr1qEsOUUrYosp8HsS6CliG6x) /
one folder per day named `YYYY-MM-DD Ddd` (for example `2026-10-11 Sun`).

For each finished video (after the Canva export in reels-agent.md):
1. File name: `<HH-MM Serbia time> <first 5-6 words of line 1>.mp4` (no slashes, quotes or colons),
   for example `13-00 Some days you dont need advice.mp4`, so the folder sorts in posting order.
2. Save it through GitHub (the Canva link cannot be downloaded from where you run):
   ```
   gh api -X POST repos/adinhadza/unpop-truths/actions/workflows/drive-upload.yml/dispatches -f ref=main \
     -f 'inputs[url]=<canva export link>' -f 'inputs[folder]=<YYYY-MM-DD Ddd>' -f 'inputs[name]=<file name>'
   ```
   Wait about 40 seconds and check the run named "Drive <folder> / <name>" finished with success
   (annotation "Saved to Drive"). Runs for different files can go in parallel. On failure read the
   annotations, export again if the link expired, retry once, then note it.
3. After all videos, create the captions file in the same day folder with the Google Drive tool
   (create_file, parentId = the day folder id found with search_files, textContent, contentMimeType
   text/plain, title `00 Captions <date>`), so it converts to a Google Doc Adin can copy from on his phone.
   One block per video, in posting order:
   ```
   13:00 Serbia (6:00 AM Chicago) - <file name>
   <caption>

   <hashtags>
   Music idea: <mood> - <one short suggestion, e.g. soft piano>
   ```
