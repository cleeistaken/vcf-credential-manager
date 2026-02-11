# SSL Certificate Setup

## Understanding SSL in This Application

There are two separate SSL connections:

1. **Browser → Application** - Uses `ssl/cert.pem` and `ssl/key.pem`
2. **Application → VCF** - Controlled by "Verify SSL" checkbox in environment settings

## Self-Signed Certificates (Default)

The startup script generates self-signed certificates automatically. Browsers will show a warning - click "Advanced" → "Proceed" to continue.

### Regenerate Certificate

If you're accessing via IP or hostname (not localhost):

```bash
./tools/regenerate_ssl_cert.sh
pkill -f gunicorn
./start_https.sh
```

This creates a certificate with your server's hostname and IP as Subject Alternative Names.

## CA-Signed Certificates (Production)

### Option 1: Upload via Web UI

1. Log in as admin
2. Go to Settings > SSL Certificate Management
3. Upload certificate (`.crt` or `.pem`) and private key (`.key` or `.pem`)
4. Click "Upload Certificates"
5. Restart server

### Option 2: Manual Installation

```bash
# Copy files to ssl directory
cp your-cert.crt ssl/cert.pem
cp your-key.key ssl/key.pem

# Set permissions
chmod 644 ssl/cert.pem
chmod 600 ssl/key.pem

# Restart
pkill -f gunicorn
./start_https.sh
```

### Generate CSR for Your CA

```bash
openssl req -new -newkey rsa:4096 -nodes \
    -keyout ssl/key.pem \
    -out ssl/server.csr \
    -subj "/CN=your-server.example.com"
```

Submit the CSR to your CA and receive the signed certificate.

## Troubleshooting

### Browser Shows "Certificate Unknown"

1. Regenerate with proper hostname: `./tools/regenerate_ssl_cert.sh`
2. Restart server
3. Clear browser cache or use incognito mode
4. Accept the self-signed certificate warning

### Certificate Expired

```bash
./tools/regenerate_ssl_cert.sh
pkill -f gunicorn
./start_https.sh
```

### Verify Certificate Details

```bash
# View certificate
openssl x509 -in ssl/cert.pem -noout -text

# Check expiration
openssl x509 -in ssl/cert.pem -noout -dates

# Verify cert and key match
openssl x509 -noout -modulus -in ssl/cert.pem | openssl md5
openssl rsa -noout -modulus -in ssl/key.pem | openssl md5
# Hashes should match
```

## VCF Endpoint SSL

The "Verify SSL Certificate" checkbox in environment settings controls whether the application verifies VCF Installer/SDDC Manager certificates.

- **Disable** for self-signed VCF certificates (lab environments)
- **Enable** for production with valid CA certificates
