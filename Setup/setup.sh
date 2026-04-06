#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_DIR="$REPO_ROOT/.venv"
REQUIREMENTS_FILE="$SCRIPT_DIR/requirements.txt"

find_python() {
	if [[ -n "${PYTHON_BIN:-}" ]] && command -v "$PYTHON_BIN" >/dev/null 2>&1; then
		echo "$PYTHON_BIN"
		return 0
	fi

	if command -v python3 >/dev/null 2>&1; then
		echo "python3"
		return 0
	fi

	return 1
}

PYTHON_CMD="$(find_python || true)"

if [[ -z "$PYTHON_CMD" ]]; then
	echo "Python 3 is required but was not found on PATH."
	echo "Install Python 3 or run with PYTHON_BIN=/path/to/python3 ./setup.sh"
	exit 1
fi

if [[ -d "$VENV_DIR" ]]; then
	echo "Virtual environment already exists at $VENV_DIR"
else
	echo "Creating virtual environment at $VENV_DIR"
	"$PYTHON_CMD" -m venv "$VENV_DIR"
fi

"$VENV_DIR/bin/python" -m pip install --upgrade pip

if [[ -f "$REQUIREMENTS_FILE" ]]; then
	echo "Installing dependencies from $REQUIREMENTS_FILE"
	"$VENV_DIR/bin/pip" install -r "$REQUIREMENTS_FILE"
else
	echo "No requirements.txt found. Skipping dependency installation."
fi

echo "Virtual environment ready."
echo "Activate it with: source $VENV_DIR/bin/activate"
