param([Parameter(Mandatory=$true)][string]$PythonPath)
$ErrorActionPreference = 'Stop'
try {
    foreach ($module in @('Microsoft.PowerShell.Utility','Microsoft.PowerShell.Security')) {
        Import-Module (Join-Path $PSHOME ('Modules/' + $module + '/' + $module + '.psd1')) -ErrorAction Stop
    }
    $file = Join-Path $env:LOCALAPPDATA 'EpsteinFilesArchive/r2-credentials.dpapi'
    $secure = (Get-Content -LiteralPath $file -Raw).Trim() | ConvertTo-SecureString
    $pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    try { $settings = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer) | ConvertFrom-Json }
    finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer) }
    $env:EPSTEIN_R2_ENDPOINT = $settings.endpoint
    $env:EPSTEIN_R2_ACCESS_KEY_ID = $settings.access_key_id
    $env:EPSTEIN_R2_SECRET_ACCESS_KEY = $settings.secret_access_key
    & $PythonPath (Join-Path $PSScriptRoot 'r2-archive.py') upload
    if ($LASTEXITCODE -ne 0) { throw 'Archive verification failed' }
} catch {
    Write-Output ('Archive wrapper stopped: ' + $_.Exception.GetType().Name + '. No originals removed.')
    exit 1
} finally {
    Remove-Item Env:EPSTEIN_R2_ENDPOINT,Env:EPSTEIN_R2_ACCESS_KEY_ID,Env:EPSTEIN_R2_SECRET_ACCESS_KEY -ErrorAction SilentlyContinue
    $settings = $null
    $secure = $null
}
