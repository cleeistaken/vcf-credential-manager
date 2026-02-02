# VCF Credentials Manager - Documentation

Complete documentation for the VCF Credentials Manager application.

## Quick Start

- **[Quick Start Guide](QUICKSTART.md)** - Get up and running in minutes

## User Guides

### Core Features
- **[Settings & User Management](SETTINGS_AND_USER_MANAGEMENT.md)** - Manage users, roles, and SSL certificates
- **[Password History](PASSWORD_HISTORY.md)** - Track and view password changes over time
- **[Column Filters](COLUMN_FILTERS.md)** - Filter credentials by multiple criteria
- **[Server Restart](SERVER_RESTART_FEATURE.md)** - Restart server and reload SSL certificates

### Administration
- **[Deployment Guide](DEPLOYMENT.md)** - Production deployment instructions
- **[Troubleshooting](TROUBLESHOOTING.md)** - Common issues and solutions

## Features Overview

### User Management
- **Admin Users** - Full access to all features
- **Read-Only Users** - View credentials only, cannot modify
- **Password Management** - Change your password anytime
- **User Administration** - Add/remove users (admin only)

### Environment Management
- **Multiple Environments** - Manage multiple VCF installations
- **VCF Installer Support** - Fetch credentials from VCF Installer
- **SDDC Manager Support** - Fetch credentials from SDDC Manager
- **Automatic Sync** - Schedule periodic credential updates
- **Manual Sync** - Trigger sync on demand

### Credential Management
- **Centralized Storage** - All credentials in SQLite database
- **Password History** - Track password changes over time
- **Export Options** - Export to CSV or Excel
- **Advanced Filtering** - Filter by hostname, type, resource, etc.
- **Search** - Quick search across all fields

### Security Features
- **HTTPS Support** - Secure communication with SSL/TLS
- **Authentication** - User login required
- **Role-Based Access** - Admin and read-only roles
- **Password Hashing** - Secure password storage
- **SSL Certificate Management** - Upload custom certificates
- **Audit Logging** - Track user actions

### System Features
- **Web Interface** - Modern, responsive UI
- **Background Sync** - Automatic credential updates
- **Graceful Restart** - Reload server without downtime
- **Comprehensive Logging** - Detailed application logs

## Getting Started

1. **Install** - Follow the [Quick Start Guide](QUICKSTART.md)
2. **Configure** - Add your VCF environments
3. **Sync** - Fetch credentials from your environments
4. **Manage** - View, filter, and export credentials

## Default Credentials

**First Login:**
- Username: `admin`
- Password: `admin`

⚠️ **Important:** Change the default password immediately after first login!

## Support

For issues or questions:
1. Check the [Troubleshooting Guide](TROUBLESHOOTING.md)
2. Review application logs in `logs/vcf_credentials.log`
3. Check Gunicorn logs in `logs/gunicorn_error.log`

## System Requirements

- **Python:** 3.9 or higher
- **Operating System:** Linux, macOS, or Windows (WSL)
- **Database:** SQLite (included)
- **Web Server:** Gunicorn (included)
- **Browser:** Modern browser with JavaScript enabled

## Quick Links

- [Quick Start](QUICKSTART.md) - Installation and setup
- [Deployment](DEPLOYMENT.md) - Production deployment
- [Settings](SETTINGS_AND_USER_MANAGEMENT.md) - User and system settings
- [Troubleshooting](TROUBLESHOOTING.md) - Common issues

## License

See the main README in the project root for license information.
