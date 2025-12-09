# UI Improvements - December 2025

## Overview

Four user experience improvements have been implemented to make the VCF Credentials Manager more intuitive and user-friendly.

---

## 1. ✅ Environments Sorted by Name

### What Changed
Environments are now automatically sorted alphabetically by name throughout the application.

### Benefits
- ✅ Easier to find specific environments
- ✅ Consistent ordering across dashboard and API
- ✅ Better organization for large deployments

### Implementation
- Dashboard view sorted alphabetically
- API responses sorted alphabetically
- Uses SQL `ORDER BY` for efficiency

### Example
**Before:** Random order (Production, Test, Dev, Staging)  
**After:** Alphabetical order (Dev, Production, Staging, Test)

---

## 2. ✅ Modal Centered on Page

### What Changed
The Add/Edit Environment modal now opens centered on the screen instead of at the top.

### Benefits
- ✅ Better visual focus
- ✅ More professional appearance
- ✅ Easier to use on large screens
- ✅ Follows modern UI best practices

### Features
- **Centered vertically and horizontally**
- **Backdrop darkens background** (50% opacity)
- **Scrollable if content is tall**
- **Responsive** - adapts to screen size
- **Click outside to close**
- **Escape key to close**

### CSS Implementation
```css
.modal {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 2rem;
}

.modal-dialog {
    margin: auto;
    max-height: 90vh;
    overflow-y: auto;
}
```

---

## 3. ✅ Toggle Switch for VCF Installer Section

### What Changed
Added a modern toggle switch to show/hide the VCF Installer configuration section.

### Benefits
- ✅ Cleaner interface when installer not needed
- ✅ Reduces visual clutter
- ✅ Modern toggle switch design
- ✅ Clearly indicates enabled/disabled state

### How It Works

#### Initial State
- Toggle is **OFF** by default
- Installer section is **hidden**
- Only SDDC Manager section is visible

#### When Toggled ON
- Installer section **slides into view**
- All installer fields become available
- Toggle switch turns **blue**

#### When Editing
- If environment has installer data → Toggle is **ON**
- If no installer data → Toggle is **OFF**

### Toggle Switch Design
- **OFF:** Gray background, slider on left
- **ON:** Blue background (#0072a3), slider on right
- **Hover:** Darker shade for feedback
- **Smooth animation:** 0.4s transition

### Visual Example
```
VCF Installer Configuration  [  ○ ]  ← OFF (hidden)
VCF Installer Configuration  [ ○  ]  ← ON (visible)
```

---

## 4. ✅ Separate SSL Verification for Installer and Manager

### What Changed
Split the single "Verify SSL certificates" checkbox into two separate checkboxes:
1. **Verify SSL certificates for Installer**
2. **Verify SSL certificates for Manager**

### Benefits
- ✅ Independent SSL verification per system
- ✅ More flexible configuration
- ✅ Handles mixed environments (one with valid cert, one without)
- ✅ Better security control

### Use Cases

#### Case 1: Both Have Valid Certificates
```
☑ Verify SSL certificates for Installer
☑ Verify SSL certificates for Manager
```

#### Case 2: Installer Self-Signed, Manager Valid
```
☐ Verify SSL certificates for Installer
☑ Verify SSL certificates for Manager
```

#### Case 3: Both Self-Signed (Lab Environment)
```
☐ Verify SSL certificates for Installer
☐ Verify SSL certificates for Manager
```

### Database Changes
New fields added to `Environment` model:
- `installer_ssl_verify` (Boolean, default: True)
- `manager_ssl_verify` (Boolean, default: True)
- `ssl_verify` (kept for backward compatibility)

### API Changes
- Test credentials endpoint uses separate SSL settings
- Credential sync uses appropriate SSL setting per system
- Both fields returned in API responses

---

## Files Modified

### Backend
1. **`database.py`**
   - Added `installer_ssl_verify` field
   - Added `manager_ssl_verify` field
   - Kept `ssl_verify` for backward compatibility

2. **`app.py`**
   - Updated `dashboard()` to sort environments
   - Updated `api_environments()` to sort environments
   - Updated credential fetching to use separate SSL settings
   - Updated test credentials to use separate SSL settings
   - Updated environment creation/update to handle both fields

### Frontend
3. **`templates/dashboard.html`**
   - Added toggle switch for installer section
   - Moved installer fields into collapsible section
   - Added separate SSL checkboxes
   - Updated CSS for toggle switch
   - Updated CSS for centered modal
   - Changed form classes to use base.html styles

4. **`static/js/dashboard.js`**
   - Added `toggleInstallerSection()` function
   - Updated `openAddEnvironmentModal()` to handle toggle
   - Updated `editEnvironment()` to show/hide installer section
   - Updated `saveEnvironment()` to save both SSL settings
   - Updated `testCredentials()` to use both SSL settings
   - Added Escape key handler for modal

---

## Visual Changes

### Modal Before
```
┌─────────────────────────────────────┐
│ [Modal at top of page]             │
│                                     │
│ User has to scroll up to see it    │
└─────────────────────────────────────┘
```

### Modal After
```
        ┌─────────────────────────┐
        │                         │
        │  [Modal centered]       │
        │                         │
        │  Easy to see and use    │
        │                         │
        └─────────────────────────┘
```

### Installer Section Before
```
VCF Installer Configuration
├─ Host: [________________]
├─ Username: [___________]
└─ Password: [___________]

(Always visible, even if not used)
```

### Installer Section After
```
VCF Installer Configuration  [ ○  ]  ← Toggle ON/OFF

(When ON:)
├─ Host: [________________]
├─ Username: [___________]
├─ Password: [___________]
└─ ☑ Verify SSL certificates for Installer

(When OFF: Hidden)
```

### SSL Verification Before
```
☑ Verify SSL certificates
(Applied to both systems)
```

### SSL Verification After
```
Installer Section:
☑ Verify SSL certificates for Installer

Manager Section:
☑ Verify SSL certificates for Manager

(Independent control)
```

---

## Testing

### Test Sorted Environments
```bash
1. Create environments: "Zebra", "Alpha", "Beta"
2. Refresh dashboard
3. Should see: Alpha, Beta, Zebra
```

### Test Centered Modal
```bash
1. Click "Add Environment"
2. Modal should appear in center of screen
3. Background should be darkened
4. Click outside modal → closes
5. Press Escape → closes
```

### Test Installer Toggle
```bash
1. Click "Add Environment"
2. Toggle should be OFF
3. Installer section should be hidden
4. Click toggle → turns blue, section appears
5. Click toggle again → turns gray, section hides
```

### Test Separate SSL Verification
```bash
1. Click "Add Environment"
2. Enable installer toggle
3. See two separate SSL checkboxes:
   - One in installer section
   - One in manager section
4. Uncheck installer SSL
5. Keep manager SSL checked
6. Save and test connection
7. Should use different SSL settings
```

### Test Editing with Installer Data
```bash
1. Create environment with installer data
2. Save
3. Edit environment
4. Installer toggle should be ON
5. Installer section should be visible
6. Both SSL checkboxes should be checked
```

---

## Migration Notes

### For Existing Environments
- Existing environments will have both SSL fields set to `True` by default
- Legacy `ssl_verify` field is maintained for compatibility
- No data migration required
- Environments will automatically sort on next page load

### For New Deployments
- All new environments use the new SSL fields
- Toggle starts in OFF position
- Both SSL checkboxes default to checked (secure by default)

---

## Keyboard Shortcuts

### Modal
- **Escape** - Close modal
- **Enter** (in form) - Submit form

### Toggle
- **Space** (when focused) - Toggle on/off

---

## Accessibility

### Toggle Switch
- ✅ Keyboard accessible
- ✅ Clear visual state
- ✅ Smooth transitions
- ✅ Hover feedback

### Modal
- ✅ Centered for better focus
- ✅ Scrollable content
- ✅ Keyboard dismissible
- ✅ Click-outside dismissible

### Checkboxes
- ✅ Clear labels
- ✅ Grouped logically
- ✅ Easy to understand

---

## Best Practices

### When to Use Installer Toggle
- **Enable** if you have VCF Installer access
- **Disable** if you only use SDDC Manager
- **Enable** when editing environment with installer data

### SSL Verification Settings
- **Enable both** for production with valid certificates
- **Disable installer** if using self-signed cert on installer
- **Disable manager** if using self-signed cert on manager
- **Disable both** for lab environments with self-signed certs

### Environment Naming
- Use clear, descriptive names
- Consider prefixes: "PROD-", "DEV-", "TEST-"
- Names are sorted alphabetically
- Use consistent naming convention

---

## Troubleshooting

### Toggle Not Working
- Clear browser cache
- Check JavaScript console for errors
- Ensure dashboard.js is loaded

### Modal Not Centered
- Try different browser
- Check screen resolution
- Clear browser cache
- Disable browser extensions

### SSL Settings Not Saving
- Check both checkboxes are visible
- Verify form submission includes both fields
- Check browser console for errors
- Review application logs

### Environments Not Sorted
- Refresh page
- Check database has name field
- Verify SQL query includes ORDER BY

---

## Summary

All four improvements are now live:

1. ✅ **Sorted Environments** - Alphabetical order everywhere
2. ✅ **Centered Modal** - Professional, modern appearance
3. ✅ **Installer Toggle** - Cleaner interface, less clutter
4. ✅ **Separate SSL** - Independent control per system

These changes improve:
- **Usability** - Easier to find and configure environments
- **Flexibility** - More control over SSL verification
- **Appearance** - Modern, professional UI
- **Organization** - Better structure and layout

The application is now more intuitive and user-friendly! 🎉

