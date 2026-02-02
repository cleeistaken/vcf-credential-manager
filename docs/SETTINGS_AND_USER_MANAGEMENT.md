# Settings and User Management

## Overview

The VCF Credentials Manager now includes a comprehensive Settings page with user management and SSL certificate management capabilities. This allows administrators to control access, manage users with different permission levels, and update SSL certificates.

## Features

### 1. User Management

#### User Roles

The system supports two types of users:

| Role | Permissions | Description |
|------|-------------|-------------|
| **Admin** | Full Access | Can manage environments, sync credentials, add/delete users, upload SSL certificates, and modify all settings |
| **Read-Only** | View Only | Can only view credentials and environment information. Cannot modify, sync, or delete anything |

#### Adding Users

**Admin users can add new users:**

1. Navigate to **Settings** → **User Management**
2. Fill in the user form:
   - **Username**: Unique username (required)
   - **Password**: Minimum 8 characters (required)
   - **Role**: Select Admin or Read-Only
3. Click **➕ Add User**

**Validation:**
- Username must be unique
- Password must be at least 8 characters
- Role must be selected

#### Deleting Users

**Admin users can delete other users:**

1. Navigate to **Settings** → **User Management**
2. Find the user in the "Existing Users" table
3. Click **🗑️ Delete** button
4. Confirm deletion

**Restrictions:**
- Cannot delete your own account
- Cannot delete the last admin user (system must have at least one admin)

#### Viewing Users

The "Existing Users" table shows:
- **Username**: User's login name
- **Role**: Admin or Read-Only badge
- **Created**: Date the user was created
- **Actions**: Delete button (if allowed)

Your own account is marked with a **"You"** badge.

### 2. SSL Certificate Management

#### Uploading SSL Certificates

**Admin users can upload custom SSL certificates:**

1. Navigate to **Settings** → **SSL Certificate Management**
2. Upload both files:
   - **Certificate File**: `.crt` or `.pem` file
   - **Private Key File**: `.key` or `.pem` file
3. Click **📤 Upload Certificates**

**Validation Process:**

The system automatically validates:
1. ✅ Certificate is valid and properly formatted
2. ✅ Private key is valid and properly formatted
3. ✅ Certificate and private key match (same modulus)

If validation fails, an error message is displayed and no changes are made.

**After Upload:**

- Certificates are saved to `ssl/server.crt` and `ssl/server.key`
- Old certificates are backed up to `.backup` files
- Proper file permissions are set (644 for cert, 600 for key)
- **Server must be restarted** for changes to take effect

#### Viewing Current Certificate

The "Current Certificate Information" section displays:
- **Subject**: Certificate subject (CN, O, etc.)
- **Issuer**: Certificate issuer
- **Valid From**: Start date
- **Valid Until**: Expiration date
- **Days Remaining**: Days until expiration

### 3. Read-Only User Experience

#### What Read-Only Users Can Do

✅ **View:**
- Dashboard with all environments
- Environment credentials
- Password history
- Export credentials to CSV/Excel

#### What Read-Only Users Cannot Do

❌ **Modify:**
- Add/edit/delete environments
- Sync credentials
- Add/delete users
- Upload SSL certificates
- Change system settings

**UI Indicators:**
- "Read-Only" badge in header
- Action buttons are hidden
- Informational message on dashboard
- 403 error if attempting API modifications

## Access Control

### Admin-Only Pages

The following pages require admin privileges:
- `/settings` - Settings page
- `/settings/users` - Add user endpoint
- `/settings/users/<id>` - Delete user endpoint
- `/settings/ssl` - Upload SSL certificates endpoint
- `/api/ssl-info` - SSL certificate information endpoint

**Access Denied Behavior:**
- Redirect to dashboard
- Flash message: "Access denied. Admin privileges required."

### Read-Only Restrictions

Read-only users receive a **403 Forbidden** response when attempting:
- `POST /api/environments` - Create environment
- `PUT /api/environments/<id>` - Update environment
- `DELETE /api/environments/<id>` - Delete environment
- `POST /api/environments/<id>/sync` - Sync credentials

**Error Response:**
```json
{
  "error": "Read-only users cannot modify data"
}
```

## Usage Examples

### Example 1: Add Read-Only User for Auditing

**Scenario:** You want to give your security team view-only access to credentials.

**Steps:**
1. Admin logs in
2. Navigate to **Settings**
3. Add new user:
   - Username: `security_audit`
   - Password: `SecurePass123!`
   - Role: **Read-Only**
4. Click **Add User**
5. Share credentials with security team

**Result:** Security team can view all credentials but cannot modify anything.

### Example 2: Replace Expiring SSL Certificate

**Scenario:** Your SSL certificate is expiring in 30 days.

**Steps:**
1. Obtain new certificate and private key from CA
2. Admin logs in
3. Navigate to **Settings** → **SSL Certificate Management**
4. Upload new certificate file
5. Upload new private key file
6. Click **Upload Certificates**
7. System validates and saves certificates
8. Restart server:
   ```bash
   pkill -f gunicorn
   ./start_https.sh
   ```

**Result:** Server now uses new SSL certificate.

### Example 3: Remove User Who Left Company

**Scenario:** An employee with admin access has left the company.

**Steps:**
1. Admin logs in
2. Navigate to **Settings** → **User Management**
3. Find the user in "Existing Users" table
4. Click **🗑️ Delete**
5. Confirm deletion

**Result:** User account is removed and can no longer access the system.

## Security Considerations

### Password Requirements

- **Minimum length**: 8 characters
- **Recommendation**: Use strong passwords with mixed case, numbers, and symbols
- **Storage**: Passwords are hashed using Werkzeug's `generate_password_hash`

### SSL Certificate Security

- **Private key permissions**: Automatically set to 600 (owner read/write only)
- **Certificate permissions**: Automatically set to 644 (owner read/write, others read)
- **Backup**: Old certificates are backed up before replacement
- **Validation**: Certificates are validated before being saved

### User Access Control

- **Role-based**: Admin vs Read-Only
- **Decorator-based**: `@admin_required` decorator for sensitive endpoints
- **API-level**: Checks in API endpoints for modification attempts
- **UI-level**: Buttons hidden for read-only users

### Session Management

- **Flask-Login**: Secure session management
- **Login required**: All pages require authentication
- **Logout**: Properly clears session

## API Endpoints

### User Management

**Add User**
```http
POST /settings/users
Content-Type: application/x-www-form-urlencoded

username=newuser&password=password123&role=readonly
```

**Delete User**
```http
DELETE /settings/users/<user_id>
```

Response:
```json
{
  "message": "User username deleted successfully"
}
```

### SSL Management

**Upload Certificates**
```http
POST /settings/ssl
Content-Type: multipart/form-data

cert_file=<certificate file>
key_file=<private key file>
```

**Get SSL Info**
```http
GET /api/ssl-info
```

Response:
```json
{
  "exists": true,
  "subject": "CN=example.com, O=Example Inc",
  "issuer": "CN=Example CA",
  "valid_from": "Jan 1 00:00:00 2024 GMT",
  "valid_until": "Jan 1 00:00:00 2025 GMT",
  "days_remaining": 180
}
```

## Database Schema Changes

### User Model Updates

Added new field:
```python
role = db.Column(db.String(20), default='admin')  # 'admin' or 'readonly'
```

**Migration:**

For existing installations, the `role` field defaults to `'admin'` for backward compatibility. All existing users are treated as admins.

**Updating existing users:**
```python
# In Python shell or migration script
from app import app, db, User

with app.app_context():
    # Update specific user to readonly
    user = User.query.filter_by(username='viewer').first()
    if user:
        user.role = 'readonly'
        db.session.commit()
```

## Troubleshooting

### Cannot Access Settings Page

**Problem:** Settings link not visible or access denied

**Solution:**
- Check if you're logged in as admin
- Verify `current_user.role == 'admin'` or `current_user.is_admin == True`
- Default admin user (username: `admin`) has admin access

### SSL Certificate Upload Fails

**Problem:** "Invalid certificate file" or "Certificate and private key do not match"

**Solutions:**

1. **Check certificate format:**
   ```bash
   openssl x509 -in certificate.crt -noout -text
   ```

2. **Check private key format:**
   ```bash
   openssl rsa -in private.key -check -noout
   ```

3. **Verify they match:**
   ```bash
   # Get certificate modulus
   openssl x509 -noout -modulus -in certificate.crt | openssl md5
   
   # Get key modulus
   openssl rsa -noout -modulus -in private.key | openssl md5
   
   # They should match!
   ```

4. **Check file permissions:**
   - Ensure files are readable by the application user

### Read-Only User Can't View Credentials

**Problem:** Read-only user gets access denied

**Solution:**
- Read-only users CAN view credentials
- Check if the issue is with a modification attempt (sync, edit, delete)
- Verify user role: `user.role == 'readonly'`

### Cannot Delete User

**Problem:** Delete button doesn't work or shows error

**Possible reasons:**

1. **Trying to delete yourself:**
   - Cannot delete your own account
   - Log in as different admin

2. **Last admin user:**
   - System must have at least one admin
   - Create another admin first, then delete

3. **Not logged in as admin:**
   - Only admins can delete users
   - Log in with admin account

## Best Practices

### User Management

1. **Principle of Least Privilege**
   - Give users the minimum access they need
   - Use read-only for viewing-only scenarios
   - Reserve admin for trusted personnel

2. **Regular Audits**
   - Review user list periodically
   - Remove users who no longer need access
   - Check for inactive accounts

3. **Strong Passwords**
   - Enforce minimum 8 characters (system requirement)
   - Recommend 12+ characters with complexity
   - Consider password manager

4. **Multiple Admins**
   - Have at least 2 admin accounts
   - Prevents lockout if one admin leaves
   - Allows admin management

### SSL Certificate Management

1. **Certificate Expiration**
   - Monitor "Days Remaining" in Settings
   - Renew certificates before expiration
   - Set calendar reminders

2. **Certificate Backup**
   - System automatically backs up old certificates
   - Keep manual backups of certificates
   - Store private keys securely

3. **Testing**
   - Test new certificates in non-production first
   - Verify certificate chain is complete
   - Check browser warnings after upload

4. **Restart Planning**
   - Plan certificate updates during maintenance windows
   - Server restart required after upload
   - Notify users of downtime

## Future Enhancements

Potential improvements:

- 🔮 **Password expiration** - Force password changes after X days
- 🔮 **Two-factor authentication** - Add 2FA support
- 🔮 **Audit logging** - Track user actions
- 🔮 **LDAP/AD integration** - Enterprise authentication
- 🔮 **API tokens** - Token-based API access
- 🔮 **Certificate auto-renewal** - Let's Encrypt integration
- 🔮 **Role customization** - Custom roles with granular permissions
- 🔮 **User groups** - Organize users into groups

## Summary

The Settings page provides comprehensive system administration:

✅ **User Management** - Add admin and read-only users
✅ **SSL Certificates** - Upload and validate custom certificates
✅ **Access Control** - Role-based permissions
✅ **Security** - Password hashing, file permissions, validation
✅ **Audit Trail** - User creation/deletion logging

Perfect for multi-user environments with security requirements! 🎉
