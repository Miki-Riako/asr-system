# ASR System with Hotword Prediction - Build Script (PowerShell)

# Color definitions
$Green = 'Green'
$Blue = 'Cyan'
$Red = 'Red'
$Yellow = 'Yellow'

Write-Host "=== ASR System with Hotword Prediction - Build Script ===" -ForegroundColor $Blue
Write-Host "=== Starting build process... ===" -ForegroundColor $Blue

# Create virtual environment
Write-Host ">>> Creating Python virtual environment..." -ForegroundColor $Green
python -m venv venv
if (-not $?) {
    Write-Host "Failed to create virtual environment! Please make sure Python 3.6+ is installed." -ForegroundColor $Red
    exit 1
}

# Activate virtual environment
Write-Host ">>> Activating Python virtual environment..." -ForegroundColor $Green
.\venv\Scripts\Activate.ps1
if (-not $?) {
    Write-Host "Failed to activate virtual environment!" -ForegroundColor $Red
    exit 1
}

# Create upload directory
Write-Host ">>> Creating necessary directories..." -ForegroundColor $Green
New-Item -ItemType Directory -Force -Path .\asr_system_backend\uploads | Out-Null

# Install backend dependencies
Write-Host ">>> Installing backend dependencies..." -ForegroundColor $Green
Push-Location .\asr_system_backend
pip install -r requirements.txt
if (-not $?) {
    Write-Host "Failed to install backend dependencies!" -ForegroundColor $Red
    Pop-Location
    exit 1
}
Pop-Location

# Install frontend dependencies
Write-Host ">>> Installing frontend dependencies..." -ForegroundColor $Green
Push-Location .\asr_system_frontend
npm install
if (-not $?) {
    Write-Host "Failed to install frontend dependencies! You may need to install Node.js first." -ForegroundColor $Red
    Pop-Location
    exit 1
}
Pop-Location

# Run database migrations
Write-Host ">>> Initializing database..." -ForegroundColor $Green
Push-Location .\asr_system_backend
python -c "from app.database import Base, engine; Base.metadata.create_all(bind=engine)"
if (-not $?) {
    Write-Host "Database initialization failed!" -ForegroundColor $Red
    Pop-Location
    exit 1
}

$env:PYTHONPATH = "$($env:PYTHONPATH);$(Get-Location)"
alembic upgrade head
if (-not $?) {
    Write-Host "Database migration failed!" -ForegroundColor $Red
    Pop-Location
    exit 1
}
Pop-Location

Write-Host "=== Build completed successfully! ===" -ForegroundColor $Blue
Write-Host "=== Use .\run.ps1 to start the application ===" -ForegroundColor $Blue 