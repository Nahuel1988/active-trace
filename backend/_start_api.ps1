# Levanta la API FastAPI contra PostgreSQL local (sin Docker).

$env:DATABASE_URL                  = "postgresql+asyncpg://activia:activia@localhost:5432/activia_trace"
$env:TEST_DATABASE_URL             = "postgresql+asyncpg://activia:activia@localhost:5432/activia_trace_test"
$env:ENCRYPTION_KEY                = "this-is-a-32-char-test-key!!!!!x"
$env:SECRET_KEY                    = "this-is-a-test-secret-key-that-is-32chars"
$env:EMAIL_LOOKUP_HMAC_KEY         = "test-hmac-key-16c"
$env:ACCESS_TOKEN_EXPIRE_MINUTES   = "15"
$env:REFRESH_TOKEN_EXPIRE_DAYS     = "7"
$env:PASSWORD_RESET_EXPIRE_MINUTES = "15"

$venv     = Join-Path (Split-Path $MyInvocation.MyCommand.Path) ".venv"
$uvicorn  = Join-Path $venv "Scripts\uvicorn.exe"

Write-Host "Iniciando API en http://localhost:8000 ..." -ForegroundColor Cyan
& $uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
