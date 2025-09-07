#!/bin/bash

# Production Deployment Script for Tutoring Assistant

set -e  # Exit on any error

echo "🚀 Starting Production Deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if .env file exists
if [ ! -f ".env" ]; then
    print_error ".env file not found!"
    print_warning "Please copy env.production to .env and update with your values:"
    echo "  cp env.production .env"
    echo "  # Edit .env with your actual configuration"
    exit 1
fi

# Check if required environment variables are set
print_status "Checking environment configuration..."

required_vars=(
    "DATABASE_URL"
    "JWT_SECRET_KEY"
    "OPENAI_API_KEY"
    "AWS_ACCESS_KEY_ID"
    "AWS_SECRET_ACCESS_KEY"
    "S3_BUCKET"
    "ENCRYPTION_KEY"
)

for var in "${required_vars[@]}"; do
    if ! grep -q "^${var}=" .env || grep -q "^${var}=your_" .env; then
        print_error "Please set ${var} in your .env file"
        exit 1
    fi
done

print_status "Environment configuration looks good!"

# Install dependencies
print_status "Installing Python dependencies..."
pip3 install -r requirements-simple.txt

# Install production dependencies
print_status "Installing production dependencies..."
pip3 install gunicorn psycopg2-binary

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p logs
mkdir -p uploads
mkdir -p vector_storage

# Set proper permissions
print_status "Setting permissions..."
chmod 755 logs uploads vector_storage

# Test database connection
print_status "Testing database connection..."
python3 -c "
from app.core.database import engine
from app.models import user, content as content_models, chat as chat_models, quiz as quiz_models
print('Creating/updating database tables...')
user.Base.metadata.create_all(bind=engine)
content_models.Base.metadata.create_all(bind=engine)
chat_models.Base.metadata.create_all(bind=engine)
quiz_models.Base.metadata.create_all(bind=engine)
print('✅ Database setup complete!')
"

# Create systemd service file (for Linux)
if command -v systemctl &> /dev/null; then
    print_status "Creating systemd service..."
    sudo tee /etc/systemd/system/tutoring-assistant.service > /dev/null <<EOF
[Unit]
Description=Tutoring Assistant API
After=network.target

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=$(pwd)
Environment=PATH=$(which python3)
ExecStart=$(which gunicorn) -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 app.main:app
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

    print_status "Enabling and starting service..."
    sudo systemctl daemon-reload
    sudo systemctl enable tutoring-assistant
    sudo systemctl start tutoring-assistant
    sudo systemctl status tutoring-assistant --no-pager
fi

# Create nginx configuration (if nginx is available)
if command -v nginx &> /dev/null; then
    print_status "Creating nginx configuration..."
    sudo tee /etc/nginx/sites-available/tutoring-assistant > /dev/null <<EOF
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /static/ {
        alias $(pwd)/static/;
    }

    location /uploads/ {
        alias $(pwd)/uploads/;
    }
}
EOF

    print_warning "Please update the nginx configuration with your actual domain name"
    print_warning "Then run: sudo ln -s /etc/nginx/sites-available/tutoring-assistant /etc/nginx/sites-enabled/"
    print_warning "And: sudo nginx -t && sudo systemctl reload nginx"
fi

# Create monitoring script
print_status "Creating monitoring script..."
cat > monitor.sh <<'EOF'
#!/bin/bash
# Simple monitoring script

echo "=== Tutoring Assistant Status ==="
echo "Date: $(date)"
echo

# Check if service is running
if systemctl is-active --quiet tutoring-assistant; then
    echo "✅ Service: Running"
else
    echo "❌ Service: Not running"
fi

# Check database connection
if python3 -c "from app.core.database import engine; engine.connect(); print('✅ Database: Connected')" 2>/dev/null; then
    echo "✅ Database: Connected"
else
    echo "❌ Database: Connection failed"
fi

# Check disk space
echo "💾 Disk Usage:"
df -h | grep -E "(Filesystem|/dev/)"

# Check memory usage
echo "🧠 Memory Usage:"
free -h

# Check recent logs
echo "📋 Recent Logs:"
journalctl -u tutoring-assistant --since "5 minutes ago" --no-pager | tail -10
EOF

chmod +x monitor.sh

print_status "🎉 Production deployment complete!"
print_status "Next steps:"
echo "1. Update your domain name in nginx configuration"
echo "2. Set up SSL certificates (Let's Encrypt recommended)"
echo "3. Configure monitoring and alerting"
echo "4. Set up automated backups"
echo "5. Run './monitor.sh' to check system status"

print_status "To start the service manually:"
echo "  gunicorn -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 app.main:app"

print_status "To check logs:"
echo "  journalctl -u tutoring-assistant -f"
