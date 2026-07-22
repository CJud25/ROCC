#!/usr/bin/env sh
set -eu

PROJECT_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
VENV_ROOT="$PROJECT_ROOT/.venv"
VENV_PYTHON="$VENV_ROOT/bin/python"
BASE_PYTHON=${ROCC_PYTHON:-python3}

if [ ! -x "$VENV_PYTHON" ]; then
    if ! command -v "$BASE_PYTHON" >/dev/null 2>&1 && [ ! -x "$BASE_PYTHON" ]; then
        echo 'Python 3.11+ was not found. Install Python 3.11+ and try again.' >&2
        exit 1
    fi
    "$BASE_PYTHON" -m venv "$VENV_ROOT"
    "$VENV_PYTHON" -m pip install --disable-pip-version-check -r "$PROJECT_ROOT/requirements.txt"
fi

exec "$VENV_PYTHON" -m streamlit run "$PROJECT_ROOT/app.py"
