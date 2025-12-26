$ErrorActionPreference = "Stop"

Write-Host "1. Cleaning old builds..."
if (Test-Path "dist") { Remove-Item "dist" -Recurse -Force }
if (Test-Path "build") { Remove-Item "build" -Recurse -Force }

Write-Host "2. Building Executable with PyInstaller..."
# Ensure we are in the environment
pyinstaller --noconfirm --onedir --windowed --clean `
    --name "HackerStation" `
    --icon "assets/hn.ico" `
    --add-data "assets;assets" `
    --distpath "dist/windows" `
    src/hn_station.py

Write-Host "------------------------------------------------"
Write-Host "Build Complete! You can test the app at:"
Write-Host "dist/windows/HackerStation/HackerStation.exe"
Write-Host ""
Write-Host "To create the installer, run: .\make_setup.ps1"
Write-Host "------------------------------------------------"