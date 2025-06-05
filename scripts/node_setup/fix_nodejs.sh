#!/bin/bash

# Display current Node.js information
echo "Checking Node.js installations..."
which node
echo "Current Node.js version: $(node --version)"

# Check if we have Node.js version managers
if command -v fnm &> /dev/null; then
    echo "Found fnm. Installing Node.js 18..."
    fnm install 18
    fnm use 18
    
    # Update PATH for current session
    eval "$(fnm env --use-on-cd)"
    
    echo "Now using Node.js version: $(node --version)"
elif command -v nvm &> /dev/null; then
    echo "Found nvm. Installing Node.js 18..."
    nvm install 18
    nvm use 18
    
    echo "Now using Node.js version: $(node --version)"
else
    echo "No Node.js version manager found."
    echo "Please install Node.js 18 manually from https://nodejs.org/download/release/v18.19.1/"
    read -p "Press Enter after installing Node.js 18 to continue, or type 'skip' to try anyway: " CONTINUE
    
    if [ "$CONTINUE" != "skip" ]; then
        # Refresh PATH
        source ~/.bashrc
    fi
fi

# Completely uninstall pnpm to start fresh
echo "Removing existing pnpm installation..."
npm uninstall -g pnpm
corepack disable pnpm 2>/dev/null || true

# Force disable corepack to avoid signature verification issues
echo "Installing pnpm directly..."
npm install -g pnpm@9.12.3

# Set environment variable to detect which Node.js is active
echo "After installation:"
echo "Node.js version: $(node --version)"
echo "npm version: $(npm --version)"
echo "pnpm location: $(which pnpm)"
echo "pnpm version: $(pnpm --version 2>/dev/null || echo 'Not installed properly')"

# Navigate to frontend directory
cd "$(dirname "$0")/frontend"

# Clean install with npm instead of pnpm
echo "Installing frontend dependencies with npm..."
rm -rf node_modules
rm -f package-lock.json

# Use a more stable approach with npm
echo "Using npm to install dependencies and run the frontend..."
npm install --legacy-peer-deps

# Run the frontend
echo "Starting frontend development server..."
npm run dev