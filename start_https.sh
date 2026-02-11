#!/bin/bash
#
# Start VCF Credentials Manager with HTTPS
# This script ensures proper initialization for first-time startup
#

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}VCF Credentials Manager - HTTPS Startup${NC}"
echo "=========================================="

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
    
    # Get the server's hostname and IP addresses
    HOSTNAME=$(hostname)
    IP_ADDR=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "127.0.0.1")
    
    # Create OpenSSL config for SAN (Subject Alternative Names)
    cat > ssl/openssl.cnf <<EOF
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
O=Organization
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
        -keyout ssl/key.pem \
        -out ssl/cert.pem \
        -days 365 \
        -config ssl/openssl.cnf \
        -extensions v3_req
    
    rm -f ssl/openssl.cnf
    echo -e "${GREEN}SSL certificates generated for ${HOSTNAME} (${IP_ADDR})${NC}"
    echo -e "${YELLOW}Note: You may still need to accept the self-signed certificate in your browser${NC}"
fi

# Check if database exists
if [ ! -f "vcf_credentials.db" ]; then
    echo -e "${YELLOW}Database not found. It will be created on first run.${NC}"
    echo "Default admin credentials will be:"
    echo "  Username: admin"
    echo "  Password: admin"
    echo -e "${RED}IMPORTANT: Change the default password after first login!${NC}"
fi

# Start Gunicorn with HTTPS
echo ""
echo "Starting Gunicorn with HTTPS..."
echo "Access the application at: https://localhost:5000"
echo "Press Ctrl+C to stop"
echo ""

# Fix for macOS fork() issue with Objective-C frameworks
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES

exec gunicorn \
    --config gunicorn_config.py \
    --certfile ssl/cert.pem \
    --keyfile ssl/key.pem \
    app:app

