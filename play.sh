#!/usr/bin/env bash
# Play the KCSM stream. Passes any args through to play.py (e.g. ./play.sh hd2)
set -euo pipefail
cd "$(dirname "$0")"

if ! command -v uv >/dev/null 2>&1; then
  cat >&2 <<'MSG'
Error: uv is not installed (it's what runs play.py and its dependencies).

Install it with:
    curl -LsSf https://astral.sh/uv/install.sh | sh

Then open a new terminal (or run: source ~/.local/bin/env) and try again.
More info: https://docs.astral.sh/uv/getting-started/installation/
MSG
  exit 1
fi

exec uv run --with-requirements requirements.txt play.py "$@"
