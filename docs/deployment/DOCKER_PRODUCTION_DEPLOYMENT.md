# 🐳 **Docker Production Deployment Guide**

This guide covers deploying the Telogical Chatbot to production using Docker on your own servers, VPS, or any Docker-compatible environment.

## 📋 **Prerequisites**

- ✅ **Linux Server** (Ubuntu 20.04+ recommended)
- ✅ **Docker & Docker Compose** installed
- ✅ **Domain Name** for your application
- ✅ **SSL Certificate** (Let's Encrypt recommended)
- ✅ **PostgreSQL Database** (managed or self-hosted)
- ✅ **Required API Keys** (OpenAI, Azure, Google OAuth)

---

## 🎯 **Step 1: Server Preparation**

### **1.1 Install Docker**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Logout and login again for group changes
```

### **1.2 Install Nginx (for SSL termination)**
```bash
sudo apt install nginx certbot python3-certbot-nginx -y
```

### **1.3 Configure Firewall**
```bash
sudo ufw allow 22      # SSH
sudo ufw allow 80      # HTTP
sudo ufw allow 443     # HTTPS
sudo ufw enable
```

---

## 🎯 **Step 2: Application Deployment**

### **2.1 Verify Deployment Files**
✅ **All Docker deployment files are already created and ready!** Your repository includes:
```
├── docker-compose.prod.yml           # ← Production Docker Compose
├── docker/compose.production.yml     # ← Alternative production config
├── nginx/telogical.conf              # ← Nginx reverse proxy config
├── sql/init.sql                      # ← Database initialization
├── .env.production.example           # ← Backend environment template
└── frontend/.env.production.example  # ← Frontend environment template
```

### **2.2 Setup Environment Files**
```bash
# Navigate to your project directory
cd Telogical_Chatbot

# Copy and edit production environment files
cp .env.production.example .env
cp frontend/.env.production.example frontend/.env.local

# Edit with your actual production values
nano .env
nano frontend/.env.local
```

### **2.2 Configure Environment Variables**

**Backend (.env):**
```bash
# AI API Keys
OPENAI_API_KEY=your-production-openai-api-key
ANTHROPIC_API_KEY=your-production-anthropic-api-key
AZURE_OPENAI_API_KEY=your-production-azure-openai-api-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/

# Telogical API Configuration
TELOGICAL_AUTH_TOKEN=your-production-telogical-auth-token
TELOGICAL_GRAPHQL_ENDPOINT=https://residential-api.telogical.com/graphql
TELOGICAL_API_URL=https://api.yourdomain.com

# Database Configuration
DATABASE_TYPE=postgres
POSTGRES_URL=postgres://user:password@your-db-host:5432/telogical_prod

# Server Configuration
HOST=0.0.0.0
PORT=8081
MODE=production
AUTH_SECRET=your-super-secure-random-string-here

# Monitoring (Optional)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your-langsmith-api-key
LANGCHAIN_PROJECT=telogical-production
```

**Frontend (.env.local):**
```bash
# Authentication
NEXTAUTH_SECRET=your-production-nextauth-secret-32-chars-minimum
NEXTAUTH_URL=https://yourdomain.com

# Backend Connection
USE_TELOGICAL_BACKEND=true
TELOGICAL_API_URL=https://api.yourdomain.com

# Database
POSTGRES_URL=postgres://user:password@your-db-host:5432/telogical_prod

# Google OAuth
GOOGLE_CLIENT_ID=your-production-google-client-id
GOOGLE_CLIENT_SECRET=your-production-google-client-secret
```

### **2.3 Deploy with Docker**
```bash
# Option 1: Use the simplified production configuration (recommended)
docker-compose -f docker-compose.prod.yml up -d

# Option 2: Use the full production configuration
docker-compose -f docker/compose.production.yml up -d

# Check service status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

---

## 🎯 **Step 3: Nginx Reverse Proxy Setup**

### **3.1 Use Pre-configured Nginx File**
✅ **Nginx configuration is already created!** Copy the ready-to-use configuration:
```bash
# Copy the pre-configured Nginx file
sudo cp nginx/telogical.conf /etc/nginx/sites-available/telogical

# Edit the domain name to match your domain
sudo nano /etc/nginx/sites-available/telogical
# Replace 'yourdomain.com' with your actual domain
```

**The included configuration (`nginx/telogical.conf`) provides:**
```nginx
# Frontend (Main Domain)
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 86400;
    }
}

# Backend API (Subdomain)
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://localhost:8081;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 86400;
    }
}
```

### **3.2 Enable Site and Get SSL**
```bash
# Enable the site
sudo ln -s /etc/nginx/sites-available/telogical /etc/nginx/sites-enabled/

# Test Nginx configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx

# Get SSL certificates
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com -d api.yourdomain.com

# Auto-renewal test
sudo certbot renew --dry-run
```

---

## 🎯 **Step 4: Database Setup**

### **4.1 External Managed Database (Recommended)**
Use a managed PostgreSQL service:
- **AWS RDS**
- **Google Cloud SQL**
- **Azure Database for PostgreSQL**
- **DigitalOcean Managed Databases**

### **4.2 Self-Hosted Database (Alternative)**
✅ **Database initialization script is already created!** If you want to host PostgreSQL on the same server:

```bash
# The sql/init.sql file will automatically initialize your database schema
# Add to docker-compose.prod.yml or use the self-hosted database option:

services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: telogical_prod
      POSTGRES_USER: telogical_user
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    ports:
      - "5432:5432"
    restart: unless-stopped

volumes:
  postgres_data:
```

---

## 🎯 **Step 5: Production Management**

### **5.1 Essential Docker Commands**
```bash
# Deploy (using simplified production config)
docker-compose -f docker-compose.prod.yml up -d

# View service status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f [service-name]

# Restart services
docker-compose -f docker-compose.prod.yml restart

# Update deployment
git pull
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# Scale services
docker-compose -f docker-compose.prod.yml up -d --scale backend=2

# Stop services
docker-compose -f docker-compose.prod.yml down
```

### **5.2 Backup Strategy**
```bash
# Create backup script
cat > backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker exec postgres_container pg_dump -U telogical_user telogical_prod > backups/backup_$DATE.sql
# Keep only last 7 days
find backups/ -name "*.sql" -mtime +7 -delete
EOF

chmod +x backup.sh

# Add to crontab for daily backups
echo "0 2 * * * /path/to/backup.sh" | crontab -
```

### **5.3 Monitoring Setup**
```bash
# Monitor resource usage
docker stats

# Set up log rotation
sudo nano /etc/logrotate.d/docker-containers

# Content:
/var/lib/docker/containers/*/*.log {
    rotate 7
    daily
    compress
    size=1M
    missingok
    delaycompress
    copytruncate
}
```

---

## 🎯 **Step 6: Security Hardening**

### **6.1 Server Security**
```bash
# Disable root login
sudo nano /etc/ssh/sshd_config
# Set: PermitRootLogin no

# Install fail2ban
sudo apt install fail2ban -y

# Configure automatic updates
sudo apt install unattended-upgrades -y
sudo dpkg-reconfigure -plow unattended-upgrades
```

### **6.2 Docker Security**
```bash
# Run containers as non-root user
# Add to Dockerfiles:
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs
USER nextjs

# Limit container resources in compose.production.yml
deploy:
  resources:
    limits:
      memory: 1G
      cpus: '0.5'
```

---

## 🎯 **Step 7: DNS Configuration**

### **7.1 Domain Setup**
Point your domains to your server IP:
```
A Record: yourdomain.com → YOUR_SERVER_IP
A Record: www.yourdomain.com → YOUR_SERVER_IP
A Record: api.yourdomain.com → YOUR_SERVER_IP
```

### **7.2 Google OAuth Configuration**
Update Google OAuth settings:
- **Authorized JavaScript Origins:**
  - `https://yourdomain.com`
  - `https://www.yourdomain.com`
- **Authorized Redirect URIs:**
  - `https://yourdomain.com/api/auth/callback/google`

---

## 🛠️ **Troubleshooting**

### **Common Issues:**

#### **Service Won't Start**
```bash
# Check logs
docker-compose -f docker/compose.production.yml logs [service-name]

# Check environment variables
docker-compose -f docker/compose.production.yml config

# Verify file permissions
ls -la .env frontend/.env.local
```

#### **Database Connection Issues**
```bash
# Test database connection
docker run --rm -it postgres:16 psql "postgres://user:password@host:5432/database"

# Check network connectivity
docker network ls
docker network inspect telogical_default
```

#### **SSL Certificate Issues**
```bash
# Check certificate status
sudo certbot certificates

# Renew certificates
sudo certbot renew

# Check Nginx logs
sudo tail -f /var/log/nginx/error.log
```

#### **Frontend Can't Connect to Backend**
```bash
# Verify TELOGICAL_API_URL in frontend
docker-compose -f docker/compose.production.yml exec frontend env | grep TELOGICAL

# Test backend health
curl -f http://localhost:8081/health

# Check internal Docker networking
docker-compose -f docker/compose.production.yml exec frontend ping backend
```

---

## 📊 **Performance Optimization**

### **8.1 Server Resources**
```bash
# Monitor server resources
htop
df -h
free -h

# Optimize Docker
docker system prune -a  # Clean unused images
```

### **8.2 Application Performance**
```yaml
# In compose.production.yml, add resource limits:
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
        reservations:
          memory: 1G
          cpus: '0.5'
```

### **8.3 Database Optimization**
```sql
-- Add indexes for better performance
CREATE INDEX idx_user_email ON "User"(email);
CREATE INDEX idx_chat_user_id ON "Chat"("userId");
CREATE INDEX idx_chat_created_at ON "Chat"("createdAt");
```

---

## 📈 **Scaling Considerations**

### **9.1 Horizontal Scaling**
```bash
# Scale backend instances
docker-compose -f docker/compose.production.yml up -d --scale backend=3

# Load balancer configuration needed for multiple instances
```

### **9.2 Vertical Scaling**
```bash
# Increase server resources (CPU, RAM)
# Update resource limits in Docker Compose
# Consider managed services for database
```

---

## 🎉 **Production Checklist**

### **Pre-Launch:**
- [ ] All environment variables configured
- [ ] SSL certificates installed and working
- [ ] Database migrations completed
- [ ] Google OAuth configured with production domains
- [ ] Backup strategy implemented
- [ ] Monitoring setup completed
- [ ] Security hardening applied

### **Post-Launch:**
- [ ] Test all functionality end-to-end
- [ ] Monitor logs for errors
- [ ] Verify performance metrics
- [ ] Set up alerting
- [ ] Document emergency procedures

---

## 🔧 **Maintenance**

### **Regular Tasks:**
```bash
# Weekly system updates
sudo apt update && sudo apt upgrade -y

# Monthly Docker cleanup
docker system prune -a

# Check SSL certificate expiry
sudo certbot certificates

# Monitor disk space
df -h

# Review application logs
docker-compose -f docker/compose.production.yml logs --tail=100
```

---

## 📞 **Support**

**Server Issues:**
- Check server logs: `/var/log/syslog`
- Monitor resources: `htop`, `df -h`
- Review Nginx logs: `/var/log/nginx/`

**Application Issues:**
- Docker logs: `docker-compose logs`
- Database connectivity: Test connection strings
- Environment variables: Verify all required variables are set

**SSL Issues:**
- Certbot logs: `/var/log/letsencrypt/`
- Nginx configuration: `sudo nginx -t`

Your Telogical Chatbot is now production-ready with Docker! 🚀