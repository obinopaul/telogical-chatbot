# 🚀 **Deploying Telogical Chatbot to Microsoft Azure**

This comprehensive guide walks you through deploying your Telogical Chatbot to Microsoft Azure using Azure App Service, Azure Database for PostgreSQL, and Azure Container Instances.

## 📋 **Prerequisites**

- ✅ **Azure Account** - Sign up at [azure.microsoft.com](https://azure.microsoft.com)
- ✅ **Azure CLI** - Install from [docs.microsoft.com](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli)
- ✅ **Docker** - For container deployment
- ✅ **Google OAuth App** - For authentication
- ✅ **Azure OpenAI** - Already configured in Azure
- ✅ **GitHub Repository** - Your Telogical project

---

## 🎯 **Step 1: Azure Resource Setup**

### **1.1 Create Resource Group**
```bash
# Login to Azure
az login

# Create resource group
az group create \
  --name telogical-rg \
  --location "East US"
```

### **1.2 Create Azure Database for PostgreSQL**
```bash
# Create PostgreSQL server
az postgres flexible-server create \
  --resource-group telogical-rg \
  --name telogical-postgres \
  --location "East US" \
  --admin-user telogical_admin \
  --admin-password "YourSecurePassword123!" \
  --sku-name Standard_B1ms \
  --tier Burstable \
  --public-access 0.0.0.0 \
  --storage-size 32

# Create database
az postgres flexible-server db create \
  --resource-group telogical-rg \
  --server-name telogical-postgres \
  --database-name telogical_db
```

### **1.3 Configure Firewall Rules**
```bash
# Allow Azure services
az postgres flexible-server firewall-rule create \
  --resource-group telogical-rg \
  --name telogical-postgres \
  --rule-name AllowAzureServices \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 0.0.0.0

# Allow your IP for management
az postgres flexible-server firewall-rule create \
  --resource-group telogical-rg \
  --name telogical-postgres \
  --rule-name AllowMyIP \
  --start-ip-address YOUR_IP \
  --end-ip-address YOUR_IP
```

---

## 🎯 **Step 2: Prepare Application for Azure**

### **2.1 Create Dockerfiles**

**Frontend Dockerfile** (`frontend/Dockerfile.azure`):
```dockerfile
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

FROM node:18-alpine AS runner
WORKDIR /app

# Copy built application
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/package*.json ./
COPY --from=builder /app/node_modules ./node_modules

EXPOSE 3000
CMD ["npm", "start"]
```

**Backend Dockerfile** (`backend/Dockerfile.azure`):
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

EXPOSE 8081
CMD ["python", "-m", "uvicorn", "run_service:app", "--host", "0.0.0.0", "--port", "8081"]
```

### **2.2 Create Azure Configuration Files**

**Azure Bicep Template** (`azure/main.bicep`):
```bicep
@description('Location for all resources')
param location string = resourceGroup().location

@description('Base name for all resources')
param baseName string = 'telogical'

// App Service Plan
resource appServicePlan 'Microsoft.Web/serverfarms@2022-03-01' = {
  name: '${baseName}-plan'
  location: location
  sku: {
    name: 'B1'
    capacity: 1
  }
  kind: 'linux'
  properties: {
    reserved: true
  }
}

// Frontend App Service
resource frontendApp 'Microsoft.Web/sites@2022-03-01' = {
  name: '${baseName}-frontend'
  location: location
  properties: {
    serverFarmId: appServicePlan.id
    siteConfig: {
      linuxFxVersion: 'NODE|18-lts'
      appSettings: [
        {
          name: 'NEXTAUTH_URL'
          value: 'https://${baseName}-frontend.azurewebsites.net'
        }
        {
          name: 'USE_TELOGICAL_BACKEND'
          value: 'true'
        }
        {
          name: 'TELOGICAL_API_URL'
          value: 'https://${baseName}-backend.azurewebsites.net'
        }
      ]
    }
  }
}

// Backend App Service
resource backendApp 'Microsoft.Web/sites@2022-03-01' = {
  name: '${baseName}-backend'
  location: location
  properties: {
    serverFarmId: appServicePlan.id
    siteConfig: {
      linuxFxVersion: 'PYTHON|3.11'
    }
  }
}
```

---

## 🎯 **Step 3: Deploy Using Azure Container Instances**

### **3.1 Build and Push Docker Images**

**Create Azure Container Registry:**
```bash
# Create container registry
az acr create \
  --resource-group telogical-rg \
  --name telogicalregistry \
  --sku Basic \
  --admin-enabled true

# Get login server
az acr show \
  --name telogicalregistry \
  --query loginServer \
  --output table
```

**Build and Push Images:**
```bash
# Login to registry
az acr login --name telogicalregistry

# Build and push frontend
cd frontend
docker build -f Dockerfile.azure -t telogicalregistry.azurecr.io/telogical-frontend:latest .
docker push telogicalregistry.azurecr.io/telogical-frontend:latest

# Build and push backend
cd ../backend
docker build -f Dockerfile.azure -t telogicalregistry.azurecr.io/telogical-backend:latest .
docker push telogicalregistry.azurecr.io/telogical-backend:latest
```

### **3.2 Deploy Container Instances**

**Backend Container:**
```bash
az container create \
  --resource-group telogical-rg \
  --name telogical-backend \
  --image telogicalregistry.azurecr.io/telogical-backend:latest \
  --registry-login-server telogicalregistry.azurecr.io \
  --registry-username telogicalregistry \
  --registry-password $(az acr credential show --name telogicalregistry --query "passwords[0].value" -o tsv) \
  --dns-name-label telogical-backend-unique \
  --ports 8081 \
  --environment-variables \
    POSTGRES_URL="postgresql://telogical_admin:YourSecurePassword123!@telogical-postgres.postgres.database.azure.com:5432/telogical_db" \
    AZURE_OPENAI_ENDPOINT="https://your-openai-resource.openai.azure.com/" \
    AZURE_OPENAI_API_KEY="your-api-key"
```

**Frontend Container:**
```bash
az container create \
  --resource-group telogical-rg \
  --name telogical-frontend \
  --image telogicalregistry.azurecr.io/telogical-frontend:latest \
  --registry-login-server telogicalregistry.azurecr.io \
  --registry-username telogicalregistry \
  --registry-password $(az acr credential show --name telogicalregistry --query "passwords[0].value" -o tsv) \
  --dns-name-label telogical-frontend-unique \
  --ports 3000 \
  --environment-variables \
    NEXTAUTH_URL="https://telogical-frontend-unique.eastus.azurecontainer.io" \
    POSTGRES_URL="postgresql://telogical_admin:YourSecurePassword123!@telogical-postgres.postgres.database.azure.com:5432/telogical_db" \
    TELOGICAL_API_URL="https://telogical-backend-unique.eastus.azurecontainer.io:8081" \
    NEXTAUTH_SECRET="your-32-character-secret" \
    GOOGLE_CLIENT_ID="your-google-client-id" \
    GOOGLE_CLIENT_SECRET="your-google-client-secret"
```

---

## 🎯 **Step 4: Deploy Using Azure App Service (Alternative)**

### **4.1 Create App Service Plans**
```bash
# Create App Service Plan
az appservice plan create \
  --name telogical-plan \
  --resource-group telogical-rg \
  --sku B1 \
  --is-linux
```

### **4.2 Create Web Apps**
```bash
# Create backend web app
az webapp create \
  --resource-group telogical-rg \
  --plan telogical-plan \
  --name telogical-backend-app \
  --runtime "PYTHON:3.11"

# Create frontend web app  
az webapp create \
  --resource-group telogical-rg \
  --plan telogical-plan \
  --name telogical-frontend-app \
  --runtime "NODE:18-lts"
```

### **4.3 Configure App Settings**
```bash
# Backend app settings
az webapp config appsettings set \
  --resource-group telogical-rg \
  --name telogical-backend-app \
  --settings \
    POSTGRES_URL="postgresql://telogical_admin:YourSecurePassword123!@telogical-postgres.postgres.database.azure.com:5432/telogical_db" \
    AZURE_OPENAI_ENDPOINT="https://your-openai-resource.openai.azure.com/" \
    AZURE_OPENAI_API_KEY="your-api-key"

# Frontend app settings
az webapp config appsettings set \
  --resource-group telogical-rg \
  --name telogical-frontend-app \
  --settings \
    NEXTAUTH_URL="https://telogical-frontend-app.azurewebsites.net" \
    POSTGRES_URL="postgresql://telogical_admin:YourSecurePassword123!@telogical-postgres.postgres.database.azure.com:5432/telogical_db" \
    TELOGICAL_API_URL="https://telogical-backend-app.azurewebsites.net" \
    NEXTAUTH_SECRET="your-32-character-secret" \
    GOOGLE_CLIENT_ID="your-google-client-id" \
    GOOGLE_CLIENT_SECRET="your-google-client-secret"
```

### **4.4 Deploy Code**
```bash
# Deploy backend
cd backend
zip -r backend.zip .
az webapp deployment source config-zip \
  --resource-group telogical-rg \
  --name telogical-backend-app \
  --src backend.zip

# Deploy frontend
cd ../frontend
zip -r frontend.zip .
az webapp deployment source config-zip \
  --resource-group telogical-rg \
  --name telogical-frontend-app \
  --src frontend.zip
```

---

## 🎯 **Step 5: Database Setup**

### **5.1 Connect to PostgreSQL**
```bash
# Install PostgreSQL client
apt-get update && apt-get install postgresql-client

# Connect to database
psql "postgresql://telogical_admin:YourSecurePassword123!@telogical-postgres.postgres.database.azure.com:5432/telogical_db"
```

### **5.2 Run Database Migrations**
```sql
-- Create User table
CREATE TABLE IF NOT EXISTS "User" (
  id VARCHAR PRIMARY KEY,
  email VARCHAR(128) UNIQUE NOT NULL,
  password VARCHAR(64),
  name VARCHAR(128),
  image TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Create Chat table
CREATE TABLE IF NOT EXISTS "Chat" (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  "createdAt" TIMESTAMP NOT NULL,
  title TEXT NOT NULL,
  "userId" UUID NOT NULL,
  visibility VARCHAR DEFAULT 'private'
);

-- Create Message table
CREATE TABLE IF NOT EXISTS "Message_v2" (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  "chatId" UUID NOT NULL,
  role VARCHAR NOT NULL,
  parts JSONB NOT NULL,
  attachments JSONB NOT NULL,
  "createdAt" TIMESTAMP NOT NULL
);

-- Create QueryCache table
CREATE TABLE IF NOT EXISTS "QueryCache" (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  chat_id UUID NOT NULL,
  user_question_hash VARCHAR(64) NOT NULL,
  user_question TEXT NOT NULL,
  ai_response TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  expires_at TIMESTAMP,
  hit_count VARCHAR DEFAULT '1',
  user_id UUID NOT NULL
);

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_user_email ON "User"(email);
CREATE INDEX IF NOT EXISTS idx_chat_user_id ON "Chat"("userId");
CREATE INDEX IF NOT EXISTS idx_message_chat_id ON "Message_v2"("chatId");
CREATE INDEX IF NOT EXISTS idx_query_cache_hash ON "QueryCache"(user_question_hash);
```

### **5.3 Create Master User**
```sql
INSERT INTO "User" (id, email, password, name, created_at)
VALUES (
  '00000000-0000-0000-0000-000000000001',
  'master@telogical.com',
  'd77f599ed8ab508114bfcd6ffeeef69122f54c1239daade578d6404950a04ec3',
  'Master Admin User',
  NOW()
) ON CONFLICT (email) DO NOTHING;
```

---

## 🎯 **Step 6: Configure Google OAuth**

### **6.1 Update Google Console**
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Navigate to **APIs & Services** → **Credentials**
3. Edit your OAuth 2.0 Client
4. Add Authorized Redirect URLs:
   ```
   https://telogical-frontend-app.azurewebsites.net/api/auth/callback/google
   https://telogical-frontend-unique.eastus.azurecontainer.io/api/auth/callback/google
   ```
5. Add Authorized JavaScript Origins:
   ```
   https://telogical-frontend-app.azurewebsites.net
   https://telogical-frontend-unique.eastus.azurecontainer.io
   ```

---

## 🎯 **Step 7: Set Up Azure KeyVault (Recommended)**

### **7.1 Create Key Vault**
```bash
az keyvault create \
  --resource-group telogical-rg \
  --name telogical-keyvault \
  --location "East US"
```

### **7.2 Store Secrets**
```bash
# Store sensitive values
az keyvault secret set \
  --vault-name telogical-keyvault \
  --name "postgres-url" \
  --value "postgresql://telogical_admin:YourSecurePassword123!@telogical-postgres.postgres.database.azure.com:5432/telogical_db"

az keyvault secret set \
  --vault-name telogical-keyvault \
  --name "nextauth-secret" \
  --value "your-32-character-secret"

az keyvault secret set \
  --vault-name telogical-keyvault \
  --name "google-client-secret" \
  --value "your-google-client-secret"
```

### **7.3 Configure App Service to Use Key Vault**
```bash
# Enable managed identity
az webapp identity assign \
  --resource-group telogical-rg \
  --name telogical-frontend-app

# Grant access to Key Vault
az keyvault set-policy \
  --name telogical-keyvault \
  --object-id $(az webapp identity show --resource-group telogical-rg --name telogical-frontend-app --query principalId --output tsv) \
  --secret-permissions get
```

---

## 🎯 **Step 8: Set Up CI/CD with GitHub Actions**

### **8.1 Create GitHub Workflow**
Create `.github/workflows/azure-deploy.yml`:

```yaml
name: Deploy to Azure

on:
  push:
    branches: [ main ]
  workflow_dispatch:

env:
  AZURE_WEBAPP_NAME_FRONTEND: telogical-frontend-app
  AZURE_WEBAPP_NAME_BACKEND: telogical-backend-app
  REGISTRY_NAME: telogicalregistry

jobs:
  deploy-frontend:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Setup Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '18'
        
    - name: Install dependencies
      run: |
        cd frontend
        npm ci
        
    - name: Build application
      run: |
        cd frontend
        npm run build
        
    - name: Deploy to Azure Web App
      uses: azure/webapps-deploy@v2
      with:
        app-name: ${{ env.AZURE_WEBAPP_NAME_FRONTEND }}
        publish-profile: ${{ secrets.AZURE_WEBAPP_PUBLISH_PROFILE_FRONTEND }}
        package: ./frontend

  deploy-backend:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
        
    - name: Install dependencies
      run: |
        cd backend
        pip install -r requirements.txt
        
    - name: Deploy to Azure Web App
      uses: azure/webapps-deploy@v2
      with:
        app-name: ${{ env.AZURE_WEBAPP_NAME_BACKEND }}
        publish-profile: ${{ secrets.AZURE_WEBAPP_PUBLISH_PROFILE_BACKEND }}
        package: ./backend
```

---

## 🎯 **Step 9: Monitoring and Scaling**

### **9.1 Enable Application Insights**
```bash
# Create Application Insights
az monitor app-insights component create \
  --app telogical-insights \
  --location "East US" \
  --resource-group telogical-rg \
  --application-type web

# Get instrumentation key
az monitor app-insights component show \
  --app telogical-insights \
  --resource-group telogical-rg \
  --query instrumentationKey
```

### **9.2 Configure Auto-Scaling**
```bash
# Create auto-scale rule
az monitor autoscale create \
  --resource-group telogical-rg \
  --resource telogical-plan \
  --resource-type Microsoft.Web/serverfarms \
  --name telogical-autoscale \
  --min-count 1 \
  --max-count 3 \
  --count 1

# Add scale-out rule
az monitor autoscale rule create \
  --resource-group telogical-rg \
  --autoscale-name telogical-autoscale \
  --condition "Percentage CPU > 70 avg 5m" \
  --scale out 1
```

---

## 🛠️ **Troubleshooting**

### **Common Issues:**

#### **App Service Deployment Issues**
```bash
# Check deployment logs
az webapp log tail --resource-group telogical-rg --name telogical-frontend-app

# Restart app service
az webapp restart --resource-group telogical-rg --name telogical-frontend-app
```

#### **Database Connection Issues**
```bash
# Test database connectivity
az postgres flexible-server connect \
  --name telogical-postgres \
  --admin-user telogical_admin \
  --admin-password "YourSecurePassword123!"
```

#### **Container Instance Issues**
```bash
# Check container logs
az container logs \
  --resource-group telogical-rg \
  --name telogical-frontend

# Restart container
az container restart \
  --resource-group telogical-rg \
  --name telogical-frontend
```

---

## 🎉 **Success!**

Your Telogical Chatbot is now live on Microsoft Azure!

**URLs:**
- **Frontend**: `https://telogical-frontend-app.azurewebsites.net`
- **Backend**: `https://telogical-backend-app.azurewebsites.net`
- **Database**: Azure Database for PostgreSQL

### **Next Steps:**
- 🔒 **Set up custom domain** with Azure DNS
- 📊 **Configure monitoring** with Application Insights
- 🚀 **Optimize performance** with Azure CDN
- 🔄 **Set up backup strategy** for database
- 🛡️ **Configure security** with Azure Security Center

---

## 📞 **Support**

**Azure Resources:**
- [Azure Documentation](https://docs.microsoft.com/en-us/azure/)
- [Azure Support](https://azure.microsoft.com/en-us/support/)
- [Azure Status](https://status.azure.com/)

**Commands for Quick Access:**
```bash
# Check resource status
az resource list --resource-group telogical-rg --output table

# Monitor costs
az consumption usage list --top 10

# Clean up resources (CAUTION!)
az group delete --name telogical-rg --yes --no-wait
```

**Happy deploying!** 🚀