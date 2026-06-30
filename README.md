# 🎧 Convert videos to MP3

A tiny, no-fuss tool that turns **every video in a folder into an MP3** and
organises the results neatly. Great for feeding audio to an AI (Gemini,
ChatGPT, Whisper, …) for **transcripts, captions, or summaries** — audio is far
smaller than video and much cheaper/faster to upload.

Works on **Windows, macOS, and Linux**. If you don't have Python or ffmpeg, the
launcher for your system installs them for you.

---

## ⚡ Quick start (no command line)

1. Put your videos in this folder (or download/clone this repo into a folder
   that has your videos).
2. Double-click the launcher for your system:

   | System  | Double-click                | Notes |
   |---------|-----------------------------|-------|
   | Windows | `convert-windows.bat`       | Installs Python automatically if missing. |
   | macOS   | `convert-macos.command`     | First time, you may need to right-click → **Open**. |
   | Linux   | `convert-linux.sh`          | Or run `bash convert-linux.sh` in a terminal. |

3. Done. Each video becomes a folder with the video and its `.mp3` inside.

> **First run needs internet** (once) to fetch the conversion engine (ffmpeg)
> and, if necessary, Python. After that it works offline.

### Example

```
Before                          After  (default layout)
------                          ---------------------------
Client Call.mp4                 Client Call/
Trip Vlog.mov                       Client Call.mp4
                                    Client Call.mp3
                                Trip Vlog/
                                    Trip Vlog.mov
                                    Trip Vlog.mp3
```

---

## 🛠 Run it yourself (command line)

If you already have Python 3.7+:

```bash
python convert_to_mp3.py                 # convert videos in this folder
python convert_to_mp3.py /path/to/videos # convert a different folder
```

### Options

| Option | What it does |
|--------|--------------|
| `--layout folder` | Each video in its own folder with the MP3. **(default)** |
| `--layout audio`  | Leave videos in place; collect all MP3s in an `audio/` subfolder. Handy for grabbing them all to upload at once. |
| `--layout beside` | Put the MP3 next to the video, same name, move nothing. |
| `--quality speech` | Smallest files (mono, 16 kHz) — tuned for AI/transcription. |
| `--quality standard` | Good all-round quality. **(default)** |
| `--quality high` | Near-lossless, best for music. |
| `--recursive` | Also process videos inside subfolders. |
| `--force` | Re-convert even if the MP3 already exists. |
| `--no-pause` | Don't wait for a key press at the end. |

```bash
python convert_to_mp3.py --layout audio --quality speech
```

> 💡 **About AI tokens:** models like Gemini charge for audio by its **duration**,
> not its file size. `--quality speech` makes uploads faster and files smaller,
> but it does **not** reduce token usage.

---

## ✅ Requirements

- **Python 3.7+** — the launchers install it for you if it's missing.
- **ffmpeg** — found automatically, or fetched via the `imageio-ffmpeg` package
  on first run (needs internet once). On Linux the launcher installs the system
  `ffmpeg` package instead.

## 📂 Supported video formats

`mp4 · mov · mkv · avi · webm · flv · wmv · m4v · mpeg · mpg · 3gp · ts · m2ts ·
mts · ogv · vob · asf · divx · f4v · mxf`

## ❓ Notes & limitations

- Re-running is safe: already-converted videos are skipped (use `--force` to redo).
- With the default `folder` layout, each processed video is moved into its own
  folder, so a normal re-run no longer sees it (nothing is redone). To re-convert
  videos that are *already organised into folders*, use **`--force --recursive`**.
- A video with no audio track is reported and skipped — the rest still convert.
  Such a file stays where it is, so it will be reported again on each run; delete
  it (or ignore the message) once you know it has no sound.
- "Install Python automatically" may show a one-time admin/password prompt and
  needs internet. On locked-down machines, install Python by hand from
  [python.org](https://www.python.org/downloads/).
- Dragging a folder onto `convert-windows.bat` works for simple paths; for paths
  with unusual characters, run `python convert_to_mp3.py "C:\\your\\folder"` instead.

## 📜 License

MIT — see [LICENSE](LICENSE).
