# Quick Reference Guide

## 🚀 New Features Quick Access

### 1. Change Password
**Location:** Header → 🔒 Change Password  
**Requirements:** Current password + New password (8+ chars)  
**Logged:** Yes

### 2. Test Credentials
**Location:** Add/Edit Environment Modal → 🧪 Test Connection (bottom left)  
**Tests:** Installer and/or Manager connectivity  
**Logged:** Yes

### 3. View Logs
**Location:** `logs/` directory  
**Files:**
- `vcf_credentials.log` - All activity
- `vcf_credentials_errors.log` - Errors only

**View live:**
```bash
tail -f logs/vcf_credentials.log
```

### 4. Delete Environment
**Location:** Dashboard → Environment Card → 🗑️ Delete  
**Confirmation:** Must type exact environment name  
**Logged:** Yes

---

## 📋 Common Tasks

### Change Admin Password (IMPORTANT!)
```
1. Login with admin/admin
2. Click "🔒 Change Password" in header
3. Current: admin
4. New: YourSecurePassword123
5. Confirm: YourSecurePassword123
6. Click "Change Password"
```

### Add New Environment with Testing
```
1. Dashboard → "➕ Add Environment"
2. Fill in details
3. Click "🧪 Test Connection"
4. Review results
5. Fix any issues
6. Test again
7. Click "Save"
```

### Check Logs for Issues
```bash
# View last 50 lines
tail -50 logs/vcf_credentials.log

# Follow live
tail -f logs/vcf_credentials.log

# Search for errors
grep ERROR logs/vcf_credentials.log

# Search for specific user
grep "admin" logs/vcf_credentials.log

# View only errors
cat logs/vcf_credentials_errors.log
```

### Safely Delete Environment
```
1. Click "🗑️ Delete" on environment
2. Read warning carefully
3. Type EXACT environment name
4. Confirm deletion
```

---

## 🔍 Troubleshooting

### Password Change Not Working
- ✅ Check current password is correct
- ✅ Ensure new password is 8+ characters
- ✅ Verify passwords match
- ✅ Check logs: `grep "Password change" logs/vcf_credentials.log`

### Test Connection Fails
- ✅ Verify host is reachable: `ping hostname`
- ✅ Check credentials are correct
- ✅ Try disabling SSL verification
- ✅ Check logs: `grep "Testing" logs/vcf_credentials.log`

### Can't Delete Environment
- ✅ Type EXACT name (case-sensitive)
- ✅ Check for typos
- ✅ Copy/paste environment name if needed

### Logs Not Creating
```bash
# Create logs directory
mkdir -p logs
chmod 755 logs

# Restart application
python app.py
```

---

## 📊 Log Examples

### Successful Login
```
[2025-12-08 10:30:45] INFO: Login attempt for user: admin
[2025-12-08 10:30:45] INFO: Successful login for user: admin
```

### Failed Login
```
[2025-12-08 10:31:20] INFO: Login attempt for user: admin
[2025-12-08 10:31:20] WARNING: Failed login attempt for user: admin
```

### Password Change
```
[2025-12-08 10:35:10] INFO: Password change attempt for user: admin
[2025-12-08 10:35:10] INFO: Password changed successfully for user: admin
```

### Credential Sync
```
[2025-12-08 10:40:00] INFO: Fetching credentials for environment: Production (ID: 1)
[2025-12-08 10:40:05] INFO: Fetched 15 credentials from installer
[2025-12-08 10:40:10] INFO: Fetched 42 credentials from manager
[2025-12-08 10:40:12] INFO: Successfully updated 57 credentials for Production
```

### Test Connection
```
[2025-12-08 10:45:00] INFO: Testing credentials for new/updated environment
[2025-12-08 10:45:01] INFO: Testing installer connection: vcf-installer.example.com
[2025-12-08 10:45:03] INFO: Installer test successful: vcf-installer.example.com
```

### Environment Deletion
```
[2025-12-08 10:50:00] INFO: Deleting environment: Test Env (ID: 5)
[2025-12-08 10:50:00] DEBUG: Removed scheduled job: env_sync_5
[2025-12-08 10:50:00] DEBUG: Deleted 12 credentials
[2025-12-08 10:50:00] INFO: Environment deleted: Test Env
```

---

## ⚙️ Configuration

### Change Log Level
Edit `app.py`:
```python
# For more detailed logs
log_level = logging.DEBUG

# For production (less verbose)
log_level = logging.INFO
```

### Change Log File Size
Edit `app.py`:
```python
# Default: 10MB
maxBytes=10485760

# Change to 20MB
maxBytes=20971520
```

### Change Password Requirements
Edit `app.py`:
```python
# Default: 8 characters
if len(new_password) < 8:

# Change to 12 characters
if len(new_password) < 12:
```

---

## 🎯 Best Practices

### Security
1. ✅ Change default admin password immediately
2. ✅ Use strong passwords (12+ characters)
3. ✅ Test credentials before saving
4. ✅ Review logs regularly
5. ✅ Enable SSL verification when possible

### Operations
1. ✅ Test new environments before syncing
2. ✅ Monitor logs for errors
3. ✅ Backup database regularly
4. ✅ Use descriptive environment names
5. ✅ Document credential changes

### Maintenance
1. ✅ Rotate logs periodically
2. ✅ Clean old log backups
3. ✅ Update passwords regularly
4. ✅ Test credential sync schedules
5. ✅ Monitor disk space for logs

---

## 📞 Quick Help

### Application Won't Start
```bash
# Check Python version
python --version  # Should be 3.8+

# Reinstall dependencies
pip install -r requirements.txt --upgrade

# Check for errors
python app.py 2>&1 | tee startup.log
```

### Can't Login
```bash
# Reset admin password
python -c "
from app import app, db, User
from werkzeug.security import generate_password_hash
with app.app_context():
    admin = User.query.filter_by(username='admin').first()
    admin.password_hash = generate_password_hash('admin')
    db.session.commit()
    print('Password reset to: admin')
"
```

### Database Issues
```bash
# Backup database
cp vcf_credentials.db vcf_credentials.db.backup

# Reinitialize (WARNING: Deletes all data)
rm vcf_credentials.db
python app.py
```

---

## 📚 Documentation

- **Full Documentation:** `README.md`
- **Quick Start:** `QUICKSTART.md`
- **New Features:** `NEW_FEATURES.md`
- **Deployment:** `DEPLOYMENT.md`
- **Architecture:** `ARCHITECTURE.md`
- **Fixes Applied:** `FIXES_APPLIED.md`

---

## 🎉 Summary

**New Features:**
1. ✅ Password change page
2. ✅ Test credentials button
3. ✅ Comprehensive logging
4. ✅ Enhanced delete confirmation

**All features are:**
- ✅ Fully functional
- ✅ Logged for audit
- ✅ User-friendly
- ✅ Production-ready

**Start using now:**
```bash
python app.py
# Visit: http://localhost:5000
# Login: admin / admin
# First task: Change password!
```

