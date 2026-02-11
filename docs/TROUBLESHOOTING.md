# Troubleshooting

## Debug Mode

Enable verbose logging for troubleshooting:

```bash
# Method 1: Use debug script
./start_https_debug.sh

# Method 2: Environment variable
DEBUG_MODE=true ./start_https.sh
```

View logs:
```bash
tail -f logs/vcf_credentials.log
```

## Common Issues

### Database Errors on Startup

```bash
# Delete database and restart (loses all data)
rm instance/vcf_credentials.db
./start_https.sh
```

### Cannot Login

Default credentials: `admin` / `admin`

Reset admin password:
```bash
python -c "
from app import app, db, User
from werkzeug.security import generate_password_hash
with app.app_context():
    user = User.query.filter_by(username='admin').first()
    user.password_hash = generate_password_hash('admin')
    db.session.commit()
"
```

### Connection Errors to VCF

1. Verify hostname is reachable: `ping vcf-host.example.com`
2. Check credentials are correct
3. Disable SSL verification for self-signed certificates
4. Check firewall rules

Test with curl:
```bash
curl -k -X POST https://vcf-installer.example.com/v1/tokens \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}'
```

### No Credentials Fetched

1. Use "Test Connection" when editing environment
2. Check logs for specific errors
3. Verify API access for the user account
4. Ensure VCF/SDDC Manager is responding

### Gunicorn Won't Start

```bash
# Check if already running
ps aux | grep gunicorn

# Kill existing processes
pkill -f gunicorn

# Restart
./start_https.sh
```

## SSL Issues

### Browser Shows Certificate Warning

This is normal for self-signed certificates. Click "Advanced" → "Proceed" in your browser.

To regenerate certificate with proper hostname:
```bash
./tools/regenerate_ssl_cert.sh
pkill -f gunicorn
./start_https.sh
```

### "sslv3 alert certificate unknown" Error

This means the browser doesn't trust the server certificate. Solutions:

1. **Accept in browser** - Safe for internal use
2. **Regenerate certificate** - `./tools/regenerate_ssl_cert.sh`
3. **Use CA-signed certificate** - Upload via Settings

### SSL Verification for VCF Endpoints

The "Verify SSL Certificate" checkbox in environment settings controls connections **to VCF**, not browser connections.

- **Disable** for self-signed VCF certificates
- **Enable** for production with valid CA certificates

### Worker Crashes with SSL Errors

```bash
# Enable debug mode to see details
./start_https_debug.sh

# Disable SSL verification in environment settings
# Increase timeout in gunicorn_config.py if needed
```

## Log Files

| File | Contents |
|------|----------|
| `logs/vcf_credentials.log` | Application logs |
| `logs/vcf_credentials_errors.log` | Error logs only |
| `logs/gunicorn_access.log` | HTTP access logs |
| `logs/gunicorn_error.log` | Gunicorn errors |

## Clean Restart

```bash
# Stop all instances
pkill -f gunicorn

# Clear logs (optional)
rm -rf logs/*

# Remove database (WARNING: loses all data)
rm instance/vcf_credentials.db

# Restart
./start_https.sh
```

## Reporting Issues

Include:
1. Error message (full traceback)
2. Steps to reproduce
3. Python version and OS
4. Relevant log excerpts
