# Password History Tracking

## Overview

The VCF Credentials Manager now tracks password changes over time, allowing you to view the complete history of password changes for each credential.

## Features

### 1. Automatic Password Change Detection

When credentials are synced, the system automatically:
- Compares new passwords with existing ones
- Saves old passwords to history before updating
- Tracks when the change occurred
- Records the source of the change (SYNC, MANUAL, SYSTEM)

### 2. Password History Modal

Click on any credential's hostname to view its complete password history:
- Current password with show/hide toggle
- Table of all previous passwords
- Timestamp of each change
- Source of each change (SYNC, MANUAL, SYSTEM)
- Copy functionality for each password

### 3. Smart Credential Management

The system now:
- **Updates** existing credentials instead of deleting and recreating
- **Preserves** password history across syncs
- **Tracks** new credentials, updates, and removals
- **Maintains** data integrity with foreign key relationships

### 4. Export with Latest Passwords

All exports (CSV and Excel) automatically use the latest/current passwords:
- No need to worry about outdated passwords in exports
- History is preserved but exports show current state
- Export format unchanged - seamless upgrade

## Database Schema

### PasswordHistory Table

```sql
CREATE TABLE password_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    credential_id INTEGER NOT NULL,
    password VARCHAR(255) NOT NULL,
    changed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    changed_by VARCHAR(50) DEFAULT 'SYSTEM',
    FOREIGN KEY (credential_id) REFERENCES credentials (id)
)
```

**Fields:**
- `id` - Primary key
- `credential_id` - Foreign key to credentials table
- `password` - The previous password value
- `changed_at` - Timestamp when password was changed
- `changed_by` - Source of change: SYNC, MANUAL, or SYSTEM

**Indexes:**
- `idx_password_history_credential_id` - Fast lookup by credential
- `idx_password_history_changed_at` - Fast sorting by date

### Relationships

```
Credential (1) -----> (many) PasswordHistory
```

- One credential can have many history entries
- History entries are deleted when credential is deleted (CASCADE)
- History is ordered by `changed_at` DESC (newest first)

## Usage

### Viewing Password History

1. **Navigate to Environment:**
   - Go to Dashboard
   - Click "👁️ View" on any environment

2. **Open History Modal:**
   - Click the **"📜 History"** button in the Actions column for any credential

3. **View History:**
   - See current password at top
   - Scroll through previous passwords in table
   - Use 👁️ to show/hide passwords
   - Use 📋 to copy passwords

### Understanding Change Sources

**SYNC** - Password changed during automatic or manual sync
```
Changed by: SYNC
Meaning: Password was updated when fetching from VCF Installer or SDDC Manager
```

**MANUAL** - Password changed by user action
```
Changed by: MANUAL
Meaning: Password was manually updated through the UI (future feature)
```

**SYSTEM** - Password changed by system operation
```
Changed by: SYSTEM
Meaning: Password changed during initial setup or system maintenance
```

## Migration

### For Existing Installations

1. **Backup your database:**
   ```bash
   cp instance/vcf_credentials.db instance/vcf_credentials.db.backup
   ```

2. **Run migration script:**
   ```bash
   python add_password_history.py
   ```

   Output:
   ```
   ============================================================
   VCF Credentials Manager - Database Migration
   Adding password history tracking
   ============================================================
   
   📦 Creating backup: instance/vcf_credentials.db.backup_20231209_143022
   🔧 Creating 'password_history' table...
   ✅ Successfully created 'password_history' table
      Indexes created for optimal performance
   
   ✅ Migration completed successfully!
      Backup saved: instance/vcf_credentials.db.backup_20231209_143022
   ```

3. **Restart application:**
   ```bash
   python app.py
   ```

4. **Sync environments:**
   - Go to dashboard
   - Click "🔄 Sync Now" on each environment
   - Future password changes will be tracked

### For New Installations

No action needed - the database will be created with the correct schema including the password_history table.

## How It Works

### Password Change Detection

When syncing credentials:

```python
# 1. Get existing credentials
existing_creds = {(hostname, username): credential}

# 2. For each new credential
for new_cred in fetched_credentials:
    if exists in database:
        if password changed:
            # Save old password to history
            history = PasswordHistory(
                credential_id=existing.id,
                password=existing.password,  # old password
                changed_at=existing.last_updated,
                changed_by='SYNC'
            )
            # Update with new password
            existing.password = new_password
    else:
        # Create new credential
```

### History Retrieval

```python
# Get credential with history
credential = Credential.query.get(id)

# Access history (automatically ordered by date DESC)
for history in credential.password_history:
    print(f"{history.password} changed at {history.changed_at}")
```

## API Endpoints

### Get Credentials (Enhanced)

```
GET /api/environments/<env_id>/credentials
```

**Response:**
```json
[
  {
    "id": 1,
    "hostname": "esxi-01.example.com",
    "username": "root",
    "password": "CurrentPassword123!",
    "has_history": true,
    ...
  }
]
```

**New field:** `has_history` - Boolean indicating if credential has password history

### Get Password History

```
GET /api/credentials/<cred_id>/history
```

**Response:**
```json
{
  "credential": {
    "id": 1,
    "hostname": "esxi-01.example.com",
    "username": "root",
    "current_password": "CurrentPassword123!",
    "last_updated": "2023-12-09T14:30:22"
  },
  "history": [
    {
      "password": "OldPassword456!",
      "changed_at": "2023-12-08T10:15:30",
      "changed_by": "SYNC"
    },
    {
      "password": "EvenOlderPassword789!",
      "changed_at": "2023-12-07T09:20:15",
      "changed_by": "SYNC"
    }
  ]
}
```

## UI Changes

### Environment Page

**Before:**
```
Hostname                | Username | Password | ... | Actions
------------------------|----------|----------|-----|----------
esxi-01.example.com     | root     | ••••••   | ... | 👁️ 📋
```

**After:**
```
Hostname                | Username | Password | ... | Actions
------------------------|----------|----------|-----|-------------------
esxi-01.example.com     | root     | ••••••   | ... | 👁️ 📋 📜 History
```

- New "📜 History" button in Actions column
- Opens password history modal
- Shows current password + all previous passwords
- Clearly visible and accessible for each credential

### History Modal

```
┌─────────────────────────────────────────┐
│ Password History                    ✕   │
├─────────────────────────────────────────┤
│ Hostname: esxi-01.example.com           │
│ Username: root                           │
│ Current Password: ••••••  👁️            │
│ Last Updated: 2023-12-09 14:30:22       │
│                                          │
│ Previous Passwords                       │
│ ┌────────────────────────────────────┐  │
│ │ Password    │ Changed At │ By │ 👁️📋│  │
│ ├────────────────────────────────────┤  │
│ │ ••••••      │ 2023-12-08 │ SYNC│ 👁️📋│  │
│ │ ••••••      │ 2023-12-07 │ SYNC│ 👁️📋│  │
│ └────────────────────────────────────┘  │
├─────────────────────────────────────────┤
│                           [Close]        │
└─────────────────────────────────────────┘
```

## Benefits

### 1. Audit Trail
- Track when passwords changed
- Identify password rotation patterns
- Compliance and security auditing

### 2. Recovery
- Access previous passwords if needed
- Useful if a system wasn't updated yet
- Helps with troubleshooting access issues

### 3. Change Detection
- Easily see which passwords changed during sync
- Identify systems with frequent password changes
- Monitor password management practices

### 4. Historical Analysis
- Understand password change frequency
- Identify systems that need attention
- Track password management compliance

## Performance

### Optimizations

1. **Indexed Queries**
   - Fast lookup by credential_id
   - Fast sorting by changed_at
   - Efficient history retrieval

2. **Lazy Loading**
   - History loaded only when requested
   - Modal loads asynchronously
   - No impact on main credential list

3. **Smart Updates**
   - Only creates history when password actually changes
   - Avoids duplicate history entries
   - Minimal database overhead

### Storage Considerations

**Typical Storage:**
- Each history entry: ~300 bytes
- 100 credentials × 10 changes = 300 KB
- 1000 credentials × 10 changes = 3 MB

**Recommendation:**
- Monitor database size
- Consider archiving old history (>1 year)
- Implement retention policy if needed

## Security

### Password Storage

**Current Passwords:**
- Stored in `credentials` table
- Used for current access
- Updated during sync

**Historical Passwords:**
- Stored in `password_history` table
- Read-only after creation
- Preserved for audit trail

**Security Considerations:**
- All passwords stored in plaintext (required for export)
- Database file should be secured (chmod 600)
- Use HTTPS for web access
- Implement database encryption if needed

### Access Control

- Login required for all history access
- History tied to environment permissions
- No public access to password history API

## Troubleshooting

### History Not Showing

**Problem:** Clicked hostname but no history appears

**Solutions:**
1. Check browser console for errors
2. Verify credential has history: look for `has_history: true` in API response
3. Try syncing environment to create initial history
4. Check logs for API errors

### History Not Being Created

**Problem:** Passwords changing but no history saved

**Solutions:**
1. Verify migration ran successfully
2. Check database for `password_history` table
3. Review logs during sync for errors
4. Ensure passwords are actually changing (not just re-syncing same password)

### Modal Not Opening

**Problem:** Click on hostname but modal doesn't appear

**Solutions:**
1. Check browser console for JavaScript errors
2. Verify modal HTML is present in page
3. Clear browser cache and reload
4. Check for CSS conflicts

## Future Enhancements

### Planned Features

1. **Manual Password Updates**
   - Allow manual password changes through UI
   - Track as `changed_by: MANUAL`

2. **History Retention Policies**
   - Configurable retention period
   - Automatic archiving of old history
   - Export history before deletion

3. **Password Comparison**
   - Visual diff between password versions
   - Highlight what changed
   - Pattern analysis

4. **Notifications**
   - Alert on password changes
   - Email notifications
   - Webhook integration

5. **Advanced Search**
   - Search password history
   - Filter by date range
   - Filter by change source

## Summary

Password history tracking provides:

✅ **Complete audit trail** of password changes
✅ **Easy access** to previous passwords
✅ **Automatic tracking** during syncs
✅ **No impact** on existing functionality
✅ **Seamless integration** with current UI
✅ **Performance optimized** with indexes
✅ **Secure storage** with proper access control

The feature is production-ready and requires minimal maintenance! 🎉

