# Docker Setup for Telogical Chatbot

This guide explains how to use Docker to run the Telogical Chatbot system (frontend and backend).

## Prerequisites

- [Docker](https://www.docker.com/products/docker-desktop/) installed on your system
- [Docker Compose](https://docs.docker.com/compose/install/) (usually included with Docker Desktop)

## Running with Docker

### Option 1: Development Mode (Recommended)

This mode is best for development as it mounts the source code as volumes, allowing you to make changes without rebuilding.

**For Windows (PowerShell)**
```powershell
# From the project root
.\scripts\run_docker_dev.ps1
```

**For Linux/macOS**
```bash
# From the project root
./scripts/run_docker_dev.sh
```

### Option 2: Production Mode

This mode builds the application for production use.

**For Windows (PowerShell)**
```powershell
# From the project root
.\scripts\run_docker.ps1
```

**For Linux/macOS**
```bash
# From the project root
./scripts/run_docker.sh
```

If you prefer to run Docker Compose directly:
```bash
# Development mode
docker-compose -f docker/compose.dev.yml up --build

# Production mode
docker-compose -f docker/compose.yml up --build
```

## Accessing the Application

Once the containers are running, you can access:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8081/info

## Docker Configuration

The Docker setup includes:

- `docker/compose.dev.yml` - Development mode with source code mounting
- `docker/compose.yml` - Production mode with built applications
- `docker/Dockerfile.backend` - Backend service configuration
- `docker/Dockerfile.frontend` - Frontend production build
- `docker/Dockerfile.frontend.dev` - Frontend development configuration

### Environment Variables

The Docker setup is configured to use your `.env` file directly, ensuring all your API keys and configuration settings are properly loaded. This approach:

1. **Preserves Your Configuration**: Uses your existing environment variables without modification
2. **Secures API Keys**: Keeps sensitive information in your `.env` file
3. **Simplifies Updates**: Any changes to your `.env` file are automatically picked up

Key configurations automatically loaded from your `.env` file include:

1. **Database**: Your Azure PostgreSQL database (citus)
2. **Azure OpenAI**: All API keys and endpoints
3. **Telogical Model**: Configuration for GPT models
4. **LangChain**: Tracing and API settings

## Troubleshooting

### Connection Issues

If the frontend can't connect to the backend:

1. Make sure all containers are running:
   ```bash
   docker-compose -f docker/compose.dev.yml ps
   ```

2. Check the logs for any errors:
   ```bash
   docker-compose -f docker/compose.dev.yml logs
   ```

### Python Module Import Issues

If you encounter errors about `ModuleNotFoundError: No module named 'backend'`, this is related to Python's module system. The Docker setup now includes a special launcher script that ensures the Python path is correctly set and the backend module can be imported.

### Frontend Authentication Issues

The Next.js frontend requires a database for user authentication. To simplify the integration, we've:

1. Created a mock authentication system that works without a database
2. Replaced the auth.ts file with a simplified version during Docker builds
3. Added the necessary dependencies for guest user authentication

This approach allows you to use the frontend without setting up complex user authentication systems.

### Frontend Database Issues

The frontend's Next.js framework requires PostgreSQL for its internal functionality. The Docker configuration is set up to:

1. Use your existing Azure PostgreSQL database for connection string only
2. Skip unnecessary database migrations during build
3. Provide all required database connection parameters

The `SKIP_DB_MIGRATION=true` flag prevents the frontend from trying to run migrations on your database, which is not necessary for the integration.

### Stopping the Containers

To stop the containers:

```bash
docker-compose -f docker/compose.dev.yml down
```

To remove all containers, volumes, and images:

```bash
docker-compose -f docker/compose.dev.yml down -v --rmi all
```