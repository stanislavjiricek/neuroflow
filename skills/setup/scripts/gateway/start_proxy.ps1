# Legacy OpenAI-compatible proxy - start script (Windows PowerShell)
# Needs OPENAI_API_KEY, OPENAI_BASE_URL and BIG_MODEL set in this window (SMALL_MODEL and PROXY_PORT optional):
#   $env:OPENAI_API_KEY  = (Get-Content "$env:USERPROFILE\.claude-gateway\gateway-key" -Raw).Trim()
#   $env:OPENAI_BASE_URL = "https://llm.example.org/v1"
#   $env:BIG_MODEL       = "<main-model>"
#   .\start_proxy.ps1
# Then in another PowerShell window:
#   $env:ANTHROPIC_BASE_URL = "http://localhost:4001"
#   $env:ANTHROPIC_AUTH_TOKEN = "dummy"
#   claude
# See skills/setup/references/custom-gateway.md (legacy appendix).

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

foreach ($name in "OPENAI_API_KEY", "OPENAI_BASE_URL", "BIG_MODEL") {
    if (-not [Environment]::GetEnvironmentVariable($name)) {
        Write-Error "Set $name first (see the comments at the top of this script)."
        exit 2
    }
}
if (-not $env:SMALL_MODEL) { $env:SMALL_MODEL = $env:BIG_MODEL }
$Port = if ($env:PROXY_PORT) { $env:PROXY_PORT } else { "4001" }
$env:PYTHONUTF8 = "1"

Write-Host "Starting proxy on http://localhost:$Port -> $env:OPENAI_BASE_URL ($env:BIG_MODEL)"

uv run --python 3.12 --with fastapi --with httpx --with uvicorn uvicorn proxy:app --host 127.0.0.1 --port $Port
