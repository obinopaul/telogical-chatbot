# PowerShell script to fix Node.js versioning issues

# First, let's identify all Node.js installations
Write-Host "Checking Node.js installations..."
where.exe node
Write-Host "Current Node.js version: $(node --version)"

# Get the location of fnm to work with it directly
$fnmPath = (Get-Command fnm -ErrorAction SilentlyContinue).Source
if ($fnmPath) {
    Write-Host "Found fnm at: $fnmPath"
    
    # Use fnm to install and use Node.js 18
    Write-Host "Installing Node.js 18 with fnm..."
    fnm install 18
    fnm use 18
    
    # Update PATH for current session
    $env:PATH = "$(fnm env --json | ConvertFrom-Json | Select-Object -ExpandProperty PATH)" + $env:PATH
    
    Write-Host "Now using Node.js version: $(node --version)"
}
else {
    Write-Host "fnm not found. Attempting to install Node.js 18 using other methods..."
    
    # Suggest downloading Node.js 18 directly
    Write-Host "Please download and install Node.js 18 from https://nodejs.org/download/release/v18.19.1/"
    $continue = Read-Host "Press Enter after installing Node.js 18 to continue, or type 'skip' to try anyway"
    
    if ($continue -ne "skip") {
        # Refresh environment variables after installation
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    }
}

# Completely uninstall pnpm to start fresh
Write-Host "Removing existing pnpm installation..."
npm uninstall -g pnpm
corepack disable pnpm

# Install pnpm directly with npm
Write-Host "Installing pnpm directly..."
npm install -g pnpm@9.12.3

# Set environment variable to detect which Node.js is active
Write-Host "After installation:"
Write-Host "Node.js version: $(node --version)"
Write-Host "npm version: $(npm --version)"
Write-Host "pnpm location: $(Get-Command pnpm -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source)"
Write-Host "pnpm version: $(pnpm --version)"

# Navigate to frontend directory
$scriptPath = $MyInvocation.MyCommand.Path
$scriptDir = Split-Path -Parent $scriptPath
cd "$scriptDir\frontend"

# Clean install with npm instead of pnpm
Write-Host "Installing frontend dependencies with npm..."
Remove-Item -Recurse -Force node_modules -ErrorAction SilentlyContinue
Remove-Item -Force package-lock.json -ErrorAction SilentlyContinue

# Use a more stable approach with npm
Write-Host "Using npm to install dependencies and run the frontend..."
npm install --legacy-peer-deps

# Run the frontend
Write-Host "Starting frontend development server..."
npm run dev