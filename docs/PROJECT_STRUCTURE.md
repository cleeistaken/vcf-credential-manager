# Project Structure

## Overview

The VCF Credentials Manager is a modern web application for managing VMware Cloud Foundation credentials with automatic syncing and export capabilities.

## Directory Structure

```
vcf-credentials-fetch/
├── web/                          # Web Application Core
│   ├── __init__.py
│   ├── models/                   # Database models
│   │   ├── __init__.py
│   │   └── database.py           # SQLAlchemy models
│   └── services/                 # Business logic
│       ├── __init__.py
│       ├── vcf_fetcher.py        # VCF API client
│       └── export_utils.py       # Export to CSV/Excel
│
├── templates/                    # HTML Templates
│   ├── base.html                 # Base template with navigation
│   ├── login.html                # Login page
│   ├── dashboard.html            # Main dashboard
│   ├── environment.html          # Credential view page
│   └── change_password.html      # Password change page
│
├── static/                       # Static Assets
│   ├── css/
│   │   └── custom.css            # Custom styles
│   └── js/
│       └── dashboard.js          # Dashboard interactions
│
├── docs/                         # Documentation
│   ├── README.md
│   ├── QUICKSTART.md
│   ├── DEPLOYMENT.md
│   ├── ARCHITECTURE.md
│   ├── PROJECT_STRUCTURE.md      # This file
│   ├── NEW_FEATURES.md
│   ├── UI_IMPROVEMENTS.md
│   ├── GUNICORN_GUIDE.md
│   ├── FIXES_APPLIED.md
│   ├── QUICK_REFERENCE.md
│   ├── PROJECT_SUMMARY.md
│   ├── CHANGELOG.md
│   └── START_HERE.md
│
├── scripts/                      # Utility Scripts
│   ├── run.sh                    # Run Flask dev server
│   ├── run_gunicorn.sh           # Run with Gunicorn (HTTP)
│   ├── run_gunicorn_https.sh     # Run with Gunicorn (HTTPS)
│   └── gunicorn_config.py        # Gunicorn configuration
│
├── logs/                         # Application Logs
│   ├── vcf_credentials.log       # General logs
│   ├── vcf_credentials_errors.log # Error logs
│   ├── gunicorn_access.log       # HTTP access logs
│   └── gunicorn_error.log        # Gunicorn errors
│
├── instance/                     # Instance-Specific Files
│   └── vcf_credentials.db        # SQLite database
│
├── ssl/                          # SSL Certificates (optional)
│   ├── cert.pem                  # SSL certificate
│   └── key.pem                   # SSL private key
│
├── app.py                        # Main Application Entry Point
├── requirements.txt              # Python Dependencies
├── Pipfile                       # Pipenv Configuration
├── Pipfile.lock                  # Pipenv Lock File
└── README.md                     # Main Documentation
```

## Components

### Web Application (`web/`)

The core web application organized into models and services.

#### Models (`web/models/`)

**database.py** - SQLAlchemy database models:
- `User` - User accounts with password hashing
- `Environment` - VCF environment configurations
- `Credential` - Retrieved credentials
- `ScheduleConfig` - Sync scheduling configuration

#### Services (`web/services/`)

**vcf_fetcher.py** - VCF API client:
- Connects to VCF Installer and SDDC Manager
- Retrieves credentials via REST APIs
- Handles authentication and SSL verification

**export_utils.py** - Export functionality:
- CSV export with proper formatting
- Excel export with styled worksheets
- Flexible data handling

### Templates (`templates/`)

HTML templates using Jinja2:

- **base.html** - Base template with navigation, styles, common layout
- **login.html** - User authentication page
- **dashboard.html** - Main page showing all environments
- **environment.html** - Credential display with export options
- **change_password.html** - Password management page

### Static Assets (`static/`)

**CSS (`static/css/`):**
- `custom.css` - Custom styles, responsive design, modern UI

**JavaScript (`static/js/`):**
- `dashboard.js` - Environment management, modals, AJAX calls

### Documentation (`docs/`)

Comprehensive documentation covering all aspects:

- **README.md** - Main documentation overview
- **QUICKSTART.md** - Quick start guide
- **DEPLOYMENT.md** - Production deployment
- **ARCHITECTURE.md** - System architecture diagrams
- **PROJECT_STRUCTURE.md** - This file
- **GUNICORN_GUIDE.md** - Gunicorn deployment guide
- **NEW_FEATURES.md** - Feature documentation
- **UI_IMPROVEMENTS.md** - UI enhancement details
- **CHANGELOG.md** - Version history

### Scripts (`scripts/`)

Utility scripts for running the application:

- **run.sh** - Start Flask development server
- **run_gunicorn.sh** - Start Gunicorn (HTTP)
- **run_gunicorn_https.sh** - Start Gunicorn (HTTPS)
- **gunicorn_config.py** - Gunicorn configuration

### Main Application (`app.py`)

Flask application with:
- Route definitions
- Authentication setup (Flask-Login)
- Database initialization
- Scheduler configuration (APScheduler)
- Logging setup
- API endpoints

## Key Features

### Authentication System
- User login/logout
- Password hashing (Werkzeug)
- Session management (Flask-Login)
- Password change functionality

### Environment Management
- Add/edit/delete environments
- VCF Installer configuration
- SDDC Manager configuration
- Separate SSL verification settings
- Connection testing

### Credential Syncing
- Automatic scheduled syncing (APScheduler)
- Manual sync on-demand
- Per-environment sync intervals
- Background processing
- Error handling and logging

### Export Functionality
- CSV export
- Excel export (.xlsx)
- Formatted output
- Download via browser

### Logging System
- Application logs
- Error logs
- Access logs (Gunicorn)
- Rotating log files
- Comprehensive event tracking

## Database Schema

### User Table
- `id` - Primary key
- `username` - Unique username
- `password_hash` - Hashed password

### Environment Table
- `id` - Primary key
- `name` - Environment name
- `description` - Optional description
- `installer_host` - VCF Installer hostname
- `installer_username` - VCF Installer username
- `installer_password` - VCF Installer password (encrypted)
- `installer_ssl_verify` - SSL verification flag
- `manager_host` - SDDC Manager hostname
- `manager_username` - SDDC Manager username
- `manager_password` - SDDC Manager password (encrypted)
- `manager_ssl_verify` - SSL verification flag
- `sync_enabled` - Auto-sync enabled flag
- `sync_interval_minutes` - Sync interval
- `last_sync` - Last sync timestamp
- `user_id` - Foreign key to User

### Credential Table
- `id` - Primary key
- `hostname` - System hostname
- `username` - Account username
- `password` - Account password
- `environment_id` - Foreign key to Environment
- `last_updated` - Last update timestamp

## API Endpoints

### Web Pages
- `GET /` - Login page
- `GET /dashboard` - Main dashboard
- `GET /environment/<id>` - View credentials
- `GET /change-password` - Password change page
- `POST /logout` - Logout

### API Endpoints
- `POST /api/environments` - Create environment
- `PUT /api/environments/<id>` - Update environment
- `DELETE /api/environments/<id>` - Delete environment
- `POST /api/sync/<id>` - Manual sync
- `POST /api/test-credentials` - Test connection
- `GET /api/export/<id>/csv` - Export CSV
- `GET /api/export/<id>/excel` - Export Excel
- `POST /api/change-password` - Change password

## Configuration

### Flask Configuration
- Secret key (change for production!)
- Database URI
- Session settings
- Debug mode

### Scheduler Configuration
- Job stores
- Executors
- Job defaults
- Timezone

### Logging Configuration
- Log levels
- File handlers
- Formatters
- Rotation settings

## Development

### Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
python app.py

# Access at http://localhost:5000
```

### Making Changes

**Adding a new route:**
1. Add route in `app.py`
2. Create template in `templates/`
3. Add JavaScript if needed in `static/js/`
4. Update navigation in `base.html`

**Adding a database field:**
1. Update model in `web/models/database.py`
2. Delete `instance/vcf_credentials.db` (dev only)
3. Restart app to recreate database

**Modifying UI:**
1. Update template in `templates/`
2. Update styles in `static/css/custom.css`
3. Update JavaScript in `static/js/dashboard.js`

## Production Deployment

### Using Gunicorn

```bash
# HTTP
./scripts/run_gunicorn.sh

# HTTPS (requires SSL certificates)
./scripts/run_gunicorn_https.sh
```

### SSL Certificates

```bash
# Generate self-signed certificate
mkdir -p ssl
openssl req -x509 -newkey rsa:4096 -nodes \
  -keyout ssl/key.pem -out ssl/cert.pem -days 365
```

### Security Considerations

1. **Change default password** immediately
2. **Use HTTPS** in production
3. **Secure database file** with proper permissions
4. **Use strong secret key** in production
5. **Enable SSL verification** for production VCF systems
6. **Restrict network access** with firewall rules
7. **Regular backups** of database
8. **Monitor logs** for suspicious activity

## File Permissions

```bash
# Secure database
chmod 600 instance/vcf_credentials.db

# Secure SSL keys
chmod 600 ssl/key.pem
chmod 644 ssl/cert.pem

# Make scripts executable
chmod +x scripts/*.sh
```

## Backup and Restore

### Backup

```bash
# Backup database
cp instance/vcf_credentials.db instance/vcf_credentials.db.backup

# Backup with timestamp
cp instance/vcf_credentials.db \
   instance/vcf_credentials.db.$(date +%Y%m%d_%H%M%S)
```

### Restore

```bash
# Restore from backup
cp instance/vcf_credentials.db.backup instance/vcf_credentials.db

# Restart application
python app.py
```

## Troubleshooting

### Common Issues

**Database locked:**
- Stop all running instances
- Check for stale connections
- Restart application

**Port in use:**
- Change port: `export FLASK_RUN_PORT=8000`
- Or kill process using port 5000

**Import errors:**
- Verify all dependencies installed
- Check Python version (3.13+)
- Reinstall: `pip install -r requirements.txt`

**Connection errors:**
- Check VCF system accessibility
- Verify credentials
- Check SSL verification settings
- Review logs in `logs/`

## Summary

The VCF Credentials Manager is a well-organized web application with:

- ✅ **Clean Structure** - Organized into logical components
- ✅ **Modern Stack** - Flask, SQLAlchemy, APScheduler
- ✅ **Comprehensive Features** - Auth, sync, export, logging
- ✅ **Production Ready** - Gunicorn, HTTPS, security
- ✅ **Well Documented** - Extensive documentation
- ✅ **Maintainable** - Clear code organization

Perfect for managing VCF credentials in any environment! 🎉
