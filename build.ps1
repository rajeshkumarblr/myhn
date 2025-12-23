Write-Host "Starting Native Windows Build for Gemini Station..." -ForegroundColor Cyan

# Check for Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error "Python is not installed or not in PATH."
    exit 1
}

# Install Requirements
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

# Clean previous builds
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }

# Build
Write-Host "Running PyInstaller..." -ForegroundColor Yellow
pyinstaller main.py `
    --name="GeminiStation" `
    --onefile `
    --windowed `
    --clean `
    --icon="assets/gemini.ico" `
    --add-data="assets;assets" `
    --distpath="dist/windows"

if ($LASTEXITCODE -eq 0) {
    Write-Host "Build Success! Executable is located at: dist/windows/GeminiStation.exe" -ForegroundColor Green
} else {
    Write-Error "Build Failed."
}
