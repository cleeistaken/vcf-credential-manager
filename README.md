# VCF Credentials Manager

A web application for managing VMware Cloud Foundation (VCF) credentials with automatic syncing and export capabilities.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
./start_https.sh

# Access at https://localhost:5000
# Default login: admin / admin
```

**Change the default password immediately after first login.**

## Features

- **Multi-Environment Support** - Manage multiple VCF environments
- **Scheduled Syncing** - Automatic credential retrieval at configurable intervals
- **Export Options** - Export credentials to CSV or Excel
- **Connection Testing** - Validate credentials before saving
- **Password History** - Track password changes over time
- **Column Filters** - Filter credentials by multiple criteria
- **User Management** - Admin and read-only user roles
- **SSL Support** - HTTPS with custom certificates

## Usage

### Add Environment

1. Click "Add Environment"
2. Enter VCF Installer and/or SDDC Manager details
3. Configure sync interval (optional)
4. Test connection and save

### Sync Credentials

- **Automatic**: Credentials sync at configured intervals
- **Manual**: Click "Sync Now" on any environment

### Export Credentials

1. Click "View" on any environment
2. Click "Export to CSV" or "Export to Excel"

## Configuration

### Environment Variables

```bash
export FLASK_SECRET_KEY=your-secret-key-here
export FLASK_RUN_PORT=5000
```

### SSL Certificates

The startup script generates self-signed certificates automatically. For production, upload CA-signed certificates via Settings > SSL Certificate Management.

## Logs

Logs are stored in the `logs/` directory:
- `vcf_credentials.log` - Application logs
- `vcf_credentials_errors.log` - Error logs
- `gunicorn_access.log` - HTTP access logs
- `gunicorn_error.log` - Gunicorn errors

## Documentation

See the `docs/` directory for detailed documentation:

- [Quick Start Guide](QUICKSTART.md) - Installation and first steps
- [Deployment Guide](docs/DEPLOYMENT.md) - Production deployment
- [Troubleshooting](docs/TROUBLESHOOTING.md) - Common issues and solutions
- [User Management](docs/USER_MANAGEMENT.md) - Users, roles, and SSL certificates
- [Features](docs/FEATURES.md) - Password history, filters, and more

## Requirements

- Python 3.9+
- Access to VCF Installer and/or SDDC Manager

## Security

- Change default admin password immediately
- Use HTTPS in production
- Restrict network access with firewall rules
- Secure the database file: `chmod 600 instance/vcf_credentials.db`
