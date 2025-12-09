# Deployment Guide

This guide covers deploying the VCF Credentials Manager in production environments.

## Prerequisites

- Linux server (Ubuntu 20.04+ or RHEL 8+ recommended)
- Python 3.8 or higher
- Nginx or Apache (for reverse proxy)
- SSL certificate (Let's Encrypt recommended)
- Firewall access to VCF environments

## Production Deployment with Nginx

### 1. Install Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and pip
sudo apt install python3 python3-pip python3-venv nginx -y

# Install certbot for Let's Encrypt
sudo apt install certbot python3-certbot-nginx -y
```

### 2. Setup Application

```bash
# Create application directory
sudo mkdir -p /opt/vcf-credentials
sudo chown $USER:$USER /opt/vcf-credentials
cd /opt/vcf-credentials

# Copy application files
# (upload your files here)

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Application

```bash
# Create environment file
cat > .env << EOF
SECRET_KEY=$(python3 -c 'import os; print(os.urandom(24).hex())')
SQLALCHEMY_DATABASE_URI=sqlite:////opt/vcf-credentials/vcf_credentials.db
FLASK_ENV=production
EOF

# Initialize database
python app.py &
sleep 5
pkill -f app.py
```

### 4. Create Systemd Service

```bash
sudo tee /etc/systemd/system/vcf-credentials.service > /dev/null << EOF
[Unit]
Description=VCF Credentials Manager
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/opt/vcf-credentials
Environment="PATH=/opt/vcf-credentials/venv/bin"
ExecStart=/opt/vcf-credentials/venv/bin/gunicorn --workers 4 --bind 127.0.0.1:8000 app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable vcf-credentials
sudo systemctl start vcf-credentials
sudo systemctl status vcf-credentials
```

### 5. Configure Nginx

```bash
sudo tee /etc/nginx/sites-available/vcf-credentials > /dev/null << EOF
server {
    listen 80;
    server_name vcf-credentials.example.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # WebSocket support (if needed)
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Increase max body size for file uploads
    client_max_body_size 10M;
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/vcf-credentials /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 6. Setup SSL with Let's Encrypt

```bash
# Obtain certificate
sudo certbot --nginx -d vcf-credentials.example.com

# Test auto-renewal
sudo certbot renew --dry-run
```

### 7. Configure Firewall

```bash
# UFW (Ubuntu)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# Or firewalld (RHEL)
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

## Docker Deployment

### Dockerfile

Create a `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create data directory
RUN mkdir -p /app/data

# Expose port
EXPOSE 5000

# Run application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "app:app"]
```

### Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  vcf-credentials:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - ./data:/app/data
      - ./vcf_credentials.db:/app/vcf_credentials.db
    environment:
      - SECRET_KEY=${SECRET_KEY}
      - SQLALCHEMY_DATABASE_URI=sqlite:////app/vcf_credentials.db
      - FLASK_ENV=production
    restart: unless-stopped
    
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - vcf-credentials
    restart: unless-stopped
```

### Deploy with Docker

```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

## Kubernetes Deployment

### Create Kubernetes Manifests

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vcf-credentials
spec:
  replicas: 2
  selector:
    matchLabels:
      app: vcf-credentials
  template:
    metadata:
      labels:
        app: vcf-credentials
    spec:
      containers:
      - name: vcf-credentials
        image: vcf-credentials:latest
        ports:
        - containerPort: 5000
        env:
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: vcf-credentials-secret
              key: secret-key
        volumeMounts:
        - name: data
          mountPath: /app/data
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: vcf-credentials-pvc

---
apiVersion: v1
kind: Service
metadata:
  name: vcf-credentials
spec:
  selector:
    app: vcf-credentials
  ports:
  - port: 80
    targetPort: 5000
  type: LoadBalancer

---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: vcf-credentials-pvc
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi
```

## Security Hardening

### 1. Database Permissions

```bash
chmod 600 /opt/vcf-credentials/vcf_credentials.db
chown $USER:$USER /opt/vcf-credentials/vcf_credentials.db
```

### 2. Application User

```bash
# Create dedicated user
sudo useradd -r -s /bin/false vcf-credentials
sudo chown -R vcf-credentials:vcf-credentials /opt/vcf-credentials

# Update systemd service
sudo sed -i 's/User=.*/User=vcf-credentials/' /etc/systemd/system/vcf-credentials.service
sudo systemctl daemon-reload
sudo systemctl restart vcf-credentials
```

### 3. SELinux (RHEL/CentOS)

```bash
# Set SELinux context
sudo semanage fcontext -a -t httpd_sys_content_t "/opt/vcf-credentials(/.*)?"
sudo restorecon -Rv /opt/vcf-credentials

# Allow network connections
sudo setsebool -P httpd_can_network_connect 1
```

### 4. Rate Limiting (Nginx)

Add to Nginx configuration:

```nginx
limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;

location /login {
    limit_req zone=login burst=2 nodelay;
    proxy_pass http://127.0.0.1:8000;
    # ... other proxy settings
}
```

## Backup and Recovery

### Automated Backup Script

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backup/vcf-credentials"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup database
cp /opt/vcf-credentials/vcf_credentials.db $BACKUP_DIR/vcf_credentials_$DATE.db

# Backup configuration
cp /opt/vcf-credentials/.env $BACKUP_DIR/env_$DATE

# Keep only last 30 days
find $BACKUP_DIR -name "*.db" -mtime +30 -delete

# Compress old backups
find $BACKUP_DIR -name "*.db" -mtime +7 ! -name "*.gz" -exec gzip {} \;
```

### Cron Job

```bash
# Add to crontab
crontab -e

# Daily backup at 2 AM
0 2 * * * /opt/vcf-credentials/backup.sh
```

## Monitoring

### Health Check Endpoint

Add to `app.py`:

```python
@app.route('/health')
def health():
    return jsonify({'status': 'healthy'}), 200
```

### Prometheus Metrics (Optional)

```bash
pip install prometheus-flask-exporter
```

## Troubleshooting

### Check Service Status

```bash
sudo systemctl status vcf-credentials
sudo journalctl -u vcf-credentials -f
```

### Check Nginx Logs

```bash
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Test Application Directly

```bash
curl http://localhost:8000/health
```

## Performance Tuning

### Gunicorn Workers

Calculate optimal workers:

```bash
# Formula: (2 x CPU cores) + 1
WORKERS=$((2 * $(nproc) + 1))
```

Update systemd service:

```bash
ExecStart=/opt/vcf-credentials/venv/bin/gunicorn --workers $WORKERS --bind 127.0.0.1:8000 app:app
```

### Database Optimization

```bash
# Vacuum database regularly
sqlite3 /opt/vcf-credentials/vcf_credentials.db "VACUUM;"
```

## Maintenance

### Update Application

```bash
cd /opt/vcf-credentials
git pull  # or upload new files
source venv/bin/activate
pip install -r requirements.txt --upgrade
sudo systemctl restart vcf-credentials
```

### Database Migration

```bash
# Backup first!
cp vcf_credentials.db vcf_credentials.db.backup

# Run migrations if needed
python migrate.py  # if you create migration scripts
```

