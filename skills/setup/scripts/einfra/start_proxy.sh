#!/usr/bin/env bash
# e-INFRA proxy start script — Unix
# Usage: bash start_proxy.sh
# Then in another terminal:
#   export ANTHROPIC_BASE_URL=http://localhost:4001
#   export ANTHROPIC_AUTH_TOKEN=dummy
#   claude
#
# To switch model: change BIG_MODEL / SMALL_MODEL below.
# Available: kimi-k2.5, deepseek-v3.2, qwen3.5-122b, deepseek-v3.2-thinking, mistral-small-4

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

BIG_MODEL="${BIG_MODEL:-kimi-k2.5}"
SMALL_MODEL="${SMALL_MODEL:-kimi-k2.5}"

echo "Starting proxy on http://localhost:4001 -> e-INFRA $BIG_MODEL"

PYTHONUTF8=1 \
  OPENAI_API_KEY="${OPENAI_API_KEY:-<YOUR_API_KEY>}" \
  OPENAI_BASE_URL="https://llm.ai.e-infra.cz/v1" \
  BIG_MODEL="$BIG_MODEL" \
  SMALL_MODEL="$SMALL_MODEL" \
  uv run --python 3.12 --with fastapi --with httpx --with uvicorn \
  uvicorn proxy:app --host 0.0.0.0 --port 4001
