# Column Filters Feature

## Overview

The environment credentials page now includes powerful filtering capabilities that allow you to quickly find specific credentials by filtering on multiple columns simultaneously.

## Features

### Filter Row

A dedicated filter row appears directly below the column headers with the following filter options:

| Column | Filter Type | Description |
|--------|-------------|-------------|
| **Hostname** | Text Input | Filter by hostname (partial match) |
| **Username** | Text Input | Filter by username (partial match) |
| **Password** | - | No filter (security) |
| **Credential Type** | Dropdown | Select from available types (SSH, API, SSO, etc.) |
| **Account Type** | Dropdown | Select from available types (USER, SERVICE, etc.) |
| **Resource Type** | Dropdown | Select from available types (ESXI, VCENTER, NSX_MANAGER, etc.) |
| **Domain** | Text Input | Filter by domain name (partial match) |
| **Source** | Dropdown | Filter by source (Installer or Manager) |
| **Last Updated** | - | No filter |
| **Actions** | Clear Button | Clear all filters |

### Filter Types

#### Text Input Filters
- **Partial matching**: Filters match any part of the field value
- **Case insensitive**: "vcenter" matches "VCENTER", "vCenter", etc.
- **Real-time filtering**: Results update as you type

**Example:**
```
Hostname filter: "mgmt"
Matches:
  - vc-mgmt.example.com
  - nsx-mgmt.example.com
  - sddc-mgmt.example.com
```

#### Dropdown Filters
- **Exact matching**: Only shows credentials with the selected value
- **Dynamic options**: Dropdowns are populated with actual values from your credentials
- **Sorted alphabetically**: Options are sorted for easy selection

**Example:**
```
Resource Type dropdown options:
  - All (shows everything)
  - ESXI
  - NSX_MANAGER
  - SDDC_MANAGER
  - VCENTER
```

### Search Bar

The global search bar at the top works **in addition to** column filters:

- Searches across: Hostname, Username, Resource Type, and Domain
- Works together with column filters for powerful filtering combinations

### Clear Filters

The **🔄 Clear** button in the Actions column:
- Clears all column filters
- Clears the search bar
- Resets the view to show all credentials

## Usage Examples

### Example 1: Find All ESXi Hosts

1. Click the **Resource Type** dropdown
2. Select **ESXI**
3. View only ESXi host credentials

**Result:** Shows only credentials for ESXi hosts

### Example 2: Find vCenter Root Accounts

1. **Resource Type** dropdown → Select **VCENTER**
2. **Username** text input → Type "root"

**Result:** Shows only vCenter credentials with "root" username

### Example 3: Find All SSH Credentials from Installer

1. **Credential Type** dropdown → Select **SSH**
2. **Source** dropdown → Select **Installer**

**Result:** Shows only SSH credentials fetched from VCF Installer

### Example 4: Find Specific Host Credentials

1. **Hostname** text input → Type "vc-mgmt.vcf04"

**Result:** Shows all credentials for hosts matching "vc-mgmt.vcf04"

### Example 5: Complex Multi-Filter Search

1. **Resource Type** → Select **NSX_MANAGER**
2. **Credential Type** → Select **API**
3. **Domain** → Type "vsphere.local"

**Result:** Shows only NSX Manager API credentials in the vsphere.local domain

## How It Works

### Filter Logic

All filters use **AND** logic - credentials must match **all** active filters to be displayed:

```
Show credential IF:
  (matches search bar OR search bar is empty)
  AND (matches hostname filter OR hostname filter is empty)
  AND (matches username filter OR username filter is empty)
  AND (matches credential type OR credential type is "All")
  AND (matches account type OR account type is "All")
  AND (matches resource type OR resource type is "All")
  AND (matches domain filter OR domain filter is empty)
  AND (matches source OR source is "All")
```

### Dynamic Dropdown Population

Dropdown filters are automatically populated based on your actual credentials:

1. When credentials load, the system scans all credentials
2. Extracts unique values for each dropdown column
3. Sorts values alphabetically
4. Populates dropdown options

**Benefits:**
- Only see options that exist in your environment
- No empty filter results
- Automatically updates when credentials change

### Real-Time Filtering

Filters apply immediately:
- Text inputs: Filter as you type
- Dropdowns: Filter on selection
- No "Apply" button needed

### No Results Message

When filters don't match any credentials:
```
┌────────────────────────────────────────────────────────┐
│  No credentials match the current filters              │
└────────────────────────────────────────────────────────┘
```

## UI Design

### Filter Row Styling

```css
Background: Light gray (#f8f8f8)
Inputs: White background with border
Focus: Blue border with subtle shadow
```

### Filter Controls

**Text Inputs:**
- Full width within column
- Placeholder text: "Filter..."
- Blue focus indicator

**Dropdowns:**
- Full width within column
- "All" option to clear filter
- Blue focus indicator

**Clear Button:**
- Link-style button
- 🔄 icon with "Clear" text
- Clears all filters at once

## Technical Implementation

### HTML Structure

```html
<thead>
  <!-- Column headers -->
  <tr>
    <th>Hostname</th>
    <th>Username</th>
    ...
  </tr>
  
  <!-- Filter row -->
  <tr class="filter-row">
    <th>
      <input type="text" id="filter-hostname" ... />
    </th>
    <th>
      <select id="filter-resource-type" ... >
        <option value="">All</option>
        <option value="ESXI">ESXI</option>
        ...
      </select>
    </th>
    ...
  </tr>
</thead>
```

### JavaScript Functions

**`populateFilterDropdowns()`**
- Extracts unique values from credentials
- Populates dropdown options
- Sorts alphabetically

**`applyFilters()`**
- Gets all filter values
- Filters credentials array
- Renders filtered results
- Shows "no results" message if needed

**`clearFilters()`**
- Resets all filter inputs
- Clears search bar
- Shows all credentials

## Benefits

### For Users

✅ **Quick filtering** - Find credentials instantly
✅ **Multiple filters** - Combine filters for precise results
✅ **Intuitive interface** - Filters appear right where you need them
✅ **No page reload** - Instant client-side filtering
✅ **Easy reset** - Clear all filters with one click

### For Large Environments

✅ **Scalability** - Handle hundreds of credentials efficiently
✅ **Performance** - Client-side filtering is fast
✅ **Usability** - Don't scroll through long lists
✅ **Productivity** - Find what you need quickly

## Common Use Cases

### Security Auditing

**Find all SSH credentials:**
```
Credential Type → SSH
```

**Find all service accounts:**
```
Account Type → SERVICE
```

### Troubleshooting

**Find all credentials for a specific host:**
```
Hostname → "problematic-host.example.com"
```

**Find all credentials from a specific source:**
```
Source → Installer (or Manager)
```

### Credential Management

**Find all vCenter credentials:**
```
Resource Type → VCENTER
```

**Find all NSX Manager admin accounts:**
```
Resource Type → NSX_MANAGER
Username → "admin"
```

### Compliance

**Find all root accounts:**
```
Username → "root"
```

**Find all credentials in a specific domain:**
```
Domain → "vsphere.local"
```

## Tips and Tricks

### Tip 1: Start Broad, Then Narrow

1. Start with one filter (e.g., Resource Type)
2. Review results
3. Add more filters to narrow down

### Tip 2: Use Partial Hostname Matching

Instead of typing full hostname:
```
❌ vc-mgmt.vcf04.showcase.tmm.broadcom.lab
✅ vc-mgmt
```

### Tip 3: Combine Search and Filters

Use the search bar for quick text search, then add column filters for precision:
```
Search: "admin"
+ Resource Type: VCENTER
= All vCenter admin accounts
```

### Tip 4: Clear Filters Frequently

Don't forget to clear filters when switching tasks:
- Click "🔄 Clear" button
- Or manually clear individual filters

### Tip 5: Bookmark Common Filters

For frequently used filter combinations, consider:
1. Apply filters
2. Note the combination
3. Reapply when needed

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| **Tab** | Move between filter inputs |
| **Enter** | (In text input) Apply filter |
| **Escape** | (Planned) Clear all filters |

## Accessibility

✅ **Keyboard navigation** - Tab through all filters
✅ **Focus indicators** - Clear visual feedback
✅ **Semantic HTML** - Proper form elements
✅ **Screen reader friendly** - Labeled inputs

## Browser Compatibility

Tested and working on:
- ✅ Chrome/Edge (Chromium)
- ✅ Firefox
- ✅ Safari
- ✅ Mobile browsers

## Performance

### Client-Side Filtering

- **Fast**: Filters 1000+ credentials instantly
- **No server load**: All filtering happens in browser
- **No network delay**: No API calls needed

### Memory Usage

- **Efficient**: Credentials loaded once
- **Minimal overhead**: Filter logic is lightweight

## Future Enhancements

Potential improvements:

- 🔮 **Date range filter** for Last Updated column
- 🔮 **Save filter presets** for common combinations
- 🔮 **Filter by password age** (days since last change)
- 🔮 **Export filtered results** (CSV/Excel of filtered view)
- 🔮 **URL parameters** to share filtered views
- 🔮 **Filter history** to quickly reapply previous filters

## Troubleshooting

### Filters Not Working

**Problem:** Typing in filter but no results change

**Solution:**
1. Check if other filters are active
2. Clear all filters and try again
3. Refresh the page

### Dropdowns Empty

**Problem:** Dropdown shows only "All" option

**Solution:**
- This means no credentials have values for that column
- Check if credentials are loaded
- Sync environment to fetch credentials

### "No credentials match" Message

**Problem:** Filters too restrictive

**Solution:**
1. Click "🔄 Clear" to reset
2. Apply filters one at a time
3. Check for typos in text filters

## Summary

The column filters feature provides:

✅ **Powerful filtering** on 7 different columns
✅ **Multiple filter types** (text input and dropdowns)
✅ **Real-time updates** as you type or select
✅ **Dynamic dropdowns** populated from actual data
✅ **Easy reset** with clear all button
✅ **Intuitive interface** integrated into table header
✅ **Fast performance** with client-side filtering

Perfect for managing large numbers of credentials across complex VCF environments! 🎉
