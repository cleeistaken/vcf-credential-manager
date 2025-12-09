# Quick Start Guide

Get up and running with VCF Credentials Manager in 5 minutes!

## Prerequisites

- Python 3.8 or higher installed
- Access to at least one VCF Installer or SDDC Manager

## Installation Steps

### 1. Install Dependencies

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install required packages
pip install -r requirements.txt
```

### 2. Start the Application

```bash
# Simple start (development mode)
python app.py

# Or use the provided script
./run.sh
```

The application will:
- Create the database automatically
- Create a default admin user
- Start on http://localhost:5000

### 3. Login

Open your browser and navigate to:
```
http://localhost:5000
```

**Default Credentials:**
- Username: `admin`
- Password: `admin`

⚠️ **IMPORTANT**: Change this password immediately after first login!

### 4. Add Your First Environment

1. Click **"Add Environment"** button
2. Fill in the form:

   **Basic Information:**
   - Environment Name: `My Production VCF`
   - Description: `Production environment`

   **VCF Installer (if applicable):**
   - Installer Host: `vcf-installer.example.com`
   - Username: `admin`
   - Password: `your-password`

   **SDDC Manager (if applicable):**
   - Manager Host: `sddc-manager.example.com`
   - Username: `administrator@vsphere.local`
   - Password: `your-password`

   **Sync Configuration:**
   - ☑ Enable automatic sync
   - Sync Interval: `60` minutes
   - ☑ Verify SSL certificates (uncheck for self-signed certs)

3. Click **"Save"**

### 5. Sync Credentials

Click **"Sync Now"** on your environment card to fetch credentials immediately.

### 6. View Credentials

Click **"View Credentials"** to see all fetched passwords in a table format.

### 7. Export Credentials

From the environment view:
- Click **"Export CSV"** for CSV format
- Click **"Export Excel"** for Excel format

## Common Use Cases

### Scenario 1: Single SDDC Manager

```
Environment: Production
Manager Host: sddc-mgr.corp.local
Manager Username: admin@local
Manager Password: ********
Sync: Every 60 minutes
```

### Scenario 2: VCF Installer Only

```
Environment: Lab Environment
Installer Host: vcf-installer.lab.local
Installer Username: admin
Installer Password: ********
Sync: Every 120 minutes
```

### Scenario 3: Both Installer and Manager

```
Environment: Complete VCF Stack
Installer Host: vcf-installer.prod.local
Installer Username: admin
Installer Password: ********
Manager Host: sddc-manager.prod.local
Manager Username: administrator@vsphere.local
Manager Password: ********
Sync: Every 30 minutes
```

## Tips

### Disable SSL Verification

If using self-signed certificates, uncheck "Verify SSL certificates" in the environment configuration.

### Adjust Sync Interval

- Minimum: 5 minutes
- Recommended: 60 minutes
- For large environments: 120+ minutes

### Search Credentials

Use the search box to filter by:
- Hostname
- Username
- Resource type
- Domain name

### Show/Hide Passwords

- Click the 👁️ (eye) icon to reveal passwords
- Click the 📋 (copy) icon to copy to clipboard

## Troubleshooting

### Can't Connect to VCF

1. Verify hostname is reachable: `ping vcf-host.example.com`
2. Check credentials are correct
3. Try disabling SSL verification
4. Check firewall rules

### Sync Not Working

1. Check environment credentials
2. Manually trigger sync to see errors
3. Check application logs in terminal
4. Verify sync interval is at least 5 minutes

### Database Issues

If you need to reset everything:

```bash
# Stop the application (Ctrl+C)
rm vcf_credentials.db
python app.py
# This creates a fresh database with default admin user
```

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- See [DEPLOYMENT.md](DEPLOYMENT.md) for production deployment
- Configure HTTPS for secure access
- Set up automated backups
- Create additional user accounts

## Security Reminders

✅ Change default admin password  
✅ Use HTTPS in production  
✅ Restrict network access with firewall  
✅ Regular backups of database  
✅ Keep dependencies updated  

## Getting Help

If you encounter issues:

1. Check the logs in the terminal
2. Review the troubleshooting section
3. Verify VCF connectivity
4. Check credentials are correct

## Example Workflow

```
1. Start Application
   └─> python app.py

2. Login
   └─> http://localhost:5000
   └─> admin / admin

3. Add Environment
   └─> Click "Add Environment"
   └─> Fill in details
   └─> Save

4. Sync Credentials
   └─> Click "Sync Now"
   └─> Wait for completion

5. View & Export
   └─> Click "View Credentials"
   └─> Browse credentials
   └─> Export as needed

6. Automate
   └─> Enable auto-sync
   └─> Set interval
   └─> Credentials update automatically
```

Enjoy using VCF Credentials Manager! 🚀

