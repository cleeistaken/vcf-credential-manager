# VCF Installer Credential Parsing Update

## Overview

The VCF Installer credential parsing has been completely rewritten based on the actual API response structure from VCF 9.0.0.0.

## Changes Made

### 1. Fixed Credential Structure Parsing

**Problem:** The original parser expected credentials in various formats, but the actual VCF Installer API returns credentials as a single dictionary object.

**Solution:** Updated parser to correctly handle the actual data structure:

```python
# Actual structure from VCF Installer:
{
  "hostSpecs": [{
    "credentials": {
      "username": "root",
      "password": "P@ssword123!"
    },
    "hostname": "esxi-01.example.com"
  }]
}
```

### 2. Added All Credential Types

The parser now extracts credentials from all VCF components:

#### ESXi Hosts
- **Source:** `hostSpecs[].credentials`
- **Accounts:** root (SSH)
- **Resource Type:** ESXI

#### vCenter Server
- **Source:** `vcenterSpec`
- **Accounts:**
  - root (SSH) - `rootVcenterPassword`
  - administrator@{ssoDomain} (SSO) - `adminUserSsoPassword`
- **Resource Type:** VCENTER

#### NSX Managers
- **Source:** `nsxtSpec`
- **Accounts:**
  - root (SSH) - `rootNsxtManagerPassword` (shared)
  - admin (API) - `nsxtAdminPassword` (shared)
  - audit (API) - `nsxtAuditPassword` (shared)
- **Resource Types:** NSX_MANAGER, NSX_VIP
- **Note:** Passwords are shared across all NSX manager nodes

#### SDDC Manager
- **Source:** `sddcManagerSpec`
- **Accounts:**
  - root (SSH) - `rootPassword`
  - admin@local (API) - `localUserPassword`
  - vcf (SSH) - `localUserPassword`
- **Resource Type:** SDDC_MANAGER
- **Note:** Both admin@local and vcf use the same password (localUserPassword)

#### Aria Operations (VCF Operations)
- **Source:** `vcfOperationsSpec`
- **Accounts:**
  - admin (API) - `adminUserPassword` (load balancer)
  - root (SSH) - `rootUserPassword` (per node)
- **Resource Types:** ARIA_OPERATIONS, ARIA_OPERATIONS_MASTER, ARIA_OPERATIONS_REPLICA, ARIA_OPERATIONS_DATA

#### Aria Operations for Networks (Fleet Management)
- **Source:** `vcfOperationsFleetManagementSpec`
- **Accounts:**
  - root (SSH) - `rootUserPassword`
  - admin (API) - `adminUserPassword`
- **Resource Type:** ARIA_OPERATIONS_NETWORKS

#### Aria Operations for Logs (Operations Collector)
- **Source:** `vcfOperationsCollectorSpec`
- **Accounts:**
  - root (SSH) - `rootUserPassword`
- **Resource Type:** ARIA_OPERATIONS_LOGS

### 3. Added Source Tracking

**New Feature:** Every credential now includes a `source` field to indicate where it came from.

**Values:**
- `VCF_INSTALLER` - Credentials from VCF Installer spec
- `SDDC_MANAGER` - Credentials from SDDC Manager API

**Benefits:**
- Easy to identify credential origin
- Helps troubleshoot sync issues
- Useful for auditing

### 4. Updated Database Schema

**New Column:** `credentials.source`
- Type: VARCHAR(50)
- Default: 'SDDC_MANAGER'
- Nullable: Yes

**Migration:** Run `python add_source_column.py` to update existing databases.

### 5. Updated UI

**Environment View:**
- Added "Source" column to credentials table
- Shows icon and label:
  - 🔧 Installer - From VCF Installer
  - 🖥️ Manager - From SDDC Manager

**Export:**
- CSV and Excel exports now include Source column
- Easy to filter/sort by source in spreadsheets

## Credential Type Mapping

### Credential Types
- **SSH** - SSH/Console access
- **API** - REST API access
- **SSO** - Single Sign-On authentication

### Account Types
- **USER** - System/root user accounts
- **SERVICE** - Service accounts (admin, vcf, etc.)

### Resource Types
- **ESXI** - ESXi hosts
- **VCENTER** - vCenter Server
- **NSX_MANAGER** - NSX Manager nodes
- **NSX_VIP** - NSX Manager VIP/Load Balancer
- **SDDC_MANAGER** - SDDC Manager
- **ARIA_OPERATIONS** - Aria Operations (load balancer)
- **ARIA_OPERATIONS_MASTER** - Aria Operations master node
- **ARIA_OPERATIONS_REPLICA** - Aria Operations replica node
- **ARIA_OPERATIONS_DATA** - Aria Operations data node
- **ARIA_OPERATIONS_NETWORKS** - Aria Operations for Networks
- **ARIA_OPERATIONS_LOGS** - Aria Operations for Logs

## Example Credentials Extracted

From a typical VCF 9.0 deployment, the parser now extracts:

### ESXi Hosts (4 hosts)
```
lvnvcfvps21.example.com | root | ******** | SSH | USER | ESXI | VCF_INSTALLER
lvnvcfvps22.example.com | root | ******** | SSH | USER | ESXI | VCF_INSTALLER
lvnvcfvps23.example.com | root | ******** | SSH | USER | ESXI | VCF_INSTALLER
lvnvcfvps24.example.com | root | ******** | SSH | USER | ESXI | VCF_INSTALLER
```

### vCenter Server (2 accounts)
```
vc-mgmt.example.com | root                          | ******** | SSH | USER    | VCENTER | VCF_INSTALLER
vc-mgmt.example.com | administrator@vsphere.local   | ******** | SSO | SERVICE | VCENTER | VCF_INSTALLER
```

### NSX Managers (9 credentials: 3 nodes × 3 accounts)
```
nsx-mgmt-a.example.com | root  | ******** | SSH | USER    | NSX_MANAGER | VCF_INSTALLER
nsx-mgmt-a.example.com | admin | ******** | API | SERVICE | NSX_MANAGER | VCF_INSTALLER
nsx-mgmt-a.example.com | audit | ******** | API | SERVICE | NSX_MANAGER | VCF_INSTALLER
... (same for nsx-mgmt-b and nsx-mgmt-c)
```

### NSX VIP (3 accounts)
```
nsx-mgmt.example.com | root  | ******** | SSH | USER    | NSX_VIP | VCF_INSTALLER
nsx-mgmt.example.com | admin | ******** | API | SERVICE | NSX_VIP | VCF_INSTALLER
nsx-mgmt.example.com | audit | ******** | API | SERVICE | NSX_VIP | VCF_INSTALLER
```

### SDDC Manager (3 accounts)
```
sddcmanager.example.com | root        | ******** | SSH | USER    | SDDC_MANAGER | VCF_INSTALLER
sddcmanager.example.com | admin@local | ******** | API | SERVICE | SDDC_MANAGER | VCF_INSTALLER
sddcmanager.example.com | vcf         | ******** | SSH | SERVICE | SDDC_MANAGER | VCF_INSTALLER
```

### Aria Operations (4 credentials: 1 LB + 3 nodes)
```
ops.example.com      | admin | ******** | API | SERVICE | ARIA_OPERATIONS        | VCF_INSTALLER
ops-a.example.com    | root  | ******** | SSH | USER    | ARIA_OPERATIONS_MASTER | VCF_INSTALLER
ops-b.example.com    | root  | ******** | SSH | USER    | ARIA_OPERATIONS_REPLICA| VCF_INSTALLER
ops-data.example.com | root  | ******** | SSH | USER    | ARIA_OPERATIONS_DATA   | VCF_INSTALLER
```

### Aria Operations for Networks (2 accounts)
```
fleet.example.com | root  | ******** | SSH | USER    | ARIA_OPERATIONS_NETWORKS | VCF_INSTALLER
fleet.example.com | admin | ******** | API | SERVICE | ARIA_OPERATIONS_NETWORKS | VCF_INSTALLER
```

### Aria Operations for Logs (1 account)
```
ops-collector.example.com | root | ******** | SSH | USER | ARIA_OPERATIONS_LOGS | VCF_INSTALLER
```

**Total:** ~30+ credentials from a single VCF deployment!

## Migration Steps

### For Existing Installations

1. **Backup your database:**
   ```bash
   cp instance/vcf_credentials.db instance/vcf_credentials.db.backup
   ```

2. **Run migration script:**
   ```bash
   python add_source_column.py
   ```

3. **Restart application:**
   ```bash
   python app.py
   ```

4. **Re-sync environments:**
   - Go to dashboard
   - Click "🔄 Sync Now" on each environment
   - Credentials will be updated with source information

### For New Installations

No action needed - the database will be created with the correct schema.

## Testing

### Verify Installer Parsing

1. Add an environment with VCF Installer configured
2. Click "🧪 Test Connection" to verify connectivity
3. Save and sync the environment
4. View credentials - should see many more credentials than before
5. Check Source column - should show "🔧 Installer"

### Verify Manager Parsing

1. Add an environment with SDDC Manager configured
2. Test and sync
3. View credentials - should show "🖥️ Manager"

### Verify Mixed Sources

1. Add an environment with both Installer and Manager
2. Sync
3. View credentials - should see mix of both sources
4. Export to Excel - verify Source column

## Troubleshooting

### No Credentials from Installer

**Check logs:**
```bash
tail -f logs/vcf_credentials.log
```

**Look for:**
- "Found X SDDCs from installer" - Should be > 0
- "Extracted X credentials from SDDC" - Should be > 0
- Any error messages

**Common issues:**
- Wrong credentials
- SSL verification enabled for self-signed certs
- Network connectivity
- VCF Installer API not accessible

### Missing Some Credential Types

**Check:**
- VCF version (some features only in newer versions)
- Deployment type (some components optional)
- Spec completeness (partial deployments may not have all components)

**Expected counts:**
- ESXi: 1 per host
- vCenter: 2 (root + admin)
- NSX: 3 per manager + 3 for VIP
- SDDC Manager: 3 (root + admin@local + vcf)
- Aria Operations: 1 + 1 per node
- Aria Operations for Networks: 2
- Aria Operations for Logs: 1

### Source Column Not Showing

**Run migration:**
```bash
python add_source_column.py
```

**Then restart and re-sync.**

## API Response Structure

### VCF Installer Spec Structure

```json
{
  "hostSpecs": [
    {
      "hostname": "esxi-01.example.com",
      "credentials": {
        "username": "root",
        "password": "password123"
      }
    }
  ],
  "vcenterSpec": {
    "vcenterHostname": "vc.example.com",
    "rootVcenterPassword": "password123",
    "adminUserSsoPassword": "password123",
    "ssoDomain": "vsphere.local"
  },
  "nsxtSpec": {
    "vipFqdn": "nsx.example.com",
    "rootNsxtManagerPassword": "password123",
    "nsxtAdminPassword": "password123",
    "nsxtAuditPassword": "password123",
    "nsxtManagers": [
      {"hostname": "nsx-a.example.com"},
      {"hostname": "nsx-b.example.com"},
      {"hostname": "nsx-c.example.com"}
    ]
  },
  "sddcManagerSpec": {
    "hostname": "sddc.example.com",
    "rootPassword": "password123",
    "localUserPassword": "password123",
    "sshPassword": "password123"
  },
  "vcfOperationsSpec": {
    "loadBalancerFqdn": "ops.example.com",
    "adminUserPassword": "password123",
    "nodes": [
      {
        "hostname": "ops-a.example.com",
        "type": "master",
        "rootUserPassword": "password123"
      }
    ]
  },
  "vcfOperationsFleetManagementSpec": {
    "hostname": "fleet.example.com",
    "rootUserPassword": "password123",
    "adminUserPassword": "password123"
  },
  "vcfOperationsCollectorSpec": {
    "hostname": "collector.example.com",
    "rootUserPassword": "password123"
  }
}
```

## Summary

✅ **Fixed:** Credential parsing to match actual VCF API structure
✅ **Added:** Support for all VCF 9.0 components
✅ **Added:** Source tracking (Installer vs Manager)
✅ **Updated:** UI to show credential source
✅ **Updated:** Exports to include source information
✅ **Improved:** Error handling and logging
✅ **Documented:** Complete credential mapping

The application now correctly parses and displays all credentials from VCF Installer! 🎉

