#!/bin/bash
#
# Regenerate SSL certificates with proper Subject Alternative Names (SANs)
# This ensures the certificate works with hostname, IP addresses, and localhost
#

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}VCF Credentials Manager - SSL Certificate Regeneration${NC}"
echo "========================================================"
echo ""

# Create ssl directory if it doesn't exist
mkdir -p ssl

# Get the server's hostname and IP addresses
HOSTNAME=$(hostname)
IP_ADDR=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "127.0.0.1")

echo -e "${YELLOW}Generating certificate for:${NC}"
echo "  Hostname: ${HOSTNAME}"
echo "  IP Address: ${IP_ADDR}"
echo "  Also includes: localhost, 127.0.0.1"
echo ""

# Backup existing certificates
if [ -f "ssl/cert.pem" ]; then
    echo "Backing up existing certificates..."
    mv ssl/cert.pem ssl/cert.pem.backup.$(date +%Y%m%d_%H%M%S)
    mv ssl/key.pem ssl/key.pem.backup.$(date +%Y%m%d_%H%M%S)
fi

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

# Generate new certificate
openssl req -x509 -newkey rsa:4096 -nodes \
    -keyout ssl/key.pem \
    -out ssl/cert.pem \
    -days 365 \
    -config ssl/openssl.cnf \
    -extensions v3_req

# Clean up config file
rm -f ssl/openssl.cnf

# Set proper permissions
chmod 644 ssl/cert.pem
chmod 600 ssl/key.pem

echo ""
echo -e "${GREEN}✓ SSL certificates generated successfully!${NC}"
echo ""
echo "Certificate details:"
openssl x509 -in ssl/cert.pem -noout -subject -issuer -dates -ext subjectAltName
echo ""
echo -e "${YELLOW}Important Notes:${NC}"
echo "1. This is a self-signed certificate - browsers will show a warning"
echo "2. Click 'Advanced' and 'Proceed' (or similar) in your browser"
echo "3. For production, use a certificate from your organization's CA"
echo "4. Restart the server for changes to take effect:"
echo "   pkill -f gunicorn && ./start_https.sh"
echo ""
