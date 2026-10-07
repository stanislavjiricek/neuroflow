#!/usr/bin/env bash
# Legacy OpenAI-compatible proxy - start script (macOS / Linux)
# Needs OPENAI_API_KEY, OPENAI_BASE_URL and BIG_MODEL in the environment (SMALL_MODEL and PROXY_PORT optional):
#   OPENAI_API_KEY="$(cat ~/.claude-gateway/gateway-key)" OPENAI_BASE_URL=https://llm.example.org/v1 \
#   BIG_MODEL=<main-model> SMALL_MODEL=<small-model> bash start_proxy.sh
# Then in another terminal:
#   export ANTHROPIC_BASE_URL=http://localhost:4001
#   export ANTHROPIC_AUTH_TOKEN=dummy
#   claude
# See skills/setup/references/custom-gateway.md (legacy appendix).

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || exit 2

: "${OPENAI_API_KEY:?set OPENAI_API_KEY (your provider key, read from a file) first}"
: "${OPENAI_BASE_URL:?set OPENAI_BASE_URL (e.g. https://llm.example.org/v1) first}"
: "${BIG_MODEL:?set BIG_MODEL (the provider model to use) first}"
PORT="${PROXY_PORT:-4001}"

echo "Starting proxy on http://localhost:$PORT -> $OPENAI_BASE_URL ($BIG_MODEL)"

PYTHONUTF8=1 \
  OPENAI_API_KEY="$OPENAI_API_KEY" \
  OPENAI_BASE_URL="$OPENAI_BASE_URL" \
  BIG_MODEL="$BIG_MODEL" \
  SMALL_MODEL="${SMALL_MODEL:-$BIG_MODEL}" \
  uv run --python 3.12 --with fastapi --with httpx --with uvicorn \
  uvicorn proxy:app --host 127.0.0.1 --port "$PORT"
