#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
convert_to_mp3.py  -  turn videos into MP3 audio, organised neatly
==================================================================

By default, every video in the folder is converted to MP3 and tidied into its
own folder so the video and its audio stay together:

    Holiday Clip.mp4   ->   Holiday Clip/Holiday Clip.mp4   (moved)
                            Holiday Clip/Holiday Clip.mp3   (new audio)

Other layouts are available with --layout (see below).

Why audio? It is far smaller than video and ideal for feeding to an AI such as
Gemini to get transcripts, captions, or a summary of what's in the video.

Requirements: Python 3.7 or newer. That's it. The conversion engine (ffmpeg)
is found automatically, or fetched for you the first time (needs internet
once). If you don't even have Python, use the START-HERE launcher for your
operating system, which installs everything for you.

Layouts (--layout):
    folder     each video gets its own folder; the video is MOVED in and the
               MP3 placed beside it. (default)
    audio      videos stay put; all MP3s collected into an "audio" subfolder.
    beside     MP3 written next to the video, same name, nothing moved.

Examples:
    python convert_to_mp3.py
    python convert_to_mp3.py "C:\\Users\\me\\Videos"
    python convert_to_mp3.py --layout audio --quality speech
    python convert_to_mp3.py --force --recursive
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

# ----------------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------------

VIDEO_EXTENSIONS = {
    "mp4", "mov", "mkv", "avi", "webm", "flv", "wmv", "m4v",
    "mpeg", "mpg", "3gp", "ts", "m2ts", "mts", "ogv", "vob",
    "asf", "divx", "f4v", "mxf",
}

# ffmpeg audio settings per quality preset.
# NOTE: AI models such as Gemini bill audio by its DURATION, not its file size,
# so a lower bitrate makes uploads faster but does NOT reduce token usage.
QUALITY_PRESETS = {
    "speech":   ["-ac", "1", "-ar", "16000", "-b:a", "64k"],  # tiny, for ASR/AI
    "standard": ["-q:a", "2"],                                # ~190k VBR (default)
    "high":     ["-q:a", "0"],                                # ~245k VBR
}

AUDIO_DIR_NAME = "audio"

# Names this script owns, so they're never treated as input videos.
SELF_NAMES = {"convert_to_mp3.py"}

# Windows device names that cannot be used as a file/folder name.
_WIN_RESERVED = (
    {"CON", "PRN", "AUX", "NUL"}
    | {"COM%d" % i for i in range(1, 10)}
    | {"LPT%d" % i for i in range(1, 10)}
)

_ILLEGAL_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


# ----------------------------------------------------------------------------
# ffmpeg bootstrap
# ----------------------------------------------------------------------------

def _try_import_imageio_ffmpeg():
    try:
        import imageio_ffmpeg  # type: ignore
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def _pip_install(package):
    """
    Install a package into the current interpreter. Returns True on success.
    Handles PEP 668 "externally-managed-environment" by retrying with an
    explicit override as a last resort.
    """
    base = [sys.executable, "-m", "pip", "install", "--disable-pip-version-check"]
    attempts = [[], ["--user"], ["--user", "--break-system-packages"]]
    for extra in attempts:
        try:
            proc = subprocess.run(
                base + extra + [package],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                universal_newlines=True,
            )
        except Exception:
            continue
        if proc.returncode == 0:
            return True
        text = (proc.stdout or "")
        # If it's not a managed-environment problem, the next flag won't help.
        if "externally-managed-environment" not in text and "--break-system-packages" not in text:
            # Surface a short hint but keep trying the remaining options.
            pass
    return False


def _bundled_ffmpeg_names():
    """Binary name(s) to look for, depending on the operating system."""
    if os.name == "nt":
        return ["ffmpeg.exe"]
    return ["ffmpeg"]


def find_bundled_ffmpeg():
    """
    Look for an ffmpeg binary shipped ALONGSIDE this script, so the tool works
    with zero internet on the very first run. Searches the script's own folder
    and a few common subfolders. This is the preferred source.
    """
    here = Path(__file__).resolve().parent
    for folder in (here / "bin", here / "ffmpeg", here / "vendor", here):
        for name in _bundled_ffmpeg_names():
            candidate = folder / name
            if candidate.is_file():
                if os.name != "nt":               # ensure it's executable on Unix
                    try:
                        mode = os.stat(candidate).st_mode
                        os.chmod(candidate, mode | 0o111)
                    except OSError:
                        pass
                return str(candidate)
    return None


def _has_internet(timeout=4):
    """Best-effort connectivity check against a couple of reliable hosts."""
    import socket
    for host, port in (("pypi.org", 443), ("1.1.1.1", 443), ("8.8.8.8", 53)):
        try:
            sock = socket.create_connection((host, port), timeout=timeout)
            sock.close()
            return True
        except OSError:
            continue
    return False


def resolve_ffmpeg():
    """
    Return a path to an ffmpeg executable, or None (after printing guidance).
    Order of preference:
      1. a bundled binary shipped with the tool (works offline),
      2. a system ffmpeg on PATH,
      3. an already-installed imageio-ffmpeg,
      4. downloading imageio-ffmpeg (needs internet; last resort).
    """
    bundled = find_bundled_ffmpeg()
    if bundled:
        return bundled

    system = shutil.which("ffmpeg")
    if system:
        return system

    found = _try_import_imageio_ffmpeg()
    if found:
        return found

    # Nothing local -> we would have to download it. Be honest about that.
    if not _has_internet():
        print("")
        print("The conversion engine (ffmpeg) is not set up yet, and there is no")
        print("internet connection to download it.")
        print("")
        print("  >>  Please connect to the internet and run this again.  <<")
        print("")
        print("(It only needs internet this one time. After that it works offline.)")
        print("Tip: the OFFLINE version of this tool already includes ffmpeg and")
        print("     never needs internet.")
        return None

    print("Setting up the conversion engine (one-time download)...")
    sys.stdout.flush()
    for attempt in (1, 2):
        if _pip_install("imageio-ffmpeg"):
            found = _try_import_imageio_ffmpeg()
            if found:
                return found
        if attempt == 1:
            print("The download didn't complete - trying once more...")
            sys.stdout.flush()

    print(ffmpeg_unavailable_message())
    return None


def ffmpeg_unavailable_message():
    return (
        "\nCould not set up ffmpeg (the conversion engine).\n"
        "Do ONE of the following, then run this again:\n"
        "  1) Use the OFFLINE version of this tool, which already includes ffmpeg\n"
        "     (it has a 'bin' folder with ffmpeg inside), or\n"
        "  2) Connect to a different network (some block downloads) and re-run, or\n"
        "  3) Install ffmpeg manually:\n"
        "       Windows : winget install Gyan.FFmpeg\n"
        "                 (or)  pip install imageio-ffmpeg\n"
        "       macOS   : brew install ffmpeg\n"
        "       Linux   : sudo apt install ffmpeg   (or your package manager)\n"
    )


# ----------------------------------------------------------------------------
# Names & filesystem helpers
# ----------------------------------------------------------------------------

def sanitize_name(name):
    """Make a string safe to use as a file/folder name on any OS."""
    cleaned = _ILLEGAL_CHARS.sub("_", name)
    cleaned = cleaned.rstrip(" .")          # Windows forbids trailing space/dot
    if not cleaned:
        cleaned = "_"
    if cleaned.upper() in _WIN_RESERVED:
        cleaned = cleaned + "_"
    return cleaned


_NUM_RE = re.compile(r"(\d+)")


def natural_key(name):
    parts = _NUM_RE.split(name.lower())
    return [int(p) if p.isdigit() else p for p in parts]


def is_video(path):
    return path.is_file() and path.suffix.lower().lstrip(".") in VIDEO_EXTENSIONS


def iter_videos(folder, recursive):
    """Yield video files in `folder` (and subfolders if recursive)."""
    found = []
    if recursive:
        for root, dirs, files in os.walk(folder):
            # Skip hidden folders and the generated audio folder.
            dirs[:] = [d for d in dirs
                       if not d.startswith(".") and d != AUDIO_DIR_NAME]
            for fname in files:
                p = Path(root) / fname
                if is_video(p) and p.name not in SELF_NAMES:
                    found.append(p)
    else:
        for p in folder.iterdir():
            if is_video(p) and p.name not in SELF_NAMES:
                found.append(p)
    found.sort(key=lambda p: natural_key(str(p)))
    return found


def next_unique_path(path):
    if not path.exists():
        return path
    i = 1
    while True:
        candidate = path.with_name("%s (%d)%s" % (path.stem, i, path.suffix))
        if not candidate.exists():
            return candidate
        i += 1


def duplicated_stems(videos):
    """Stems (lower-cased) shared by more than one video, e.g. clip.mp4+clip.mov."""
    seen = {}
    for v in videos:
        key = v.stem.lower()
        seen[key] = seen.get(key, 0) + 1
    return {k for k, n in seen.items() if n > 1}


def mp3_name_for(video, dup_stems):
    """The .mp3 filename. Disambiguated only when stems collide."""
    stem = video.stem
    if stem.lower() in dup_stems:
        base = "%s.%s" % (stem, video.suffix.lstrip(".").lower())
    else:
        base = stem
    return sanitize_name(base) + ".mp3"


def plan_targets(root, video, layout, dup_stems):
    """
    Return (target_dir, mp3_path, video_dest_or_None) for one video.
    video_dest is set only for the 'folder' layout (where the video moves).
    """
    mp3name = mp3_name_for(video, dup_stems)
    if layout == "folder":
        target_dir = root / sanitize_name(video.stem)
        if video.parent == target_dir:
            target_dir = video.parent          # already organised: act in place
        video_dest = target_dir / video.name
        return target_dir, target_dir / mp3name, video_dest
    if layout == "audio":
        target_dir = root / AUDIO_DIR_NAME
        return target_dir, target_dir / mp3name, None
    # 'beside'
    return video.parent, video.parent / mp3name, None


# ----------------------------------------------------------------------------
# Conversion
# ----------------------------------------------------------------------------

def convert(ffmpeg, src, dst, audio_opts):
    """
    Convert src -> dst (an .mp3 path). Writes to a temp '.part' file beside the
    source (a folder that always exists) and only creates the destination
    folder once conversion succeeds, so failures leave nothing behind.
    """
    tmp = src.parent / (dst.name + ".part")
    if tmp.exists():
        try:
            tmp.unlink()
        except OSError:
            pass
    cmd = [
        ffmpeg, "-y",
        "-i", str(src),
        "-vn",                      # drop the video stream
        "-c:a", "libmp3lame",
    ] + audio_opts + [
        "-f", "mp3",                # force the muxer (output name ends in .part)
        "-loglevel", "error", "-stats",
        str(tmp),
    ]
    sys.stdout.flush()
    try:
        result = subprocess.run(cmd)
    except FileNotFoundError:
        return False, "ffmpeg executable not found"
    except Exception as exc:  # pragma: no cover - defensive
        return False, str(exc)

    def _cleanup():
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass

    if result.returncode != 0:
        _cleanup()
        return False, "ffmpeg exited with code %d" % result.returncode
    if not tmp.exists() or tmp.stat().st_size == 0:
        _cleanup()
        return False, "no audio produced (does the video have sound?)"
    try:
        dst.parent.mkdir(parents=True, exist_ok=True)
        os.replace(str(tmp), str(dst))
    except OSError as exc:
        _cleanup()
        return False, "could not save output: %s" % exc
    return True, ""


def process_one(ffmpeg, video, root, layout, audio_opts, dup_stems, force):
    """Returns one of: 'done', 'skip', or ('fail', message)."""
    target_dir, mp3_path, video_dest = plan_targets(root, video, layout, dup_stems)

    if mp3_path.exists() and not force:
        return "skip"

    ok, msg = convert(ffmpeg, video, mp3_path, audio_opts)
    if not ok:
        return ("fail", msg)

    # Audio succeeded -> for the 'folder' layout, move the video in next to it.
    if video_dest is not None:
        try:
            if video.resolve() != video_dest.resolve():
                dest = next_unique_path(video_dest)
                shutil.move(str(video), str(dest))
        except OSError as exc:
            print("        (audio saved, but could not move the video: %s)" % exc)
    return "done"


# ----------------------------------------------------------------------------
# Main workflow
# ----------------------------------------------------------------------------

def run(root, ffmpeg, layout, audio_opts, force, recursive):
    videos = iter_videos(root, recursive)
    if not videos:
        print("No video files found in:\n  %s" % root)
        return 0, 0, 0

    dup = duplicated_stems(videos)
    total = len(videos)
    width = len(str(total))
    print("Found %d video(s). Layout: %s\n" % (total, layout))

    converted = skipped = failed = 0
    for index, video in enumerate(videos, start=1):
        try:
            rel = video.relative_to(root)
        except ValueError:
            rel = video.name
        print("[%*d/%d] %s" % (width, index, total, rel))
        sys.stdout.flush()

        result = process_one(ffmpeg, video, root, layout, audio_opts, dup, force)
        if result == "skip":
            skipped += 1
            print("        already done - skipped (use --force to redo)")
        elif result == "done":
            converted += 1
        else:  # ('fail', message)
            failed += 1
            print("        SKIPPED: %s" % result[1])

    return converted, skipped, failed


# ----------------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------------

def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Convert every video in a folder to MP3, organised neatly.")
    parser.add_argument(
        "folder", nargs="?", default=None,
        help="Folder containing the videos. Defaults to the folder this "
             "script is in.")
    parser.add_argument(
        "--layout", choices=["folder", "audio", "beside"], default="folder",
        help="folder = each video in its own folder with the MP3 (default); "
             "audio = all MP3s in one 'audio' subfolder; "
             "beside = MP3 next to the video.")
    parser.add_argument(
        "--quality", choices=sorted(QUALITY_PRESETS.keys()), default="standard",
        help="speech = smallest, tuned for AI/transcription; standard = good "
             "all-round (default); high = near-lossless.")
    parser.add_argument(
        "--recursive", action="store_true",
        help="Also process videos inside subfolders.")
    parser.add_argument(
        "--force", action="store_true",
        help="Re-convert even if the MP3 already exists.")
    parser.add_argument(
        "--no-pause", action="store_true",
        help="Do not wait for a key press before closing.")
    return parser.parse_args(argv)


def pause(no_pause):
    if no_pause or not sys.stdin.isatty():
        return
    try:
        input("\nPress Enter to close...")
    except (EOFError, KeyboardInterrupt):
        pass


def make_output_unicode_safe():
    """Stop legacy Windows consoles (cp1252) from crashing on non-ASCII names."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="backslashreplace")
        except Exception:
            pass


def main(argv=None):
    make_output_unicode_safe()
    args = parse_args(argv if argv is not None else sys.argv[1:])

    if args.folder:
        root = Path(args.folder).expanduser().resolve()
    else:
        root = Path(__file__).resolve().parent

    if not root.is_dir():
        print("Not a folder: %s" % root)
        pause(args.no_pause)
        return 1

    print("Convert videos to MP3")
    print("=" * 52)
    print("Folder : %s" % root)
    print("Layout : %s    Quality: %s" % (args.layout, args.quality))
    print("=" * 52)

    ffmpeg = resolve_ffmpeg()   # prints its own guidance if it can't be found
    if not ffmpeg:
        pause(args.no_pause)
        return 1

    audio_opts = QUALITY_PRESETS[args.quality]
    converted, skipped, failed = run(
        root, ffmpeg, args.layout, audio_opts, args.force, args.recursive)

    print("\n" + "-" * 52)
    print("Done.  Converted: %d   Already done: %d   Failed: %d"
          % (converted, skipped, failed))
    if failed:
        print("Some files were skipped (see messages above). Their videos are")
        print("untouched so you can fix the issue and run again.")
    pause(args.no_pause)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nCancelled.")
        sys.exit(130)
    except Exception:
        import traceback
        print("\nUnexpected error:")
        traceback.print_exc()
        try:
            if sys.stdin.isatty():
                input("\nPress Enter to close...")
        except Exception:
            pass
        sys.exit(1)
