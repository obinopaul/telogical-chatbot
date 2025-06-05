# PowerShell script to run Docker Compose for Telogical Chatbot

# Get the current directory
$scriptPath = $MyInvocation.MyCommand.Path
$scriptDir = Split-Path -Parent $scriptPath
$projectRoot = Split-Path -Parent $scriptDir

# Define the docker-compose file path
$composeFilePath = Join-Path $projectRoot "docker\compose.yml"
$envFilePath = Join-Path $projectRoot ".env"

# Print information
Write-Host "Starting Docker Compose for Telogical Chatbot..."
Write-Host "Project root: $projectRoot"
Write-Host "Docker Compose file: $composeFilePath"
Write-Host "Environment file: $envFilePath"

# Check if .env file exists
if (-not (Test-Path $envFilePath)) {
    Write-Host "Error: .env file not found at $envFilePath" -ForegroundColor Red
    exit 1
}

# Build and run Docker Compose with environment file
Write-Host "`nBuilding and running Docker Compose..."
docker-compose -f "$composeFilePath" --env-file "$envFilePath" up --build