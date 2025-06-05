# Telogical Chatbot: Installation and Running Guide

This document provides detailed instructions for setting up and running the Telogical Chatbot system, consisting of a Python backend and a Next.js frontend.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Backend Setup](#backend-setup)
- [Frontend Setup](#frontend-setup)
- [Running the Complete System](#running-the-complete-system)
- [Troubleshooting](#troubleshooting)

## Prerequisites

These prerequisites must be installed before proceeding:

### Node.js Setup

#### For Windows (PowerShell)

1. **Install Node.js 18 LTS**
   
   **Option 1: Direct Download (Recommended)**
   - Visit [Node.js Downloads](https://nodejs.org/en/download/)
   - Download and install Node.js 18.x LTS for Windows
   - Follow the installation wizard, accepting the default settings

   **Option 2: Using NVM for Windows**
   ```powershell
   # Install NVM for Windows
   # Download and install from: https://github.com/coreybutler/nvm-windows/releases
   
   # After installation, open a new PowerShell window and run:
   nvm install 18.19.1
   nvm use 18.19.1
   ```

   **Option 3: Using FNM (Fast Node Manager)**
   ```powershell
   # Install FNM using winget
   winget install Schniz.fnm

   # Or install FNM using Chocolatey
   # choco install fnm
   
   # Open a new PowerShell window after installation
   fnm install 18
   fnm use 18
   ```

2. **Verify Node.js Installation**
   ```powershell
   node --version
   # Should show v18.x.x
   
   npm --version
   # Should show 9.x.x or higher
   ```

#### For Linux/macOS

1. **Install Node.js 18 LTS**
   
   **Option 1: Using FNM (Recommended)**
   ```bash
   # Install FNM
   curl -fsSL https://fnm.vercel.app/install | bash
   
   # Add to your shell profile (add to .bashrc or .zshrc)
   echo 'eval "$(fnm env --use-on-cd)"' >> ~/.bashrc
   source ~/.bashrc
   
   # Install and use Node.js 18
   fnm install 18
   fnm use 18
   ```

   **Option 2: Using NVM**
   ```bash
   # Install NVM
   curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
   
   # Add to your shell profile (add to .bashrc or .zshrc)
   source ~/.bashrc
   
   # Install and use Node.js 18
   nvm install 18
   nvm use 18
   ```

2. **Verify Node.js Installation**
   ```bash
   node --version
   # Should show v18.x.x
   
   npm --version
   # Should show 9.x.x or higher
   ```

### Python Environment Setup

#### For Windows (PowerShell)

1. **Install Python 3.9+**
   - Download and install from [Python.org](https://www.python.org/downloads/)
   - Be sure to check "Add Python to PATH" during installation

2. **Create and Activate Virtual Environment**
   ```powershell
   # Navigate to project root
   cd C:\path\to\Telogical_Chatbot
   
   # Create virtual environment
   python -m venv venv
   
   # Activate virtual environment
   .\venv\Scripts\Activate.ps1
   
   # Verify Python version
   python --version
   # Should show Python 3.9.x or higher
   ```

#### For Linux/macOS

1. **Install Python 3.9+**
   ```bash
   # For Ubuntu/Debian
   sudo apt update
   sudo apt install python3.9 python3.9-venv python3-pip
   
   # For macOS with Homebrew
   brew install python@3.9
   ```

2. **Create and Activate Virtual Environment**
   ```bash
   # Navigate to project root
   cd /path/to/Telogical_Chatbot
   
   # Create virtual environment
   python3.9 -m venv venv
   
   # Activate virtual environment
   source venv/bin/activate
   
   # Verify Python version
   python --version
   # Should show Python 3.9.x or higher
   ```

## Backend Setup

Follow these steps to set up and run the backend:

### 1. Configure Environment Variables

#### For Windows (PowerShell)

```powershell
# Navigate to project root
cd C:\path\to\Telogical_Chatbot

# Create .env file (use Set-Content instead of cat)
@"
# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY=your_key_here
AZURE_OPENAI_ENDPOINT=your_endpoint_here
AZURE_OPENAI_DEPLOYMENT_MAP={"gpt-4o": "gpt-4.1", "gpt-4o-mini": "gpt-4.1"}

# Telogical Model Configuration
TELOGICAL_API_KEY_GPT=your_key_here
TELOGICAL_MODEL_ENDPOINT_GPT=your_endpoint_here
TELOGICAL_MODEL_DEPLOYMENT_GPT=gpt-4.1
TELOGICAL_MODEL_API_VERSION_GPT=2024-12-01-preview

# Database Configuration
DATABASE_TYPE=postgres
POSTGRES_USER=postgres_user
POSTGRES_PASSWORD=your_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=chatbot

# Web server configuration
HOST=0.0.0.0
PORT=8081
"@ | Set-Content .env
```

#### For Linux/macOS

```bash
# Navigate to project root
cd /path/to/Telogical_Chatbot

# Create .env file
cat > .env << 'EOF'
# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY=your_key_here
AZURE_OPENAI_ENDPOINT=your_endpoint_here
AZURE_OPENAI_DEPLOYMENT_MAP={"gpt-4o": "gpt-4.1", "gpt-4o-mini": "gpt-4.1"}

# Telogical Model Configuration
TELOGICAL_API_KEY_GPT=your_key_here
TELOGICAL_MODEL_ENDPOINT_GPT=your_endpoint_here
TELOGICAL_MODEL_DEPLOYMENT_GPT=gpt-4.1
TELOGICAL_MODEL_API_VERSION_GPT=2024-12-01-preview

# Database Configuration
DATABASE_TYPE=postgres
POSTGRES_USER=postgres_user
POSTGRES_PASSWORD=your_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=chatbot

# Web server configuration
HOST=0.0.0.0
PORT=8081
EOF
```

### 2. Install Backend Dependencies

Make sure your virtual environment is activated before proceeding.

#### For Windows (PowerShell)

```powershell
# Ensure virtual environment is activated
# You should see (venv) at the beginning of your prompt
# If not, run: .\venv\Scripts\Activate.ps1

# Install dependencies
cd C:\path\to\Telogical_Chatbot
pip install -e .

# If the above fails, try:
pip install -r requirements.txt

# If no requirements.txt exists, install core dependencies:
pip install fastapi uvicorn langchain-openai langchain-core httpx numpy
```

#### For Linux/macOS

```bash
# Ensure virtual environment is activated
# You should see (venv) at the beginning of your prompt
# If not, run: source venv/bin/activate

# Install dependencies
cd /path/to/Telogical_Chatbot
pip install -e .

# If the above fails, try:
pip install -r requirements.txt

# If no requirements.txt exists, install core dependencies:
pip install fastapi uvicorn langchain-openai langchain-core httpx numpy
```

### 3. Run the Backend Server

#### For Windows (PowerShell)

```powershell
# Ensure virtual environment is activated
# If not, run: .\venv\Scripts\Activate.ps1

# Start the backend service
cd C:\path\to\Telogical_Chatbot
python backend\run_service.py
```

#### For Linux/macOS

```bash
# Ensure virtual environment is activated
# If not, run: source venv/bin/activate

# Start the backend service
cd /path/to/Telogical_Chatbot
python backend/run_service.py
```

Verify the backend is running by opening your browser and navigating to:
```
http://localhost:8081/info
```

You should see JSON output with information about available agents and models.

## Frontend Setup

Follow these steps to set up and run the frontend:

### 1. Configure Environment Variables

#### For Windows (PowerShell)

```powershell
# Navigate to frontend directory
cd C:\path\to\Telogical_Chatbot\frontend

# Create .env.local file
@"
# Authentication (required for the Next.js template)
AUTH_SECRET=random_secret_string_here

# Telogical Backend Configuration
USE_TELOGICAL_BACKEND=true
TELOGICAL_API_URL=http://localhost:8081
"@ | Set-Content .env.local
```

#### For Linux/macOS

```bash
# Navigate to frontend directory
cd /path/to/Telogical_Chatbot/frontend

# Create .env.local file
cat > .env.local << 'EOF'
# Authentication (required for the Next.js template)
AUTH_SECRET=random_secret_string_here

# Telogical Backend Configuration
USE_TELOGICAL_BACKEND=true
TELOGICAL_API_URL=http://localhost:8081
EOF
```

### 2. Install Frontend Dependencies

#### For Windows (PowerShell)

```powershell
# IMPORTANT: Make sure you're using Node.js v18
# Check with: node --version
# If not v18, install and use it as described in Prerequisites

# Install pnpm globally first
cd C:\path\to\Telogical_Chatbot
npm install -g pnpm@9.12.3

# Navigate to frontend directory and install dependencies
cd frontend
pnpm install --frozen-lockfile

# If you encounter errors with pnpm, try:
npm install --legacy-peer-deps
```

#### For Linux/macOS

```bash
# IMPORTANT: Make sure you're using Node.js v18
# Check with: node --version
# If not v18, install and use it as described in Prerequisites

# Install pnpm globally first
cd /path/to/Telogical_Chatbot
npm install -g pnpm@9.12.3

# Navigate to frontend directory and install dependencies
cd frontend
pnpm install --frozen-lockfile

# If you encounter errors with pnpm, try:
npm install --legacy-peer-deps
```

### 3. Run the Frontend Development Server

#### For Windows (PowerShell)

```powershell
# Navigate to frontend directory
cd C:\path\to\Telogical_Chatbot\frontend

# Start the development server
pnpm dev

# If using npm instead:
# npm run dev
```

#### For Linux/macOS

```bash
# Navigate to frontend directory
cd /path/to/Telogical_Chatbot/frontend

# Start the development server
pnpm dev

# If using npm instead:
# npm run dev
```

Access the frontend by opening your browser and navigating to:
```
http://localhost:3000
```

## Running the Complete System

To run the complete system, you need to have both the backend and frontend running simultaneously.

### Method 1: Using Separate Terminal Windows

#### Terminal 1: Run the Backend

**For Windows (PowerShell)**
```powershell
cd C:\path\to\Telogical_Chatbot
.\venv\Scripts\Activate.ps1
python backend\run_service.py
```

**For Linux/macOS**
```bash
cd /path/to/Telogical_Chatbot
source venv/bin/activate
python backend/run_service.py
```

#### Terminal 2: Run the Frontend

**For Windows (PowerShell)**
```powershell
cd C:\path\to\Telogical_Chatbot\frontend
npm run dev
```

**For Linux/macOS**
```bash
cd /path/to/Telogical_Chatbot/frontend
npm run dev
```

### Method 2: Using a Script (Optional)

#### For Windows (PowerShell)

```powershell
cd C:\path\to\Telogical_Chatbot

@"
# Start the backend
Start-Process -NoNewWindow powershell -ArgumentList "-Command `"cd '$pwd'; .\venv\Scripts\Activate.ps1; python backend\run_service.py`""

# Wait for backend to start
Start-Sleep -Seconds 5

# Start the frontend
Start-Process -NoNewWindow powershell -ArgumentList "-Command `"cd '$pwd\frontend'; npm run dev`""

Write-Host "Press Ctrl+C to stop all processes"
while ($true) { Start-Sleep -Seconds 1 }
"@ | Out-File -FilePath run_all.ps1

.\run_all.ps1
```

#### For Linux/macOS

```bash
cd /path/to/Telogical_Chatbot

cat > run_all.sh << 'EOF'
#!/bin/bash

# Start the backend
source venv/bin/activate
cd "$(dirname "$0")"
python backend/run_service.py &
BACKEND_PID=$!

# Wait for backend to start
sleep 5

# Start the frontend
cd frontend
npm run dev &
FRONTEND_PID=$!

# Handle termination
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT TERM
wait
EOF

chmod +x run_all.sh
./run_all.sh
```

### Method 3: Using Docker (Recommended for Compatibility Issues)

If you're experiencing Node.js version issues, using Docker is the most reliable method to run the frontend.

#### Prerequisites
- Install [Docker](https://www.docker.com/products/docker-desktop/)
- Install [Docker Compose](https://docs.docker.com/compose/install/) (usually included with Docker Desktop)

#### Running with Docker Compose

**For Windows (PowerShell) or Linux/macOS**
```bash
# From the project root directory
docker-compose -f docker-compose.frontend.yml up
```

This will:
1. Build a Docker container for the frontend using Node.js 18
2. Build a Docker container for the backend
3. Run both containers, connecting them together
4. Map port 3000 for the frontend and 8081 for the backend

You can then access the frontend at http://localhost:3000 and the backend at http://localhost:8081.

## Troubleshooting

### Backend Issues

1. **Port conflicts**
   
   If port 8081 is already in use:
   
   **For Windows (PowerShell)**
   ```powershell
   # Edit .env file and change PORT to another value (e.g., 8082)
   # Then restart the backend server
   ```
   
   **For Linux/macOS**
   ```bash
   # Edit .env file and change PORT to another value (e.g., 8082)
   # Then restart the backend server
   ```

2. **Database connection issues**
   
   If using PostgreSQL:
   
   **For Windows (PowerShell)**
   ```powershell
   # Edit .env to use SQLite instead
   @"
   DATABASE_TYPE=sqlite
   SQLITE_DB_PATH=checkpoints.db
   "@ | Add-Content .env
   ```
   
   **For Linux/macOS**
   ```bash
   # Edit .env to use SQLite instead
   echo "DATABASE_TYPE=sqlite" >> .env
   echo "SQLITE_DB_PATH=checkpoints.db" >> .env
   ```

3. **Missing libraries or modules**
   
   **For Windows (PowerShell)**
   ```powershell
   # Install additional dependencies as needed
   pip install langchain-anthropic langchain-openai langchain-community
   ```
   
   **For Linux/macOS**
   ```bash
   # Install additional dependencies as needed
   pip install langchain-anthropic langchain-openai langchain-community
   ```

### Frontend Issues

1. **Node.js version conflicts**
   
   The most common issue is using the wrong Node.js version. This project requires Node.js 18 because it uses React 19 RC which has compatibility issues with newer Node.js versions:
   
   #### Quick Fix Script
   
   We've provided fix scripts that will handle the Node.js versioning issues automatically:
   
   **For Windows (PowerShell)**
   ```powershell
   # Run the fix script from the project root
   cd C:\path\to\Telogical_Chatbot
   .\fix_nodejs.ps1
   
   # If that doesn't work, try the more aggressive approach:
   .\force_nodejs18.ps1
   ```
   
   **For Linux/macOS**
   ```bash
   # Run the fix script from the project root
   cd /path/to/Telogical_Chatbot
   ./fix_nodejs.sh
   ```
   
   #### Manual Fix
   
   If the script doesn't work, try these manual steps:
   
   **For Windows (PowerShell)**
   ```powershell
   # Using NVM for Windows
   nvm install 18.19.1
   nvm use 18.19.1
   
   # Or using FNM
   fnm install 18
   fnm use 18
   
   # Verify version
   node --version
   # Should show v18.x.x
   
   # Remove any existing pnpm installation
   npm uninstall -g pnpm
   corepack disable pnpm
   
   # Install pnpm directly
   npm install -g pnpm@9.12.3
   
   # Clean and reinstall frontend with npm instead
   cd C:\path\to\Telogical_Chatbot\frontend
   Remove-Item -Recurse -Force node_modules -ErrorAction SilentlyContinue
   npm install --legacy-peer-deps
   npm run dev
   ```
   
   **For Linux/macOS**
   ```bash
   # Using NVM
   nvm install 18
   nvm use 18
   
   # Or using FNM
   fnm install 18
   fnm use 18
   
   # Verify version
   node --version
   # Should show v18.x.x
   
   # Remove any existing pnpm installation
   npm uninstall -g pnpm
   corepack disable pnpm
   
   # Install pnpm directly
   npm install -g pnpm@9.12.3
   
   # Clean and reinstall frontend with npm instead
   cd /path/to/Telogical_Chatbot/frontend
   rm -rf node_modules
   npm install --legacy-peer-deps
   npm run dev
   ```

2. **"Cannot find matching keyid" error with pnpm**
   
   This error is related to corepack signature verification and usually happens when:
   - You have multiple Node.js versions installed
   - Your system is using a different Node.js version for pnpm than what you see with `node --version`
   
   **Solution:**
   ```powershell
   # For Windows
   
   # 1. Check which Node.js installations you have
   where.exe node
   
   # 2. If using fnm, make sure it's properly setting the PATH
   fnm install 18
   fnm use 18
   
   # 3. Completely remove pnpm and install it directly
   npm uninstall -g pnpm
   corepack disable pnpm
   npm install -g pnpm@9.12.3
   
   # 4. Use npm instead of pnpm for this project
   cd C:\path\to\Telogical_Chatbot\frontend
   npm install --legacy-peer-deps
   npm run dev
   ```
   
   ```bash
   # For Linux/macOS
   
   # 1. Check which Node.js installations you have
   which node
   
   # 2. If using fnm, make sure it's properly setting the PATH
   fnm install 18
   fnm use 18
   eval "$(fnm env --use-on-cd)"
   
   # 3. Completely remove pnpm and install it directly
   npm uninstall -g pnpm
   corepack disable pnpm
   npm install -g pnpm@9.12.3
   
   # 4. Use npm instead of pnpm for this project
   cd /path/to/Telogical_Chatbot/frontend
   npm install --legacy-peer-deps
   npm run dev
   ```

3. **Next.js build errors**
   
   Try running in debug mode:
   
   **For Windows (PowerShell)**
   ```powershell
   cd C:\path\to\Telogical_Chatbot\frontend
   npm run dev -- --debug
   ```
   
   **For Linux/macOS**
   ```bash
   cd /path/to/Telogical_Chatbot/frontend
   npm run dev -- --debug
   ```

### Integration Issues

1. **Backend connection refused**
   
   Check that:
   - Backend server is running on port 8081
   - Frontend's `.env.local` file has the correct backend URL
   - No firewall or network issues blocking local connections

2. **CORS errors**
   
   If you see CORS errors in the browser console, make sure the backend's middleware is configured correctly.

3. **Streaming issues**
   
   If chat streaming doesn't work:
   - Check browser console for errors
   - Verify that the backend's /stream endpoint is working
   - Test with a simple command like:
   
   **For Windows (PowerShell)**
   ```powershell
   Invoke-WebRequest -Method Post -ContentType "application/json" -Body '{"message":"hello"}' -Uri http://localhost:8081/telogical-assistant/stream
   ```
   
   **For Linux/macOS**
   ```bash
   curl -X POST -H "Content-Type: application/json" -d '{"message":"hello"}' http://localhost:8081/telogical-assistant/stream
   ```

For any other issues, check the console logs in both the backend and frontend terminals for specific error messages.

## Next Steps

Once the system is running, you can explore:

1. Adding authentication
2. Customizing the UI
3. Deploying to production
4. Adding more AI models or features