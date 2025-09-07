# 🚀 Production Deployment Guide

This guide will walk you through deploying the Tutoring Assistant to production.

## Prerequisites

- Ubuntu 20.04+ or similar Linux distribution
- Docker and Docker Compose installed
- Domain name pointing to your server
- SSL certificate (Let's Encrypt recommended)

## Step 1: Server Setup

### 1.1 Update your server
```bash
sudo apt update && sudo apt upgrade -y
```

### 1.2 Install Docker and Docker Compose
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 1.3 Install additional tools
```bash
sudo apt install -y nginx certbot python3-certbot-nginx
```

## Step 2: Application Setup

### 2.1 Clone and prepare the application
```bash
git clone <your-repo-url>
cd tutoring-assistant
```

### 2.2 Configure environment variables
```bash
# Copy the production environment template
cp env.production.example .env.production

# Edit with your actual values
nano .env.production
```

**Required environment variables:**
- `POSTGRES_PASSWORD`: Strong password for PostgreSQL
- `JWT_SECRET_KEY`: Random string (minimum 32 characters)
- `ENCRYPTION_KEY`: 32-byte encryption key
- `OPENAI_API_KEY`: Your OpenAI API key
- `AWS_ACCESS_KEY_ID`: AWS access key
- `AWS_SECRET_ACCESS_KEY`: AWS secret key
- `S3_BUCKET`: S3 bucket name for file storage

### 2.3 Generate secure keys
```bash
# Generate JWT secret key
openssl rand -base64 32

# Generate encryption key
openssl rand -base64 32
```

## Step 3: Database Setup

### 3.1 Start PostgreSQL
```bash
# Using Docker Compose
docker-compose -f docker-compose.production.yml up -d db

# Wait for database to be ready
docker-compose -f docker-compose.production.yml logs db
```

### 3.2 Create database tables
```bash
# Run database migrations
docker-compose -f docker-compose.production.yml run --rm app python -c "
from app.core.database import engine
from app.models import user, content as content_models, chat as chat_models, quiz as quiz_models
user.Base.metadata.create_all(bind=engine)
content_models.Base.metadata.create_all(bind=engine)
chat_models.Base.metadata.create_all(bind=engine)
quiz_models.Base.metadata.create_all(bind=engine)
print('Database tables created successfully!')
"
```

## Step 4: Deploy with Docker

### 4.1 Start all services
```bash
docker-compose -f docker-compose.production.yml up -d
```

### 4.2 Check service status
```bash
docker-compose -f docker-compose.production.yml ps
```

### 4.3 View logs
```bash
# All services
docker-compose -f docker-compose.production.yml logs -f

# Specific service
docker-compose -f docker-compose.production.yml logs -f app
```

## Step 5: Configure Nginx

### 5.1 Update nginx configuration
```bash
# Edit nginx.conf and update your domain name
nano nginx.conf
```

### 5.2 Copy nginx configuration
```bash
sudo cp nginx.conf /etc/nginx/sites-available/tutoring-assistant
sudo ln -s /etc/nginx/sites-available/tutoring-assistant /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Step 6: SSL Certificate

### 6.1 Get SSL certificate with Let's Encrypt
```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

### 6.2 Test SSL renewal
```bash
sudo certbot renew --dry-run
```

## Step 7: Monitoring and Maintenance

### 7.1 Set up monitoring
```bash
# Install monitoring tools
sudo apt install -y htop iotop nethogs

# Create monitoring script
chmod +x scripts/deploy_production.sh
./scripts/deploy_production.sh
```

### 7.2 Set up automated backups
```bash
# Create backup script
cat > backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/backups/tutoring-assistant"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup database
docker-compose -f docker-compose.production.yml exec -T db pg_dump -U postgres tutoring_assistant_prod > $BACKUP_DIR/db_$DATE.sql

# Backup uploads
tar -czf $BACKUP_DIR/uploads_$DATE.tar.gz uploads/

# Keep only last 7 days of backups
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
EOF

chmod +x backup.sh

# Add to crontab
echo "0 2 * * * /path/to/backup.sh" | crontab -
```

### 7.3 Set up log rotation
```bash
# Create logrotate configuration
sudo tee /etc/logrotate.d/tutoring-assistant << 'EOF'
/var/log/tutoring-assistant/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
}
EOF
```

## Step 8: Security Hardening

### 8.1 Configure firewall
```bash
# Install UFW
sudo apt install -y ufw

# Configure firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

### 8.2 Set up fail2ban
```bash
# Install fail2ban
sudo apt install -y fail2ban

# Configure fail2ban
sudo tee /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[nginx-http-auth]
enabled = true

[nginx-limit-req]
enabled = true
EOF

sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

## Step 9: Performance Optimization

### 9.1 Configure Redis
```bash
# Edit Redis configuration for production
docker-compose -f docker-compose.production.yml exec redis redis-cli CONFIG SET maxmemory 256mb
docker-compose -f docker-compose.production.yml exec redis redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

### 9.2 Optimize PostgreSQL
```bash
# Create PostgreSQL configuration
docker-compose -f docker-compose.production.yml exec db psql -U postgres -c "
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;
SELECT pg_reload_conf();
"
```

## Step 10: Testing

### 10.1 Test all endpoints
```bash
# Health check
curl https://yourdomain.com/health

# API endpoints
curl https://yourdomain.com/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","username":"test","password":"password123","first_name":"Test","last_name":"User","tenant_name":"Test University"}'
```

### 10.2 Load testing
```bash
# Install Apache Bench
sudo apt install -y apache2-utils

# Run load test
ab -n 1000 -c 10 https://yourdomain.com/health
```

## Troubleshooting

### Common Issues

1. **Database connection failed**
   ```bash
   # Check if PostgreSQL is running
   docker-compose -f docker-compose.production.yml ps db
   
   # Check logs
   docker-compose -f docker-compose.production.yml logs db
   ```

2. **Application not starting**
   ```bash
   # Check application logs
   docker-compose -f docker-compose.production.yml logs app
   
   # Check environment variables
   docker-compose -f docker-compose.production.yml exec app env | grep -E "(DATABASE|JWT|OPENAI)"
   ```

3. **Nginx 502 Bad Gateway**
   ```bash
   # Check if application is running
   docker-compose -f docker-compose.production.yml ps app
   
   # Check nginx logs
   sudo tail -f /var/log/nginx/error.log
   ```

### Monitoring Commands

```bash
# Check service status
docker-compose -f docker-compose.production.yml ps

# Check resource usage
docker stats

# Check logs
docker-compose -f docker-compose.production.yml logs -f

# Check database
docker-compose -f docker-compose.production.yml exec db psql -U postgres -d tutoring_assistant_prod -c "SELECT COUNT(*) FROM users;"
```

## Maintenance

### Regular Tasks

1. **Update application**
   ```bash
   git pull
   docker-compose -f docker-compose.production.yml build app
   docker-compose -f docker-compose.production.yml up -d app
   ```

2. **Database maintenance**
   ```bash
   # Vacuum database
   docker-compose -f docker-compose.production.yml exec db psql -U postgres -d tutoring_assistant_prod -c "VACUUM ANALYZE;"
   ```

3. **Monitor disk space**
   ```bash
   df -h
   docker system prune -f
   ```

## Support

For issues and questions:
1. Check the logs first
2. Review this guide
3. Check the GitHub issues
4. Contact support

---

**Congratulations!** Your Tutoring Assistant is now running in production! 🎉
