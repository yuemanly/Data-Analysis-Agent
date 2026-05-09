$ErrorActionPreference = "Stop"

$RepoUrl = "https://github.com/Zafer-Liu/VizPilot_AI.git"
$ProjectName = "VizPilot_AI"
$InstallDir = Join-Path $env:USERPROFILE ".vizpilot-ai"
$ProjectDir = Join-Path $InstallDir $ProjectName

function Info($msg) {
    Write-Host "[VizPilot AI] $msg"
}

Info "Checking Python..."
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Python not found. Please install Python 3.10+ first."
}

Info "Checking Git..."
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw "Git not found. Please install Git first."
}

New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null

if (Test-Path $ProjectDir) {
    Info "Project already exists. Updating..."
    Set-Location $ProjectDir
    git pull
} else {
    Info "Cloning project..."
    git clone $RepoUrl $ProjectDir
    Set-Location $ProjectDir
}

Info "Creating virtual environment..."
python -m venv .venv

Info "Installing dependencies..."
& ".\.venv\Scripts\python.exe" -m pip install --upgrade pip
& ".\.venv\Scripts\pip.exe" install -r requirements.txt

$Launcher = Join-Path $env:USERPROFILE "vizpilot-ai.bat"

@"
@echo off
cd /d "$ProjectDir"
call ".venv\Scripts\activate.bat"
python app.py
pause
"@ | Set-Content -Encoding ASCII $Launcher

Info "Installed successfully."
Info "Start with: $Launcher"
Info "Or run:"
Info "cd $ProjectDir"
Info ".\.venv\Scripts\activate"
Info "python app.py"