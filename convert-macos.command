#!/bin/bash
# ============================================================================
#  Double-click this on macOS to convert every video in this folder to MP3.
#  Installs Python automatically if needed. ffmpeg is handled by the script.
#  (If macOS blocks it: right-click -> Open the first time.)
# ============================================================================
cd "$(dirname "$0")" || exit 1

echo "Convert videos to MP3 (macOS)"
echo "============================="

find_python() {
    if command -v python3 >/dev/null 2>&1; then echo python3; return; fi
    if command -v python  >/dev/null 2>&1 && \
       python -c 'import sys; exit(0 if sys.version_info[0]==3 else 1)' 2>/dev/null; then
        echo python; return
    fi
    echo ""
}

PY="$(find_python)"

if [ -z "$PY" ]; then
    echo "Python 3 was not found. Trying to set it up..."
    if command -v brew >/dev/null 2>&1; then
        echo "Installing Python via Homebrew..."
        if ! brew install python; then
            echo
            echo "Homebrew could not install Python."
            echo "Install it from https://www.python.org/downloads/ and run this again."
            read -n 1 -s -r -p "Press any key to close..."; echo
            exit 1
        fi
    else
        echo
        echo "Opening the macOS developer tools installer (it includes python3)."
        echo "Click 'Install' in the popup, let it finish, then run this again."
        xcode-select --install 2>/dev/null
        echo
        read -n 1 -s -r -p "Press any key to close..."; echo
        exit 1
    fi
    PY="$(find_python)"
fi

if [ -z "$PY" ]; then
    echo
    echo "Could not set up Python automatically."
    echo "Install it from https://www.python.org/downloads/ and run this again."
    read -n 1 -s -r -p "Press any key to close..."; echo
    exit 1
fi

# ffmpeg is found or fetched automatically by the Python script.
"$PY" "convert_to_mp3.py" --no-pause "$@"
code=$?

echo
read -n 1 -s -r -p "Press any key to close..."; echo
exit $code
