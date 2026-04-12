# e-INFRA proxy start script — Windows PowerShell
# Usage: .\start_proxy.ps1
# Then in another PowerShell:
#   $env:ANTHROPIC_BASE_URL = "http://localhost:4001"
#   $env:ANTHROPIC_AUTH_TOKEN = "dummy"
#   claude
#
# To switch model: change BIG_MODEL / SMALL_MODEL below.
# Available: kimi-k2.5, deepseek-v3.2, qwen3.5-122b, deepseek-v3.2-thinking, mistral-small-4

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

$env:PYTHONUTF8      = "1"
$env:OPENAI_API_KEY  = "<YOUR_API_KEY>"
$env:OPENAI_BASE_URL = "https://llm.ai.e-infra.cz/v1"
$env:BIG_MODEL       = "kimi-k2.5"
$env:SMALL_MODEL     = "kimi-k2.5"

Write-Host "Starting proxy on http://localhost:4001 -> e-INFRA $env:BIG_MODEL"

uv run --python 3.12 --with fastapi --with httpx --with uvicorn uvicorn proxy:app --host 0.0.0.0 --port 4001
