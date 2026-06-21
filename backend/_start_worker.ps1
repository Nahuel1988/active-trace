# Levanta el worker de cola de comunicaciones contra localhost.

$env:DATABASE_URL                 = "postgresql+asyncpg://activia:activia@localhost:5432/activia_trace"
$env:ENCRYPTION_KEY               = "this-is-a-32-char-test-key!!!!!x"
$env:SECRET_KEY                   = "this-is-a-test-secret-key-that-is-32chars"
$env:EMAIL_LOOKUP_HMAC_KEY        = "test-hmac-key-16c"
$env:WORKER_POLL_INTERVAL_SECONDS = "10"

$venv   = Join-Path (Split-Path $MyInvocation.MyCommand.Path) ".venv"
$python = Join-Path $venv "Scripts\python.exe"

Write-Host "Iniciando worker..." -ForegroundColor Cyan
& $python -m app.workers.main
