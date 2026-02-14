# Ubuntu Service Installation Guide

Automated installation script for VCF Credential Manager on Ubuntu 24.04 as a systemd service.

---

## Quick Start

### Option 1: Download Release Bundle

```bash
# 1. Download the latest release
wget https://github.com/cleeistaken/vcf-credential-manager/releases/latest/download/vcf-credential-manager-rel-vX.X.X.zip

# 2. Extract the archive (extracts to vcf-credential-manager-rel-vX.X.X/)
unzip vcf-credential-manager-rel-vX.X.X.zip
# Or using tar:
# tar -xzf vcf-credential-manager-rel-vX.X.X.tar.gz

# 3. Run installation
cd vcf-credential-manager-rel-vX.X.X/tools
sudo ./install-vcf-credential-manager.sh

# 4. Access application
https://localhost
```

### Option 2: Clone Repository

```bash
# 1. Clone the repository
git clone https://github.com/cleeistaken/vcf-credential-manager.git
cd vcf-credential-manager/tools

# 2. Run installation
sudo ./install-vcf-credential-manager.sh

# 3. Access application
https://localhost
```

**Default login:** admin / admin

**Change password immediately after first login!**

---

## What Gets Installed

- VCF Credential Manager application (copied from local files)
- Python 3.9+ with pipenv environment
- Self-signed SSL certificates
- Systemd service (auto-start on boot)
- HTTPS on port 443
- Firewall configuration (UFW)

**Installation location:** `/opt/vcf-credential-manager`

---

## Requirements

- Ubuntu 24.04 LTS
- Root/sudo access
- 2GB RAM, 5GB disk space
- Port 443 available
- Internet connection (for installing system dependencies)

---

## Service Management

```bash
# Check status
sudo systemctl status vcf-credential-manager

# Start/Stop/Restart
sudo systemctl start vcf-credential-manager
sudo systemctl stop vcf-credential-manager
sudo systemctl restart vcf-credential-manager

# View logs
sudo journalctl -u vcf-credential-manager -f
sudo tail -f /opt/vcf-credential-manager/logs/vcf_credentials.log
```

---

## Uninstall

```bash
cd tools
sudo ./uninstall-vcf-credential-manager.sh
```

**Warning:** This deletes all data including the database!

---

## Customization

### Change Port from 443

```bash
# Edit startup script
sudo nano /opt/vcf-credential-manager/start_https_443.sh
# Change: --bind 0.0.0.0:443
# To:     --bind 0.0.0.0:8443

# Update firewall
sudo ufw allow 8443/tcp
sudo ufw delete allow 443/tcp

# Restart
sudo systemctl restart vcf-credential-manager
```

### Use Custom SSL Certificates

```bash
# Copy your certificates
sudo cp your-cert.pem /opt/vcf-credential-manager/ssl/cert.pem
sudo cp your-key.pem /opt/vcf-credential-manager/ssl/key.pem

# Set permissions
sudo chmod 644 /opt/vcf-credential-manager/ssl/cert.pem
sudo chmod 600 /opt/vcf-credential-manager/ssl/key.pem

# Restart
sudo systemctl restart vcf-credential-manager
```

---

## Directory Structure

```
/opt/vcf-credential-manager/
├── app.py                    # Flask application
├── start_https_443.sh        # Startup script (port 443)
├── ssl/                      # SSL certificates
├── logs/                     # Application logs
├── instance/                 # SQLite database
└── .venv/                    # Python virtual environment
```

---

## Troubleshooting

### Installation fails with "externally-managed-environment"

**Fixed automatically.** Script uses `--break-system-packages` for pipenv.

### Installation fails with "Python X.X.X was not found"

**Fixed automatically.** Script configures app to use Python 3.12.

### Service fails with "Permission denied"

**Fixed automatically.** Script sets correct ownership (root:root).

### Service hangs during startup

**Fixed automatically.** Script uses `Type=exec` in systemd service.

### Port 443 Already in Use

```bash
# Check what's using the port
sudo netstat -tlnp | grep :443

# Stop conflicting service
sudo systemctl stop nginx  # or apache2
```

### Cannot Access from Remote Host

```bash
# Check firewall
sudo ufw status | grep 443

# Add firewall rule if needed
sudo ufw allow 443/tcp
```

### Database Errors

```bash
# Reset database (backup first!)
sudo systemctl stop vcf-credential-manager
sudo cp /opt/vcf-credential-manager/instance/vcf_credentials.db ~/backup/
sudo rm /opt/vcf-credential-manager/instance/vcf_credentials.db
sudo systemctl start vcf-credential-manager
```

### SSL Certificate Errors

```bash
# Regenerate certificates
sudo systemctl stop vcf-credential-manager
sudo rm /opt/vcf-credential-manager/ssl/*.pem
cd /opt/vcf-credential-manager
sudo openssl req -x509 -newkey rsa:4096 -nodes \
    -keyout ssl/key.pem -out ssl/cert.pem -days 365 \
    -subj "/C=US/ST=State/L=City/O=Organization/OU=IT/CN=vcf-credential-manager"
sudo chmod 644 ssl/cert.pem
sudo chmod 600 ssl/key.pem
sudo systemctl start vcf-credential-manager
```

---

## Quick Diagnostic Commands

```bash
# Check service status
sudo systemctl status vcf-credential-manager

# View recent logs
sudo journalctl -u vcf-credential-manager -n 50

# Check if listening on port 443
sudo netstat -tlnp | grep :443

# Check firewall
sudo ufw status

# Check file permissions
ls -la /opt/vcf-credential-manager/

# Test HTTPS access
curl -k https://localhost
```

---

## Backup

```bash
# Backup database
sudo cp /opt/vcf-credential-manager/instance/vcf_credentials.db ~/backup/

# Backup SSL certificates (if custom)
sudo cp /opt/vcf-credential-manager/ssl/*.pem ~/backup/
```

---

## Update Application

### Option 1: Use the Update Script (Recommended)

The update script preserves your database, SSL certificates, and logs while updating the application code.

```bash
# 1. Download the new release
wget https://github.com/cleeistaken/vcf-credential-manager/releases/latest/download/vcf-credential-manager-rel-vX.X.X.zip

# 2. Extract the archive (extracts to vcf-credential-manager-rel-vX.X.X/)
unzip vcf-credential-manager-rel-vX.X.X.zip
# Or using tar:
# tar -xzf vcf-credential-manager-rel-vX.X.X.tar.gz

# 3. Run the update script
cd vcf-credential-manager-rel-vX.X.X/tools
sudo ./update-vcf-credential-manager.sh
```

**Update script options:**
```bash
# Normal update with automatic backup
sudo ./update-vcf-credential-manager.sh

# Update without creating a backup
sudo ./update-vcf-credential-manager.sh --no-backup

# Force update even if versions match
sudo ./update-vcf-credential-manager.sh --force

# Show help
sudo ./update-vcf-credential-manager.sh --help
```

**What the update script preserves:**
- Database (credentials, environments, users)
- SSL certificates
- Log files

**What gets updated:**
- Application code
- Static files (CSS, JS, images)
- Templates
- Python dependencies

**Rollback:** Backups are stored in `/opt/vcf-credential-manager-backups/`. To rollback:
```bash
sudo systemctl stop vcf-credential-manager
sudo cp -a /opt/vcf-credential-manager-backups/backup_YYYYMMDD_HHMMSS/installation/* /opt/vcf-credential-manager/
sudo systemctl start vcf-credential-manager
```

### Option 2: Re-run Installer (Fresh Install)

This creates a backup of the existing installation but does NOT preserve the database.

```bash
# 1. Backup your database first!
sudo cp /opt/vcf-credential-manager/instance/vcf_credentials.db ~/backup/

# 2. Download the new release
wget https://github.com/cleeistaken/vcf-credential-manager/releases/latest/download/vcf-credential-manager-rel-vX.X.X.zip

# 3. Extract and run installer (extracts to vcf-credential-manager-rel-vX.X.X/)
unzip vcf-credential-manager-rel-vX.X.X.zip
cd vcf-credential-manager-rel-vX.X.X/tools
sudo ./install-vcf-credential-manager.sh

# 4. Restore database (optional)
sudo systemctl stop vcf-credential-manager
sudo cp ~/backup/vcf_credentials.db /opt/vcf-credential-manager/instance/
sudo systemctl start vcf-credential-manager
```

### Option 3: Manual Update

```bash
# Stop service
sudo systemctl stop vcf-credential-manager

# Backup database
sudo cp /opt/vcf-credential-manager/instance/vcf_credentials.db ~/backup/

# Copy new files (from your downloaded/cloned source)
sudo rsync -av --exclude='.git' --exclude='instance' --exclude='logs' \
    /path/to/new/vcf-credential-manager/ /opt/vcf-credential-manager/

# Update dependencies
cd /opt/vcf-credential-manager
sudo PIPENV_VENV_IN_PROJECT=1 pipenv install --skip-lock

# Restart service
sudo systemctl start vcf-credential-manager
```

---

## Advanced Configuration

### Adjust Gunicorn Workers

```bash
# Edit Gunicorn config
sudo nano /opt/vcf-credential-manager/gunicorn_config.py

# Adjust these values:
workers = 4  # (2 x CPU cores) + 1
threads = 2  # Threads per worker
```

**Recommended settings by system size:**
- Small (2 cores, 4GB RAM): workers=2, threads=2
- Medium (4 cores, 8GB RAM): workers=4, threads=2
- Large (8 cores, 16GB RAM): workers=8, threads=4

### Run as Non-Root User (Port > 1024)

```bash
# 1. Change port to 8443 (see above)

# 2. Edit service file
sudo nano /etc/systemd/system/vcf-credential-manager.service
# Change: User=root → User=vcfcredmgr
# Change: Group=root → Group=vcfcredmgr

# 3. Fix ownership
sudo chown -R vcfcredmgr:vcfcredmgr /opt/vcf-credential-manager

# 4. Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart vcf-credential-manager
```

### Use Let's Encrypt Certificates

```bash
# 1. Install certbot
sudo apt-get install certbot

# 2. Get certificate (requires DNS/HTTP validation)
sudo certbot certonly --standalone -d your-domain.com

# 3. Copy certificates
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem \
    /opt/vcf-credential-manager/ssl/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem \
    /opt/vcf-credential-manager/ssl/key.pem

# 4. Set permissions and restart
sudo chmod 644 /opt/vcf-credential-manager/ssl/cert.pem
sudo chmod 600 /opt/vcf-credential-manager/ssl/key.pem
sudo systemctl restart vcf-credential-manager
```

### Log Rotation

```bash
sudo nano /etc/logrotate.d/vcf-credential-manager
```

Add:
```
/opt/vcf-credential-manager/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    missingok
    create 0640 root root
    sharedscripts
    postrotate
        systemctl reload vcf-credential-manager > /dev/null 2>&1 || true
    endscript
}
```

---

## Additional Documentation

- [Deployment Guide](DEPLOYMENT.md) - Production deployment options
- [Troubleshooting](TROUBLESHOOTING.md) - General troubleshooting
- [User Management](USER_MANAGEMENT.md) - Users, roles, and SSL certificates

---

**Made for VMware Cloud Foundation administrators**
