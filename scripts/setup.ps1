$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

if (Test-Path ".env") {
    Write-Host "WasteHub .env already exists. Nothing was changed."
    exit 0
}

Write-Host ""
Write-Host "WasteHub first-time setup"
Write-Host "-------------------------"

$adminName = Read-Host "System administrator full name"
$adminEmail = Read-Host "System administrator email"
$adminPhone = Read-Host "System administrator phone number"
$securePassword = Read-Host "System administrator password (minimum 12 characters)" -AsSecureString
$adminPassword = [System.Net.NetworkCredential]::new("", $securePassword).Password

if ($adminPassword.Length -lt 12) {
    throw "Administrator password must contain at least 12 characters."
}

$dbPassword = ([guid]::NewGuid().ToString("N") + [guid]::NewGuid().ToString("N"))
$secretKey = ([guid]::NewGuid().ToString("N") + [guid]::NewGuid().ToString("N") + [guid]::NewGuid().ToString("N"))

$lines = @(
    "APP_NAME=WasteHub API",
    "APP_ENV=production",
    "DEBUG=false",
    "API_V1_PREFIX=/api/v1",
    "",
    "POSTGRES_DB=wastehub",
    "POSTGRES_USER=wastehub",
    "POSTGRES_PASSWORD=$dbPassword",
    "DATABASE_URL=postgresql+psycopg://wastehub:$dbPassword@db:5432/wastehub",
    "",
    "SECRET_KEY=$secretKey",
    "ACCESS_TOKEN_EXPIRE_MINUTES=240",
    "",
    "MEDIA_ROOT=/app/media",
    "PAYMENT_PROVIDER=manual_verification",
    "CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000",
    "",
    "WASTEHUB_ADMIN_NAME=$adminName",
    "WASTEHUB_ADMIN_EMAIL=$adminEmail",
    "WASTEHUB_ADMIN_PHONE=$adminPhone",
    "WASTEHUB_ADMIN_PASSWORD=$adminPassword"
)

$lines | Set-Content -Path ".env" -Encoding UTF8
Write-Host ""
Write-Host "Secure WasteHub configuration created in .env."
Write-Host "Starting the application..."
& cmd /c "scripts\start.cmd"
exit $LASTEXITCODE
