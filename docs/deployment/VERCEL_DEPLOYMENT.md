# 🚀 **Deploying Telogical Chatbot to Vercel**

This guide walks you through deploying the **frontend** of your Telogical Chatbot to Vercel, with the backend deployed separately on another platform.

## 📋 **Prerequisites**

- ✅ **Vercel Account** - Sign up at [vercel.com](https://vercel.com)
- ✅ **Separate Backend Deployment** - Backend deployed on Render, Azure, or other platform
- ✅ **PostgreSQL Database** - Managed database service
- ✅ **Google OAuth App** - For authentication
- ✅ **Production Environment Variables** - All API keys and credentials

---

## 🎯 **Step 1: Prepare Your Repository**

### **1.1 Verify Frontend Structure**
✅ **All required files are already configured!** Your frontend directory includes:
```
frontend/
├── .env.production.example     # ← Production environment template
├── vercel.json                 # ← Vercel configuration (already created)
├── app/
├── components/
├── lib/
├── package.json
├── next.config.ts              # ← Updated with image domains
├── tailwind.config.ts
└── tsconfig.json
```

### **1.2 Environment Variables Template**
Your production environment should use `frontend/.env.production.example`:

```bash
# Authentication (Required)
NEXTAUTH_SECRET=your-production-nextauth-secret-32-chars-minimum
NEXTAUTH_URL=https://your-app.vercel.app

# Database Connection (Required)
POSTGRES_URL=postgres://user:password@your-production-db-host:5432/database_name

# Telogical Backend Connection (Required)
USE_TELOGICAL_BACKEND=true
TELOGICAL_API_URL=https://your-backend-domain.com

# Google OAuth (Required)
GOOGLE_CLIENT_ID=your-production-google-client-id
GOOGLE_CLIENT_SECRET=your-production-google-client-secret

# Production Settings
NODE_ENV=production
```

---

## 🎯 **Step 2: Deploy Backend First**

**⚠️ Important:** Deploy your backend **before** deploying the frontend, as the frontend needs the backend URL.

### **2.1 Choose Backend Platform**
- **Render**: Follow [Render Deployment Guide](RENDER_DEPLOYMENT.md)
- **Azure**: Follow [Azure Deployment Guide](AZURE_DEPLOYMENT.md)  
- **Docker VPS**: Follow [Docker Production Deployment Guide](DOCKER_PRODUCTION_DEPLOYMENT.md)

### **2.2 Get Backend URL**
Once deployed, note your backend URL (e.g., `https://your-backend.render.com`)

---

## 🎯 **Step 3: Deploy Frontend to Vercel**

### **3.1 Connect GitHub Repository**
1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click **"New Project"**
3. Import your GitHub repository
4. **Root Directory**: Select `frontend`
5. **Framework Preset**: Next.js (auto-detected)

### **3.2 Configure Build Settings**
✅ **Build settings are pre-configured in `frontend/vercel.json`!** Vercel will auto-detect:
```bash
Build Command: npm run build
Output Directory: .next
Install Command: npm install
Root Directory: frontend
Framework: Next.js
```

### **3.3 Environment Variables**
Add these in **Vercel Dashboard → Project Settings → Environment Variables**:

| Variable | Value | Notes |
|----------|-------|-------|
| `NEXTAUTH_SECRET` | `your-32-char-random-secret` | Generate with `openssl rand -base64 32` |
| `NEXTAUTH_URL` | `https://your-app.vercel.app` | Your Vercel domain |
| `POSTGRES_URL` | `postgres://user:pass@host:5432/db` | Your managed database |
| `USE_TELOGICAL_BACKEND` | `true` | Enable backend integration |
| `TELOGICAL_API_URL` | `https://your-backend.render.com` | Your backend URL |
| `GOOGLE_CLIENT_ID` | `your-google-client-id` | From Google Console |
| `GOOGLE_CLIENT_SECRET` | `your-google-client-secret` | From Google Console |
| `NODE_ENV` | `production` | Production mode |

---

## 🎯 **Step 4: Configure Google OAuth**

### **4.1 Update Google Console**
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Navigate to **APIs & Services** → **Credentials**
3. Edit your OAuth 2.0 Client
4. **Authorized JavaScript Origins:**
   ```
   https://your-app.vercel.app
   ```
5. **Authorized Redirect URIs:**
   ```
   https://your-app.vercel.app/api/auth/callback/google
   ```

### **4.2 Custom Domain (Optional)**
If using a custom domain:
1. Add domain in **Vercel Dashboard → Project Settings → Domains**
2. Update Google OAuth with your custom domain
3. Update `NEXTAUTH_URL` environment variable

---

## 🎯 **Step 5: Database Setup**

### **5.1 Verify Database Schema**
Ensure your PostgreSQL database has the required tables. Connect and run:

```sql
-- Verify User table exists
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' AND table_name = 'User';

-- Verify Chat table exists  
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' AND table_name = 'Chat';

-- If tables don't exist, create them:
CREATE TABLE IF NOT EXISTS "User" (
  id VARCHAR PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  password VARCHAR(255),
  name VARCHAR(255),
  image TEXT,
  "createdAt" TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS "Chat" (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  "createdAt" TIMESTAMP NOT NULL DEFAULT NOW(),
  title TEXT NOT NULL,
  "userId" VARCHAR NOT NULL REFERENCES "User"(id),
  visibility VARCHAR DEFAULT 'private'
);
```

### **5.2 Test Database Connection**
In Vercel deployment logs, verify database connectivity:
```
✓ Database connection successful
✓ Authentication tables found
```

---

## 🎯 **Step 6: Deploy and Test**

### **6.1 Trigger Deployment**
1. Push changes to your main branch
2. Vercel will automatically deploy
3. Monitor build logs in Vercel Dashboard

### **6.2 Verify Deployment**
Check your deployment at `https://your-app.vercel.app`:

- ✅ **Page loads** without errors
- ✅ **Authentication works** (Google OAuth)
- ✅ **Chat interface** displays correctly
- ✅ **Backend connection** works (test sending a message)
- ✅ **Database** stores chat history

### **6.3 Check Build Logs**
If deployment fails, check:
1. **Build Logs** in Vercel Dashboard
2. **Environment Variables** are all set
3. **Backend URL** is accessible
4. **Database connection** string is correct

---

## 🛠️ **Troubleshooting**

### **Build Failures**
```bash
# Common issues:
- Missing environment variables
- Incorrect TELOGICAL_API_URL
- Database connection issues
- Next.js build errors

# Check Vercel build logs for specific errors
```

### **Authentication Issues**
```bash
# Verify these settings:
✓ NEXTAUTH_URL matches your domain
✓ NEXTAUTH_SECRET is 32+ characters
✓ Google OAuth URLs are correct
✓ Database User table exists
```

### **Backend Connection Issues**
```bash
# Test backend URL directly:
curl https://your-backend.render.com/health

# Verify TELOGICAL_API_URL in Vercel environment variables
# Check backend logs for CORS issues
```

### **Database Issues**
```bash
# Test database connection:
psql "postgres://user:pass@host:5432/db"

# Verify tables exist and user permissions
# Check POSTGRES_URL format
```

---

## 📊 **Performance Optimization**

### **7.1 Vercel Configuration**
Create `frontend/vercel.json`:
```json
{
  "functions": {
    "app/**/*": {
      "maxDuration": 30
    }
  },
  "regions": ["iad1"],
  "framework": "nextjs"
}
```

### **7.2 Next.js Optimization**
Your `frontend/next.config.ts` should already have:
```typescript
const nextConfig = {
  images: {
    remotePatterns: [
      { hostname: 'avatar.vercel.sh' },
      { hostname: 'lh3.googleusercontent.com' }  // ← Added for Google profile images
    ]
  },
  experimental: {
    serverComponentsExternalPackages: ['postgres']
  }
}
```

### **7.3 Edge Runtime (Optional)**
For better performance, consider using Edge Runtime for API routes:
```typescript
export const runtime = 'edge';
```

---

## 🎯 **Step 7: Custom Domain Setup (Optional)**

### **7.1 Add Custom Domain**
1. **Vercel Dashboard** → **Project Settings** → **Domains**
2. Add your domain (e.g., `chat.yourdomain.com`)
3. Configure DNS as instructed by Vercel
4. **Update environment variables:**
   ```bash
   NEXTAUTH_URL=https://chat.yourdomain.com
   ```
5. **Update Google OAuth** with new domain

### **7.2 SSL Certificate**
Vercel automatically provides SSL certificates for all domains.

---

## 📈 **Monitoring and Scaling**

### **8.1 Vercel Analytics**
Enable analytics in **Vercel Dashboard** → **Analytics** for:
- Page views and performance
- Core Web Vitals
- User engagement metrics

### **8.2 Function Monitoring**
Monitor your API routes in **Vercel Dashboard** → **Functions**:
- Response times
- Error rates  
- Invocation counts

### **8.3 Database Monitoring**
Monitor your PostgreSQL database:
- Connection pool usage
- Query performance
- Storage usage

---

## 🎉 **Success!**

Your Telogical Chatbot frontend is now live on Vercel!

**Production URLs:**
- **Frontend**: `https://your-app.vercel.app`  
- **Backend**: `https://your-backend.render.com` (or your chosen platform)

### **Architecture Overview:**
```
User → Vercel (Frontend) → Your Backend Platform → AI APIs
                         ↓
                  Managed PostgreSQL Database
```

### **Next Steps:**
- 🔒 **Monitor performance** in Vercel Analytics
- 📊 **Set up alerts** for errors and downtime  
- 🚀 **Optimize based on usage** patterns
- 🔄 **Set up CI/CD** for automatic deployments

---

## 📞 **Support**

**Vercel Issues:**
- [Vercel Documentation](https://vercel.com/docs)
- [Vercel Community](https://github.com/vercel/vercel/discussions)
- Check deployment logs in Vercel Dashboard

**Application Issues:**
- Verify all environment variables are set correctly
- Test backend health endpoint
- Check database connectivity
- Review authentication configuration

**Happy deploying!** 🚀