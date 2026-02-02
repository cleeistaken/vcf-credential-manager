#!/bin/bash
#
# Start VCF Credentials Manager with HTTPS and DEBUG MODE
# This script enables verbose logging for troubleshooting
#

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}VCF Credentials Manager - HTTPS Startup (DEBUG MODE)${NC}"
echo "=========================================="
echo -e "${YELLOW}⚠️  DEBUG MODE ENABLED - Verbose logging active${NC}"
echo ""

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}Warning: Virtual environment not activated${NC}"
    echo "Please activate your virtual environment first:"
    echo "  pipenv shell"
    echo "  or"
    echo "  source venv/bin/activate"
    exit 1
fi

# Create necessary directories
echo "Creating required directories..."
mkdir -p logs
mkdir -p ssl

# Check for SSL certificates
if [ ! -f "ssl/cert.pem" ] || [ ! -f "ssl/key.pem" ]; then
    echo -e "${YELLOW}SSL certificates not found. Generating self-signed certificates...${NC}"
    openssl req -x509 -newkey rsa:4096 -nodes \
        -keyout ssl/key.pem \
        -out ssl/cert.pem \
        -days 365 \
        -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
    echo -e "${GREEN}SSL certificates generated${NC}"
fi

# Check if database exists
if [ ! -f "vcf_credentials.db" ]; then
    echo -e "${YELLOW}Database not found. It will be created on first run.${NC}"
    echo "Default admin credentials will be:"
    echo "  Username: admin"
    echo "  Password: admin"
    echo -e "${RED}IMPORTANT: Change the default password after first login!${NC}"
fi

# Start Gunicorn with HTTPS and DEBUG MODE
echo ""
echo "Starting Gunicorn with HTTPS and DEBUG MODE..."
echo "Access the application at: https://localhost:5000"
echo "Press Ctrl+C to stop"
echo ""
echo -e "${YELLOW}Debug logs will be written to: logs/vcf_credentials.log${NC}"
echo ""

# Export DEBUG_MODE environment variable
export DEBUG_MODE=true

# Fix for macOS fork() issue with Objective-C frameworks
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES

exec gunicorn \
    --config gunicorn_config.py \
    --certfile ssl/cert.pem \
    --keyfile ssl/key.pem \
    app:app
