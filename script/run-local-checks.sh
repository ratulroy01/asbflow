#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV_PATH="${VENV_PATH:-.venv}"

resolve_python() {
  local path="$1"
  local fallback="$2"

  if [[ -x "$path/bin/python" ]]; then
    printf '%s\n' "$path/bin/python"
    return
  fi

  if [[ -x "$path/Scripts/python.exe" ]]; then
    printf '%s\n' "$path/Scripts/python.exe"
    return
  fi

  printf '%s\n' "$fallback"
}

PYTHON_EXE="$(resolve_python "$VENV_PATH" "$PYTHON_BIN")"

printf 'Using Python executable: %s\n' "$PYTHON_EXE"
printf 'Running local checks...\n'

"$PYTHON_EXE" -m pytest -q test/unit
"$PYTHON_EXE" -m black --check src test
"$PYTHON_EXE" -m isort --check-only src test

printf '\nAll local checks passed.\n'
