# User Management

## User Roles

| Role | Permissions |
|------|-------------|
| **Admin** | Full access - manage environments, users, SSL certificates |
| **Read-Only** | View credentials and export only |

## Managing Users

**Settings > User Management** (admin only)

### Add User

1. Enter username (unique)
2. Enter password (min 8 characters)
3. Select role (Admin or Read-Only)
4. Click "Add User"

### Delete User

1. Find user in the list
2. Click "Delete"
3. Confirm deletion

**Note**: Cannot delete yourself or the last admin user.

## SSL Certificate Management

**Settings > SSL Certificate Management** (admin only)

### Upload Certificates

1. Upload certificate file (`.crt` or `.pem`)
2. Upload private key file (`.key` or `.pem`)
3. Click "Upload Certificates"
4. Restart server for changes to take effect

The system validates that the certificate and key match before saving.

### Current Certificate Info

View certificate details including:
- Subject and issuer
- Valid from/until dates
- Days remaining until expiration

## Server Restart

**Settings > Restart Server** (admin only)

Click "Restart Server" to:
- Reload SSL certificates after upload
- Apply configuration changes

All users will be disconnected and need to log in again.
