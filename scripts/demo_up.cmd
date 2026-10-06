@echo off
setlocal

echo.
echo ========================================
echo   Starting WasteHub Demo Environment
echo ========================================
echo.

docker compose -f docker-compose.demo.yml up -d --build
if errorlevel 1 goto :error

echo.
echo Waiting for WasteHub API to become ready...
set /a API_WAIT_TRIES=0
:wait_api
powershell -NoProfile -Command "try { $r = Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/ -TimeoutSec 2; if ($r.StatusCode -eq 200) { exit 0 } } catch {}; exit 1"
if errorlevel 1 (
    set /a API_WAIT_TRIES+=1
    if %API_WAIT_TRIES% GEQ 90 (
        echo.
        echo WasteHub API did not become ready within 3 minutes.
        docker compose -f docker-compose.demo.yml logs api
        goto :error
    )
    timeout /t 2 /nobreak >nul
    goto :wait_api
)

echo.
echo Seeding classroom demo data...
docker compose -f docker-compose.demo.yml exec -T -e PYTHONPATH=/app api python scripts/seed_demo.py
if errorlevel 1 goto :error

echo.
echo ========================================
echo   WasteHub is ready
echo ========================================
echo Frontend: http://localhost:3000
echo API docs: http://localhost:8000/docs
echo.
echo Demo resident:   resident@wastehub.demo
echo Password:        WasteHubResident123!
echo.
echo Demo collector:  collector@wastehub.demo
echo Password:        WasteHubCollector123!
echo.
echo Demo supervisor: supervisor@wastehub.demo
echo Password:        WasteHubSupervisor123!
echo.
echo Demo admin:      admin@wastehub.demo
echo Password:        WasteHubAdmin123!
echo.
exit /b 0

:error
echo.
echo WasteHub could not start successfully.
echo Run: docker compose -f docker-compose.demo.yml logs
exit /b 1
