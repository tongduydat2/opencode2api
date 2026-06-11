#!/bin/bash
set -e

# Install requirements if needed
pip install -r requirements.txt

# Run Python proxy server with environment variables set
export API_KEY="${API_KEY:-test-key}"
export OPENCODE_PROXY_MANAGE_BACKEND="${OPENCODE_PROXY_MANAGE_BACKEND:-true}"
export OPENCODE_PATH="${OPENCODE_PATH:-/home/tongdat/.opencode/bin/opencode}"
export OPENCODE_PROXY_PORT="${OPENCODE_PROXY_PORT:-10000}"
export OPENCODE_SERVER_PORT="${OPENCODE_SERVER_PORT:-10001}"
export DISABLE_TOOLS="${DISABLE_TOOLS:-true}"
export OPENCODE_METRICS_ENABLED="${OPENCODE_METRICS_ENABLED:-true}"
export OPENCODE_HEALTH_DETAILS_ENABLED="${OPENCODE_HEALTH_DETAILS_ENABLED:-true}"

python3 -m uvicorn python_src.main:app --host 0.0.0.0 --port "$OPENCODE_PROXY_PORT"
