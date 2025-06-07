# 🚀 **Deploying Telogical Chatbot to Render**

This guide walks you through deploying your Telogical Chatbot to Render for production use.

## 📋 **Prerequisites**

- ✅ **Render Account** - Sign up at [render.com](https://render.com)
- ✅ **PostgreSQL Database** - Render PostgreSQL or external provider
- ✅ **Google OAuth App** - For authentication
- ✅ **Azure OpenAI** - For AI responses
- ✅ **GitHub Repository** - Your Telogical project

---

## 🎯 **Step 1: Prepare Your Repository**

### **1.1 Create Build Scripts**
Add to `frontend/package.json`:

```json
{
  "scripts": {
    "build": "next build",
    "start": "next start",
    "postinstall": "prisma generate || echo 'Prisma not configured'"
  }
}
```

Add to `backend/requirements.txt`:
```txt
fastapi==0.104.1
uvicorn==0.24.0
python-dotenv==1.0.0
openai==1.3.0
psycopg2-binary==2.9.9
pydantic==2.5.0
httpx==0.25.2
```

### **1.2 Create Render Configuration**
Create `render.yaml` in project root:

```yaml
services:
  # Frontend Service
  - type: web
    name: telogical-frontend
    env: node
    plan: starter
    buildCommand: cd frontend && npm install && npm run build
    startCommand: cd frontend && npm start
    envVars:
      - key: NODE_ENV
        value: production
      - key: NEXTAUTH_URL
        fromService:
          type: web
          name: telogical-frontend
          property: url
      - key: POSTGRES_URL
        fromDatabase:
          name: telogical-db
          property: connectionString
      - key: NEXTAUTH_SECRET
        generateValue: true
      - key: USE_TELOGICAL_BACKEND
        value: true
      - key: TELOGICAL_API_URL
        fromService:
          type: web
          name: telogical-backend
          property: url

  # Backend Service  
  - type: web
    name: telogical-backend
    env: python
    plan: starter
    buildCommand: cd backend && pip install -r requirements.txt
    startCommand: cd backend && python -m uvicorn run_service:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: POSTGRES_URL
        fromDatabase:
          name: telogical-db
          property: connectionString
      - key: OPENAI_API_KEY
        sync: false
      - key: AZURE_OPENAI_ENDPOINT
        sync: false

databases:
  - name: telogical-db
    plan: starter
```

---

## 🎯 **Step 2: Deploy to Render**

### **2.1 Connect GitHub Repository**
1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **"New +"** → **"Blueprint"**
3. Connect your GitHub repository
4. Select the repository containing your Telogical project

### **2.2 Alternative: Manual Service Creation**

#### **Create PostgreSQL Database**
1. Click **"New +"** → **"PostgreSQL"**
2. Name: `telogical-db`
3. Plan: **Starter** (free tier)
4. Region: Choose closest to your users
5. Click **"Create Database"**

#### **Create Backend Service**
1. Click **"New +"** → **"Web Service"**
2. Connect your repository
3. **Configuration:**
   ```
   Name: telogical-backend
   Environment: Python
   Region: Same as database
   Branch: main
   Root Directory: backend
   Build Command: pip install -r requirements.txt
   Start Command: python -m uvicorn run_service:app --host 0.0.0.0 --port $PORT
   ```

#### **Create Frontend Service**
1. Click **"New +"** → **"Web Service"**
2. Connect your repository
3. **Configuration:**
   ```
   Name: telogical-frontend
   Environment: Node
   Region: Same as backend
   Branch: main
   Root Directory: frontend
   Build Command: npm install && npm run build
   Start Command: npm start
   ```

---

## 🎯 **Step 3: Configure Environment Variables**

### **3.1 Backend Environment Variables**
In your backend service settings:

| Variable | Value | Notes |
|----------|-------|-------|
| `POSTGRES_URL` | `postgresql://user:pass@host:5432/db` | From database |
| `OPENAI_API_KEY` | `your-openai-api-key` | Azure OpenAI key |
| `AZURE_OPENAI_ENDPOINT` | `https://your-resource.openai.azure.com/` | Azure endpoint |
| `AZURE_OPENAI_API_VERSION` | `2024-12-01-preview` | API version |
| `HOST` | `0.0.0.0` | Required for Render |
| `PORT` | `$PORT` | Render auto-assigns |

### **3.2 Frontend Environment Variables**
In your frontend service settings:

| Variable | Value | Notes |
|----------|-------|-------|
| `POSTGRES_URL` | `postgresql://user:pass@host:5432/db` | Same as backend |
| `NEXTAUTH_URL` | `https://your-app.onrender.com` | Your frontend URL |
| `NEXTAUTH_SECRET` | `your-32-character-random-string` | Generate securely |
| `GOOGLE_CLIENT_ID` | `your-google-client-id` | From Google Console |
| `GOOGLE_CLIENT_SECRET` | `your-google-client-secret` | From Google Console |
| `USE_TELOGICAL_BACKEND` | `true` | Enable backend |
| `TELOGICAL_API_URL` | `https://your-backend.onrender.com` | Backend URL |

---

## 🎯 **Step 4: Database Setup**

### **4.1 Get Database Connection String**
1. Go to your PostgreSQL database in Render
2. Copy the **"External Connection String"**
3. Format: `postgresql://user:password@host:5432/database`

### **4.2 Run Database Migrations**
Connect to your database and run:

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
  "userId" UUID NOT NULL REFERENCES "User"(id),
  visibility VARCHAR DEFAULT 'private'
);

-- Add other tables as needed...
```

### **4.3 Create Master User**
```sql
INSERT INTO "User" (id, email, password, name, created_at)
VALUES (
  '00000000-0000-0000-0000-000000000001',
  'master@telogical.com',
  'd77f599ed8ab508114bfcd6ffeeef69122f54c1239daade578d6404950a04ec3',
  'Master Admin User',
  NOW()
);
```

---

## 🎯 **Step 5: Configure Google OAuth**

### **5.1 Update Google Console**
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Navigate to **APIs & Services** → **Credentials**
3. Edit your OAuth 2.0 Client
4. Add Authorized Redirect URLs:
   ```
   https://your-app.onrender.com/api/auth/callback/google
   ```
5. Add Authorized JavaScript Origins:
   ```
   https://your-app.onrender.com
   ```

---

## 🎯 **Step 6: Deploy and Monitor**

### **6.1 Trigger Deployment**
1. Push changes to your main branch
2. Render will automatically deploy both services
3. Monitor build logs in Render Dashboard

### **6.2 Check Service Health**
- ✅ **Backend**: Visit `https://your-backend.onrender.com/health`
- ✅ **Frontend**: Visit `https://your-frontend.onrender.com`
- ✅ **Database**: Check connection in logs

### **6.3 Test Full Functionality**
- ✅ **Authentication**: Test login/registration
- ✅ **Chat**: Send messages and receive responses
- ✅ **Database**: Verify chat history persistence
- ✅ **Caching**: Test response caching

---

## 🛠️ **Troubleshooting**

### **Common Issues:**

#### **Build Failures**
```bash
# Check build logs in Render Dashboard
# Verify package.json and requirements.txt
# Ensure all dependencies are listed
```

#### **Service Connection Issues**
```bash
# Verify service URLs in environment variables
# Check internal service communication
# Ensure services are in same region
```

#### **Database Connection Issues**
```bash
# Verify POSTGRES_URL format
# Check database service status
# Test connection from service logs
```

#### **Authentication Problems**
```bash
# Verify NEXTAUTH_URL matches frontend domain
# Check Google OAuth redirect URLs
# Ensure NEXTAUTH_SECRET is set
```

---

## 📊 **Performance Optimization**

### **7.1 Service Plans**
For production, consider upgrading:
- **Starter Plan**: Free tier with limitations
- **Standard Plan**: Better performance and uptime
- **Pro Plan**: High-performance applications

### **7.2 Database Optimization**
```sql
-- Add indexes for better performance
CREATE INDEX idx_user_email ON "User"(email);
CREATE INDEX idx_chat_user_id ON "Chat"("userId");
CREATE INDEX idx_chat_created_at ON "Chat"("createdAt");
```

### **7.3 Caching Strategy**
Enable caching in your application:
```typescript
// Add Redis cache if needed
// Use Render Redis add-on
```

---

## 🎯 **Step 7: Custom Domain (Optional)**

### **7.1 Add Custom Domain**
1. Go to your frontend service
2. Click **"Settings"** → **"Custom Domains"**
3. Add your domain (e.g., `chat.yourdomain.com`)
4. Configure DNS records as shown

### **7.2 SSL Certificate**
Render automatically provides SSL certificates for custom domains.

---

## 📈 **Monitoring and Scaling**

### **8.1 Monitor Performance**
- **Render Dashboard**: View metrics and logs
- **Uptime Monitoring**: Set up alerts
- **Performance**: Monitor response times

### **8.2 Scaling Options**
- **Vertical Scaling**: Upgrade service plans
- **Horizontal Scaling**: Add more service instances
- **Database Scaling**: Upgrade PostgreSQL plan

---

## 🎉 **Success!**

Your Telogical Chatbot is now live on Render!

**URLs:**
- **Frontend**: `https://your-frontend.onrender.com`
- **Backend**: `https://your-backend.onrender.com`
- **Database**: Managed PostgreSQL

### **Next Steps:**
- 🔒 **Set up monitoring** and alerts
- 📊 **Optimize performance** based on usage
- 🚀 **Scale services** as needed
- 🔄 **Set up CI/CD** for automatic deployments

---

## 📞 **Support**

**Render Resources:**
- [Render Documentation](https://render.com/docs)
- [Render Community](https://community.render.com)
- [Render Status](https://status.render.com)

**Telogical Support:**
- Check service logs in Render Dashboard
- Verify environment variables
- Test database connectivity
- Review authentication settings

**Happy deploying!** 🚀