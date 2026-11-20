# Writes DATABASE_URL into apps/api/.env without showing the password on screen or in chat.
# Usage (from the repo root):  powershell -ExecutionPolicy Bypass -File scripts\set-db-password.ps1
$ErrorActionPreference = "Stop"

$envFile = Join-Path $PSScriptRoot "..\apps\api\.env"
$projectRef = "qcpgmznxtnbqmsyazydw"

$hostDefault = "aws-0-eu-central-1.pooler.supabase.com"
$poolerHost = Read-Host "Pooler host (Enter = $hostDefault)"
if ([string]::IsNullOrWhiteSpace($poolerHost)) { $poolerHost = $hostDefault }

$secure = Read-Host "Supabase database password" -AsSecureString
$bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
try {
    $plain = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
} finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
}
if ([string]::IsNullOrEmpty($plain)) { throw "Password is empty." }

$encoded = [Uri]::EscapeDataString($plain)   # safe even if the password contains @ : / #
$line = "DATABASE_URL=postgresql+asyncpg://postgres.${projectRef}:${encoded}@${poolerHost}:6543/postgres"

$lines = Get-Content $envFile | Where-Object { $_ -notmatch '^\s*#?\s*DATABASE_URL=' }
$lines += $line
Set-Content -Path $envFile -Value $lines -Encoding utf8
Write-Host "DATABASE_URL saved to $envFile"
