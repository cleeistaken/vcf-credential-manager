# VCF Credentials Manager

A modern web application for managing and retrieving credentials from VMware Cloud Foundation (VCF) environments. This application provides a secure, user-friendly interface for fetching and storing credentials from VCF Installer and SDDC Manager instances.

## Features

- 🔐 **Secure Authentication**: User account management with password hashing
- 🌐 **HTTPS Support**: Built-in support for secure connections
- 🔄 **Automated Sync**: Configurable intervals for automatic credential retrieval
- 📊 **Modern UI**: Built with VMware Clarity Design System
- 💾 **SQLite Database**: Persistent storage for credentials and configurations
- 📤 **Export Options**: Export credentials to CSV or Excel formats
- 🎯 **Multi-Environment**: Manage multiple VCF environments from a single interface
- ⏰ **Scheduled Tasks**: Background jobs for automatic credential updates

## Requirements

- Python 3.8 or higher
- pip (Python package manager)
- Access to VCF Installer and/or SDDC Manager instances

## Installation

1. **Clone or download the repository**

```bash
cd vcf-credentials-fetch
```

2. **Create a virtual environment (recommended)**

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Initialize the database**

```bash
python app.py
```

On first run, the application will automatically:
- Create the SQLite database (`vcf_credentials.db`)
- Create a default admin user (username: `admin`, password: `admin`)

**⚠️ IMPORTANT: Change the default admin password immediately after first login!**

## Usage

### Development Mode

Run the application in development mode:

```bash
python app.py
```

The application will be available at `http://localhost:5000`

### Production Deployment

For production, use a WSGI server with HTTPS:

1. **Generate SSL certificates** (or use existing ones):

```bash
# Self-signed certificate (for testing)
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365

# Or use Let's Encrypt for production
```

2. **Run with Gunicorn**:

```bash
gunicorn --certfile=cert.pem --keyfile=key.pem --bind 0.0.0.0:443 app:app
```

3. **Or use a reverse proxy** (recommended):
   - Configure Nginx or Apache as a reverse proxy
   - Handle SSL termination at the proxy level
   - Forward requests to Gunicorn running on localhost

### Environment Variables

You can configure the application using environment variables:

```bash
export SECRET_KEY="your-secret-key-here"
export SQLALCHEMY_DATABASE_URI="sqlite:///vcf_credentials.db"
```

## Configuration

### Adding Environments

1. Log in to the web interface
2. Click "Add Environment"
3. Fill in the environment details:
   - **Environment Name**: A friendly name for the environment
   - **Description**: Optional description
   - **VCF Installer**: Host, username, and password for the installer
   - **SDDC Manager**: Host, username, and password for the manager
   - **Sync Configuration**: Enable automatic sync and set interval (in minutes)

### Managing Credentials

- **View Credentials**: Click on an environment to view its credentials
- **Sync Now**: Manually trigger a credential sync
- **Export**: Download credentials as CSV or Excel
- **Search**: Filter credentials by hostname, username, or resource type

### Scheduled Syncing

Enable automatic credential syncing for each environment:

1. Edit the environment
2. Check "Enable automatic sync"
3. Set the sync interval in minutes (minimum 5 minutes)
4. Save the configuration

The application will automatically fetch credentials at the specified interval.

## Database Schema

### Users Table
- `id`: Primary key
- `username`: Unique username
- `password_hash`: Hashed password
- `is_admin`: Admin flag
- `created_at`: Account creation timestamp

### Environments Table
- `id`: Primary key
- `name`: Environment name
- `description`: Optional description
- `installer_host`, `installer_username`, `installer_password`: VCF Installer credentials
- `manager_host`, `manager_username`, `manager_password`: SDDC Manager credentials
- `ssl_verify`: SSL verification flag
- `sync_enabled`: Auto-sync enabled flag
- `sync_interval_minutes`: Sync interval
- `last_sync`: Last sync timestamp

### Credentials Table
- `id`: Primary key
- `environment_id`: Foreign key to environments
- `hostname`: Resource hostname
- `username`: Credential username
- `password`: Credential password
- `credential_type`: Type of credential (USER, SERVICE, etc.)
- `account_type`: Account type
- `resource_type`: Resource type (ESXI, VCENTER, NSX_MANAGER, etc.)
- `domain_name`: Domain name
- `last_updated`: Last update timestamp

## API Endpoints

### Authentication
- `POST /login`: User login
- `GET /logout`: User logout

### Environments
- `GET /api/environments`: List all environments
- `POST /api/environments`: Create new environment
- `GET /api/environments/<id>`: Get environment details
- `PUT /api/environments/<id>`: Update environment
- `DELETE /api/environments/<id>`: Delete environment
- `POST /api/environments/<id>/sync`: Manually sync credentials

### Credentials
- `GET /api/environments/<id>/credentials`: Get credentials for environment
- `GET /api/environments/<id>/export/csv`: Export as CSV
- `GET /api/environments/<id>/export/excel`: Export as Excel

## Security Considerations

1. **Change Default Credentials**: Always change the default admin password
2. **Use HTTPS**: Always use HTTPS in production
3. **Secure Database**: Protect the SQLite database file with appropriate permissions
4. **Network Security**: Restrict access to the application using firewalls
5. **SSL Verification**: Enable SSL verification for VCF connections when possible
6. **Regular Updates**: Keep dependencies updated for security patches

## Troubleshooting

### Connection Issues

If you can't connect to VCF Installer or SDDC Manager:

1. Verify the hostname is correct and reachable
2. Check username and password
3. Try disabling SSL verification for self-signed certificates
4. Check firewall rules

### Database Issues

If the database becomes corrupted:

```bash
# Backup existing database
cp vcf_credentials.db vcf_credentials.db.backup

# Delete and reinitialize
rm vcf_credentials.db
python app.py
```

### Sync Issues

If automatic syncing isn't working:

1. Check the application logs
2. Verify the environment credentials are correct
3. Manually trigger a sync to see error messages
4. Check that the sync interval is at least 5 minutes

## CLI Commands

The application includes CLI commands for management:

```bash
# Initialize database
flask --app app init-db

# Create admin user
flask --app app create-admin
```

## Architecture

- **Backend**: Flask web framework with SQLAlchemy ORM
- **Frontend**: HTML/CSS/JavaScript with VMware Clarity Design System
- **Database**: SQLite for simplicity and portability
- **Scheduler**: APScheduler for background tasks
- **Authentication**: Flask-Login for session management

## Original Code Integration

This application is a complete rewrite of the original CLI-based credential fetcher. The core credential fetching logic from the original `sddc_installer.py` and `sddc_manager.py` has been integrated into the `vcf_fetcher.py` module.

## Contributing

Contributions are welcome! Please ensure:

1. Code follows PEP 8 style guidelines
2. All new features include appropriate error handling
3. Security best practices are followed

## License

This project is provided as-is for use with VMware Cloud Foundation environments.

## Support

For issues or questions:

1. Check the troubleshooting section
2. Review application logs
3. Verify VCF connectivity and credentials

## Changelog

### Version 2.0.0 (Current)
- Complete rewrite as web application
- Added user authentication
- Implemented Clarity UI design
- Added SQLite database storage
- Implemented scheduled credential syncing
- Added CSV/Excel export functionality
- Multi-environment support

### Version 1.0.0 (Original)
- CLI-based credential fetcher
- YAML configuration files
- CSV export only

