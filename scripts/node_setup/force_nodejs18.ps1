# PowerShell script to force Node.js 18 for frontend installation
# This is a more aggressive approach to bypass Node.js versioning issues

# Show current Node.js situation
Write-Host "Current Node.js environment:"
where.exe node
Write-Host "Current Node.js version: $(node --version)"

# Check if Node.js 18 is already installed via fnm
if (Test-Path "$env:APPDATA\fnm\node-versions\v18.19.1") {
    Write-Host "Node.js 18.19.1 is already installed via fnm"
} else {
    Write-Host "Node.js 18.19.1 is not installed via fnm"
    
    # Suggest downloading Node.js 18 directly
    Write-Host "Please download and install Node.js 18 from https://nodejs.org/download/release/v18.19.1/"
    Read-Host "Press Enter after installing Node.js 18 to continue"
}

# Force NODE_OPTIONS to bypass compatibility checks
$env:NODE_OPTIONS="--no-warnings"

# Create a temporary batch file to modify environment and run npm
$TempFile = "$env:TEMP\run_with_node18.bat"
$scriptPath = $MyInvocation.MyCommand.Path
$scriptDir = Split-Path -Parent $scriptPath

# Create the batch file content
@"
@echo off
echo Setting up temporary Node.js 18 environment...

:: Unset problematic variables
set NODE_PATH=
set COREPACK_ROOT=
set COREPACK_HOME=

:: If using fnm, try to use its Node.js 18 installation
if exist "%APPDATA%\fnm\node-versions\v18.19.1\installation" (
    echo Using fnm's Node.js 18 installation
    set PATH=%APPDATA%\fnm\node-versions\v18.19.1\installation;%PATH%
) else if exist "%APPDATA%\nvm\v18.19.1" (
    echo Using nvm's Node.js 18 installation
    set PATH=%APPDATA%\nvm\v18.19.1;%PATH%
)

:: Show which node we're using
echo Using Node.js from:
where node
echo Node.js version:
node --version

:: Set some bypasses for npm
set NODE_OPTIONS=--no-warnings

:: Navigate to frontend directory
cd "$scriptDir\frontend"

:: Remove old installation
if exist node_modules rmdir /s /q node_modules
if exist package-lock.json del package-lock.json

:: Install using npm (bypassing pnpm completely)
echo Installing frontend dependencies with npm...
call npm install --legacy-peer-deps --no-fund --no-audit

:: Run the dev server
echo Starting frontend server...
call npm run dev

"@ | Out-File -FilePath $TempFile -Encoding ascii

Write-Host "Created temporary batch file to run with Node.js 18"
Write-Host "Executing..."

# Execute the batch file
Start-Process "cmd.exe" -ArgumentList "/c $TempFile" -NoNewWindow -Wait