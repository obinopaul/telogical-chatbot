#!/bin/bash
# Azure Deployment Script for Telogical Chatbot
# This script automates the entire Azure deployment process
#
# Prerequisites:
# 1. Azure CLI installed and logged in (az login)
# 2. Docker installed
# 3. All environment variables set in azure-env-backend.txt and azure-env-frontend.txt
#
# Usage: ./azure-deploy.sh

set -e  # Exit on any error

# Configuration
RESOURCE_GROUP="telogical-rg"
LOCATION="East US"
REGISTRY_NAME="telogicalregistry"
POSTGRES_SERVER="telogical-postgres"
POSTGRES_ADMIN="telogical_admin"
POSTGRES_PASSWORD="YourSecurePassword123!"
DATABASE_NAME="telogical_prod"

echo "🚀 Starting Azure deployment for Telogical Chatbot..."

# Step 1: Create Resource Group
echo "📦 Creating resource group..."
az group create \
  --name $RESOURCE_GROUP \
  --location "$LOCATION"

# Step 2: Create Azure Container Registry
echo "🐳 Creating Azure Container Registry..."
az acr create \
  --resource-group $RESOURCE_GROUP \
  --name $REGISTRY_NAME \
  --sku Basic \
  --admin-enabled true

echo "🔑 Logging into Azure Container Registry..."
az acr login --name $REGISTRY_NAME

# Step 3: Create PostgreSQL Database
echo "🗄️ Creating PostgreSQL Flexible Server..."
az postgres flexible-server create \
  --resource-group $RESOURCE_GROUP \
  --name $POSTGRES_SERVER \
  --location "$LOCATION" \
  --admin-user $POSTGRES_ADMIN \
  --admin-password "$POSTGRES_PASSWORD" \
  --sku-name Standard_B1ms \
  --tier Burstable \
  --public-access 0.0.0.0 \
  --storage-size 32 \
  --version 16

echo "📋 Creating database..."
az postgres flexible-server db create \
  --resource-group $RESOURCE_GROUP \
  --server-name $POSTGRES_SERVER \
  --database-name $DATABASE_NAME

echo "🔥 Configuring firewall rules..."
az postgres flexible-server firewall-rule create \
  --resource-group $RESOURCE_GROUP \
  --name $POSTGRES_SERVER \
  --rule-name allow-azure-services \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 0.0.0.0

# Step 4: Build and Push Docker Images
echo "🏗️ Building backend Docker image..."
docker build -f docker/Dockerfile.backend -t $REGISTRY_NAME.azurecr.io/telogical-backend:latest .

echo "📤 Pushing backend image to registry..."
docker push $REGISTRY_NAME.azurecr.io/telogical-backend:latest

echo "🏗️ Building frontend Docker image..."
docker build -f docker/Dockerfile.frontend -t $REGISTRY_NAME.azurecr.io/telogical-frontend:latest .

echo "📤 Pushing frontend image to registry..."
docker push $REGISTRY_NAME.azurecr.io/telogical-frontend:latest

# Step 5: Get ACR credentials
echo "🔐 Getting container registry credentials..."
ACR_LOGIN_SERVER=$(az acr show --name $REGISTRY_NAME --resource-group $RESOURCE_GROUP --query loginServer --output tsv)
ACR_USERNAME=$(az acr credential show --name $REGISTRY_NAME --resource-group $RESOURCE_GROUP --query username --output tsv)
ACR_PASSWORD=$(az acr credential show --name $REGISTRY_NAME --resource-group $RESOURCE_GROUP --query passwords[0].value --output tsv)

# Step 6: Deploy Backend Container
echo "🚀 Deploying backend container..."
az container create \
  --resource-group $RESOURCE_GROUP \
  --name telogical-backend \
  --image $REGISTRY_NAME.azurecr.io/telogical-backend:latest \
  --registry-login-server $ACR_LOGIN_SERVER \
  --registry-username $ACR_USERNAME \
  --registry-password $ACR_PASSWORD \
  --dns-name-label telogical-backend \
  --ports 8081 \
  --environment-variables-file azure-env-backend.txt \
  --cpu 1 \
  --memory 2 \
  --location "$LOCATION"

# Step 7: Get backend URL and update frontend environment
echo "🔗 Getting backend URL..."
BACKEND_URL=$(az container show --resource-group $RESOURCE_GROUP --name telogical-backend --query ipAddress.fqdn --output tsv)

# Update frontend environment file with actual backend URL
sed -i.bak "s|TELOGICAL_API_URL=.*|TELOGICAL_API_URL=https://$BACKEND_URL:8081|" azure-env-frontend.txt

# Step 8: Deploy Frontend Container
echo "🚀 Deploying frontend container..."
az container create \
  --resource-group $RESOURCE_GROUP \
  --name telogical-frontend \
  --image $REGISTRY_NAME.azurecr.io/telogical-frontend:latest \
  --registry-login-server $ACR_LOGIN_SERVER \
  --registry-username $ACR_USERNAME \
  --registry-password $ACR_PASSWORD \
  --dns-name-label telogical-frontend \
  --ports 3000 \
  --environment-variables-file azure-env-frontend.txt \
  --cpu 1 \
  --memory 1.5 \
  --location "$LOCATION"

# Step 9: Get deployment URLs
echo "🎉 Deployment completed successfully!"
echo ""
echo "📋 Deployment Summary:"
echo "====================="
BACKEND_URL=$(az container show --resource-group $RESOURCE_GROUP --name telogical-backend --query ipAddress.fqdn --output tsv)
FRONTEND_URL=$(az container show --resource-group $RESOURCE_GROUP --name telogical-frontend --query ipAddress.fqdn --output tsv)
POSTGRES_URL=$(az postgres flexible-server show-connection-string --server-name $POSTGRES_SERVER --database-name $DATABASE_NAME --admin-user $POSTGRES_ADMIN --query connectionStrings.psql_cmd --output tsv)

echo "🌐 Frontend URL: https://$FRONTEND_URL:3000"
echo "🔧 Backend URL: https://$BACKEND_URL:8081"
echo "🗄️ Database: $POSTGRES_SERVER.postgres.database.azure.com"
echo ""
echo "✅ Next Steps:"
echo "1. Update Google OAuth settings with these URLs"
echo "2. Test the deployment at the frontend URL"
echo "3. Monitor logs in Azure Portal"
echo ""
echo "🔍 Useful Commands:"
echo "- Check backend logs: az container logs --resource-group $RESOURCE_GROUP --name telogical-backend"
echo "- Check frontend logs: az container logs --resource-group $RESOURCE_GROUP --name telogical-frontend"
echo "- Check backend health: curl https://$BACKEND_URL:8081/health"
echo "- Check frontend health: curl https://$FRONTEND_URL:3000/api/health"