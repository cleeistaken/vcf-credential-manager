# Gunicorn Deployment Guide

## Understanding the SSL Error

The error you're seeing:
```
Invalid request from ip=127.0.0.1: [SSL: SSLV3_ALERT_ILLEGAL_PARAMETER] sslv3 alert illegal parameter
```

This happens when:
1. A client tries to connect with HTTPS
2. But Gunicorn is running in HTTP mode (no SSL configured)
3. Or SSL certificates are missing/invalid

## Solutions

### Option 1: HTTP Only (Recommended for Development)

Run Gunicorn without SSL:

```bash
./run_gunicorn.sh
```

Or manually:
```bash
gunicorn --config gunicorn_config.py app:app
```

**Access:** http://localhost:5000 (HTTP, not HTTPS)

**Pros:**
- ✅ Simple setup
- ✅ No certificate needed
- ✅ Fast startup
- ✅ Good for development/testing

**Cons:**
- ❌ No encryption
- ❌ Not suitable for production

---

### Option 2: HTTPS with Self-Signed Certificate (Development/Testing)

Run Gunicorn with auto-generated self-signed certificate:

```bash
./run_gunicorn_https.sh
```

This script will:
1. Check if SSL certificates exist
2. Generate self-signed certificate if needed
3. Start Gunicorn with HTTPS

**Access:** https://localhost:5000 (HTTPS)

**Browser Warning:**
You'll see a security warning because it's self-signed. This is normal.
- Chrome: Click "Advanced" → "Proceed to localhost (unsafe)"
- Firefox: Click "Advanced" → "Accept the Risk and Continue"

**Pros:**
- ✅ Encrypted connection
- ✅ Tests HTTPS functionality
- ✅ Auto-generates certificate

**Cons:**
- ⚠️ Browser security warnings
- ❌ Not trusted by browsers
- ❌ Not suitable for production

---

### Option 3: HTTPS with Valid Certificate (Production)

For production, use a reverse proxy (Nginx/Apache) with a valid SSL certificate.

#### Step 1: Get SSL Certificate

**Option A: Let's Encrypt (Free, Recommended)**
```bash
sudo certbot certonly --standalone -d yourdomain.com
```

**Option B: Commercial Certificate**
Purchase from a certificate authority.

**Option C: Self-Signed (Not Recommended for Production)**
```bash
mkdir -p ssl
openssl req -x509 -newkey rsa:4096 -nodes \
    -out ssl/cert.pem \
    -keyout ssl/key.pem \
    -days 365
```

#### Step 2: Configure Nginx as Reverse Proxy

**Install Nginx:**
```bash
sudo apt install nginx  # Ubuntu/Debian
sudo yum install nginx  # RHEL/CentOS
```

**Create Nginx Configuration:**
```bash
sudo nano /etc/nginx/sites-available/vcf-credentials
```

**Configuration:**
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    client_max_body_size 10M;
}
```

**Enable Site:**
```bash
sudo ln -s /etc/nginx/sites-available/vcf-credentials /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### Step 3: Run Gunicorn (HTTP Only)

Since Nginx handles SSL, run Gunicorn in HTTP mode:

```bash
./run_gunicorn.sh
```

Or with systemd:
```bash
sudo systemctl start vcf-credentials
```

**Pros:**
- ✅ Production-ready
- ✅ Trusted SSL certificate
- ✅ No browser warnings
- ✅ Better performance
- ✅ Load balancing capable

---

## Configuration Files

### gunicorn_config.py

Pre-configured settings:
- **Workers:** Auto-calculated based on CPU cores
- **Bind:** 0.0.0.0:5000
- **Timeout:** 30 seconds
- **Logging:** Automatic to logs/ directory

**Customize:**
```python
# Edit gunicorn_config.py
workers = 4  # Number of worker processes
timeout = 60  # Request timeout in seconds
bind = "0.0.0.0:8000"  # Change port
```

### Startup Scripts

**run_gunicorn.sh** - HTTP mode
- Simple startup
- No SSL
- Development/testing

**run_gunicorn_https.sh** - HTTPS mode
- Auto-generates certificate
- Self-signed SSL
- Testing HTTPS functionality

---

## Common Issues

### Issue 1: SSL Error (Your Current Issue)

**Problem:** Client connects with HTTPS but Gunicorn is HTTP

**Solution:**
```bash
# Use HTTP (recommended)
./run_gunicorn.sh
# Access: http://localhost:5000

# OR use HTTPS
./run_gunicorn_https.sh
# Access: https://localhost:5000
```

**Important:** Match your URL scheme to your Gunicorn mode:
- HTTP mode → http://localhost:5000
- HTTPS mode → https://localhost:5000

---

### Issue 2: Port Already in Use

**Error:** `[ERROR] Connection in use: ('0.0.0.0', 5000)`

**Solution:**
```bash
# Find process using port 5000
lsof -i :5000

# Kill it
kill -9 <PID>

# Or use different port
gunicorn --bind 0.0.0.0:8000 app:app
```

---

### Issue 3: Workers Dying

**Error:** `[CRITICAL] WORKER TIMEOUT`

**Solution:**
```bash
# Increase timeout
gunicorn --timeout 120 app:app

# Or reduce workers
gunicorn --workers 2 app:app
```

---

### Issue 4: Permission Denied (Logs)

**Error:** `[ERROR] Error opening file for writing`

**Solution:**
```bash
# Create logs directory
mkdir -p logs

# Fix permissions
chmod 755 logs
```

---

## Performance Tuning

### Calculate Optimal Workers

```python
# Formula: (2 x CPU cores) + 1
import multiprocessing
workers = multiprocessing.cpu_count() * 2 + 1
```

**Example:**
- 2 CPU cores → 5 workers
- 4 CPU cores → 9 workers
- 8 CPU cores → 17 workers

### Worker Types

**sync** (default) - Good for most cases
```bash
gunicorn --worker-class sync app:app
```

**gevent** - Better for I/O bound tasks
```bash
pip install gevent
gunicorn --worker-class gevent app:app
```

**gthread** - Thread-based workers
```bash
gunicorn --worker-class gthread --threads 4 app:app
```

---

## Monitoring

### View Logs

```bash
# Access log
tail -f logs/gunicorn_access.log

# Error log
tail -f logs/gunicorn_error.log

# Application log
tail -f logs/vcf_credentials.log
```

### Check Status

```bash
# If using systemd
sudo systemctl status vcf-credentials

# Check process
ps aux | grep gunicorn

# Check port
netstat -tlnp | grep 5000
```

---

## Systemd Service (Production)

Create service file:

```bash
sudo nano /etc/systemd/system/vcf-credentials.service
```

**Content:**
```ini
[Unit]
Description=VCF Credentials Manager
After=network.target

[Service]
Type=simple
User=vcfuser
WorkingDirectory=/opt/vcf-credentials
Environment="PATH=/opt/vcf-credentials/venv/bin"
ExecStart=/opt/vcf-credentials/venv/bin/gunicorn --config gunicorn_config.py app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable and start:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable vcf-credentials
sudo systemctl start vcf-credentials
sudo systemctl status vcf-credentials
```

---

## Quick Reference

### Development (HTTP)
```bash
./run_gunicorn.sh
# Access: http://localhost:5000
```

### Testing HTTPS (Self-Signed)
```bash
./run_gunicorn_https.sh
# Access: https://localhost:5000
# Expect browser warning
```

### Production (Nginx + Gunicorn)
```bash
# Setup Nginx with SSL
sudo systemctl start nginx

# Run Gunicorn (HTTP)
./run_gunicorn.sh

# Access: https://yourdomain.com
```

### Manual Commands
```bash
# HTTP
gunicorn --bind 0.0.0.0:5000 --workers 4 app:app

# HTTPS
gunicorn --certfile=ssl/cert.pem --keyfile=ssl/key.pem --bind 0.0.0.0:5000 app:app

# With config file
gunicorn --config gunicorn_config.py app:app
```

---

## Best Practices

### Development
- ✅ Use HTTP mode (`./run_gunicorn.sh`)
- ✅ Use Flask development server for debugging (`python app.py`)
- ✅ Use self-signed cert for HTTPS testing

### Production
- ✅ Use reverse proxy (Nginx/Apache)
- ✅ Use valid SSL certificate (Let's Encrypt)
- ✅ Run Gunicorn as systemd service
- ✅ Use HTTP between Nginx and Gunicorn
- ✅ Monitor logs regularly
- ✅ Set up log rotation

---

## Troubleshooting Checklist

- [ ] Check if using correct URL scheme (http:// vs https://)
- [ ] Verify SSL certificates exist (if using HTTPS)
- [ ] Check port is not in use
- [ ] Verify logs directory exists
- [ ] Check file permissions
- [ ] Ensure virtual environment is activated
- [ ] Verify all dependencies installed
- [ ] Check firewall rules
- [ ] Review Gunicorn logs
- [ ] Test with curl: `curl -v http://localhost:5000`

---

## Summary

**Your SSL Error Fix:**

The error happens because you're connecting with HTTPS but Gunicorn is running HTTP.

**Quick Fix:**
```bash
# Use HTTP (no SSL)
./run_gunicorn.sh
# Access: http://localhost:5000 (not https://)
```

**Or for HTTPS:**
```bash
# Use HTTPS (with SSL)
./run_gunicorn_https.sh
# Access: https://localhost:5000 (with https://)
```

**Production Setup:**
Use Nginx with valid SSL certificate + Gunicorn in HTTP mode.

---

All scripts are ready to use! Just choose the appropriate one for your needs. 🚀

