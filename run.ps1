# ASR System with Hotword Prediction - Run Script (PowerShell)

# Color definitions
$Green = 'Green'
$Blue = 'Cyan'
$Red = 'Red'
$Yellow = 'Yellow'

# Process tracking files
$BackendInfoFile = ".backend_info.txt"
$FrontendInfoFile = ".frontend_info.txt"

function Start-Services {
    Write-Host "=== ASR System with Hotword Prediction - Run Script ===" -ForegroundColor $Blue
    
    # Check if already running
    if (Test-Path $BackendInfoFile) {
        Write-Host "Backend service appears to be already running. Please stop services first." -ForegroundColor $Red
        return
    }
    
    if (Test-Path $FrontendInfoFile) {
        Write-Host "Frontend service appears to be already running. Please stop services first." -ForegroundColor $Red
        return
    }
    
    # Activate virtual environment
    Write-Host ">>> Activating Python virtual environment..." -ForegroundColor $Green
    .\venv\Scripts\Activate.ps1
    
    # Start backend service
    Write-Host ">>> Starting backend service..." -ForegroundColor $Green
    Push-Location .\asr_system_backend
    $backendProcess = Start-Process -FilePath "cmd.exe" -ArgumentList "/c", "uvicorn app.main:app --reload --host 0.0.0.0 --port 8000" -NoNewWindow -PassThru -RedirectStandardOutput "..\backend.log" -RedirectStandardError "..\backend_error.log"
    $backendPID = $backendProcess.Id
    "$backendPID" | Out-File -FilePath "..\$BackendInfoFile"
    Pop-Location
    
    # Start frontend service
    Write-Host ">>> Starting frontend service..." -ForegroundColor $Green
    Push-Location .\asr_system_frontend
    $frontendProcess = Start-Process -FilePath "cmd.exe" -ArgumentList "/c", "npm run dev" -NoNewWindow -PassThru -RedirectStandardOutput "..\frontend.log" -RedirectStandardError "..\frontend_error.log"
    $frontendPID = $frontendProcess.Id
    "$frontendPID" | Out-File -FilePath "..\$FrontendInfoFile"
    Pop-Location
    
    Write-Host "=== Services started successfully! ===" -ForegroundColor $Blue
    Write-Host "Backend service running at: http://localhost:8000" -ForegroundColor $Green
    Write-Host "Frontend service running at: http://localhost:5173" -ForegroundColor $Green
    Write-Host "API Documentation: http://localhost:8000/docs" -ForegroundColor $Green
    Write-Host "=== Use .\run.ps1 logs to view logs ===" -ForegroundColor $Blue
    Write-Host "=== Use .\run.ps1 stop to stop services ===" -ForegroundColor $Blue
}

function Stop-AppServices {
    Write-Host "=== Stopping services... ===" -ForegroundColor $Blue
    
    # Stop backend
    if (Test-Path $BackendInfoFile) {
        $backendPID = Get-Content $BackendInfoFile
        Write-Host ">>> Stopping backend service (PID: $backendPID)..." -ForegroundColor $Green
        
        try {
            Stop-Process -Id $backendPID -Force -ErrorAction SilentlyContinue
            Remove-Item $BackendInfoFile -Force
        } catch {
            Write-Host "Failed to stop backend service: $_" -ForegroundColor $Yellow
        }
    } else {
        Write-Host "Backend service PID file not found. Service might not be running." -ForegroundColor $Yellow
    }
    
    # Stop frontend
    if (Test-Path $FrontendInfoFile) {
        $frontendPID = Get-Content $FrontendInfoFile
        Write-Host ">>> Stopping frontend service (PID: $frontendPID)..." -ForegroundColor $Green
        
        try {
            Stop-Process -Id $frontendPID -Force -ErrorAction SilentlyContinue
            Remove-Item $FrontendInfoFile -Force
        } catch {
            Write-Host "Failed to stop frontend service: $_" -ForegroundColor $Yellow
        }
    } else {
        Write-Host "Frontend service PID file not found. Service might not be running." -ForegroundColor $Yellow
    }
    
    # Find and terminate potentially existing Node and Python processes
    Write-Host ">>> Cleaning up any remaining processes..." -ForegroundColor $Green
    
    try {
        # Find potential node processes (vite)
        $nodeProcesses = Get-Process -Name "node" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -match "vite" }
        foreach ($process in $nodeProcesses) {
            Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
            Write-Host "Terminated frontend Node process (PID: $($process.Id))" -ForegroundColor $Green
        }
        
        # Find potential python processes (uvicorn)
        $pythonProcesses = Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -match "uvicorn" }
        foreach ($process in $pythonProcesses) {
            Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
            Write-Host "Terminated backend Python process (PID: $($process.Id))" -ForegroundColor $Green
        }
    } catch {
        Write-Host "Error cleaning up remaining processes: $_" -ForegroundColor $Yellow
    }
    
    Write-Host "=== Services stopped ===" -ForegroundColor $Blue
}

function Show-Logs {
    param (
        [string]$LogType
    )
    
    switch ($LogType) {
        "backend" {
            Write-Host "=== Showing backend logs (Press Ctrl+C to exit) ===" -ForegroundColor $Blue
            Get-Content -Path "backend.log" -Wait
        }
        "frontend" {
            Write-Host "=== Showing frontend logs (Press Ctrl+C to exit) ===" -ForegroundColor $Blue
            Get-Content -Path "frontend.log" -Wait
        }
        default {
            Write-Host "=== Showing backend logs (Check new window for frontend logs) ===" -ForegroundColor $Blue
            Start-Process PowerShell -ArgumentList "-Command", "Get-Content -Path 'frontend.log' -Wait"
            Get-Content -Path "backend.log" -Wait
        }
    }
}

# Main command handling
switch ($args[0]) {
    "stop" {
        Stop-AppServices
    }
    "logs" {
        Show-Logs -LogType $args[1]
    }
    default {
        Start-Services
    }
}
 