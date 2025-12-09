# Troubleshooting Guide

## Common Issues and Solutions

### Database Initialization Errors

#### Issue: "dialect.do_execute" error on first startup with Gunicorn

**Symptoms:**
```
File ".../sqlalchemy/engine/base.py", line 1967, in _exec_single_context
    self.dialect.do_execute(
    cursor, str_statement, effective_parameters, context
)
```

**Cause:**
When using Gunicorn with multiple workers, database initialization can fail due to race conditions or improper initialization timing.

**Solution:**
The application now includes automatic database initialization that runs before workers are forked. This is handled by:

1. **Automatic initialization in `app.py`:**
   - The `init_database()` function runs when the app module is loaded
   - Creates all database tables
   - Creates default admin user if none exists
   - Schedules enabled environments

2. **Gunicorn preload configuration:**
   - `gunicorn_config.py` sets `preload_app = True`
   - This ensures the app is loaded once before forking workers
   - Database is initialized before any workers start

3. **Use the startup script:**
   ```bash
   ./start_https.sh
   ```
   This script ensures proper initialization and checks for required files.

**Alternative Solutions:**

If you still encounter issues:

1. **Delete the database and restart:**
   ```bash
   rm vcf_credentials.db
   ./start_https.sh
   ```

2. **Use single worker mode:**
   Edit `gunicorn_config.py` and set:
   ```python
   workers = 1
   ```

3. **Initialize database manually:**
   ```bash
   python -c "from app import app, db; app.app_context().push(); db.create_all()"
   ```

---

### SSL/HTTPS Issues

#### Issue: SSL certificate errors

**Symptoms:**
- Browser shows "Your connection is not private"
- Certificate warnings in logs

**Solution:**
This is expected with self-signed certificates. You can:

1. **Accept the certificate in your browser** (for development/testing)
2. **Use a proper CA-signed certificate** (for production)
3. **Add the self-signed cert to your trusted certificates** (for testing)

#### Issue: "SSLV3_ALERT_ILLEGAL_PARAMETER" error

**Symptoms:**
```
[SSL: SSLV3_ALERT_ILLEGAL_PARAMETER] sslv3 alert illegal parameter (_ssl.c:2580)
```

**Cause:**
Incompatible SSL/TLS configuration between client and server.

**Solution:**
The application now uses proper SSL configuration in `gunicorn_config.py`. If you still see this:

1. Regenerate SSL certificates:
   ```bash
   rm ssl/cert.pem ssl/key.pem
   ./start_https.sh
   ```

2. Use modern TLS versions:
   Ensure your client (browser/curl) supports TLS 1.2+

---

### Authentication Issues

#### Issue: Cannot login after first startup

**Symptoms:**
- Login page loads but credentials don't work
- "Invalid username or password" error

**Solution:**

1. **Use default credentials:**
   - Username: `admin`
   - Password: `admin`

2. **Reset admin password:**
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

3. **Create new admin user:**
   ```bash
   flask --app app create_admin
   ```

---

### Credential Fetching Issues

#### Issue: "AttributeError: 'str' object has no attribute 'get'"

**Symptoms:**
Error when fetching credentials from VCF Installer

**Solution:**
This has been fixed in the latest version. The VCF Installer parsing logic now handles various response formats correctly. Update to the latest version.

#### Issue: No credentials fetched from environment

**Symptoms:**
- Sync completes but no credentials shown
- "Fetched 0 credentials" in logs

**Solutions:**

1. **Check connection settings:**
   - Use "🧪 Test Connection" when adding/editing environment
   - Verify hostname is reachable
   - Verify credentials are correct
   - Check SSL verification settings

2. **Check logs:**
   ```bash
   tail -f logs/vcf_credentials.log
   ```
   Look for specific error messages

3. **Verify API access:**
   - Ensure the user account has API access
   - Check VCF/SDDC Manager is responding
   - Verify no firewall blocking

---

### Logging Issues

#### Issue: Duplicate log messages

**Symptoms:**
Every log message appears twice in console

**Solution:**
This has been fixed. The application now uses `app.logger` exclusively with `propagate = False` to prevent duplicate messages.

If you still see duplicates:
1. Restart the application
2. Clear any custom logging configuration
3. Check no external logging handlers are attached

---

### Performance Issues

#### Issue: Slow credential sync

**Symptoms:**
- Sync takes a long time
- Application becomes unresponsive during sync

**Solutions:**

1. **Increase timeout:**
   Edit `gunicorn_config.py`:
   ```python
   timeout = 60  # Increase from 30
   ```

2. **Adjust sync intervals:**
   - Use longer intervals for large environments
   - Disable auto-sync and use manual sync

3. **Check network latency:**
   - Verify network connection to VCF/SDDC Manager
   - Check for firewall/proxy issues

---

### Export Issues

#### Issue: Export fails or downloads empty file

**Symptoms:**
- CSV/Excel export button doesn't work
- Downloaded file is empty or corrupted

**Solutions:**

1. **Ensure credentials exist:**
   - Run sync first
   - Verify credentials are shown in the table

2. **Check browser console:**
   - Open browser developer tools (F12)
   - Look for JavaScript errors

3. **Check file permissions:**
   ```bash
   ls -la logs/
   ```
   Ensure the application can write files

---

## Getting Help

### Enable Debug Logging

Edit `app.py` and set:
```python
app.config['DEBUG'] = True
```

Or set environment variable:
```bash
export FLASK_DEBUG=1
```

### Check Logs

Application logs are in:
- `logs/vcf_credentials.log` - All application logs
- `logs/vcf_credentials_errors.log` - Error logs only
- `logs/gunicorn_access.log` - HTTP access logs
- `logs/gunicorn_error.log` - Gunicorn errors

### Verify Installation

```bash
# Check Python version
python --version  # Should be 3.13+

# Check dependencies
pip list | grep -E "Flask|SQLAlchemy|gunicorn"

# Verify database
sqlite3 vcf_credentials.db ".tables"
```

### Clean Restart

```bash
# Stop all running instances
pkill -f gunicorn
pkill -f "python app.py"

# Remove database (WARNING: deletes all data)
rm vcf_credentials.db

# Clear logs
rm -rf logs/*

# Restart
./start_https.sh
```

---

## Known Limitations

1. **SQLite Database:**
   - Not suitable for high-concurrency environments
   - Consider PostgreSQL/MySQL for production with many users

2. **Self-Signed Certificates:**
   - Browser warnings are expected
   - Use proper CA-signed certificates for production

3. **Background Scheduler:**
   - Runs in-process with the application
   - Consider external scheduler (cron/systemd) for critical environments

4. **Password History:**
   - Only tracks changes detected during sync
   - Manual password changes in VCF are not tracked retroactively

---

## Reporting Issues

When reporting issues, please include:

1. **Error message** (full traceback if available)
2. **Steps to reproduce**
3. **Environment details:**
   - Python version
   - Operating system
   - Deployment method (dev server/Gunicorn)
4. **Relevant log excerpts** from `logs/vcf_credentials.log`
5. **Configuration** (sanitize passwords!)

