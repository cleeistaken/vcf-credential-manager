# Features

## Password History

Track password changes over time for audit and recovery purposes.

### View History

1. Go to environment credentials view
2. Click "History" button on any credential
3. See current password and all previous passwords with timestamps

### How It Works

- Passwords are automatically saved to history when they change during sync
- History shows when each change occurred and the source (SYNC, MANUAL, SYSTEM)
- Exports always use the current password

## Column Filters

Filter credentials by multiple criteria simultaneously.

### Available Filters

| Column | Filter Type |
|--------|-------------|
| Hostname | Text (partial match) |
| Username | Text (partial match) |
| Credential Type | Dropdown (SSH, API, SSO, etc.) |
| Account Type | Dropdown (USER, SERVICE, etc.) |
| Resource Type | Dropdown (ESXI, VCENTER, NSX_MANAGER, etc.) |
| Domain | Text (partial match) |
| Source | Dropdown (Installer, Manager) |

### Usage

- Filters appear in the row below column headers
- Text filters match any part of the value (case-insensitive)
- Dropdown options are populated from your actual credentials
- Click "Clear" to reset all filters
- Combine with the search bar for more precise filtering

### Examples

| Goal | Filters |
|------|---------|
| Find all ESXi hosts | Resource Type: ESXI |
| Find vCenter root accounts | Resource Type: VCENTER, Username: "root" |
| Find SSH credentials from Installer | Credential Type: SSH, Source: Installer |

## Server Restart

Restart the server from the web UI without SSH access.

### When to Use

- After uploading new SSL certificates
- After configuration changes
- To apply updates

### How to Restart

1. Go to Settings > SSL Certificate Management
2. Scroll to "Restart Server" section
3. Click "Restart Server"
4. Confirm the action
5. Wait ~5-10 seconds
6. Log in again

**Note**: Only works when running under Gunicorn. All users will be disconnected.
