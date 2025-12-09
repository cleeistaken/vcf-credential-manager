# VCF Credentials Manager

A modern web application for managing VMware Cloud Foundation (VCF) credentials with automatic syncing and export capabilities.

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py

# Access at http://localhost:5000
# Default login: admin / admin
```

## 📋 Features

- 🔐 **Secure Authentication** - User login with password management
- 🌐 **Multi-Environment Support** - Manage multiple VCF environments
- ⏰ **Scheduled Syncing** - Automatic credential retrieval at configurable intervals
- 📊 **Export Options** - Export credentials to CSV or Excel
- 🧪 **Connection Testing** - Validate credentials before saving
- 📝 **Comprehensive Logging** - Track all operations
- 🔒 **SSL Support** - HTTPS with custom certificates
- 🎨 **Modern UI** - Clean, responsive interface
- 🔄 **Manual Sync** - On-demand credential refresh
- 🗑️ **Safe Deletion** - Confirmation prompts to prevent accidents

## 📁 Project Structure

```
vcf-credentials-fetch/
├── web/                   # Web Application
│   ├── models/           # Database models
│   │   └── database.py   # SQLAlchemy models (User, Environment, Credential)
│   └── services/         # Web services
│       ├── vcf_fetcher.py    # VCF API client
│       └── export_utils.py   # Export utilities
├── templates/            # HTML templates
│   ├── base.html
│   ├── login.html
│   ├── dashboard.html
│   ├── environment.html
│   └── change_password.html
├── static/               # CSS, JavaScript
│   ├── css/
│   │   └── custom.css
│   └── js/
│       └── dashboard.js
├── docs/                 # Documentation
├── scripts/              # Utility scripts
├── logs/                 # Application logs
├── instance/             # SQLite database
├── ssl/                  # SSL certificates (optional)
├── app.py               # Main application entry point
└── requirements.txt      # Python dependencies
```

## 🔧 Installation

### Requirements
- Python 3.13+
- pip or pipenv

### Install Dependencies

**Using pip:**
```bash
pip install -r requirements.txt
```

**Using pipenv:**
```bash
pipenv install
pipenv shell
```

## 🌐 Usage

### Development Server

```bash
python app.py
```

Access at `http://localhost:5000`

Default credentials:
- **Username:** admin
- **Password:** admin

⚠️ **Important:** Change the default password after first login!

### Production Deployment

#### HTTP (Development/Testing)

```bash
./scripts/run_gunicorn.sh
```

#### HTTPS (Production)

1. Generate SSL certificates:
```bash
mkdir -p ssl
openssl req -x509 -newkey rsa:4096 -nodes \
  -keyout ssl/key.pem -out ssl/cert.pem -days 365
```

2. Run with HTTPS:
```bash
./scripts/run_gunicorn_https.sh
```

See [docs/GUNICORN_GUIDE.md](docs/GUNICORN_GUIDE.md) for detailed deployment instructions.

## 📖 How to Use

### 1. Login
- Navigate to `http://localhost:5000`
- Login with default credentials (admin/admin)
- Change password immediately via "Change Password" link

### 2. Add Environment
- Click "➕ Add Environment" button
- Fill in environment details:
  - **Name:** Descriptive name for the environment
  - **Description:** Optional description
  - **VCF Installer:** (Optional) Hostname, username, password, SSL verification
  - **SDDC Manager:** (Optional) Hostname, username, password, SSL verification
  - **Sync Settings:** Enable automatic sync and set interval (minutes)
- Use "🧪 Test Connection" to validate credentials
- Click "Save" to create environment

### 3. View Credentials
- Click "👁️ View" on any environment card
- See all credentials in a table format
- Export to CSV or Excel using the export buttons

### 4. Sync Credentials
- **Automatic:** Credentials sync at configured intervals
- **Manual:** Click "🔄 Sync Now" on any environment card

### 5. Edit Environment
- Click "✏️ Edit" on any environment card
- Update settings as needed
- Test connection before saving

### 6. Delete Environment
- Click "🗑️ Delete" on any environment card
- Type the environment name to confirm deletion
- This prevents accidental deletions

## 🔐 Security

### Authentication
- Passwords hashed with Werkzeug (PBKDF2-SHA256)
- Session-based authentication with Flask-Login
- Secure session cookies

### HTTPS Support
- Custom SSL certificates supported
- Self-signed certificates for development
- Production-grade SSL configuration

### SSL Verification
- Per-environment SSL verification settings
- Separate settings for VCF Installer and SDDC Manager
- Disable for self-signed certificates in lab environments

### Best Practices

```bash
# Secure the database file
chmod 600 instance/vcf_credentials.db

# Use HTTPS in production
./scripts/run_gunicorn_https.sh

# Enable SSL verification for production systems
# (in the web UI when adding environments)

# Change default admin password immediately
# Use "Change Password" link in the UI

# Restrict network access
# Use firewall rules to limit access to trusted IPs
```

## 🛠️ Configuration

### Environment Variables

```bash
# Flask configuration
export FLASK_ENV=production
export FLASK_SECRET_KEY=your-secret-key-here
export FLASK_RUN_PORT=5000

# Database location (optional)
export DATABASE_URL=sqlite:///instance/vcf_credentials.db
```

### Application Settings

Edit `app.py` to customize:
- Secret key (change for production!)
- Database location
- Session timeout
- Logging configuration

## 📊 Logging

Application logs are stored in the `logs/` directory:

- **vcf_credentials.log** - General application logs
- **vcf_credentials_errors.log** - Error logs only
- **gunicorn_access.log** - HTTP access logs (when using Gunicorn)
- **gunicorn_error.log** - Gunicorn error logs

Logs include:
- User login/logout events
- Environment operations (add, edit, delete)
- Credential sync operations
- API calls and errors
- Connection test results

## 🐛 Troubleshooting

### Database Issues

**Problem:** Database errors on startup

**Solution:**
```bash
# Remove old database (will lose data!)
rm instance/vcf_credentials.db

# Restart application (creates new database)
python app.py
```

### Port Already in Use

**Problem:** Port 5000 already in use

**Solution:**
```bash
# Use different port
export FLASK_RUN_PORT=8000
python app.py
```

### Connection Errors

**Problem:** Cannot connect to VCF systems

**Solutions:**
- Verify hostname/IP is correct
- Check username and password
- Disable SSL verification for self-signed certificates
- Use "🧪 Test Connection" button to diagnose
- Check firewall rules
- Review logs in `logs/vcf_credentials_errors.log`

### SSL Certificate Errors

**Problem:** SSL verification failures

**Solutions:**
```bash
# For development, use self-signed certificates
openssl req -x509 -newkey rsa:4096 -nodes \
  -keyout ssl/key.pem -out ssl/cert.pem -days 365

# Or disable SSL verification in environment settings
# (not recommended for production)
```

### Gunicorn Issues

**Problem:** Gunicorn won't start

**Solution:**
```bash
# Check if already running
ps aux | grep gunicorn

# Kill existing processes
pkill gunicorn

# Restart
./scripts/run_gunicorn.sh
```

## 📚 Documentation

Comprehensive documentation available in the `docs/` directory:

- **[START_HERE.md](docs/START_HERE.md)** - Overview and getting started
- **[QUICKSTART.md](docs/QUICKSTART.md)** - Quick setup guide
- **[DEPLOYMENT.md](docs/DEPLOYMENT.md)** - Production deployment guide
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - System architecture
- **[GUNICORN_GUIDE.md](docs/GUNICORN_GUIDE.md)** - Gunicorn deployment
- **[NEW_FEATURES.md](docs/NEW_FEATURES.md)** - Feature documentation
- **[UI_IMPROVEMENTS.md](docs/UI_IMPROVEMENTS.md)** - UI enhancements
- **[PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md)** - File organization
- **[CHANGELOG.md](docs/CHANGELOG.md)** - Version history

## 🔄 Scheduled Syncing

The application uses APScheduler for automatic credential syncing:

- Each environment can have its own sync schedule
- Sync intervals configured in minutes
- Syncs run in the background
- Last sync time displayed on environment cards
- Manual sync available anytime

### How It Works

1. Enable sync when creating/editing an environment
2. Set sync interval (e.g., 60 minutes)
3. Application automatically fetches credentials at intervals
4. Credentials stored in database
5. View updated credentials anytime

## 📤 Export Options

### CSV Export
- Simple comma-separated format
- Compatible with Excel, Google Sheets
- Includes all credential fields

### Excel Export
- Native .xlsx format
- Formatted headers
- Auto-sized columns
- Professional appearance

## 🤝 Contributing

### Development Setup

```bash
# Clone repository
git clone <repository-url>
cd vcf-credentials-fetch

# Install dependencies
pip install -r requirements.txt

# Run development server
python app.py
```

### Code Style
- Follow PEP 8 guidelines
- Use type hints where appropriate
- Add docstrings to functions
- Update documentation for new features

## 🎯 Roadmap

- [ ] Multi-user support with user management
- [ ] Role-based access control (RBAC)
- [ ] API endpoints for automation
- [ ] Credential rotation capabilities
- [ ] Audit logging with retention
- [ ] Integration with secret managers (HashiCorp Vault, etc.)
- [ ] Email notifications for sync failures
- [ ] Dashboard with statistics and charts
- [ ] Backup and restore functionality

## 📝 License

See LICENSE file for details.

## 📞 Support

### Getting Help

1. Check the documentation in `docs/`
2. Review troubleshooting section above
3. Check application logs in `logs/`
4. Verify configuration settings

### Reporting Issues

When reporting issues, include:
- Python version
- Operating system
- Error messages from logs
- Steps to reproduce
- Expected vs actual behavior

## ✨ Recent Updates

### Version 2.3.0
- Simplified to web-only application
- Removed CLI interface
- Streamlined documentation
- Improved focus on web features

### Version 2.1.0
- Added password change functionality
- Implemented connection testing
- Enhanced logging system
- Added delete confirmation prompts
- Sorted environments alphabetically
- Centered modals
- Added installer toggle
- Separate SSL verification settings

See [CHANGELOG.md](docs/CHANGELOG.md) for complete version history.

---

**Made with ❤️ for VMware Cloud Foundation administrators**
