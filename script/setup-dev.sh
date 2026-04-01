#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV_PATH="${VENV_PATH:-.venv}"

resolve_venv_python() {
  local path="$1"

  if [[ -x "$path/bin/python" ]]; then
    printf '%s\n' "$path/bin/python"
    return
  fi

  if [[ -x "$path/Scripts/python.exe" ]]; then
    printf '%s\n' "$path/Scripts/python.exe"
    return
  fi

  printf 'Unable to find virtual environment Python executable under %s\n' "$path" >&2
  exit 1
}

if [[ ! -d "$VENV_PATH" ]]; then
  printf "Creating virtual environment in '%s'...\n" "$VENV_PATH"
  "$PYTHON_BIN" -m venv "$VENV_PATH"
else
  printf "Using existing virtual environment in '%s'...\n" "$VENV_PATH"
fi

VENV_PYTHON="$(resolve_venv_python "$VENV_PATH")"

printf 'Installing development dependencies...\n'
"$VENV_PYTHON" -m pip install --upgrade pip
"$VENV_PYTHON" -m pip install -e ".[dev]"

if [[ -d .git ]]; then
  printf 'Installing pre-commit hooks...\n'
  "$VENV_PYTHON" -m pre_commit install
else
  printf 'Skipping pre-commit hook installation (no .git folder found).\n'
fi

printf '\nDevelopment environment is ready.\n'
printf 'Activate with: source %s/bin/activate\n' "$VENV_PATH"
