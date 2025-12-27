$ErrorActionPreference = "Stop"

Write-Host "1. Cleaning old builds..."
if (Test-Path "dist") { Remove-Item "dist" -Recurse -Force }
if (Test-Path "build") { Remove-Item "build" -Recurse -Force }

Write-Host "2. Building Executable with PyInstaller..."
# Changed name to HNStation to avoid AV flags
pyinstaller --noconfirm --onedir --windowed --clean `
    --name "HNStation" `
    --icon "assets/hn.ico" `
    --add-data "assets;assets" `
    --distpath "dist/windows" `
    main.py

Write-Host "------------------------------------------------"
Write-Host "Build Complete! You can test the app at:"
Write-Host "dist/windows/HNStation/HNStation.exe"
Write-Host ""
Write-Host "To create the installer, run: .\make_setup.ps1"
Write-Host "------------------------------------------------"