# Telogical Chatbot

An AI assistant for telecom market intelligence, integrating a Python backend with a Next.js frontend.

## Overview

This project combines:
- A Python backend with specialized AI agents for telecom market intelligence
- A Next.js frontend with a modern chatbot interface

## Documentation

- [Installation and Running Guide](docs/guides/INSTALLATION_AND_RUNNING.md) - Setup and run the system
- [Integration Guide](docs/guides/INTEGRATION.md) - How the frontend and backend connect
- [Docker Guide](docs/guides/Docker.md) - Run the system using Docker
- [Database Guide](docs/DATABASE_GUIDE.md) - PostgreSQL database management and SQL operations

## Deployment

Deploy your Telogical Chatbot to production using one of our comprehensive deployment guides:

- [🐳 Docker Production Deployment](docs/deployment/DOCKER_PRODUCTION_DEPLOYMENT.md) - Self-hosted Docker deployment with SSL and reverse proxy
- [🚀 Deploy to Render](docs/deployment/RENDER_DEPLOYMENT.md) - Full-stack deployment on Render with PostgreSQL
- [🚀 Deploy to Microsoft Azure](docs/deployment/AZURE_DEPLOYMENT.md) - Enterprise deployment with Azure App Service and Container Instances  
- [🚀 Deploy to Vercel](docs/deployment/VERCEL_DEPLOYMENT.md) - Deploy frontend to Vercel with separate backend

## Quick Start

### Running with Docker (Recommended for First-time Setup)

The easiest way to get started is with Docker:

```bash
# Clone the repository
git clone <repository-url>
cd Telogical_Chatbot

# Run with Docker Compose using the helper script
.\scripts\run_docker_dev.ps1  # For Windows PowerShell (development mode)
./scripts/run_docker_dev.sh   # For Linux/macOS (development mode)
```

Visit http://localhost:3000 to access the frontend.

### Manual Setup

If you prefer manual setup, follow the detailed [Installation and Running Guide](docs/guides/INSTALLATION_AND_RUNNING.md).

## Fixing Node.js Version Issues

If you encounter Node.js version issues with the frontend (which requires Node.js 18), use our helper scripts:

```bash
# For Windows
.\scripts\node_setup\fix_nodejs.ps1

# For Linux/macOS
./scripts/node_setup/fix_nodejs.sh
```

## License

See the [LICENSE](LICENSE) file for details.