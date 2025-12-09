# Changelog

All notable changes to the VCF Credentials Manager project.

## [2.3.0] - 2025-12-09

### Simplified to Web-Only Application

#### Removed
- **CLI Interface**: Removed entire `cli/` package and all CLI code
- **CLI Entry Point**: Removed `vcf-cli.py`
- **Config Directory**: Removed `config/` directory (CLI-specific)
- **CLI Documentation**: Removed migration guides and CLI-specific docs

#### Updated
- **README.md**: Focused on web application only
- **PROJECT_STRUCTURE.md**: Updated to reflect web-only structure
- **CHANGELOG.md**: Added v2.3.0 entry

#### Benefits
- ✅ **Simplified codebase** - Single focus on web interface
- ✅ **Easier maintenance** - Less code to maintain
- ✅ **Clearer purpose** - Web application for credential management
- ✅ **Better documentation** - Focused on web features

### Why This Change?
The web interface provides all necessary functionality with a better user experience:
- Modern UI with visual feedback
- Real-time connection testing
- Scheduled automatic syncing
- Easy export options
- Multi-environment management
- Comprehensive logging

The CLI interface was redundant and added unnecessary complexity.

## [2.2.0] - 2025-12-09

### Major Refactoring & Reorganization

#### Removed
- **Database Migration Code**: Removed `migrate_database.py` and `DATABASE_MIGRATION.md`
- **Legacy CLI Files**: Removed all old `sddc_*.py` files
- **Unused Templates**: Removed `base_simple.html` and `test_clarity.html`
- **Scattered Files**: Cleaned up root directory

#### Refactored - CLI Application
- **Complete Rewrite**: Refactored entire CLI codebase for better maintainability
- **Modular Structure**: Organized into `models/` and `services/` packages
- **Base Service**: Created `BaseVcfService` with common API functionality
- **Improved Models**: Enhanced `Credential` and `VcfConfig` with validation
- **Better Services**: Optimized `InstallerService` and `ManagerService`
- **Export Service**: New `CredentialExporter` for output handling
- **Type Hints**: Added comprehensive type hints throughout
- **Error Handling**: Improved error messages and exception handling
- **Context Managers**: Proper resource management with `__enter__`/`__exit__`
- **Performance**: Optimized API calls and data processing

#### Reorganized - File Structure
- **CLI Package**: All CLI code in `cli/` directory
  - `cli/models/` - Data models (Credential, VcfConfig)
  - `cli/services/` - Business logic (Installer, Manager, Exporter)
  - `cli/vcf_credentials_cli.py` - Main CLI entry point
- **Web Package**: All web code in `web/` directory
  - `web/models/` - Database models
  - `web/services/` - Web services (VCF fetcher, exporters)
- **Documentation**: All docs in `docs/` directory
- **Startup**: `start_https.sh` - Main startup script
- **Configuration**: `gunicorn_config.py` - Gunicorn configuration

#### Added
- **New CLI Entry Point**: `vcf-cli.py` for easy CLI access
- **PROJECT_STRUCTURE.md**: Comprehensive structure documentation
- **Enhanced README.md**: Complete project overview
- **Package Init Files**: Proper Python package structure

#### Improved
- **Code Quality**: Better organization, readability, and maintainability
- **Documentation**: Comprehensive inline docs and README files
- **Error Messages**: More helpful and descriptive errors
- **Performance**: Faster execution and better resource usage
- **Testability**: Easier to test with modular structure

### Benefits
- ✅ **Cleaner Codebase**: Well-organized, easy to navigate
- ✅ **Better Performance**: Optimized CLI operations
- ✅ **Easier Maintenance**: Modular, testable code
- ✅ **Improved DX**: Better developer experience
- ✅ **Production Ready**: Professional structure and quality

## [2.1.0] - 2025-12-09

### Added - UI Improvements
- **Sorted Environments**: Environments now display in alphabetical order by name
- **Centered Modal**: Add/Edit Environment modal now opens centered on screen
- **Installer Toggle**: Added toggle switch to show/hide VCF Installer configuration section
- **Separate SSL Verification**: Independent SSL verification checkboxes for Installer and Manager

### Added - Security & Features
- **Password Change Page**: Dedicated page for users to change their password
- **Test Credentials Button**: Test VCF connections before saving environment
- **Robust Logging**: Comprehensive logging system with rotating log files
- **Enhanced Delete Confirmation**: Must type environment name to confirm deletion

### Changed
- Modal now uses flexbox centering for better positioning
- Form styling updated to match base template
- Database model updated with separate SSL verify fields
- API endpoints updated to handle separate SSL settings

### Technical
- Added `installer_ssl_verify` and `manager_ssl_verify` fields to database
- Implemented toggle switch with CSS animations
- Added keyboard shortcuts (Escape to close modal)
- Improved modal backdrop and click-outside-to-close functionality

## [2.0.0] - 2025-12-08

### Added
- Complete web interface with self-contained CSS
- User authentication system
- SQLite database for persistent storage
- Scheduled credential syncing
- CSV and Excel export functionality
- Multi-environment support

### Changed
- Migrated from CLI to web application
- Replaced Clarity UI CDN with embedded styles
- Updated all icons to use emojis for reliability

### Fixed
- SQLAlchemy version compatibility (updated to 2.0.35)
- White page issue (removed external CDN dependencies)
- Icon display issues (switched to emoji icons)

## [1.0.0] - Original

### Initial Release
- CLI-based credential fetcher
- YAML configuration files
- CSV export
- Support for VCF Installer and SDDC Manager

