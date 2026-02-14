#!/bin/bash
################################################################################
# VCF Credential Manager Update Script
# 
# This script updates an existing VCF Credential Manager installation to a
# new version while preserving the database, SSL certificates, and configuration.
#
# Prerequisites:
# - Download a new release bundle and extract it, OR
# - Clone/pull the latest from the repository
#
# Usage:
# cd vcf-credential-manager/tools
# sudo ./update-vcf-credential-manager.sh
#
# Options:
#   --no-backup     Skip creating a backup before update
#   --force         Force update even if versions match
#   --help          Show this help message
################################################################################

set -e  # Exit on error
set -u  # Exit on undefined variable

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'  # No Color

# Configuration variables
APP_NAME="vcf-credential-manager"
INSTALL_DIR="/opt/${APP_NAME}"
SERVICE_NAME="vcf-credential-manager"
BACKUP_DIR="/opt/${APP_NAME}-backups"

# Get the directory where this script is located (tools directory)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# Source directory is the parent of tools directory
SOURCE_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"

# Options
CREATE_BACKUP=true
FORCE_UPDATE=false

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

log_step() {
    echo -e "${CYAN}[STEP]${NC} $1"
}

# Show help message
show_help() {
    echo "VCF Credential Manager Update Script"
    echo ""
    echo "Usage: sudo $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --no-backup     Skip creating a backup before update"
    echo "  --force         Force update even if versions match"
    echo "  --help          Show this help message"
    echo ""
    echo "Examples:"
    echo "  sudo $0                    # Normal update with backup"
    echo "  sudo $0 --no-backup        # Update without backup"
    echo "  sudo $0 --force            # Force update"
    echo ""
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --no-backup)
                CREATE_BACKUP=false
                shift
                ;;
            --force)
                FORCE_UPDATE=true
                shift
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root or with sudo"
        exit 1
    fi
}

# Check if VCF Credential Manager is installed
check_installation() {
    log_info "Checking existing installation..."
    
    if [[ ! -d "$INSTALL_DIR" ]]; then
        log_error "VCF Credential Manager is not installed at $INSTALL_DIR"
        log_error "Please run the installation script first: install-vcf-credential-manager.sh"
        exit 1
    fi
    
    if [[ ! -f "$INSTALL_DIR/app.py" ]]; then
        log_error "Installation appears to be corrupted (app.py not found)"
        exit 1
    fi
    
    log_success "Found existing installation at $INSTALL_DIR"
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

# Get version from version.json file
get_version() {
    local dir="$1"
    local version_file="$dir/static/json/version.json"
    
    if [[ -f "$version_file" ]]; then
        # Try to extract version info
        local version=$(python3 -c "import json; d=json.load(open('$version_file')); print(d.get('tag') or d.get('commit_short', 'unknown'))" 2>/dev/null || echo "unknown")
        echo "$version"
    else
        echo "unknown"
    fi
}

# Compare versions
compare_versions() {
    log_info "Comparing versions..."
    
    local current_version=$(get_version "$INSTALL_DIR")
    local new_version=$(get_version "$SOURCE_DIR")
    
    echo ""
    echo "  Current installed version: $current_version"
    echo "  New version to install:    $new_version"
    echo ""
    
    if [[ "$current_version" == "$new_version" ]] && [[ "$FORCE_UPDATE" != "true" ]]; then
        log_warning "Versions appear to be the same."
        read -p "Do you want to continue with the update anyway? (yes/no): " -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
            log_info "Update cancelled."
            exit 0
        fi
    fi
}

# Confirm update
confirm_update() {
    echo ""
    echo "=========================================="
    echo "  VCF Credential Manager Update"
    echo "=========================================="
    echo ""
    log_warning "This will update VCF Credential Manager to a new version."
    echo ""
    echo "The following will be PRESERVED:"
    echo "  - Database (credentials, environments, users)"
    echo "  - SSL certificates"
    echo "  - Log files"
    echo ""
    echo "The following will be UPDATED:"
    echo "  - Application code"
    echo "  - Static files (CSS, JS, images)"
    echo "  - Templates"
    echo "  - Python dependencies"
    echo ""
    
    if [[ "$CREATE_BACKUP" == "true" ]]; then
        echo "A backup will be created before the update."
    else
        log_warning "Backup creation is DISABLED (--no-backup flag)"
    fi
    echo ""
    
    read -p "Do you want to continue? (yes/no): " -r
    echo ""
    
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        log_info "Update cancelled."
        exit 0
    fi
}

# Stop the service
stop_service() {
    log_step "Stopping VCF Credential Manager service..."
    
    if systemctl is-active --quiet "${SERVICE_NAME}.service"; then
        systemctl stop "${SERVICE_NAME}.service"
        log_success "Service stopped"
    else
        log_warning "Service was not running"
    fi
}

# Create backup
create_backup() {
    if [[ "$CREATE_BACKUP" != "true" ]]; then
        log_warning "Skipping backup (--no-backup flag)"
        return
    fi
    
    log_step "Creating backup..."
    
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_path="${BACKUP_DIR}/backup_${timestamp}"
    
    mkdir -p "$BACKUP_DIR"
    mkdir -p "$backup_path"
    
    # Backup the entire installation directory
    log_info "Backing up installation directory..."
    cp -a "$INSTALL_DIR" "$backup_path/installation"
    
    # Create a manifest file
    cat > "$backup_path/manifest.txt" << EOF
VCF Credential Manager Backup
=============================
Date: $(date)
Source Version: $(get_version "$INSTALL_DIR")
Installation Directory: $INSTALL_DIR

Contents:
- installation/  : Full installation directory backup
EOF
    
    log_success "Backup created at: $backup_path"
    
    # Clean up old backups (keep last 5)
    log_info "Cleaning up old backups (keeping last 5)..."
    cd "$BACKUP_DIR"
    ls -dt backup_* 2>/dev/null | tail -n +6 | xargs rm -rf 2>/dev/null || true
}

# Update application files
update_application_files() {
    log_step "Updating application files..."
    
    # Files and directories to preserve (not overwrite)
    local preserve_items=(
        "instance"           # Database
        "ssl"                # SSL certificates
        "logs"               # Log files
        ".venv"              # Virtual environment (will be updated separately)
        "gunicorn.pid"       # PID file
    )
    
    # Create temporary directory for preserved items
    local temp_preserve="/tmp/vcf-update-preserve-$$"
    mkdir -p "$temp_preserve"
    
    # Preserve important files
    log_info "Preserving database, certificates, and logs..."
    for item in "${preserve_items[@]}"; do
        if [[ -e "$INSTALL_DIR/$item" ]]; then
            cp -a "$INSTALL_DIR/$item" "$temp_preserve/" 2>/dev/null || true
        fi
    done
    
    # Also preserve the Pipfile.original if it exists (contains original Python version)
    if [[ -f "$INSTALL_DIR/Pipfile.original" ]]; then
        cp "$INSTALL_DIR/Pipfile.original" "$temp_preserve/"
    fi
    
    # Copy new application files
    log_info "Copying new application files..."
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
        --exclude='logs' \
        --exclude='ssl' \
        --exclude='*.db' \
        --exclude='Pipfile.lock' \
        --exclude='.venv' \
        --exclude='venv' \
        --exclude='gunicorn.pid' \
        --delete \
        "$SOURCE_DIR/" "$INSTALL_DIR/"
    
    # Restore preserved items
    log_info "Restoring preserved files..."
    for item in "${preserve_items[@]}"; do
        if [[ -e "$temp_preserve/$item" ]]; then
            # Remove any new version of the item first
            rm -rf "$INSTALL_DIR/$item" 2>/dev/null || true
            # Restore the preserved item
            cp -a "$temp_preserve/$item" "$INSTALL_DIR/"
        fi
    done
    
    # Restore Pipfile.original if it was preserved
    if [[ -f "$temp_preserve/Pipfile.original" ]]; then
        cp "$temp_preserve/Pipfile.original" "$INSTALL_DIR/"
    fi
    
    # Clean up temp directory
    rm -rf "$temp_preserve"
    
    log_success "Application files updated"
}

# Update Python dependencies
update_python_dependencies() {
    log_step "Updating Python dependencies..."
    
    cd "$INSTALL_DIR"
    
    # Get the system Python version
    PYTHON_MAJOR_MINOR=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    log_info "System Python version: ${PYTHON_MAJOR_MINOR}"
    
    # Update Pipfile to use system Python version if needed
    if [[ -f "Pipfile" ]]; then
        log_info "Configuring Pipfile to use system Python ${PYTHON_MAJOR_MINOR}..."
        sed -i "s/python_version = .*/python_version = \"${PYTHON_MAJOR_MINOR}\"/" Pipfile || true
        sed -i 's/python_full_version = .*//' Pipfile || true
    fi
    
    # Update dependencies
    log_info "Installing/updating dependencies with pipenv..."
    PIPENV_VENV_IN_PROJECT=1 PIPENV_PYTHON=3 pipenv install --skip-lock
    
    log_success "Python dependencies updated"
}

# Update database schema if needed
update_database() {
    log_step "Checking database schema..."
    
    cd "$INSTALL_DIR"
    
    # Run database migrations/updates
    # This creates any new tables that might have been added
    PIPENV_VENV_IN_PROJECT=1 pipenv run python3 -c 'from app import app, db; app.app_context().push(); db.create_all()' || true
    
    log_success "Database schema updated"
}

# Update startup scripts
update_startup_scripts() {
    log_step "Updating startup scripts..."
    
    # Make scripts executable
    chmod +x "$INSTALL_DIR/start_https.sh" 2>/dev/null || true
    chmod +x "$INSTALL_DIR/start_https_443.sh" 2>/dev/null || true
    
    # Recreate the port 443 startup script if it doesn't exist
    if [[ ! -f "$INSTALL_DIR/start_https_443.sh" ]]; then
        log_info "Creating Gunicorn HTTPS script for port 443..."
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
    fi
    
    log_success "Startup scripts updated"
}

# Set proper permissions
set_permissions() {
    log_step "Setting permissions..."
    
    # Set root ownership for the entire directory (service runs as root for port 443)
    chown -R root:root "$INSTALL_DIR"
    chmod -R 755 "$INSTALL_DIR"
    
    # SSL certificates - restrictive permissions
    chmod 600 "$INSTALL_DIR/ssl/key.pem" 2>/dev/null || true
    chmod 644 "$INSTALL_DIR/ssl/cert.pem" 2>/dev/null || true
    
    # Database - restrictive permissions
    chmod 600 "$INSTALL_DIR/instance/vcf_credentials.db" 2>/dev/null || true
    
    # Logs directory
    chmod 755 "$INSTALL_DIR/logs"
    chmod 644 "$INSTALL_DIR/logs"/*.log 2>/dev/null || true
    
    # Instance directory
    chmod 755 "$INSTALL_DIR/instance"
    
    log_success "Permissions set"
}

# Reload systemd and start service
start_service() {
    log_step "Starting VCF Credential Manager service..."
    
    systemctl daemon-reload
    systemctl start "${SERVICE_NAME}.service"
    
    sleep 5
    
    if systemctl is-active --quiet "${SERVICE_NAME}.service"; then
        log_success "Service started successfully"
    else
        log_error "Service failed to start. Check logs with: journalctl -u ${SERVICE_NAME}.service -n 50"
        exit 1
    fi
}

# Display update summary
display_summary() {
    local new_version=$(get_version "$INSTALL_DIR")
    
    echo ""
    echo "=========================================="
    echo "  VCF Credential Manager Update Complete"
    echo "=========================================="
    echo ""
    log_success "Update completed successfully!"
    echo ""
    echo "Update Details:"
    echo "  - Installation Directory: $INSTALL_DIR"
    echo "  - New Version: $new_version"
    echo ""
    
    if [[ "$CREATE_BACKUP" == "true" ]]; then
        echo "Backup Location:"
        echo "  - $BACKUP_DIR"
        echo ""
    fi
    
    echo "Preserved Items:"
    echo "  - Database: $INSTALL_DIR/instance/vcf_credentials.db"
    echo "  - SSL Certificates: $INSTALL_DIR/ssl/"
    echo "  - Log Files: $INSTALL_DIR/logs/"
    echo ""
    echo "Useful Commands:"
    echo "  - Check status: systemctl status $SERVICE_NAME"
    echo "  - View logs: journalctl -u $SERVICE_NAME -f"
    echo "  - Restart service: systemctl restart $SERVICE_NAME"
    echo "  - Application logs: tail -f $INSTALL_DIR/logs/*.log"
    echo ""
    
    if [[ "$CREATE_BACKUP" == "true" ]]; then
        echo "To rollback to the previous version:"
        echo "  1. Stop the service: systemctl stop $SERVICE_NAME"
        echo "  2. Restore from backup: cp -a $BACKUP_DIR/backup_*/installation/* $INSTALL_DIR/"
        echo "  3. Start the service: systemctl start $SERVICE_NAME"
        echo ""
    fi
    
    echo "=========================================="
}

# Main update flow
main() {
    parse_args "$@"
    
    echo ""
    echo "=========================================="
    echo "  VCF Credential Manager Updater"
    echo "=========================================="
    echo ""
    
    check_root
    check_installation
    validate_source
    compare_versions
    confirm_update
    stop_service
    create_backup
    update_application_files
    update_python_dependencies
    update_database
    update_startup_scripts
    set_permissions
    start_service
    display_summary
}

# Run main function
main "$@"
