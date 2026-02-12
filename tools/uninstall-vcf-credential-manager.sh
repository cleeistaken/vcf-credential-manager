#!/bin/bash
################################################################################
# VCF Credential Manager Uninstallation Script
# 
# This script removes the VCF Credential Manager application and all
# associated files, services, and configurations.
#
# Usage:
# sudo ./uninstall-vcf-credential-manager.sh
################################################################################

set -e  # Exit on error

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
CHROOT_DIR="/opt/${APP_NAME}-chroot"
SERVICE_NAME="vcf-credential-manager"

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

# Confirm uninstallation
confirm_uninstall() {
    echo ""
    echo "=========================================="
    echo "  VCF Credential Manager Uninstaller"
    echo "=========================================="
    echo ""
    log_warning "This will completely remove VCF Credential Manager and all its data."
    echo ""
    read -p "Are you sure you want to continue? (yes/no): " -r
    echo ""
    
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        log_info "Uninstallation cancelled."
        exit 0
    fi
}

# Stop and disable service
stop_service() {
    log_info "Stopping and disabling service..."
    
    if systemctl is-active --quiet "${SERVICE_NAME}.service"; then
        systemctl stop "${SERVICE_NAME}.service"
        log_success "Service stopped"
    else
        log_warning "Service is not running"
    fi
    
    if systemctl is-enabled --quiet "${SERVICE_NAME}.service" 2>/dev/null; then
        systemctl disable "${SERVICE_NAME}.service"
        log_success "Service disabled"
    else
        log_warning "Service is not enabled"
    fi
}

# Remove systemd service file
remove_service_file() {
    log_info "Removing systemd service file..."
    
    if [[ -f "/etc/systemd/system/${SERVICE_NAME}.service" ]]; then
        rm -f "/etc/systemd/system/${SERVICE_NAME}.service"
        systemctl daemon-reload
        log_success "Service file removed"
    else
        log_warning "Service file not found"
    fi
}

# Unmount chroot filesystems
unmount_chroot() {
    log_info "Unmounting chroot filesystems..."
    
    if [[ -d "$CHROOT_DIR" ]]; then
        umount "$CHROOT_DIR/proc" 2>/dev/null || true
        umount "$CHROOT_DIR/sys" 2>/dev/null || true
        umount "$CHROOT_DIR/dev" 2>/dev/null || true
        log_success "Chroot filesystems unmounted"
    fi
}

# Remove installation directories
remove_directories() {
    log_info "Removing installation directories..."
    
    if [[ -d "$INSTALL_DIR" ]]; then
        rm -rf "$INSTALL_DIR"
        log_success "Removed $INSTALL_DIR"
    else
        log_warning "Installation directory not found"
    fi
    
    if [[ -d "$CHROOT_DIR" ]]; then
        rm -rf "$CHROOT_DIR"
        log_success "Removed $CHROOT_DIR"
    else
        log_warning "Chroot directory not found"
    fi
}

# Remove application user and group
remove_user() {
    log_info "Removing application user and group..."
    
    if id "$APP_USER" &>/dev/null; then
        userdel "$APP_USER"
        log_success "Removed user: $APP_USER"
    else
        log_warning "User $APP_USER not found"
    fi
    
    if getent group "$APP_GROUP" > /dev/null 2>&1; then
        groupdel "$APP_GROUP" 2>/dev/null || true
        log_success "Removed group: $APP_GROUP"
    else
        log_warning "Group $APP_GROUP not found"
    fi
}

# Remove firewall rules
remove_firewall_rules() {
    log_info "Removing firewall rules..."
    
    if command -v ufw &> /dev/null; then
        ufw delete allow 443/tcp 2>/dev/null || true
        log_success "Firewall rules removed"
    else
        log_warning "UFW not found, skipping firewall cleanup"
    fi
}

# Display completion message
display_completion() {
    echo ""
    echo "=========================================="
    log_success "VCF Credential Manager has been completely removed"
    echo "=========================================="
    echo ""
    log_info "The following items have been removed:"
    echo "  - Systemd service"
    echo "  - Installation directory ($INSTALL_DIR)"
    echo "  - Chroot directory ($CHROOT_DIR)"
    echo "  - Application user and group"
    echo "  - Firewall rules"
    echo ""
    log_warning "Note: System dependencies (Python, nginx, etc.) were NOT removed"
    echo ""
}

# Main uninstallation flow
main() {
    check_root
    confirm_uninstall
    stop_service
    remove_service_file
    unmount_chroot
    remove_directories
    remove_user
    remove_firewall_rules
    display_completion
}

# Run main function
main "$@"
