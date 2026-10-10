@echo off
setlocal
cd /d "%~dp0.."

if not exist ".env" goto first_setup

findstr /B /C:"POSTGRES_PASSWORD=" ".env" >nul || goto first_setup
findstr /B /C:"WASTEHUB_ADMIN_EMAIL=" ".env" >nul || goto first_setup
findstr /B /C:"PAYMENT_PROVIDER=manual_verification" ".env" >nul || goto first_setup
goto start_wastehub

:first_setup
echo WasteHub 1.0 configuration is not ready.
echo Running first-time setup...
call scripts\setup.cmd
exit /b %errorlevel%

:start_wastehub
echo Starting WasteHub...
docker compose up -d --build
if errorlevel 1 exit /b %errorlevel%

echo Waiting for the API to become healthy...
set /a WASTEHUB_WAIT_ATTEMPTS=0

:wait_api
docker inspect --format="{{.State.Health.Status}}" wastehub-api 2>nul | findstr /I "healthy" >nul
if not errorlevel 1 goto api_ready

set /a WASTEHUB_WAIT_ATTEMPTS+=1
if %WASTEHUB_WAIT_ATTEMPTS% GEQ 40 (
  echo WasteHub API did not become healthy in time.
  docker compose logs --tail=80 api
  exit /b 1
)

timeout /t 3 /nobreak >nul
goto wait_api

:api_ready
docker compose exec -T api python scripts/bootstrap_admin.py
if errorlevel 1 exit /b %errorlevel%

echo.
echo WasteHub is ready.
echo Frontend: http://localhost:3000
echo API docs: http://localhost:8000/docs
echo.
docker compose ps
endlocal
