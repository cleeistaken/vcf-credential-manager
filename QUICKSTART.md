# Quick Start Guide

## 🚀 Get Started in 3 Minutes

### Prerequisites
- Python 3.13+
- pip or pipenv

### Step 1: Install Dependencies

**Using pipenv (recommended):**
```bash
pipenv install
pipenv shell
```

**Using pip:**
```bash
pip install -r requirements.txt
```

### Step 2: Start the Application

```bash
./start_https.sh
```

That's it! The script will:
- ✅ Check your virtual environment
- ✅ Create required directories
- ✅ Generate SSL certificates
- ✅ Initialize the database
- ✅ Create default admin user
- ✅ Start the server

### Step 3: Access the Application

1. Open your browser to: **https://localhost:5000**
2. Accept the self-signed certificate warning (click "Advanced" → "Proceed")
3. Login with default credentials:
   - **Username:** `admin`
   - **Password:** `admin`
4. **IMPORTANT:** Change your password immediately!
   - Click "Change Password" in the top-right menu

## 🎯 What to Do Next

### 1. Add Your First Environment

1. Click "➕ Add Environment"
2. Fill in the details:
   - **Name:** e.g., "Production VCF"
   - **Description:** Optional description
   - **VCF Installer:** (Optional)
     - Hostname: e.g., `vcf-installer.example.com`
     - Username: e.g., `admin`
     - Password: Your installer password
     - ☑️ Verify SSL Certificates (uncheck for self-signed certs)
   - **SDDC Manager:** (Optional)
     - Hostname: e.g., `sddc-manager.example.com`
     - Username: e.g., `administrator@vsphere.local`
     - Password: Your SDDC Manager password
     - ☑️ Verify SSL Certificates (uncheck for self-signed certs)
   - **Sync Settings:**
     - ☑️ Enable automatic sync
     - Interval: e.g., `60` minutes

3. Click "🧪 Test Connection" to verify credentials
4. Click "Save"

### 2. Sync Credentials

**Automatic Sync:**
- Credentials will sync automatically at the configured interval

**Manual Sync:**
- Click "🔄 Sync Now" on any environment card

### 3. View Credentials

1. Click "👁️ View" on any environment card
2. See all credentials in a table
3. Click on any credential to see password history
4. Export to CSV or Excel using the buttons at the top

## 📋 Common Tasks

### Change Your Password
1. Click "Change Password" (top-right menu)
2. Enter current password
3. Enter new password (min 8 characters)
4. Confirm new password
5. Click "Change Password"

### Edit an Environment
1. Click "✏️ Edit" on any environment card
2. Modify settings
3. Click "🧪 Test Connection" to verify changes
4. Click "Save"

### Delete an Environment
1. Click "🗑️ Delete" on any environment card
2. Confirm deletion in the popup
3. All credentials for that environment will be deleted

### Export Credentials
1. Click "👁️ View" on any environment
2. Click "📥 Export to CSV" or "📊 Export to Excel"
3. File downloads automatically

### View Password History
1. Click "👁️ View" on any environment
2. Click "📜 History" button for any credential
3. See all previous passwords and change dates
4. Click "👁️" to show/hide passwords
5. Click "📋" to copy passwords

## 🔧 Troubleshooting

### Can't Start the Application?

**Check virtual environment:**
```bash
which python  # Should point to your virtualenv
```

**Activate virtual environment:**
```bash
pipenv shell  # If using pipenv
# or
source venv/bin/activate  # If using venv
```

### Can't Login?

**Default credentials:**
- Username: `admin`
- Password: `admin`

**Reset password:**
```bash
python -c "
from app import app, db, User
from werkzeug.security import generate_password_hash
with app.app_context():
    user = User.query.filter_by(username='admin').first()
    user.password_hash = generate_password_hash('admin')
    db.session.commit()
    print('Password reset to: admin')
"
```

### SSL Certificate Warning?

This is normal with self-signed certificates. Click:
1. "Advanced" (or "Show Details")
2. "Proceed to localhost" (or "Accept the Risk")

For production, use proper CA-signed certificates.

### Credentials Not Syncing?

1. **Check connection:** Click "🧪 Test Connection" when editing environment
2. **Check logs:** `tail -f logs/vcf_credentials.log`
3. **Verify credentials:** Ensure username/password are correct
4. **Check SSL settings:** Uncheck "Verify SSL" if using self-signed certs
5. **Check network:** Ensure VCF/SDDC Manager is reachable

### Application Crashed?

**Check logs:**
```bash
tail -f logs/vcf_credentials.log
tail -f logs/vcf_credentials_errors.log
```

**Restart application:**
```bash
# Stop (Ctrl+C in terminal where it's running)
# Or kill all instances:
pkill -f gunicorn

# Start again:
./start_https.sh
```

**Fresh start (removes all data):**
```bash
rm vcf_credentials.db
./start_https.sh
```

## 📖 More Information

- **Full Documentation:** [README.md](README.md)
- **Troubleshooting Guide:** [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)
- **Technical Details:** [docs/DATABASE_INITIALIZATION_FIX.md](docs/DATABASE_INITIALIZATION_FIX.md)
- **Recent Changes:** [CHANGES.md](CHANGES.md)

## 🔒 Security Best Practices

1. **Change default password immediately** after first login
2. **Use strong passwords** (min 8 characters, mix of letters/numbers/symbols)
3. **Use HTTPS** in production (not self-signed certificates)
4. **Restrict access** to the application (firewall rules)
5. **Secure the database file:**
   ```bash
   chmod 600 vcf_credentials.db
   ```
6. **Set a secret key** for production:
   ```bash
   export SECRET_KEY="your-random-secret-key-here"
   ```
7. **Keep credentials secure** - don't share exports
8. **Regular backups** of the database file

## 💡 Tips

- **Sync Interval:** Set based on how often passwords change (60-1440 minutes)
- **SSL Verification:** Disable only if you trust the self-signed certificates
- **Password History:** Track password changes over time
- **Export Regularly:** Backup credentials to CSV/Excel
- **Monitor Logs:** Check logs periodically for errors
- **Test First:** Always use "Test Connection" before saving

## 🆘 Need Help?

1. **Check logs:** `logs/vcf_credentials.log`
2. **Read troubleshooting guide:** [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)
3. **Check database:** `sqlite3 vcf_credentials.db ".tables"`

## 📊 System Requirements

- **Python:** 3.13 or higher
- **OS:** Linux, macOS, or Windows
- **RAM:** 512MB minimum
- **Disk:** 100MB minimum
- **Network:** Access to VCF Installer and/or SDDC Manager

## 🎉 You're All Set!

Your VCF Credentials Manager is now running and ready to use. Enjoy!

**Access:** https://localhost:5000  
**Default Login:** admin / admin  
**Don't forget to change your password!**

