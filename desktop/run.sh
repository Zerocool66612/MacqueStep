#!/bin/sh
set -eu
cd "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
if [ ! -x .venv/bin/python ]; then
 python3 -m venv .venv || { echo 'Install Python venv support first (Ubuntu: sudo apt install python3-venv).'; exit 1; }
fi
if ! .venv/bin/python -c 'import PySide6, pyte' 2>/dev/null; then
 .venv/bin/python -m pip install -r requirements.txt
fi
exec .venv/bin/python desktop.py "$@"
