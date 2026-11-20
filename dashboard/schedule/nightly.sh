#!/bin/sh
# Nightly ETL wrapper (TEMPLATE; not installed by this repo). Edit REPO, then point cron or launchd at this file.
# Credentials are read from an env file OUTSIDE the repo; never commit it.
#   MINDBENCH_DRIVE_FOLDER_ID=...           (the Drive folder DataPipe writes to)
#   GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
REPO="$HOME/MindBench"                       # <-- edit
ENV_FILE="$HOME/.mindbench.env"              # <-- edit (optional; leave missing to load files already in data/raw only)
[ -f "$ENV_FILE" ] && . "$ENV_FILE" && export MINDBENCH_DRIVE_FOLDER_ID GOOGLE_APPLICATION_CREDENTIALS
cd "$REPO" || exit 2
export PATH="$HOME/.local/bin:$PATH"          # where uv is installed
mkdir -p data
uv run --project dashboard python -m mindbench_dashboard.nightly >> data/nightly.log 2>&1
