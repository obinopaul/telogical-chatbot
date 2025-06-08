# 🚀 **Deploying Telogical Chatbot to Render**

This guide walks you through deploying your complete Telogical Chatbot (frontend + backend) to Render using the production-ready Docker configuration.

## 📋 **Prerequisites**

- ✅ **Render Account** - Sign up at [render.com](https://render.com)
- ✅ **GitHub Repository** - Your Telogical project pushed to GitHub
- ✅ **Google OAuth App** - For authentication
- ✅ **Production API Keys** - OpenAI, Azure OpenAI, Anthropic, etc.
- ✅ **Domain Names** (Optional) - For custom domains

---

## 🎯 **Step 1: Prepare Your Repository**

### **1.1 Verify Production Files**
Ensure these files exist from the recent production preparation:
```
├── .env.production.example           # ← Backend environment template
├── frontend/.env.production.example  # ← Frontend environment template
├── docker/compose.production.yml     # ← Production Docker config
├── requirements.txt                  # ← Updated with pinned versions
├── DEPLOYMENT_READINESS.md          # ← Production readiness guide
```

### **1.2 Verify Render Blueprint**
✅ **The `render.yaml` file is already created and ready!** No need to create it manually.

The repository includes a complete Render blueprint at `render.yaml` with:
- PostgreSQL database configuration
- Backend service (Docker-based)  
- Frontend service (Docker-based)
- Auto-linked environment variables
- Auto-generated secrets

---

## 🎯 **Step 2: Deploy to Render**

### **2.1 Using Blueprint (Recommended)**
1. **The `render.yaml` file is already in your repository** ✅
2. Push your code to GitHub (if not already done)
3. Go to [Render Dashboard](https://dashboard.render.com)
4. Click **"New"** → **"Blueprint"**
5. Connect your GitHub repository
6. Render will automatically detect `render.yaml` and create all services

### **2.2 Manual Service Creation (Alternative)**

#### **A. Create PostgreSQL Database**
1. **Render Dashboard** → **"New"** → **"PostgreSQL"**
2. **Configuration:**
   ```
   Name: telogical-database
   Database: telogical_prod
   User: telogical_user
   Region: Oregon (or your preferred region)
   Plan: Starter ($7/month)
   ```

#### **B. Create Backend Service**
1. **Render Dashboard** → **"New"** → **"Web Service"**
2. **Configuration:**
   ```
   Name: telogical-backend
   Repository: <your-github-repo>
   Environment: Docker
   Region: Oregon (same as database)
   Branch: main
   Dockerfile Path: ./docker/Dockerfile.backend
   ```

#### **C. Create Frontend Service**
1. **Render Dashboard** → **"New"** → **"Web Service"**
2. **Configuration:**
   ```
   Name: telogical-frontend
   Repository: <your-github-repo>
   Environment: Docker
   Region: Oregon (same as backend)
   Branch: main
   Dockerfile Path: ./docker/Dockerfile.frontend
   ```

---

## 🎯 **Step 3: Configure Environment Variables**

### **3.1 Backend Environment Variables**
In **Backend Service Settings** → **Environment**:

| Variable | Value | Source |
|----------|-------|---------|
| `DATABASE_TYPE` | `postgres` | Manual |
| `POSTGRES_URL` | `postgres://user:pass@host:5432/db` | From Database |
| `HOST` | `0.0.0.0` | Manual |
| `PORT` | `10000` | Manual |
| `MODE` | `production` | Manual |
| `OPENAI_API_KEY` | `your-openai-api-key` | Manual (Secret) |
| `ANTHROPIC_API_KEY` | `your-anthropic-api-key` | Manual (Secret) |
| `AZURE_OPENAI_API_KEY` | `your-azure-openai-api-key` | Manual (Secret) |
| `AZURE_OPENAI_ENDPOINT` | `https://your-resource.openai.azure.com/` | Manual |
| `AZURE_OPENAI_DEPLOYMENT_MAP` | `{"gpt-4o": "your-deployment"}` | Manual |
| `TELOGICAL_AUTH_TOKEN` | `your-telogical-token` | Manual (Secret) |
| `TELOGICAL_AUTH_TOKEN_2` | `your-telogical-token-2` | Manual (Secret) |
| `AUTH_SECRET` | `your-secure-random-string` | Manual (Secret) |

### **3.2 Frontend Environment Variables**
In **Frontend Service Settings** → **Environment**:

| Variable | Value | Source |
|----------|-------|---------|
| `NEXTAUTH_SECRET` | `your-32-char-secret` | Manual (Secret) |
| `NEXTAUTH_URL` | `https://telogical-frontend.onrender.com` | From Service URL |
| `USE_TELOGICAL_BACKEND` | `true` | Manual |
| `TELOGICAL_API_URL` | `https://telogical-backend.onrender.com` | From Backend Service |
| `POSTGRES_URL` | `postgres://user:pass@host:5432/db` | From Database |
| `GOOGLE_CLIENT_ID` | `your-google-client-id` | Manual |
| `GOOGLE_CLIENT_SECRET` | `your-google-client-secret` | Manual (Secret) |
| `NODE_ENV` | `production` | Manual |

---

## 🎯 **Step 4: Database Setup**

### **4.1 Get Database Connection**
1. Go to your **PostgreSQL service** in Render
2. Copy the **"External Connection String"**
3. Format: `postgres://user:password@host:5432/database`

### **4.2 Initialize Database Schema**
Connect to your database and run:

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
```

### **4.3 Create Test User (Optional)**
```sql
-- Create a test user for initial testing
INSERT INTO "User" (id, email, name, "createdAt")
VALUES (
  'test-user-001',
  'test@telogical.com',
  'Test User',
  NOW()
) ON CONFLICT (email) DO NOTHING;
```

---

## 🎯 **Step 5: Configure Google OAuth**

### **5.1 Update Google Console**
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Navigate to **APIs & Services** → **Credentials**
3. Edit your OAuth 2.0 Client ID
4. **Authorized JavaScript Origins:**
   ```
   https://telogical-frontend.onrender.com
   https://your-custom-domain.com  (if using custom domain)
   ```
5. **Authorized Redirect URIs:**
   ```
   https://telogical-frontend.onrender.com/api/auth/callback/google
   https://your-custom-domain.com/api/auth/callback/google  (if using custom domain)
   ```

---

## 🎯 **Step 6: Deploy and Monitor**

### **6.1 Trigger Deployment**
1. **Push changes** to your main branch
2. **Render will automatically deploy** both services
3. **Monitor build logs** in each service dashboard

### **6.2 Check Service Health**
Once deployed, verify:

#### **Backend Health Check**
```bash
curl https://telogical-backend.onrender.com/health
# Should return: {"status": "healthy"}
```

#### **Frontend Health Check**
```bash
curl https://telogical-frontend.onrender.com/api/health
# Should return: {"status": "ok"}
```

### **6.3 Test Full Application**
Visit `https://telogical-frontend.onrender.com` and test:

- ✅ **Page loads** without errors
- ✅ **Google OAuth login** works
- ✅ **Chat interface** displays correctly
- ✅ **Send message** and receive AI response
- ✅ **Chat history** persists in database

---

## 🛠️ **Troubleshooting**

### **Build Failures**

#### **Backend Build Issues**
```bash
# Common fixes:
- Check requirements.txt has all dependencies
- Verify Dockerfile.backend exists and is correct
- Check for Python version compatibility
- Review build logs for specific error messages
```

#### **Frontend Build Issues**
```bash
# Common fixes:
- Verify all environment variables are set
- Check that TELOGICAL_API_URL points to backend service
- Ensure POSTGRES_URL is correct
- Review Next.js build logs
```

### **Service Connection Issues**

#### **Frontend Can't Connect to Backend**
```bash
# Verify these settings:
✓ TELOGICAL_API_URL in frontend matches backend URL
✓ Backend service is running and healthy
✓ Both services are in the same region
✓ No CORS issues (check backend logs)
```

#### **Database Connection Issues**
```bash
# Check these settings:
✓ POSTGRES_URL format is correct
✓ Database service is running
✓ Connection string includes SSL options if required
✓ Database allows connections from Render IPs
```

### **Authentication Problems**
```bash
# Verify these settings:
✓ NEXTAUTH_URL matches your frontend domain
✓ NEXTAUTH_SECRET is set and 32+ characters
✓ Google OAuth redirect URLs are correct
✓ User table exists in database
```

---

## 📊 **Performance & Scaling**

### **7.1 Service Plans**
Consider upgrading for production:
- **Starter Plan**: $7/month - 512MB RAM, shared CPU
- **Standard Plan**: $25/month - 2GB RAM, dedicated CPU
- **Pro Plan**: $85/month - 8GB RAM, high performance

### **7.2 Database Scaling**
- **Starter**: $7/month - 1GB storage, 97 connections
- **Standard**: $20/month - 10GB storage, 197 connections
- **Pro**: $65/month - 50GB storage, 297 connections

### **7.3 Monitoring Setup**
```bash
# Enable logging in Render Dashboard:
- Service metrics and uptime
- Build and deployment logs
- Database connection monitoring
- Error rate tracking
```

---

## 🎯 **Step 8: Custom Domain (Optional)**

### **8.1 Add Custom Domain**
1. **Frontend Service** → **Settings** → **Custom Domains**
2. Add your domain (e.g., `chat.yourdomain.com`)
3. **Configure DNS records** as instructed by Render
4. **Update environment variables:**
   ```bash
   NEXTAUTH_URL=https://chat.yourdomain.com
   ```
5. **Update Google OAuth** with new domain

### **8.2 Backend Custom Domain (Optional)**
1. **Backend Service** → **Settings** → **Custom Domains**
2. Add API subdomain (e.g., `api.yourdomain.com`)
3. **Update frontend environment:**
   ```bash
   TELOGICAL_API_URL=https://api.yourdomain.com
   ```

### **8.3 SSL Certificates**
Render automatically provides SSL certificates for all custom domains.

---

## 📈 **Production Monitoring**

### **8.1 Service Monitoring**
Monitor these metrics in Render Dashboard:
- **Response times** and error rates
- **Memory usage** and CPU utilization
- **Database connections** and query performance
- **Uptime** and availability

### **8.2 Application Logging**
Set up structured logging:
```python
# Backend logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Log important events
logger.info(f"User {user_id} started chat {chat_id}")
```

### **8.3 Alerts and Notifications**
Configure alerts for:
- Service downtime
- High error rates
- Database connection issues
- Resource usage thresholds

---

## 💰 **Cost Estimation**

### **Monthly Costs (Starter Plan)**
- **Frontend Service**: $7/month
- **Backend Service**: $7/month  
- **PostgreSQL Database**: $7/month
- **Total**: ~$21/month

### **Monthly Costs (Production Plan)**
- **Frontend Service**: $25/month (Standard)
- **Backend Service**: $25/month (Standard)
- **PostgreSQL Database**: $20/month (Standard)
- **Total**: ~$70/month

---

## 🎉 **Success!**

Your Telogical Chatbot is now live on Render!

**Production URLs:**
- **Frontend**: `https://telogical-frontend.onrender.com`
- **Backend**: `https://telogical-backend.onrender.com`
- **Database**: Managed PostgreSQL

### **Architecture Overview:**
```
User → Render (Frontend) → Render (Backend) → AI APIs
                         ↓
                    Render PostgreSQL
```

### **Next Steps:**
- 🔒 **Monitor service health** and performance
- 📊 **Set up alerts** for critical issues
- 🚀 **Scale services** based on usage
- 🔄 **Implement CI/CD** for automated deployments
- 💾 **Set up backups** for database

---

## 📞 **Support**

**Render Resources:**
- [Render Documentation](https://render.com/docs)
- [Render Community](https://community.render.com)
- [Render Status Page](https://status.render.com)

**Application Issues:**
- Check service logs in Render Dashboard
- Verify all environment variables are correct
- Test database connectivity
- Review authentication configuration
- Monitor resource usage and performance

**Happy deploying!** 🚀