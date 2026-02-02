# Server Restart Feature

## Overview

Added a "Restart Server" button to the Settings page that allows administrators to gracefully restart the Gunicorn server and reload SSL certificates without needing SSH access or manual intervention.

## Feature Description

### Location

**Settings Page** → **SSL Certificate Management** → **Restart Server** section

### Purpose

- Restart Gunicorn server gracefully
- Reload SSL certificates after upload
- Apply configuration changes
- No SSH access required

### Access Control

- **Admin only** - Requires admin privileges
- Protected by `@admin_required` decorator
- Logged for security audit trail

## How It Works

### Graceful Restart Process

1. **User clicks "Restart Server" button**
2. **Confirmation prompt** appears with warnings
3. **Server sends SIGHUP signal** to Gunicorn master process
4. **Gunicorn performs graceful restart:**
   - Spawns new worker processes
   - Reloads SSL certificates
   - Completes in-flight requests
   - Terminates old workers
   - New workers start serving requests
5. **User is redirected** to login page after 5 seconds

### Technical Implementation

**Signal Used:** `SIGHUP` (Hang Up)
- Standard Unix signal for graceful reload
- Gunicorn interprets this as "reload configuration"
- Workers are restarted, SSL certs reloaded
- No downtime for active connections

**Process Discovery:**
```bash
pgrep -f 'gunicorn.*app:app'
```
- Finds all Gunicorn processes
- Sends SIGHUP to master process
- Master handles worker restart

## User Interface

### Restart Server Card

```
┌─────────────────────────────────────────────────┐
│ Restart Server                                  │
│                                                 │
│ Restart the Gunicorn server to apply new SSL   │
│ certificates or configuration changes.          │
│                                                 │
│ ⚠ Warning: Restarting the server will:         │
│   • Disconnect all active users                 │
│   • Reload SSL certificates                     │
│   • Apply any configuration changes             │
│   • Take approximately 5-10 seconds             │
│                                                 │
│ [🔄 Restart Server]                             │
└─────────────────────────────────────────────────┘
```

### Confirmation Dialog

```
Are you sure you want to restart the server?

All users will be disconnected and need to log in again.

This will take approximately 5-10 seconds.

[Cancel]  [OK]
```

### Status Messages

**During Restart:**
```
┌─────────────────────────────────────────────────┐
│ 🔄 Restarting server... Please wait...         │
└─────────────────────────────────────────────────┘
```

**Success:**
```
┌─────────────────────────────────────────────────┐
│ ✓ Server restart initiated.                     │
│   You will be redirected to the login page      │
│   in 5 seconds...                               │
└─────────────────────────────────────────────────┘
```

**Error:**
```
┌─────────────────────────────────────────────────┐
│ ✕ Failed to restart server: [error message]    │
└─────────────────────────────────────────────────┘
```

## Usage Scenarios

### Scenario 1: After Uploading SSL Certificates

**Steps:**
1. Upload new SSL certificate and key
2. System validates and saves certificates
3. Click "🔄 Restart Server" button
4. Confirm restart
5. Wait 5 seconds
6. Log in again
7. New certificates are now active

### Scenario 2: After Configuration Changes

**Steps:**
1. Make configuration changes (if any)
2. Click "🔄 Restart Server" button
3. Confirm restart
4. Server reloads with new configuration

### Scenario 3: Troubleshooting

**Steps:**
1. If server is behaving unexpectedly
2. Click "🔄 Restart Server" button
3. Fresh start may resolve issues

## Security Features

### Access Control

**Admin Only:**
- Only admin users can see the restart button
- API endpoint protected by `@admin_required`
- Non-admin users get 403 Forbidden

**Audit Logging:**
```
WARNING: Server restart initiated by user: admin
INFO: Sent SIGHUP to Gunicorn process 12345
```

### Confirmation Required

- Double confirmation prevents accidental restarts
- Clear warning about disconnecting users
- Estimated downtime displayed

### Graceful Restart

- No abrupt termination
- In-flight requests complete
- Minimal disruption
- SSL certificates reloaded properly

## API Endpoint

### POST /api/restart-server

**Authentication:** Required (admin only)

**Request:**
```http
POST /api/restart-server HTTP/1.1
Content-Type: application/json
```

**Success Response:**
```json
{
  "message": "Server restart initiated successfully",
  "note": "Please log in again after restart"
}
```

**Error Response (Not Gunicorn):**
```json
{
  "error": "Server restart is only available when running under Gunicorn",
  "note": "Please restart manually: ./start_https.sh"
}
```

**Error Response (Failed):**
```json
{
  "error": "Failed to restart server",
  "details": "Process not found"
}
```

## Technical Details

### Gunicorn Signal Handling

**SIGHUP Signal:**
- Graceful reload of configuration
- Reloads SSL certificates
- Spawns new workers
- Terminates old workers after completing requests

**Process:**
```
Master Process (PID 12345)
├── Worker 1 (PID 12346) ← Old worker
├── Worker 2 (PID 12347) ← Old worker
│
[SIGHUP received]
│
├── Worker 3 (PID 12350) ← New worker (spawned)
├── Worker 4 (PID 12351) ← New worker (spawned)
│
[Old workers complete requests and exit]
│
├── Worker 3 (PID 12350) ← Active
└── Worker 4 (PID 12351) ← Active
```

### SSL Certificate Reload

**How Gunicorn Reloads Certificates:**
1. SIGHUP signal received by master
2. Master reads `gunicorn_config.py`
3. Loads new `certfile` and `keyfile`
4. New workers start with new certificates
5. Old workers finish and exit
6. All new connections use new certificates

### Process Discovery

**Finding Gunicorn:**
```python
subprocess.run(['pgrep', '-f', 'gunicorn.*app:app'])
```

**Why this works:**
- `pgrep` finds processes by name pattern
- `-f` matches full command line
- `gunicorn.*app:app` matches our Gunicorn instance
- Returns PIDs of all matching processes

### Development vs Production

**Production (Gunicorn):**
- ✅ Restart button works
- ✅ Sends SIGHUP signal
- ✅ Graceful reload

**Development (Flask dev server):**
- ❌ Restart button shows error
- ❌ Cannot send SIGHUP
- ℹ️ Message: "Please restart manually"

## Limitations

### Only Works with Gunicorn

The restart feature only works when running under Gunicorn:
- ✅ Production deployment with `./start_https.sh`
- ✅ Manual Gunicorn start
- ❌ Flask development server (`flask run`)
- ❌ Direct Python execution (`python app.py`)

### Requires pgrep Command

The feature requires `pgrep` to be available:
- ✅ Linux (all distributions)
- ✅ macOS
- ❌ Windows (use WSL or manual restart)

### User Disconnection

All users are disconnected during restart:
- Sessions are invalidated
- Users must log in again
- Active operations may be interrupted

## Troubleshooting

### Restart Button Not Visible

**Problem:** Can't see the restart button

**Solution:**
- Verify you're logged in as admin
- Check Settings page → SSL Certificate Management section
- Scroll down to "Restart Server" card

### Restart Fails with Error

**Problem:** "Server restart is only available when running under Gunicorn"

**Solution:**
- You're running Flask dev server
- Restart manually: `./start_https.sh`
- Or use Gunicorn for production

### Server Doesn't Restart

**Problem:** Clicked restart but server still running old version

**Solution:**
1. Check logs: `tail -f logs/vcf_credentials.log`
2. Verify Gunicorn is running: `ps aux | grep gunicorn`
3. Manual restart: `pkill -f gunicorn && ./start_https.sh`

### Redirected But Can't Log In

**Problem:** Redirected to login but page won't load

**Solution:**
- Wait 10-15 seconds for server to fully restart
- Refresh the page
- Clear browser cache if needed

## Best Practices

### When to Use Restart

**Do restart after:**
- ✅ Uploading new SSL certificates
- ✅ Modifying `gunicorn_config.py`
- ✅ Changing environment variables
- ✅ Troubleshooting server issues

**Don't restart for:**
- ❌ Adding/editing environments (not needed)
- ❌ Adding users (not needed)
- ❌ Syncing credentials (not needed)
- ❌ Viewing credentials (not needed)

### Timing

**Best time to restart:**
- During maintenance windows
- Low-traffic periods
- After notifying users
- When no critical operations are running

**Avoid restarting:**
- During active credential syncs
- When users are actively working
- During peak usage hours

### Communication

**Before restarting:**
1. Notify users if possible
2. Check for active operations
3. Choose low-impact time
4. Have backup plan

## Files Modified

### templates/settings.html

**Added:**
- Restart Server card with warning
- Restart button (red, styled like delete)
- Status message area
- JavaScript `restartServer()` function
- Confirmation dialog
- Auto-redirect after success

### app.py

**Added:**
- `/api/restart-server` endpoint
- Admin-only access control
- Gunicorn process discovery
- SIGHUP signal sending
- Error handling
- Audit logging

## Testing

### Test Restart Functionality

1. **Start server with Gunicorn:**
   ```bash
   ./start_https.sh
   ```

2. **Log in as admin**

3. **Navigate to Settings → SSL Certificate Management**

4. **Scroll to "Restart Server" section**

5. **Click "🔄 Restart Server"**

6. **Confirm in dialog**

7. **Verify:**
   - Status shows "Restarting server..."
   - Success message appears
   - Redirected to login after 5 seconds
   - Can log in again
   - Server is responsive

### Test Access Control

1. **Create read-only user**

2. **Log in as read-only user**

3. **Try to access Settings**
   - Should be denied

4. **Try API directly:**
   ```bash
   curl -X POST https://localhost:5000/api/restart-server
   ```
   - Should return 403 Forbidden

### Test SSL Certificate Reload

1. **Upload new SSL certificate**

2. **Click "🔄 Restart Server"**

3. **After restart, check certificate:**
   ```bash
   openssl s_client -connect localhost:5000 -showcerts
   ```
   - Should show new certificate

## Summary

✅ **Restart button added** - Convenient server restart from UI
✅ **Graceful reload** - Uses SIGHUP for clean restart
✅ **SSL certificate reload** - New certs loaded automatically
✅ **Admin only** - Secure access control
✅ **User-friendly** - Clear warnings and status messages
✅ **Audit logging** - All restarts logged
✅ **Safe operation** - Confirmation required, graceful process

No more SSH access needed to restart the server after certificate updates! 🎉
