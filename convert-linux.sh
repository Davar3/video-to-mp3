#!/usr/bin/env bash
# ============================================================================
#  Run this on Linux to convert every video in this folder to MP3.
#  Usage:  ./convert-linux.sh        (or: bash convert-linux.sh)
#  Installs python3 + ffmpeg via your package manager if they're missing
#  (you may be asked for your password).
# ============================================================================
cd "$(dirname "$0")" || exit 1

echo "Convert videos to MP3 (Linux)"
echo "============================="

have() { command -v "$1" >/dev/null 2>&1; }

# Detect a package manager and define how to install a list of packages.
detect_pm() {
    if   have apt-get; then echo apt
    elif have dnf;     then echo dnf
    elif have pacman;  then echo pacman
    elif have zypper;  then echo zypper
    elif have apk;     then echo apk
    else echo ""; fi
}

PM="$(detect_pm)"

pm_install() {  # args: logical names "python ffmpeg"
    local want="$1"
    case "$PM" in
        apt)    sudo apt-get update && sudo apt-get install -y $want ;;
        dnf)    sudo dnf install -y $want ;;
        pacman) sudo pacman -S --needed --noconfirm $want ;;
        zypper) sudo zypper install -y $want ;;
        apk)    sudo apk add $want ;;
        *)      return 1 ;;
    esac
}

# Map logical -> distro package names.
py_pkg()  { case "$PM" in pacman) echo "python" ;; *) echo "python3" ;; esac; }
pip_pkg() { case "$PM" in pacman) echo "python-pip" ;; apk) echo "py3-pip" ;; *) echo "python3-pip" ;; esac; }
ff_pkg()  { echo "ffmpeg"; }

if ! have python3; then
    if [ -z "$PM" ]; then
        echo "No supported package manager found. Please install python3 manually."
        exit 1
    fi
    echo "Python 3 not found. Installing (you may be prompted for your password)..."
    # pip is a fallback path for fetching ffmpeg if the system package is absent.
    pm_install "$(py_pkg) $(pip_pkg) $(ff_pkg)" || { echo "Install failed. Install python3 manually."; exit 1; }
fi

# Prefer a system ffmpeg (avoids pip). If it's missing, try to install it;
# the Python script will fall back to imageio-ffmpeg if that doesn't work.
if ! have ffmpeg && [ -n "$PM" ]; then
    echo "Installing ffmpeg..."
    pm_install "$(ff_pkg)" || echo "(ffmpeg will be fetched by the script instead)"
fi

if ! have python3; then
    echo "Could not set up Python. Please install python3 and try again."
    exit 1
fi

python3 "convert_to_mp3.py" --no-pause "$@"
code=$?

echo
read -n 1 -s -r -p "Press Enter to close..." _ ; echo
exit $code
