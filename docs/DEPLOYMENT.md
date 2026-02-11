# Deployment Guide

## Quick Start (Development)

```bash
pip install -r requirements.txt
./start_https.sh
```

## Production with Systemd

### 1. Setup Application

```bash
# Create directory
sudo mkdir -p /opt/vcf-credentials
cd /opt/vcf-credentials

# Copy files and create venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Create Systemd Service

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

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable vcf-credentials
sudo systemctl start vcf-credentials
```

### 3. Configure Nginx (Optional)

```nginx
server {
    listen 443 ssl;
    server_name vcf-credentials.example.com;
    
    ssl_certificate /etc/ssl/certs/server.crt;
    ssl_certificate_key /etc/ssl/private/server.key;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Docker

### Dockerfile

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "app:app"]
```

### Docker Compose

```yaml
version: '3.8'
services:
  vcf-credentials:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - ./instance:/app/instance
    environment:
      - SECRET_KEY=${SECRET_KEY}
    restart: unless-stopped
```

```bash
docker-compose up -d
```

## Security Checklist

- [ ] Change default admin password
- [ ] Use CA-signed SSL certificates
- [ ] Restrict network access (firewall)
- [ ] Secure database file: `chmod 600 instance/vcf_credentials.db`
- [ ] Set strong SECRET_KEY
- [ ] Regular backups of database

## Backup

```bash
# Backup database
cp /opt/vcf-credentials/instance/vcf_credentials.db /backup/vcf_$(date +%Y%m%d).db

# Cron job for daily backups
0 2 * * * cp /opt/vcf-credentials/instance/vcf_credentials.db /backup/vcf_$(date +\%Y\%m\%d).db
```

## Maintenance

```bash
# Update application
cd /opt/vcf-credentials
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart vcf-credentials

# View logs
sudo journalctl -u vcf-credentials -f
```
