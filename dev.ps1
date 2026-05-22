$ErrorActionPreference = "Stop"

$Root    = Split-Path -Parent $MyInvocation.MyCommand.Definition
$Python  = Join-Path $Root "apps\backend\venv\Scripts\python.exe"

# --- Validate prerequisites ---

if (-not (Test-Path $Python)) {
    Write-Host "ERROR: Backend venv not found at: $Python"
    Write-Host "  Run: cd apps\backend && python -m venv venv && venv\Scripts\pip install -r requirements.txt"
    exit 1
}

# --- Start backend ---

Write-Host "[backend] Starting uvicorn on port 8000..."
$backend = Start-Process -FilePath $Python `
    -ArgumentList "-m", "uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000" `
    -WorkingDirectory (Join-Path $Root "apps\backend") `
    -PassThru -NoNewWindow

# --- Wait for backend to accept TCP connections on port 8000 ---

Write-Host "[backend] Waiting for port 8000 to open..."
$timeout = 60
$elapsed = 0
$ready   = $false

while ($elapsed -lt $timeout) {
    try {
        $tcp = New-Object System.Net.Sockets.TcpClient
        $tcp.Connect("127.0.0.1", 8000)
        $tcp.Close()
        $ready = $true
        break
    } catch {
        # not ready yet
    }
    Start-Sleep -Seconds 2
    $elapsed += 2
    Write-Host "[backend] Still waiting... ($elapsed s)"
}

if (-not $ready) {
    Write-Host "ERROR: Backend did not become healthy within $timeout seconds."
    Stop-Process -Id $backend.Id -Force -ErrorAction SilentlyContinue
    exit 1
}

Write-Host "[backend] Ready."

# --- Start admin ---

Write-Host "[admin]   Starting Next.js dev server..."
$admin = Start-Process -FilePath "npm" `
    -ArgumentList "run", "dev" `
    -WorkingDirectory (Join-Path $Root "apps\admin") `
    -PassThru -NoNewWindow

# --- Start mobile ---

Write-Host "[mobile]  Starting Expo..."
$mobile = Start-Process -FilePath "npm" `
    -ArgumentList "start" `
    -WorkingDirectory (Join-Path $Root "apps\mobile-ui-lab") `
    -PassThru -NoNewWindow

Write-Host ""
Write-Host "All services started."
Write-Host "  Backend : http://localhost:8000"
Write-Host "  Admin   : http://localhost:3000"
Write-Host "  Mobile  : Expo DevTools (see terminal above)"
Write-Host ""
Write-Host "Press Ctrl+C to stop all services."

try {
    # Keep script alive; wait for any process to exit unexpectedly
    while ($true) {
        foreach ($proc in @($backend, $admin, $mobile)) {
            if ($proc.HasExited) {
                Write-Host "WARNING: A process (PID $($proc.Id)) exited with code $($proc.ExitCode)."
            }
        }
        Start-Sleep -Seconds 5
    }
} finally {
    Write-Host "`n[dev] Shutting down all services..."
    foreach ($proc in @($backend, $admin, $mobile)) {
        if (-not $proc.HasExited) {
            Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
        }
    }
    Write-Host "[dev] Done."
}
