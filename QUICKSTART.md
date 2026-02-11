# Quick Start Guide

## Prerequisites

- Python 3.9+
- pip or pipenv

## Installation

```bash
# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Start the Application

```bash
./start_https.sh
```

The script will:
- Create required directories
- Generate SSL certificates (if needed)
- Initialize the database
- Start the server

## First Login

1. Open https://localhost:5000
2. Accept the self-signed certificate warning
3. Login: `admin` / `admin`
4. **Change your password immediately** via the menu

## Add Your First Environment

1. Click "Add Environment"
2. Fill in details:
   - **Name**: e.g., "Production VCF"
   - **VCF Installer** (optional): hostname, username, password
   - **SDDC Manager** (optional): hostname, username, password
   - **Sync Settings**: enable auto-sync, set interval
3. Uncheck "Verify SSL" if using self-signed certificates
4. Click "Test Connection" to verify
5. Click "Save"

## Common Tasks

| Task | How |
|------|-----|
| Sync credentials | Click "Sync Now" on environment card |
| View credentials | Click "View" on environment card |
| Export | Click "Export to CSV" or "Export to Excel" |
| Password history | Click "History" button on any credential |
| Filter credentials | Use the filter row below column headers |

## Troubleshooting

### Can't connect to VCF?

1. Verify hostname is reachable
2. Check credentials are correct
3. Disable SSL verification for self-signed certs
4. Check firewall rules

### SSL certificate warning?

Normal for self-signed certificates. Click "Advanced" → "Proceed" in your browser.

### Need to reset?

```bash
# Stop server
pkill -f gunicorn

# Delete database (loses all data)
rm instance/vcf_credentials.db

# Restart
./start_https.sh
```

## Next Steps

- [Deployment Guide](docs/DEPLOYMENT.md) - Production setup
- [Troubleshooting](docs/TROUBLESHOOTING.md) - More solutions
