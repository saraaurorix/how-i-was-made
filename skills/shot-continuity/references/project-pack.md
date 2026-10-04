# The project pack: store everything, mapped to the project

The director's ask: all of this should be stored, mapped against the project, so it can be used as content for the website.

Every video keeps **`project_pack.json`** in its folder, rewritten by a script after every round. The website build reads it to make the song page, the locations strip, the making-of and the easter-egg pages. Paths are relative to the video's folder.

| Key | What |
|---|---|
| `single`, `version`, `folder`, `written`, `spine` | the video in one line |
| `song` | the WAV, `lyrics.md`, `lines_timed.json`, `words.json`, `casting.json` (who sings each line as sung), `timing.json` |
| `plan` | the board (md + json), the design bible, `scenes.json` (staging lines), the pick document, the build log |
| `scenes[]` | id, title, staging line, the shot ids in it |
| `references.sets[]` | id, title, lighting `state`, file, the scenes that use it (the set pack) |
| `references.characters[]` | id, name, files, the fixed `identity_line`; a character with versions carries `generations[]` (id, file, note) |
| `references.looks[]` | id, file, the master-wardrobe source, where it is worn |
| `shots[]` | id, minute, t0/t1, section, scene, join, the lines with who sings them, place, look, cast, type, source (NEW / REUSE x / EDIT), picture, expression, action, text in frame, note, and the files: still, clip, lip_clip, segment; `state` = made or still standing in |
| `cuts[]` | every WIP and final with its date and note |
| `qa` | the continuity assessment, the cut-sheet PDF and pages, sequence sheets, stills sheets, evidence sheets, face sheets, the joins report, clip strips, lip checks |
| `site_ideas[]` | what in the pack could be content |

Rules: rewrite the pack after every round (it is generated, never hand-edited); keep old cuts in `cuts[]`; keep superseded character generations in `generations[]` with a note, because the making-of wants them; a still standing in for a clip is marked in `state`, so the site never shows a placeholder as finished.
