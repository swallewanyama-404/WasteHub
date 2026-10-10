@echo off
setlocal
cd /d "%~dp0.."

if not exist ".env" (
  echo WasteHub configuration not found.
  echo Running first-time setup...
  call scripts\setup.cmd
  exit /b %errorlevel%
)

echo Starting WasteHub...
docker compose up -d --build
if errorlevel 1 exit /b %errorlevel%

echo Waiting for the API to become healthy...
:wait_api
docker inspect --format="{{.State.Health.Status}}" wastehub-api 2>nul | findstr /I "healthy" >nul
if errorlevel 1 (
  timeout /t 3 /nobreak >nul
  goto wait_api
)

docker compose exec -T api python scripts/bootstrap_admin.py
if errorlevel 1 exit /b %errorlevel%

echo.
echo WasteHub is ready.
echo Frontend: http://localhost:3000
echo API docs: http://localhost:8000/docs
echo.
docker compose ps
endlocal
