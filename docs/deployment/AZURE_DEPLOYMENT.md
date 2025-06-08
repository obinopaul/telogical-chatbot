# 🚀 **Deploying Telogical Chatbot to Microsoft Azure**

This comprehensive guide walks you through deploying your Telogical Chatbot to Microsoft Azure using Azure Container Instances, Azure Database for PostgreSQL, and Azure Container Registry.

## 📋 **Prerequisites**

- ✅ **Azure Account** - Sign up at [azure.microsoft.com](https://azure.microsoft.com)
- ✅ **Azure CLI** - Install from [docs.microsoft.com](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli)
- ✅ **Docker** - For building container images
- ✅ **GitHub Repository** - Your Telogical project
- ✅ **Production Environment Variables** - All API keys and credentials
- ✅ **Domain Names** (Optional) - For custom domains

---

## 🎯 **Step 1: Verify Deployment Files**

✅ **All Azure deployment files are already created and ready!** Your repository includes:
```
├── azure-deploy.sh              # ← Automated deployment script
├── azure-cleanup.sh             # ← Resource cleanup script  
├── azure-env-backend.txt        # ← Backend environment template
├── azure-env-frontend.txt       # ← Frontend environment template
└── sql/init.sql                 # ← Database initialization script
```

**You can now choose between:**
- **Option A**: Automated deployment using `azure-deploy.sh` (recommended)
- **Option B**: Manual step-by-step deployment (advanced users)

---

## 🎯 **Step 2A: Automated Deployment (Recommended)**

### **2A.1 Edit Environment Files**
```bash
# Edit backend environment variables
nano azure-env-backend.txt

# Edit frontend environment variables  
nano azure-env-frontend.txt
```

### **2A.2 Run Automated Deployment**
```bash
# Make sure you're logged into Azure
az login

# Run the automated deployment script
./azure-deploy.sh
```

The script will automatically:
- Create resource group and container registry
- Set up PostgreSQL database
- Build and push Docker images
- Deploy container instances
- Configure networking and security

**Skip to Step 6 if using automated deployment.**

---

## 🎯 **Step 2B: Manual Azure Resource Setup (Advanced)**

### **1.1 Login and Create Resource Group**
```bash
# Login to Azure
az login

# Set default subscription (if you have multiple)
az account set --subscription "your-subscription-id"

# Create resource group
az group create \
  --name telogical-rg \
  --location "East US"
```

### **1.2 Create Azure Container Registry**
```bash
# Create container registry for your Docker images
az acr create \
  --resource-group telogical-rg \
  --name telogicalregistry \
  --sku Basic \
  --admin-enabled true

# Get login server
az acr show --name telogicalregistry --resource-group telogical-rg --query loginServer --output tsv

# Login to the registry
az acr login --name telogicalregistry
```

### **1.3 Create Azure Database for PostgreSQL**
```bash
# Create PostgreSQL Flexible Server
az postgres flexible-server create \
  --resource-group telogical-rg \
  --name telogical-postgres \
  --location "East US" \
  --admin-user telogical_admin \
  --admin-password "YourSecurePassword123!" \
  --sku-name Standard_B1ms \
  --tier Burstable \
  --public-access 0.0.0.0 \
  --storage-size 32 \
  --version 16

# Create database
az postgres flexible-server db create \
  --resource-group telogical-rg \
  --server-name telogical-postgres \
  --database-name telogical_prod

# Configure firewall to allow Azure services
az postgres flexible-server firewall-rule create \
  --resource-group telogical-rg \
  --name telogical-postgres \
  --rule-name allow-azure-services \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 0.0.0.0
```

---

## 🎯 **Step 2: Build and Push Container Images**

### **2.1 Build Backend Image**
```bash
# Navigate to your project directory
cd /path/to/Telogical_Chatbot

# Build backend image
docker build -f docker/Dockerfile.backend -t telogicalregistry.azurecr.io/telogical-backend:latest .

# Push to Azure Container Registry
docker push telogicalregistry.azurecr.io/telogical-backend:latest
```

### **2.2 Build Frontend Image**
```bash
# Build frontend image
docker build -f docker/Dockerfile.frontend -t telogicalregistry.azurecr.io/telogical-frontend:latest .

# Push to Azure Container Registry
docker push telogicalregistry.azurecr.io/telogical-frontend:latest
```

### **2.3 Verify Images**
```bash
# List images in registry
az acr repository list --name telogicalregistry --output table

# Show image tags
az acr repository show-tags --name telogicalregistry --repository telogical-backend --output table
az acr repository show-tags --name telogicalregistry --repository telogical-frontend --output table
```

---

## 🎯 **Step 3: Database Setup**

### **3.1 Get Database Connection String**
```bash
# Get connection string
az postgres flexible-server show-connection-string \
  --server-name telogical-postgres \
  --database-name telogical_prod \
  --admin-user telogical_admin

# Example output format:
# postgres://telogical_admin:YourSecurePassword123!@telogical-postgres.postgres.database.azure.com:5432/telogical_prod?sslmode=require
```

### **3.2 Initialize Database Schema**
```bash
# Connect to database using psql
psql "postgres://telogical_admin:YourSecurePassword123!@telogical-postgres.postgres.database.azure.com:5432/telogical_prod?sslmode=require"

# Run the following SQL commands:
```

```sql
-- Create User table for authentication
CREATE TABLE IF NOT EXISTS "User" (
  id VARCHAR PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  password VARCHAR(255),
  name VARCHAR(255),
  image TEXT,
  "createdAt" TIMESTAMP DEFAULT NOW()
);

-- Create Chat table for conversation history
CREATE TABLE IF NOT EXISTS "Chat" (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  "createdAt" TIMESTAMP NOT NULL DEFAULT NOW(),
  title TEXT NOT NULL,
  "userId" VARCHAR NOT NULL REFERENCES "User"(id),
  visibility VARCHAR DEFAULT 'private'
);

-- Create Message table for chat messages
CREATE TABLE IF NOT EXISTS "Message" (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  "chatId" UUID NOT NULL REFERENCES "Chat"(id),
  role VARCHAR NOT NULL,
  content TEXT NOT NULL,
  "createdAt" TIMESTAMP DEFAULT NOW()
);

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_user_email ON "User"(email);
CREATE INDEX IF NOT EXISTS idx_chat_user_id ON "Chat"("userId");
CREATE INDEX IF NOT EXISTS idx_chat_created_at ON "Chat"("createdAt");
CREATE INDEX IF NOT EXISTS idx_message_chat_id ON "Message"("chatId");

-- Create test user (optional)
INSERT INTO "User" (id, email, name, "createdAt")
VALUES (
  'azure-test-user-001',
  'test@telogical.com',
  'Azure Test User',
  NOW()
) ON CONFLICT (email) DO NOTHING;
```

---

## 🎯 **Step 4: Create Environment Variables**

### **4.1 Create Backend Environment File**
```bash
# Create backend environment file
cat > backend.env << 'EOF'
# Database Configuration
DATABASE_TYPE=postgres
POSTGRES_URL=postgres://telogical_admin:YourSecurePassword123!@telogical-postgres.postgres.database.azure.com:5432/telogical_prod?sslmode=require

# Server Configuration
HOST=0.0.0.0
PORT=8081
MODE=production

# AI API Keys
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key
AZURE_OPENAI_API_KEY=your-azure-openai-api-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_MAP={"gpt-4o": "your-deployment-name"}

# Telogical API Configuration
TELOGICAL_AUTH_TOKEN=your-telogical-auth-token
TELOGICAL_GRAPHQL_ENDPOINT=https://residential-api.telogical.com/graphql
TELOGICAL_AUTH_TOKEN_2=your-telogical-auth-token-2
TELOGICAL_GRAPHQL_ENDPOINT_2=https://llmapi.telogical.com/graphql

# Security
AUTH_SECRET=your-secure-random-string-here

# Monitoring (Optional)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your-langsmith-api-key
LANGCHAIN_PROJECT=telogical-azure-production
EOF
```

### **4.2 Create Frontend Environment File**
```bash
# Create frontend environment file
cat > frontend.env << 'EOF'
# Authentication
NEXTAUTH_SECRET=your-32-character-random-secret-string
NEXTAUTH_URL=https://telogical-frontend.eastus.azurecontainer.io

# Backend Connection
USE_TELOGICAL_BACKEND=true
TELOGICAL_API_URL=https://telogical-backend.eastus.azurecontainer.io

# Database Connection
POSTGRES_URL=postgres://telogical_admin:YourSecurePassword123!@telogical-postgres.postgres.database.azure.com:5432/telogical_prod?sslmode=require

# Google OAuth
GOOGLE_CLIENT_ID=your-google-oauth-client-id
GOOGLE_CLIENT_SECRET=your-google-oauth-client-secret

# Production Settings
NODE_ENV=production
EOF
```

---

## 🎯 **Step 5: Deploy Container Instances**

### **5.1 Deploy Backend Container**
```bash
# Get ACR credentials
ACR_LOGIN_SERVER=$(az acr show --name telogicalregistry --resource-group telogical-rg --query loginServer --output tsv)
ACR_USERNAME=$(az acr credential show --name telogicalregistry --resource-group telogical-rg --query username --output tsv)
ACR_PASSWORD=$(az acr credential show --name telogicalregistry --resource-group telogical-rg --query passwords[0].value --output tsv)

# Deploy backend container
az container create \
  --resource-group telogical-rg \
  --name telogical-backend \
  --image telogicalregistry.azurecr.io/telogical-backend:latest \
  --registry-login-server $ACR_LOGIN_SERVER \
  --registry-username $ACR_USERNAME \
  --registry-password $ACR_PASSWORD \
  --dns-name-label telogical-backend \
  --ports 8081 \
  --environment-variables-file backend.env \
  --cpu 1 \
  --memory 2 \
  --location "East US"
```

### **5.2 Deploy Frontend Container**
```bash
# First, update frontend.env with actual backend URL
BACKEND_URL=$(az container show --resource-group telogical-rg --name telogical-backend --query ipAddress.fqdn --output tsv)

# Update frontend environment file
sed -i "s|TELOGICAL_API_URL=.*|TELOGICAL_API_URL=https://$BACKEND_URL:8081|" frontend.env

# Deploy frontend container
az container create \
  --resource-group telogical-rg \
  --name telogical-frontend \
  --image telogicalregistry.azurecr.io/telogical-frontend:latest \
  --registry-login-server $ACR_LOGIN_SERVER \
  --registry-username $ACR_USERNAME \
  --registry-password $ACR_PASSWORD \
  --dns-name-label telogical-frontend \
  --ports 3000 \
  --environment-variables-file frontend.env \
  --cpu 1 \
  --memory 1.5 \
  --location "East US"
```

### **5.3 Verify Deployment**
```bash
# Check container status
az container show --resource-group telogical-rg --name telogical-backend --query instanceView.state --output tsv
az container show --resource-group telogical-rg --name telogical-frontend --query instanceView.state --output tsv

# Get URLs
BACKEND_URL=$(az container show --resource-group telogical-rg --name telogical-backend --query ipAddress.fqdn --output tsv)
FRONTEND_URL=$(az container show --resource-group telogical-rg --name telogical-frontend --query ipAddress.fqdn --output tsv)

echo "Backend URL: https://$BACKEND_URL:8081"
echo "Frontend URL: https://$FRONTEND_URL:3000"

# Test health endpoints
curl -f "https://$BACKEND_URL:8081/health"
curl -f "https://$FRONTEND_URL:3000/api/health"
```

---

## 🎯 **Step 6: Configure Google OAuth**

### **6.1 Update Google Console**
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Navigate to **APIs & Services** → **Credentials**
3. Edit your OAuth 2.0 Client ID
4. **Authorized JavaScript Origins:**
   ```
   https://telogical-frontend.eastus.azurecontainer.io:3000
   https://your-custom-domain.com  (if using custom domain)
   ```
5. **Authorized Redirect URIs:**
   ```
   https://telogical-frontend.eastus.azurecontainer.io:3000/api/auth/callback/google
   https://your-custom-domain.com/api/auth/callback/google  (if using custom domain)
   ```

---

## 🎯 **Step 7: Set Up Load Balancer and SSL (Optional)**

### **7.1 Create Application Gateway**
```bash
# Create public IP for Application Gateway
az network public-ip create \
  --resource-group telogical-rg \
  --name telogical-appgw-ip \
  --allocation-method Static \
  --sku Standard

# Create virtual network
az network vnet create \
  --resource-group telogical-rg \
  --name telogical-vnet \
  --address-prefix 10.0.0.0/16 \
  --subnet-name appgw-subnet \
  --subnet-prefix 10.0.1.0/24

# Create Application Gateway
az network application-gateway create \
  --resource-group telogical-rg \
  --name telogical-appgw \
  --location "East US" \
  --capacity 2 \
  --sku Standard_v2 \
  --public-ip-address telogical-appgw-ip \
  --vnet-name telogical-vnet \
  --subnet appgw-subnet \
  --servers $FRONTEND_URL:3000 $BACKEND_URL:8081
```

### **7.2 Configure SSL Certificate**
```bash
# Upload SSL certificate (if you have one)
az network application-gateway ssl-cert create \
  --resource-group telogical-rg \
  --gateway-name telogical-appgw \
  --name telogical-ssl-cert \
  --cert-file path/to/your/certificate.pfx \
  --cert-password your-cert-password

# Or use Azure managed certificate for custom domain
```

---

## 🎯 **Step 8: Monitoring and Logging**

### **8.1 Enable Container Insights**
```bash
# Create Log Analytics workspace
az monitor log-analytics workspace create \
  --resource-group telogical-rg \
  --workspace-name telogical-logs \
  --location "East US"

# Get workspace ID
WORKSPACE_ID=$(az monitor log-analytics workspace show \
  --resource-group telogical-rg \
  --workspace-name telogical-logs \
  --query customerId --output tsv)

# Update containers with logging
az container create \
  --resource-group telogical-rg \
  --name telogical-backend-monitored \
  --image telogicalregistry.azurecr.io/telogical-backend:latest \
  --log-analytics-workspace $WORKSPACE_ID \
  --log-analytics-workspace-key $(az monitor log-analytics workspace get-shared-keys --resource-group telogical-rg --workspace-name telogical-logs --query primarySharedKey --output tsv)
```

### **8.2 Set Up Application Insights**
```bash
# Create Application Insights
az monitor app-insights component create \
  --resource-group telogical-rg \
  --app telogical-insights \
  --location "East US" \
  --application-type web

# Get instrumentation key
INSIGHTS_KEY=$(az monitor app-insights component show \
  --resource-group telogical-rg \
  --app telogical-insights \
  --query instrumentationKey --output tsv)

echo "Application Insights Key: $INSIGHTS_KEY"
```

---

## 🛠️ **Troubleshooting**

### **Container Issues**
```bash
# Check container logs
az container logs --resource-group telogical-rg --name telogical-backend
az container logs --resource-group telogical-rg --name telogical-frontend

# Check container events
az container show --resource-group telogical-rg --name telogical-backend --query instanceView.events

# Restart container
az container restart --resource-group telogical-rg --name telogical-backend
```

### **Database Connection Issues**
```bash
# Test database connectivity
psql "postgres://telogical_admin:YourSecurePassword123!@telogical-postgres.postgres.database.azure.com:5432/telogical_prod?sslmode=require" -c "SELECT 1;"

# Check firewall rules
az postgres flexible-server firewall-rule list \
  --resource-group telogical-rg \
  --name telogical-postgres
```

### **Image Registry Issues**
```bash
# Check registry access
az acr check-health --name telogicalregistry

# List repositories
az acr repository list --name telogicalregistry

# Check image details
az acr repository show --name telogicalregistry --repository telogical-backend
```

---

## 📊 **Performance and Scaling**

### **9.1 Scale Container Instances**
```bash
# Update container with more resources
az container create \
  --resource-group telogical-rg \
  --name telogical-backend \
  --cpu 2 \
  --memory 4 \
  # ... other parameters
```

### **9.2 Use Azure Container Apps (Alternative)**
For better scaling and management, consider Azure Container Apps:
```bash
# Create Container Apps environment
az containerapp env create \
  --name telogical-env \
  --resource-group telogical-rg \
  --location "East US"

# Deploy as Container Apps (better for production)
az containerapp create \
  --name telogical-backend \
  --resource-group telogical-rg \
  --environment telogical-env \
  --image telogicalregistry.azurecr.io/telogical-backend:latest \
  --min-replicas 1 \
  --max-replicas 10 \
  --cpu 1.0 \
  --memory 2.0Gi
```

---

## 💰 **Cost Estimation**

### **Monthly Costs (Basic Setup)**
- **Container Instances (2x)**: ~$30-50/month
- **PostgreSQL Flexible Server**: ~$15-30/month
- **Container Registry**: ~$5/month
- **Total**: ~$50-85/month

### **Monthly Costs (Production Setup)**
- **Container Apps (2x)**: ~$50-100/month
- **PostgreSQL (Standard)**: ~$50-100/month
- **Application Gateway**: ~$20-40/month
- **Log Analytics**: ~$10-20/month
- **Total**: ~$130-260/month

---

## 🎯 **Step 9: Custom Domain Setup (Optional)**

### **9.1 Configure DNS**
```bash
# Get Application Gateway public IP
GATEWAY_IP=$(az network public-ip show \
  --resource-group telogical-rg \
  --name telogical-appgw-ip \
  --query ipAddress --output tsv)

echo "Point your domain to: $GATEWAY_IP"
```

### **9.2 Update Environment Variables**
```bash
# Update frontend environment for custom domain
az container update \
  --resource-group telogical-rg \
  --name telogical-frontend \
  --set environmentVariables[0].name=NEXTAUTH_URL \
  --set environmentVariables[0].value=https://your-custom-domain.com
```

---

## 🎉 **Success!**

Your Telogical Chatbot is now live on Microsoft Azure!

**Production URLs:**
- **Frontend**: `https://telogical-frontend.eastus.azurecontainer.io:3000`
- **Backend**: `https://telogical-backend.eastus.azurecontainer.io:8081`
- **Database**: Azure Database for PostgreSQL

### **Architecture Overview:**
```
Internet → Application Gateway (SSL) → Container Instances → Azure PostgreSQL
                                    ↓
                              Azure Container Registry
                                    ↓
                            Log Analytics & App Insights
```

### **Next Steps:**
- 🔒 **Set up Azure Key Vault** for secrets management
- 📊 **Configure alerts** in Azure Monitor
- 🚀 **Implement auto-scaling** with Container Apps
- 🔄 **Set up CI/CD** with Azure DevOps or GitHub Actions
- 💾 **Configure database backups** and recovery

---

## 📞 **Support**

**Azure Resources:**
- [Azure Documentation](https://docs.microsoft.com/azure)
- [Azure Container Instances](https://docs.microsoft.com/azure/container-instances)
- [Azure Database for PostgreSQL](https://docs.microsoft.com/azure/postgresql)

**Application Issues:**
- Check container logs with `az container logs`
- Monitor resources in Azure Portal
- Verify environment variables and secrets
- Test database connectivity
- Review Application Insights for performance metrics

**Happy deploying!** 🚀