param([Parameter(Mandatory=$true)][string]$PythonPath)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$credentialFolder = Join-Path $env:LOCALAPPDATA 'EpsteinFilesArchive'
$credentialFile = Join-Path $credentialFolder 'r2-credentials.dpapi'
Write-Host 'Private R2 archive setup: epstein-files-archive'
Write-Host 'Keys are hidden and encrypted for this Windows user, outside OneDrive and Git.'
Write-Host 'The test uploads four small evidence samples, restores them, and checks SHA-256.'
Write-Host 'No original files will be deleted. Leave Cloudflare public access disabled.'
function Reveal([Security.SecureString]$Value) {
    $pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($Value)
    try { [Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer) }
    finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer) }
}
try {
    if (Test-Path -LiteralPath $credentialFile) {
        $protected = Get-Content -LiteralPath $credentialFile -Raw | ConvertTo-SecureString
        $settings = (Reveal $protected) | ConvertFrom-Json
    } else {
        $endpoint = (Read-Host 'S3 endpoint URL (https://ACCOUNT_ID.r2.cloudflarestorage.com)').Trim().TrimEnd('/')
        if ($endpoint -notmatch '^https://[a-f0-9]{32}(\.(eu|us|fedramp))?\.r2\.cloudflarestorage\.com$') {
            throw 'Use the S3 account endpoint shown by Cloudflare, without bucket or object path.'
        }
        $access = Read-Host 'Access Key ID (hidden)' -AsSecureString
        $secret = Read-Host 'Secret Access Key (hidden)' -AsSecureString
        $settings = [ordered]@{endpoint=$endpoint; access_key_id=(Reveal $access); secret_access_key=(Reveal $secret)}
        if (-not $settings.access_key_id -or -not $settings.secret_access_key) { throw 'Both keys are required.' }
        $protected = ConvertTo-SecureString ($settings | ConvertTo-Json -Compress) -AsPlainText -Force
        New-Item -ItemType Directory -Path $credentialFolder -Force | Out-Null
        $protected | ConvertFrom-SecureString | Set-Content -LiteralPath $credentialFile -Encoding ASCII
    }
    $env:EPSTEIN_R2_ENDPOINT = $settings.endpoint
    $env:EPSTEIN_R2_ACCESS_KEY_ID = $settings.access_key_id
    $env:EPSTEIN_R2_SECRET_ACCESS_KEY = $settings.secret_access_key
    & $PythonPath (Join-Path $PSScriptRoot 'r2-smoke.py')
    if ($LASTEXITCODE -ne 0) { throw 'Upload/restore test did not pass. Keep all local evidence.' }
} catch {
    Write-Host 'Setup or test stopped. No original files were removed.' -ForegroundColor Yellow
    Write-Host 'Tell the assistant which step stopped; do not share your keys.'
} finally {
    Remove-Item Env:EPSTEIN_R2_ENDPOINT,Env:EPSTEIN_R2_ACCESS_KEY_ID,Env:EPSTEIN_R2_SECRET_ACCESS_KEY -ErrorAction SilentlyContinue
    $settings = $null
    $protected = $null
    $access = $null
    $secret = $null
}
Read-Host 'Press Enter to close this setup window'
