#!/bin/bash
################################################################################
# VCF Credential Manager Installation Script for Ubuntu 24.04
# 
# This script installs and configures the VCF Credential Manager application
# as a systemd service running on port 443 (HTTPS).
#
# Prerequisites:
# - Download a release bundle and extract it, OR
# - Clone the repository: git clone https://github.com/cleeistaken/vcf-credential-manager.git
#
# Requirements:
# - Ubuntu 24.04
# - Root/sudo access
# - Internet connection (for installing system dependencies)
#
# Usage:
# cd vcf-credential-manager/tools
# sudo ./install-vcf-credential-manager.sh
################################################################################

set -e  # Exit on error
set -u  # Exit on undefined variable

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'  # No Color

# Configuration variables
APP_NAME="vcf-credential-manager"
APP_USER="vcfcredmgr"
APP_GROUP="vcfcredmgr"
INSTALL_DIR="/opt/${APP_NAME}"
SERVICE_NAME="vcf-credential-manager"
HTTPS_PORT=443

# Get the directory where this script is located (tools directory)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# Source directory is the parent of tools directory
SOURCE_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root or with sudo"
        exit 1
    fi
}

# Check Ubuntu version
check_ubuntu_version() {
    log_info "Checking Ubuntu version..."
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        if [[ "$ID" != "ubuntu" ]]; then
            log_error "This script is designed for Ubuntu only"
            exit 1
        fi
        log_success "Running on Ubuntu $VERSION"
    else
        log_error "Cannot determine OS version"
        exit 1
    fi
}

# Validate source directory contains required files
validate_source() {
    log_info "Validating source directory: $SOURCE_DIR"
    
    # Check for required files
    local required_files=("app.py" "Pipfile" "requirements.txt" "gunicorn_config.py")
    local missing_files=()
    
    for file in "${required_files[@]}"; do
        if [[ ! -f "$SOURCE_DIR/$file" ]]; then
            missing_files+=("$file")
        fi
    done
    
    if [[ ${#missing_files[@]} -gt 0 ]]; then
        log_error "Missing required files in source directory:"
        for file in "${missing_files[@]}"; do
            echo "  - $file"
        done
        log_error "Please ensure you have downloaded the complete release bundle or cloned the repository."
        exit 1
    fi
    
    log_success "Source directory validated"
}

# Install system dependencies
install_dependencies() {
    log_info "Installing system dependencies..."
    
    apt-get update
    apt-get install -y \
        python3 \
        python3-pip \
        python3-venv \
        python3-dev \
        build-essential \
        libssl-dev \
        libffi-dev \
        openssl \
        curl \
        rsync
    
    # Install pipenv - use --break-system-packages for Ubuntu 24.04
    # This is safe because pipenv will create isolated virtual environments
    log_info "Installing pipenv..."
    pip3 install --break-system-packages --upgrade pipenv
    
    log_success "System dependencies installed"
}

# Create application user and group
create_app_user() {
    log_info "Creating application user and group..."
    
    if ! getent group "$APP_GROUP" > /dev/null 2>&1; then
        groupadd --system "$APP_GROUP"
        log_success "Created group: $APP_GROUP"
    else
        log_warning "Group $APP_GROUP already exists"
    fi
    
    if ! id "$APP_USER" > /dev/null 2>&1; then
        useradd --system \
            --gid "$APP_GROUP" \
            --shell /bin/bash \
            --home-dir "$INSTALL_DIR" \
            --comment "VCF Credential Manager Service User" \
            "$APP_USER"
        log_success "Created user: $APP_USER"
    else
        log_warning "User $APP_USER already exists"
    fi
}

# Copy application files to installation directory
copy_application_files() {
    log_info "Copying application files to $INSTALL_DIR..."
    
    if [[ -d "$INSTALL_DIR" ]]; then
        log_warning "Installation directory already exists. Backing up..."
        mv "$INSTALL_DIR" "${INSTALL_DIR}.backup.$(date +%Y%m%d_%H%M%S)"
    fi
    
    # Create installation directory
    mkdir -p "$INSTALL_DIR"
    
    # Copy all files except excluded directories/files
    rsync -av \
        --exclude='.git' \
        --exclude='.gitignore' \
        --exclude='.idea' \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        --exclude='*.pyo' \
        --exclude='.DS_Store' \
        --exclude='.env' \
        --exclude='instance' \
        --exclude='logs/*.log' \
        --exclude='ssl/*.pem' \
        --exclude='ssl/*.key' \
        --exclude='ssl/*.crt' \
        --exclude='*.db' \
        --exclude='Pipfile.lock' \
        --exclude='.venv' \
        --exclude='venv' \
        "$SOURCE_DIR/" "$INSTALL_DIR/"
    
    log_success "Application files copied to $INSTALL_DIR"
}

# Create necessary directories
create_directories() {
    log_info "Creating necessary directories..."
    
    mkdir -p "$INSTALL_DIR/logs"
    mkdir -p "$INSTALL_DIR/instance"
    mkdir -p "$INSTALL_DIR/ssl"
    
    # Set initial ownership for directories that need to be writable by root
    # (service runs as root for port 443 binding)
    chown root:root "$INSTALL_DIR/logs"
    chown root:root "$INSTALL_DIR/instance"
    chmod 755 "$INSTALL_DIR/logs"
    chmod 755 "$INSTALL_DIR/instance"
    
    log_success "Directories created"
}

# Generate SSL certificates
generate_ssl_certificates() {
    log_info "Generating SSL certificates..."
    
    mkdir -p "$INSTALL_DIR/ssl"
    
    if [[ ! -f "$INSTALL_DIR/ssl/cert.pem" ]] || [[ ! -f "$INSTALL_DIR/ssl/key.pem" ]]; then
        # Get the server's hostname and IP addresses for SAN
        HOSTNAME=$(hostname)
        IP_ADDR=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "127.0.0.1")
        
        # Create OpenSSL config for SAN (Subject Alternative Names)
        cat > "$INSTALL_DIR/ssl/openssl.cnf" <<EOF
[req]
default_bits = 4096
prompt = no
default_md = sha256
distinguished_name = dn
req_extensions = v3_req

[dn]
C=US
ST=State
L=City
O=VCF Credentials Manager
CN=${HOSTNAME}

[v3_req]
subjectAltName = @alt_names

[alt_names]
DNS.1 = ${HOSTNAME}
DNS.2 = localhost
DNS.3 = *.local
IP.1 = ${IP_ADDR}
IP.2 = 127.0.0.1
EOF

        openssl req -x509 -newkey rsa:4096 -nodes \
            -keyout "$INSTALL_DIR/ssl/key.pem" \
            -out "$INSTALL_DIR/ssl/cert.pem" \
            -days 365 \
            -config "$INSTALL_DIR/ssl/openssl.cnf" \
            -extensions v3_req
        
        # Clean up config file
        rm -f "$INSTALL_DIR/ssl/openssl.cnf"
        
        log_success "SSL certificates generated for: $HOSTNAME, localhost, $IP_ADDR"
    else
        log_warning "SSL certificates already exist"
    fi
    
    chmod 600 "$INSTALL_DIR/ssl/key.pem"
    chmod 644 "$INSTALL_DIR/ssl/cert.pem"
}

# Setup Python environment with pipenv
setup_python_environment() {
    log_info "Setting up Python environment with pipenv..."
    
    cd "$INSTALL_DIR"
    
    # Get the system Python version
    PYTHON_VERSION=$(python3 --version | awk '{print $2}')
    PYTHON_MAJOR_MINOR=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    log_info "System Python version: $PYTHON_VERSION (${PYTHON_MAJOR_MINOR})"
    
    # Verify Python version meets minimum requirements (3.9+)
    PYTHON_MAJOR=$(echo "$PYTHON_MAJOR_MINOR" | cut -d. -f1)
    PYTHON_MINOR=$(echo "$PYTHON_MAJOR_MINOR" | cut -d. -f2)
    
    if [[ "$PYTHON_MAJOR" -lt 3 ]] || [[ "$PYTHON_MAJOR" -eq 3 && "$PYTHON_MINOR" -lt 9 ]]; then
        log_error "Python 3.9 or higher is required. Current version: $PYTHON_VERSION"
        exit 1
    fi
    
    # Ensure proper ownership before creating virtual environment
    log_info "Setting ownership for Python environment setup..."
    chown -R "$APP_USER:$APP_GROUP" "$INSTALL_DIR"
    
    # Check if Pipfile exists and modify it to use system Python
    if [[ -f "Pipfile" ]]; then
        log_info "Configuring Pipfile to use system Python ${PYTHON_MAJOR_MINOR}..."
        # Backup original Pipfile
        cp Pipfile Pipfile.original
        
        # Update Pipfile to use system Python version
        sed -i "s/python_version = .*/python_version = \"${PYTHON_MAJOR_MINOR}\"/" Pipfile || true
        sed -i 's/python_full_version = .*//' Pipfile || true
        
        # Ensure modified files have correct ownership
        chown "$APP_USER:$APP_GROUP" Pipfile Pipfile.original
    fi
    
    # Install dependencies using pipenv with system Python
    # --skip-lock: Skip Pipfile.lock generation if there are version conflicts
    log_info "Installing dependencies with pipenv..."
    sudo -u "$APP_USER" PIPENV_VENV_IN_PROJECT=1 PIPENV_PYTHON=3 pipenv install --skip-lock
    
    log_success "Python environment configured"
}

# Create custom startup script for port 443
configure_gunicorn_script() {
    log_info "Creating custom Gunicorn HTTPS script for port 443..."
    
    # Check if the original startup script exists
    if [[ -f "$INSTALL_DIR/start_https.sh" ]]; then
        # Make the original script executable
        chmod +x "$INSTALL_DIR/start_https.sh"
    fi
    
    # Create a custom version that binds to 0.0.0.0:443
    cat > "$INSTALL_DIR/start_https_443.sh" << 'EOF'
#!/bin/bash
# Custom Gunicorn HTTPS startup script for port 443

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cd "$SCRIPT_DIR"

# Activate pipenv environment and run gunicorn
export PIPENV_VENV_IN_PROJECT=1
exec pipenv run gunicorn \
    --config gunicorn_config.py \
    --bind 0.0.0.0:443 \
    --certfile ssl/cert.pem \
    --keyfile ssl/key.pem \
    --pid gunicorn.pid \
    --access-logfile logs/gunicorn_access.log \
    --error-logfile logs/gunicorn_error.log \
    app:app
EOF
    
    chmod +x "$INSTALL_DIR/start_https_443.sh"
    
    log_success "Gunicorn script configured for port 443"
}

# Create systemd service file
create_systemd_service() {
    log_info "Creating systemd service..."
    
    cat > "/etc/systemd/system/${SERVICE_NAME}.service" << EOF
[Unit]
Description=VCF Credential Manager Service
After=network.target
Wants=network-online.target

[Service]
Type=exec
User=root
Group=root
WorkingDirectory=${INSTALL_DIR}
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
Environment="PIPENV_VENV_IN_PROJECT=1"
Environment="PYTHONUNBUFFERED=1"

# Use the custom script that runs on port 443
ExecStart=${INSTALL_DIR}/start_https_443.sh

# PID file for proper process tracking
PIDFile=${INSTALL_DIR}/gunicorn.pid

# Restart policy
Restart=always
RestartSec=10
StartLimitInterval=200
StartLimitBurst=5

# Security settings
NoNewPrivileges=false
PrivateTmp=false
ProtectSystem=full
ProtectHome=true

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=${SERVICE_NAME}

# Allow binding to privileged port 443
AmbientCapabilities=CAP_NET_BIND_SERVICE
CapabilityBoundingSet=CAP_NET_BIND_SERVICE

[Install]
WantedBy=multi-user.target
EOF
    
    log_success "Systemd service file created"
}

# Set proper permissions
set_permissions() {
    log_info "Setting proper permissions..."
    
    # Since the service runs as root (for port 443), set root ownership for the entire directory
    # This allows root to write temp files, PID files, etc.
    chown -R root:root "$INSTALL_DIR"
    chmod -R 755 "$INSTALL_DIR"
    
    # SSL certificates - restrictive permissions
    chmod 600 "$INSTALL_DIR/ssl/key.pem"
    chmod 644 "$INSTALL_DIR/ssl/cert.pem"
    
    # Database - restrictive permissions
    chmod 600 "$INSTALL_DIR/instance/vcf_credentials.db" 2>/dev/null || true
    
    # Logs directory
    chmod 755 "$INSTALL_DIR/logs"
    chmod 644 "$INSTALL_DIR/logs"/*.log 2>/dev/null || true
    
    # Instance directory
    chmod 755 "$INSTALL_DIR/instance"
    
    log_success "Permissions set"
}

# Initialize database
initialize_database() {
    log_info "Initializing database..."
    
    cd "$INSTALL_DIR"
    PIPENV_VENV_IN_PROJECT=1 pipenv run python3 -c 'from app import app, db; app.app_context().push(); db.create_all()' || true
    
    log_success "Database initialized"
}

# Configure firewall
configure_firewall() {
    log_info "Configuring firewall..."
    
    if command -v ufw &> /dev/null; then
        ufw allow 443/tcp comment 'VCF Credential Manager HTTPS'
        log_success "Firewall rule added for port 443"
    else
        log_warning "UFW not found, skipping firewall configuration"
    fi
}

# Enable and start service
enable_service() {
    log_info "Enabling and starting service..."
    
    systemctl daemon-reload
    systemctl enable "${SERVICE_NAME}.service"
    systemctl start "${SERVICE_NAME}.service"
    
    sleep 5
    
    if systemctl is-active --quiet "${SERVICE_NAME}.service"; then
        log_success "Service started successfully"
    else
        log_error "Service failed to start. Check logs with: journalctl -u ${SERVICE_NAME}.service -n 50"
        exit 1
    fi
}

# Display installation summary
display_summary() {
    echo ""
    echo "=========================================="
    echo "  VCF Credential Manager Installation"
    echo "=========================================="
    echo ""
    log_success "Installation completed successfully!"
    echo ""
    echo "Installation Details:"
    echo "  - Source Directory: $SOURCE_DIR"
    echo "  - Installation Directory: $INSTALL_DIR"
    echo "  - Service Name: $SERVICE_NAME"
    echo "  - HTTPS Port: $HTTPS_PORT"
    echo "  - Application User: $APP_USER"
    echo ""
    echo "SSL Certificates:"
    echo "  - Certificate: $INSTALL_DIR/ssl/cert.pem"
    echo "  - Private Key: $INSTALL_DIR/ssl/key.pem"
    echo ""
    echo "Access the application:"
    echo "  - URL: https://localhost:$HTTPS_PORT"
    echo "  - Default Username: admin"
    echo "  - Default Password: admin"
    echo ""
    echo "⚠️  IMPORTANT: Change the default password immediately after first login!"
    echo ""
    echo "Useful Commands:"
    echo "  - Check status: systemctl status $SERVICE_NAME"
    echo "  - View logs: journalctl -u $SERVICE_NAME -f"
    echo "  - Restart service: systemctl restart $SERVICE_NAME"
    echo "  - Stop service: systemctl stop $SERVICE_NAME"
    echo "  - Application logs: tail -f $INSTALL_DIR/logs/*.log"
    echo ""
    echo "=========================================="
}

# Main installation flow
main() {
    echo ""
    echo "=========================================="
    echo "  VCF Credential Manager Installer"
    echo "=========================================="
    echo ""
    
    check_root
    check_ubuntu_version
    validate_source
    install_dependencies
    create_app_user
    copy_application_files
    create_directories
    generate_ssl_certificates
    setup_python_environment
    configure_gunicorn_script
    initialize_database
    set_permissions
    create_systemd_service
    configure_firewall
    enable_service
    display_summary
}

# Run main function
main "$@"
