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
$stage = 'loading saved credentials'
$diagnostic = Join-Path $projectRoot 'tmp/r2-setup-status.json'
try {
    if (Test-Path -LiteralPath $credentialFile) {
        $protected = Get-Content -LiteralPath $credentialFile -Raw | ConvertTo-SecureString
        $settings = (Reveal $protected) | ConvertFrom-Json
        Write-Host 'Saved credentials found. Keys do not need to be entered again.'
        $stage = 'checking endpoint'
        $replacement = (Read-Host 'S3 endpoint URL (Enter keeps saved endpoint)').Trim().TrimEnd('/')
        if ($replacement) { $settings.endpoint = $replacement }
    } else {
        $stage = 'checking endpoint'
        $endpoint = (Read-Host 'S3 endpoint URL (https://ACCOUNT_ID.r2.cloudflarestorage.com)').Trim().TrimEnd('/')
        if ($endpoint -notmatch '^https://[a-f0-9]{32}(\.(eu|us|fedramp))?\.r2\.cloudflarestorage\.com$') {
            throw 'Use the S3 account endpoint shown by Cloudflare, without bucket or object path.'
        }
        $stage = 'reading keys'
        $access = Read-Host 'Access Key ID (hidden)' -AsSecureString
        $secret = Read-Host 'Secret Access Key (hidden)' -AsSecureString
        $settings = [ordered]@{endpoint=$endpoint; access_key_id=(Reveal $access); secret_access_key=(Reveal $secret)}
        if (-not $settings.access_key_id -or -not $settings.secret_access_key) { throw 'Both keys are required.' }
    }
    $stage = 'checking endpoint'
    if ($settings.endpoint -notmatch '^https://[a-f0-9]{32}(\.(eu|us|fedramp))?\.r2\.cloudflarestorage\.com$') {
        throw 'Invalid endpoint format'
    }
    $stage = 'saving encrypted credentials'
    $protected = ConvertTo-SecureString ($settings | ConvertTo-Json -Compress) -AsPlainText -Force
    New-Item -ItemType Directory -Path $credentialFolder -Force | Out-Null
    $protected | ConvertFrom-SecureString | Set-Content -LiteralPath $credentialFile -Encoding ASCII
    $stage = 'starting Python upload and restore test'
    if (-not (Test-Path -LiteralPath $PythonPath -PathType Leaf)) { throw 'Python missing' }
    $env:EPSTEIN_R2_ENDPOINT = $settings.endpoint
    $env:EPSTEIN_R2_ACCESS_KEY_ID = $settings.access_key_id
    $env:EPSTEIN_R2_SECRET_ACCESS_KEY = $settings.secret_access_key
    & $PythonPath (Join-Path $PSScriptRoot 'r2-smoke.py')
    if ($LASTEXITCODE -ne 0) { throw 'Upload/restore test did not pass. Keep all local evidence.' }
    @{status='passed'; stage='four-sample upload and restore'} | ConvertTo-Json | Set-Content -LiteralPath $diagnostic -Encoding UTF8
} catch {
    Write-Host 'Setup or test stopped. No original files were removed.' -ForegroundColor Yellow
    Write-Host ('Stopped at: ' + $stage) -ForegroundColor Yellow
    if ($stage -eq 'checking endpoint') {
        Write-Host 'Expected HTTPS account endpoint with a 32-character account ID.'
        Write-Host 'Use the exact S3 API endpoint for this bucket. No bucket name, path, query, brackets or quotes.'
        Write-Host 'The .eu, .us and .fedramp jurisdiction variants are supported.'
    } elseif ($stage -eq 'loading saved credentials') {
        Write-Host 'The saved file could not be decrypted by this Windows user.'
    } elseif ($stage -eq 'starting Python upload and restore test') {
        Write-Host 'See the safe diagnostic above and tmp/r2-smoke-status.json for the failed operation.'
    }
    @{status='stopped'; stage=$stage} | ConvertTo-Json | Set-Content -LiteralPath $diagnostic -Encoding UTF8
    Write-Host 'Share only the stopped-at message or safe error code, never the keys.'
} finally {
    Remove-Item Env:EPSTEIN_R2_ENDPOINT,Env:EPSTEIN_R2_ACCESS_KEY_ID,Env:EPSTEIN_R2_SECRET_ACCESS_KEY -ErrorAction SilentlyContinue
    $settings = $null
    $protected = $null
    $access = $null
    $secret = $null
}
Read-Host 'Press Enter to close this setup window'
