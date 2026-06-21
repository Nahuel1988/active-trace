# Corre las migraciones Alembic contra la base de datos principal (activia_trace).

$env:DATABASE_URL = "postgresql+asyncpg://activia:activia@localhost:5432/activia_trace"

$venv = Join-Path (Split-Path $MyInvocation.MyCommand.Path) ".venv"
$alembic = Join-Path $venv "Scripts\alembic.exe"

Write-Host "Corriendo migraciones..." -ForegroundColor Cyan
& $alembic upgrade head
