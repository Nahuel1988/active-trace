# Crea el usuario y las dos bases de datos necesarias para desarrollo local.
# Requiere que psql esté en el PATH (instalación estándar de PostgreSQL).
# Ejecutar UNA SOLA VEZ por máquina, como superusuario de postgres.

param(
    [string]$PgUser = "postgres"
)

$sql = @"
DO `$`$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'activia') THEN
        CREATE ROLE activia WITH LOGIN PASSWORD 'activia';
    END IF;
END
`$`$;

SELECT 'CREATE DATABASE activia_trace OWNER activia'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'activia_trace')\gexec

SELECT 'CREATE DATABASE activia_trace_test OWNER activia'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'activia_trace_test')\gexec

GRANT ALL PRIVILEGES ON DATABASE activia_trace TO activia;
GRANT ALL PRIVILEGES ON DATABASE activia_trace_test TO activia;
"@

Write-Host "Creando usuario y bases de datos..." -ForegroundColor Cyan
$sql | psql -U $PgUser
Write-Host "Listo. Bases creadas: activia_trace y activia_trace_test." -ForegroundColor Green
