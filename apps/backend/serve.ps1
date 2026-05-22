$ErrorActionPreference = "Stop"

$ScriptDir      = Split-Path -Parent $MyInvocation.MyCommand.Definition
$MobileUiLabEnv = [System.IO.Path]::GetFullPath((Join-Path $ScriptDir "..\mobile-ui-lab\.env"))
$Python     = Join-Path $ScriptDir "venv\Scripts\python.exe"
$NgrokLog   = "$env:TEMP\ngrok_serve.log"
$NgrokErrLog= "$env:TEMP\ngrok_serve_err.log"

# --- Validate prerequisites ---

$NgrokCmd = Get-Command ngrok -ErrorAction SilentlyContinue
if (-not $NgrokCmd) {
    Write-Host "ERROR: ngrok not found."
    Write-Host "  1. Install:  winget install ngrok"
    Write-Host "  2. Auth:     ngrok config add-authtoken YOUR_TOKEN"
    exit 1
}

if (-not (Test-Path $Python)) {
    Write-Host "ERROR: venv not found at: $Python"
    Write-Host "  Run: python -m venv venv && venv\Scripts\pip install -r requirements.txt"
    exit 1
}

# --- Helper: start uvicorn and return the process ---

function Start-Uvicorn {
    Write-Host "[backend] Starting uvicorn on port 8000..."
    return Start-Process -FilePath $Python `
        -ArgumentList "-m", "uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000" `
        -WorkingDirectory $ScriptDir `
        -PassThru -NoNewWindow
}

function Set-ExpoApiBaseUrl {
    param(
        [Parameter(Mandatory = $true)][string]$EnvPath,
        [Parameter(Mandatory = $true)][string]$ApiUrl
    )

    if (Test-Path $EnvPath) {
        $envFile = Get-Item $EnvPath
        if ($envFile.Length -gt 1MB) {
            $backupPath = "$EnvPath.corrupt-$(Get-Date -Format 'yyyyMMddHHmmss')"
            Move-Item -LiteralPath $EnvPath -Destination $backupPath -Force
            Write-Host "[serve]   WARNING: mobile .env was too large; moved to $backupPath"
            [System.IO.File]::WriteAllLines($EnvPath, @(
                "EXPO_PUBLIC_API_BASE_URL=$ApiUrl",
                "EXPO_PUBLIC_APP_ENV=local"
            ))
            return
        }

        $lines = Get-Content $EnvPath
        $updated = $false
        $lines = $lines | ForEach-Object {
            if ($_ -match "^EXPO_PUBLIC_API_BASE_URL=") {
                $updated = $true
                "EXPO_PUBLIC_API_BASE_URL=$ApiUrl"
            } else {
                $_
            }
        }

        if (-not $updated) {
            $lines += "EXPO_PUBLIC_API_BASE_URL=$ApiUrl"
        }

        [System.IO.File]::WriteAllLines($EnvPath, $lines)
        return
    }

    [System.IO.File]::WriteAllLines($EnvPath, @(
        "EXPO_PUBLIC_API_BASE_URL=$ApiUrl",
        "EXPO_PUBLIC_APP_ENV=local"
    ))
}

# --- Helper: start ngrok, wait for tunnel URL, update mobile-ui-lab/.env, return process ---

function Start-Ngrok {
    # Kill any stale ngrok on port 4040
    Stop-Process -Name ngrok -Force -ErrorAction SilentlyContinue
    Start-Sleep 1

    Write-Host "[tunnel]  Starting ngrok..."
    $proc = Start-Process -FilePath $NgrokCmd.Source `
        -ArgumentList "http", "8000", "--log=stdout" `
        -PassThru -NoNewWindow `
        -RedirectStandardOutput $NgrokLog `
        -RedirectStandardError  $NgrokErrLog

    # Poll ngrok local API until tunnel URL appears (up to 20s)
    $url = ""
    for ($i = 1; $i -le 20; $i++) {
        Start-Sleep 1
        try {
            $api = Invoke-RestMethod "http://localhost:4040/api/tunnels" -ErrorAction Stop
            $url = ($api.tunnels | Where-Object { $_.proto -eq "https" } | Select-Object -First 1).public_url
            if ($url) { break }
        } catch {}
    }

    if (-not $url) {
        Write-Host "[tunnel]  WARNING: Could not get ngrok tunnel URL. Will retry next cycle."
        return $proc
    }

    # Update mobile-ui-lab/.env
    $apiUrl  = "$url/api/v1"
    Set-ExpoApiBaseUrl -EnvPath $MobileUiLabEnv -ApiUrl $apiUrl

    Write-Host ""
    Write-Host "  >> Tunnel:             $url"
    Write-Host "  >> mobile-ui-lab/.env: EXPO_PUBLIC_API_BASE_URL=$apiUrl"
    Write-Host ""

    return $proc
}

# --- Initial start ---

$Uvicorn = Start-Uvicorn
Start-Sleep 2
$Ngrok = Start-Ngrok

Write-Host "[serve]   Running with auto-restart -- press Ctrl+C to stop"

# --- Watch loop: restart whichever process dies ---

try {
    while ($true) {
        Start-Sleep 3

        if ($Uvicorn.HasExited) {
            Write-Host "[backend] Process exited (code $($Uvicorn.ExitCode)). Restarting..."
            Start-Sleep 2
            $Uvicorn = Start-Uvicorn
            Start-Sleep 2
        }

        if ($Ngrok.HasExited) {
            Write-Host "[tunnel]  ngrok exited. Restarting..."
            $Ngrok = Start-Ngrok
        }
    }
} finally {
    Stop-Process -Id $Uvicorn.Id -Force -ErrorAction SilentlyContinue
    Stop-Process -Id $Ngrok.Id  -Force -ErrorAction SilentlyContinue
    Write-Host "Shutdown complete."
}
