# Debug Mode and Troubleshooting SSL Issues

## Debug Mode

### Enabling Debug Mode

Debug mode provides verbose logging to help troubleshoot issues.

#### Method 1: Use Debug Startup Script

```bash
./start_https_debug.sh
```

This automatically enables debug mode and starts the server.

#### Method 2: Set Environment Variable

```bash
# Set DEBUG_MODE environment variable
export DEBUG_MODE=true

# Start server normally
./start_https.sh
```

#### Method 3: Temporary Debug Mode

```bash
# One-time debug mode
DEBUG_MODE=true ./start_https.sh
```

### What Debug Mode Does

When debug mode is enabled:
- ✅ **Verbose logging** - DEBUG level messages in logs
- ✅ **Detailed errors** - Full stack traces
- ✅ **Request details** - SSL verification status, timeouts, etc.
- ✅ **Connection info** - Detailed connection attempts

### Viewing Debug Logs

```bash
# Watch logs in real-time
tail -f logs/vcf_credentials.log

# View recent logs
tail -100 logs/vcf_credentials.log

# Search for errors
grep -i error logs/vcf_credentials.log

# Search for SSL issues
grep -i ssl logs/vcf_credentials.log
```

## CA Certificate for Internal CAs

### Using Internal CA Certificates

If your VCF endpoints use certificates signed by an internal CA, you can upload the CA certificate to enable SSL verification.

#### Upload CA Certificate

1. Go to **Settings** → **SSL Certificate Management**
2. Upload your server certificate and key (required)
3. Upload your **CA Certificate** (optional)
4. Click "Upload Certificates"
5. Restart the server

The application will automatically use the CA certificate to verify VCF endpoint certificates.

#### CA Certificate File Location

```
ssl/ca-bundle.crt
```

This file is used when:
- SSL verification is enabled for an environment
- The CA bundle file exists
- Connecting to VCF Installer or SDDC Manager

### Benefits of Using CA Certificate

**With CA Certificate:**
- ✅ SSL verification enabled
- ✅ Secure connections
- ✅ No certificate warnings
- ✅ Production-ready

**Without CA Certificate (SSL verification disabled):**
- ⚠️ SSL verification disabled
- ⚠️ Less secure
- ⚠️ Only for testing/lab environments

## SSL Certificate Issues

### Common SSL Errors

#### Error: "sslv3 alert bad certificate"

```
[WARNING] Invalid request from ip=127.0.0.1: [SSL: SSLV3_ALERT_BAD_CERTIFICATE] 
sslv3 alert bad certificate (_ssl.c:2580)
```

**Cause:** Your browser doesn't trust the server's SSL certificate (self-signed or internal CA).

**Solutions:**

1. **Accept the Certificate in Browser**:
   - Click "Advanced" or "Details"
   - Click "Proceed" or "Accept Risk"
   - This is safe for internal/lab environments

2. **Upload CA-Signed Certificate**:
   - Get a certificate from your internal CA
   - Upload via Settings → SSL Certificate Management
   - Restart server

3. **Use Reverse Proxy**:
   - Put Nginx/Apache in front with valid certificates
   - More suitable for production

#### Error: "sslv3 alert certificate unknown"

```
[WARNING] Invalid request from ip=127.0.0.1: [SSL: SSLV3_ALERT_CERTIFICATE_UNKNOWN] 
sslv3 alert certificate unknown (_ssl.c:2580)
```

**Cause:** The VCF endpoint doesn't trust your client certificate, or there's an SSL handshake issue.

**Solutions:**

1. **Disable SSL Verification** (for testing/self-signed certs):
   - When adding/editing environment
   - Uncheck "Verify SSL Certificate" for Installer and/or Manager
   - This bypasses certificate validation

2. **Use Proper SSL Certificates**:
   - Upload valid SSL certificates in Settings
   - Ensure certificates are not expired
   - Verify certificate chain is complete

3. **Check VCF Endpoint**:
   - Verify VCF Installer/Manager is accessible
   - Test with curl:
     ```bash
     curl -k https://vcf-installer.example.com/v1/tokens
     ```

#### Error: "Worker was sent SIGKILL! Perhaps out of memory?"

```
[ERROR] Worker (pid:27261) was sent SIGKILL! Perhaps out of memory?
```

**Cause:** Worker process crashed, often due to:
- SSL handshake failure causing worker to hang
- Timeout issues
- Memory issues (less common)

**Solutions:**

1. **Disable SSL Verification**:
   - Uncheck SSL verification boxes when testing connections
   - This prevents SSL handshake issues

2. **Increase Timeout**:
   - Default timeout is 30 seconds
   - VCF endpoints may be slow to respond

3. **Check VCF Endpoint Availability**:
   ```bash
   # Test connectivity
   ping vcf-installer.example.com
   
   # Test HTTPS port
   nc -zv vcf-installer.example.com 443
   ```

### SSL Verification Settings

#### When to Disable SSL Verification

**Disable SSL verification when:**
- ✅ Using self-signed certificates
- ✅ Testing in lab environment
- ✅ Certificate validation issues
- ✅ Internal/private CA certificates

**Enable SSL verification when:**
- ✅ Production environment
- ✅ Valid CA-signed certificates
- ✅ Security requirements mandate it

#### How to Disable SSL Verification

**When Adding Environment:**
1. Go to Dashboard
2. Click "Add Environment"
3. Uncheck "Verify SSL Certificate (Installer)"
4. Uncheck "Verify SSL Certificate (Manager)"
5. Save

**When Testing Connection:**
- SSL verification uses the checkbox settings
- Test will show if SSL is causing issues

### Debug Logging for SSL Issues

With debug mode enabled, you'll see:

```
DEBUG: Requesting token from https://vcf-installer.example.com/v1/tokens (SSL verify: False)
DEBUG: Successfully obtained token from vcf-installer.example.com
```

Or if there's an error:

```
ERROR: SSL Error connecting to vcf-installer.example.com: [SSL: CERTIFICATE_VERIFY_FAILED]
DEBUG: SSL verify was set to: True
```

## Troubleshooting Steps

### Step 1: Enable Debug Mode

```bash
./start_https_debug.sh
```

### Step 2: Test Connection

1. Log in to application
2. Add or edit environment
3. **Uncheck both SSL verification boxes**
4. Click "Test Connection"
5. Watch logs:
   ```bash
   tail -f logs/vcf_credentials.log
   ```

### Step 3: Check Logs for Errors

Look for:
- `SSL Error` - Certificate issues
- `Timeout` - Slow/unreachable endpoint
- `Connection error` - Network issues
- `401` - Invalid credentials
- `404` - Wrong endpoint URL

### Step 4: Verify VCF Endpoint

```bash
# Test with curl (disable SSL verification)
curl -k -X POST https://vcf-installer.example.com/v1/tokens \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}'

# Should return a token if credentials are correct
```

### Step 5: Check Gunicorn Logs

```bash
# Check Gunicorn error log
tail -f logs/gunicorn_error.log

# Check Gunicorn access log
tail -f logs/gunicorn_access.log
```

## Common Issues and Solutions

### Issue 1: SSL Certificate Verification Fails

**Symptoms:**
- Test connection fails
- SSL errors in logs
- Worker crashes

**Solution:**
```bash
# Disable SSL verification in environment settings
# Uncheck "Verify SSL Certificate" boxes
```

### Issue 2: Connection Timeout

**Symptoms:**
- Test hangs for 30 seconds
- Timeout error in logs

**Solution:**
```bash
# Check VCF endpoint is reachable
ping vcf-installer.example.com

# Check firewall rules
# Ensure port 443 is accessible
```

### Issue 3: Invalid Credentials

**Symptoms:**
- 401 Unauthorized error
- "Invalid credentials" message

**Solution:**
```bash
# Verify credentials with curl
curl -k -X POST https://vcf-installer.example.com/v1/tokens \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}'
```

### Issue 4: Worker Keeps Crashing

**Symptoms:**
- Worker SIGKILL messages
- Server restarts frequently

**Solution:**
```bash
# 1. Enable debug mode
./start_https_debug.sh

# 2. Disable SSL verification
# 3. Check logs for specific error
tail -f logs/vcf_credentials.log

# 4. Increase worker timeout in gunicorn_config.py
# timeout = 60  # Increase from 30 to 60 seconds
```

## Debug Mode vs Normal Mode

### Normal Mode (Production)

```bash
./start_https.sh
```

- INFO level logging
- Less verbose
- Better performance
- Recommended for production

### Debug Mode (Troubleshooting)

```bash
./start_https_debug.sh
```

- DEBUG level logging
- Very verbose
- Detailed error messages
- Recommended for troubleshooting

## Log File Locations

```
logs/
├── vcf_credentials.log       # Application logs (main)
├── vcf_credentials_error.log # Error logs only
├── gunicorn_access.log       # HTTP access logs
└── gunicorn_error.log        # Gunicorn errors
```

## Getting Help

When reporting issues, include:

1. **Debug logs:**
   ```bash
   tail -100 logs/vcf_credentials.log
   ```

2. **Error message:**
   - Copy the exact error from logs

3. **Environment details:**
   - VCF version
   - SSL verification enabled/disabled
   - Self-signed or CA-signed certificates

4. **Steps to reproduce:**
   - What you were doing when error occurred

## Summary

✅ **Enable debug mode** - Use `./start_https_debug.sh`
✅ **Disable SSL verification** - For self-signed certificates
✅ **Check logs** - `tail -f logs/vcf_credentials.log`
✅ **Test with curl** - Verify VCF endpoint directly
✅ **Increase timeout** - If connections are slow

Most SSL issues can be resolved by disabling SSL verification for self-signed certificates! 🎉
