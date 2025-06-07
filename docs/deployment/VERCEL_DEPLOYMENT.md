# 🚀 **Deploying Telogical Chatbot to Vercel**

This guide walks you through deploying your Telogical Chatbot to Vercel for production use.

## 📋 **Prerequisites**

- ✅ **Vercel Account** - Sign up at [vercel.com](https://vercel.com)
- ✅ **PostgreSQL Database** - Azure PostgreSQL or other cloud provider
- ✅ **Google OAuth App** - For authentication
- ✅ **Azure OpenAI** - For AI responses
- ✅ **GitHub Repository** - Your Telogical project

---

## 🎯 **Step 1: Prepare Your Repository**

### **1.1 Environment Variables Setup**
Create a `.env.example` file in your frontend directory:

```bash
# Telogical Backend Configuration
USE_TELOGICAL_BACKEND=true
TELOGICAL_API_URL=https://your-backend-url.com

# Database
POSTGRES_URL=postgres://username:password@host:5432/database

# Authentication
NEXTAUTH_URL=https://your-app.vercel.app
NEXTAUTH_SECRET=your-32-character-random-string

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
```

### **1.2 Vercel Configuration**
Create `vercel.json` in your project root:

```json
{
  "version": 2,
  "builds": [
    {
      "src": "frontend/package.json",
      "use": "@vercel/next",
      "config": {
        "projectSettings": {
          "framework": "nextjs"
        }
      }
    },
    {
      "src": "backend/**/*.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "backend/$1"
    },
    {
      "src": "/(.*)",
      "dest": "frontend/$1"
    }
  ],
  "env": {
    "POSTGRES_URL": "@postgres_url",
    "NEXTAUTH_SECRET": "@nextauth_secret",
    "GOOGLE_CLIENT_ID": "@google_client_id",
    "GOOGLE_CLIENT_SECRET": "@google_client_secret"
  }
}
```

---

## 🎯 **Step 2: Deploy Frontend to Vercel**

### **2.1 Connect GitHub Repository**
1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click **"New Project"**
3. Import your GitHub repository
4. Select **"frontend"** as the root directory

### **2.2 Configure Build Settings**
```bash
# Framework Preset: Next.js
# Root Directory: frontend
# Build Command: npm run build
# Output Directory: .next
# Install Command: npm install
```

### **2.3 Environment Variables**
Add these in Vercel Dashboard → Settings → Environment Variables:

| Variable | Value | Environment |
|----------|-------|-------------|
| `POSTGRES_URL` | `postgres://user:pass@host:5432/db` | Production |
| `NEXTAUTH_URL` | `https://your-app.vercel.app` | Production |
| `NEXTAUTH_SECRET` | `your-32-char-secret` | Production |
| `GOOGLE_CLIENT_ID` | `your-google-client-id` | Production |
| `GOOGLE_CLIENT_SECRET` | `your-google-client-secret` | Production |
| `USE_TELOGICAL_BACKEND` | `true` | Production |
| `TELOGICAL_API_URL` | `https://your-backend-url` | Production |

---

## 🎯 **Step 3: Deploy Backend**

### **Option A: Separate Backend Deployment (Recommended)**

#### **3.1 Deploy to Railway/Render**
```bash
# Create requirements.txt in backend/
pip freeze > requirements.txt

# Deploy using Railway or Render
# Point TELOGICAL_API_URL to your backend URL
```

#### **3.2 Update Frontend Environment**
```bash
TELOGICAL_API_URL=https://your-backend.railway.app
# or
TELOGICAL_API_URL=https://your-backend.render.com
```

### **Option B: Vercel Serverless Functions**

#### **3.1 Create API Routes**
Create `frontend/api/backend/` directory:

```typescript
// frontend/api/backend/stream.ts
import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  const body = await request.json();
  
  // Your Python backend logic here
  // Note: Limited to 10s execution time on Vercel
  
  return NextResponse.json({ response: "..." });
}
```

---

## 🎯 **Step 4: Configure Google OAuth**

### **4.1 Update Google Console**
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Navigate to **APIs & Services** → **Credentials**
3. Edit your OAuth 2.0 Client
4. Add Authorized Redirect URLs:
   ```
   https://your-app.vercel.app/api/auth/callback/google
   ```
5. Add Authorized JavaScript Origins:
   ```
   https://your-app.vercel.app
   ```

---

## 🎯 **Step 5: Database Setup**

### **5.1 PostgreSQL Configuration**
Ensure your PostgreSQL database allows connections from Vercel:

```sql
-- Update your PostgreSQL connection settings
-- Ensure SSL is enabled for Vercel connections
```

### **5.2 Run Migrations**
```bash
# Connect to your database and run:
npm run db:migrate
# or manually run the SQL from your schema files
```

---

## 🎯 **Step 6: Deploy and Test**

### **6.1 Trigger Deployment**
1. Push changes to your main branch
2. Vercel will automatically deploy
3. Monitor build logs in Vercel Dashboard

### **6.2 Test Deployment**
- ✅ **Authentication**: Test Google OAuth login
- ✅ **Database**: Verify user creation and chat storage
- ✅ **AI Responses**: Test chatbot functionality
- ✅ **Performance**: Check loading speeds

---

## 🛠️ **Troubleshooting**

### **Common Issues:**

#### **Build Failures**
```bash
# Check package.json scripts
npm run build  # Should work locally first
```

#### **Environment Variables**
```bash
# Verify all required variables are set
# Check Vercel Dashboard → Settings → Environment Variables
```

#### **Database Connections**
```bash
# Ensure POSTGRES_URL is correct
# Check PostgreSQL allows external connections
# Verify SSL settings
```

#### **Authentication Issues**
```bash
# Verify NEXTAUTH_URL matches your domain
# Check Google OAuth settings
# Ensure NEXTAUTH_SECRET is set
```

---

## 📊 **Performance Optimization**

### **6.1 Enable Caching**
```typescript
// next.config.js
module.exports = {
  experimental: {
    serverComponentsExternalPackages: ['postgres']
  },
  images: {
    domains: ['your-domain.com']
  }
}
```

### **6.2 Database Connection Pooling**
```typescript
// Use connection pooling for better performance
const client = postgres(process.env.POSTGRES_URL!, {
  ssl: { rejectUnauthorized: false },
  max: 10, // Connection pool size
  idle_timeout: 20000
});
```

---

## 🎉 **Success!**

Your Telogical Chatbot should now be live on Vercel! 

**Production URL:** `https://your-app.vercel.app`

### **Next Steps:**
- 🔒 **Set up custom domain** (optional)
- 📊 **Monitor analytics** in Vercel Dashboard
- 🚀 **Optimize performance** based on usage
- 🔄 **Set up CI/CD** for automatic deployments

---

## 📞 **Support**

If you encounter issues:
1. Check Vercel build logs
2. Verify environment variables
3. Test database connectivity
4. Review authentication settings
5. Monitor application logs in Vercel Dashboard

**Happy deploying!** 🚀