#!/bin/bash

# Bash script to run Docker Compose for Telogical Chatbot

# Get the project root directory
SCRIPT_DIR="$(dirname "$0")"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Define the docker-compose file path
COMPOSE_FILE="$PROJECT_ROOT/docker/compose.yml"
ENV_FILE="$PROJECT_ROOT/.env"

# Print information
echo "Starting Docker Compose for Telogical Chatbot..."
echo "Project root: $PROJECT_ROOT"
echo "Docker Compose file: $COMPOSE_FILE"
echo "Environment file: $ENV_FILE"

# Check if .env file exists
if [ ! -f "$ENV_FILE" ]; then
    echo "Error: .env file not found at $ENV_FILE"
    exit 1
fi

# Build and run Docker Compose with environment file
echo -e "\nBuilding and running Docker Compose..."
docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up --build