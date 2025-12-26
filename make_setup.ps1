$ErrorActionPreference = "Stop"

# Path to Inno Setup Compiler (Standard Install Path)
$ISCC = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"

# Check if the build exists first
if (-not (Test-Path "dist\windows\HackerStation\HackerStation.exe")) {
    Write-Error "Error: Build not found! Please run '.\build.ps1' first."
}

if (Test-Path $ISCC) {
    Write-Host "Creating Installer..."
    & $ISCC "setup.iss"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "------------------------------------------------"
        Write-Host "SUCCESS! Installer created at:"
        Write-Host "dist/HackerStation-Setup.exe"
        Write-Host "------------------------------------------------"
    } else {
        Write-Error "Inno Setup Compiler failed."
    }
} else {
    Write-Error "Inno Setup not found at default location ($ISCC). Please install it."
}