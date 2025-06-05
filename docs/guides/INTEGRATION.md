# Telogical Chatbot Integration Guide

This document explains how to run the integrated Telogical Chatbot system, which consists of a backend API service and a Next.js frontend.

## System Architecture

The system consists of two main components:

1. **Backend**: A FastAPI service that connects to AI models and provides chat functionality
2. **Frontend**: A Next.js web application that provides the user interface

## Setup and Configuration

### 1. Configure the Backend

Ensure the backend's `.env` file has the necessary environment variables:

```
# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY=your_key_here
AZURE_OPENAI_ENDPOINT=your_endpoint_here
AZURE_OPENAI_DEPLOYMENT_MAP={"gpt-4o": "your_deployment_name", "gpt-4o-mini": "your_deployment_name"}

# Database Configuration
DATABASE_TYPE=postgres
POSTGRES_USER=postgres_user
POSTGRES_PASSWORD=postgres_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=chatbot

# Web server configuration
HOST=0.0.0.0
PORT=8081
```

### 2. Configure the Frontend

Ensure the frontend's `.env.local` file has the following configuration:

```
# Telogical Backend Configuration
USE_TELOGICAL_BACKEND=true
TELOGICAL_API_URL=http://localhost:8081
```

## Running the System

### 1. Start the Backend Service

```bash
cd /path/to/project
python backend/run_service.py
```

This will start the FastAPI server at http://localhost:8081.

### 2. Start the Frontend Development Server

```bash
cd /path/to/project/frontend
pnpm install  # Only needed first time
pnpm dev
```

This will start the Next.js development server, typically at http://localhost:3000.

## How the Integration Works

The integration connects the frontend to the backend through a custom adapter layer:

1. **API Adapter**: `frontend/lib/api/telogical-adapter.ts` converts between the frontend's AI SDK format and the backend's API format.

2. **Custom Provider**: `frontend/lib/ai/telogical-provider.ts` implements the AI SDK provider interface to work with the Telogical backend.

3. **Provider Configuration**: `frontend/lib/ai/providers.ts` is modified to use the Telogical provider when `USE_TELOGICAL_BACKEND=true`.

4. **Model Definitions**: `frontend/lib/ai/models.ts` is updated to include the Telogical AI models.

## Functionality

When a user sends a message in the frontend:

1. The message is sent to the Telogical backend API.
2. The backend processes the message through the appropriate AI agent.
3. The response is streamed back to the frontend.
4. The frontend displays the response, including reasoning steps and tool calls.

## Troubleshooting

### Backend Issues

- Ensure the backend service is running on the correct port (8081).
- Check backend logs for any errors related to missing environment variables or API key issues.
- Verify that the database connection is properly configured.

### Frontend Issues

- Make sure `USE_TELOGICAL_BACKEND=true` is set in the `.env.local` file.
- Check that `TELOGICAL_API_URL` is pointing to the correct backend URL.
- If there are connection issues, check network settings and CORS configuration.
- Look for errors in the browser console.

## Next Steps

- **Authentication**: Implement shared authentication between frontend and backend.
- **CORS Configuration**: Configure backend CORS settings for production deployment.
- **Error Handling**: Enhance error handling for various failure scenarios.
- **Deployment**: Create deployment configuration for production environments.