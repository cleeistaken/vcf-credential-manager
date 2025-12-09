# Database Initialization Fix for Gunicorn

## Issue Description

When starting the application for the first time using Gunicorn (especially with the `start_https.sh` or `run_gunicorn_https.sh` scripts), the application would crash immediately after login with a database error:

```
File ".../sqlalchemy/engine/base.py", line 1967, in _exec_single_context
    self.dialect.do_execute(
        cursor, str_statement, effective_parameters, context
    )
File ".../sqlalchemy/engine/default.py", line 941, in do_execute
    cursor.execute(statement, parameters)
```

## Root Cause

The issue occurred because:

1. **Flask Dev Server vs. Gunicorn:**
   - When running with `python app.py`, the database initialization code in the `if __name__ == '__main__':` block executes properly
   - When running with Gunicorn, the app module is imported (not executed directly), so the `if __name__ == '__main__':` block never runs
   - This meant the database tables were never created

2. **Multiple Workers:**
   - Gunicorn was configured to use multiple workers (`workers = multiprocessing.cpu_count() * 2 + 1`)
   - Without proper initialization, multiple workers could attempt to create tables simultaneously, causing race conditions

3. **Timing Issue:**
   - The database initialization happened too late or not at all
   - When the first request came in (after login), the application tried to query tables that didn't exist

## Solution Implemented

### 1. Created `init_database()` Function

Added a dedicated initialization function in `app.py` that runs when the module is loaded:

```python
def init_database():
    """Initialize database and create default admin user if needed"""
    with app.app_context():
        try:
            # Create all tables
            db.create_all()
            app.logger.info("Database tables created/verified")
            
            # Create default admin if no users exist
            if User.query.count() == 0:
                admin = User(
                    username='admin',
                    password_hash=generate_password_hash('admin'),
                    is_admin=True
                )
                db.session.add(admin)
                db.session.commit()
                app.logger.info("Created default admin user")
            
            # Schedule all enabled environments
            environments = Environment.query.filter_by(sync_enabled=True).all()
            for env in environments:
                schedule_environment_sync(env)
                
            app.logger.info("Database initialization complete")
        except Exception as e:
            app.logger.error(f"Error initializing database: {e}", exc_info=True)
            raise

# Initialize database when app is created
init_database()
```

**Key Points:**
- Runs immediately when the module is imported (works with both Flask dev server and Gunicorn)
- Uses `app.app_context()` to ensure proper Flask context
- Includes error handling and logging
- Idempotent - safe to run multiple times

### 2. Updated Gunicorn Configuration

Modified `gunicorn_config.py` to use preload mode:

```python
# Preload app to initialize database before forking workers
preload_app = True

# Start with 1 worker to avoid database initialization race conditions
workers = 1
```

**Benefits:**
- `preload_app = True` loads the application once before forking workers
- Database initialization happens once in the master process
- All workers inherit the initialized state
- Eliminates race conditions

### 3. Created Startup Script

Added `start_https.sh` to automate the startup process:

```bash
#!/bin/bash
# Start VCF Credentials Manager with HTTPS

# Check virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Warning: Virtual environment not activated"
    exit 1
fi

# Create directories
mkdir -p logs ssl

# Generate SSL certificates if needed
if [ ! -f "ssl/cert.pem" ] || [ ! -f "ssl/key.pem" ]; then
    openssl req -x509 -newkey rsa:4096 -nodes \
        -keyout ssl/key.pem -out ssl/cert.pem -days 365 \
        -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
fi

# Start Gunicorn
exec gunicorn \
    --config gunicorn_config.py \
    --certfile ssl/cert.pem \
    --keyfile ssl/key.pem \
    app:app
```

**Features:**
- Checks for virtual environment activation
- Creates required directories
- Generates SSL certificates automatically
- Provides clear user feedback
- Handles first-time setup gracefully

## Testing

The fix has been tested with:

1. **Fresh Installation:**
   ```bash
   rm vcf_credentials.db  # Remove existing database
   ./start_https.sh       # Start with Gunicorn
   ```
   Result: ✅ Database created, admin user created, login successful

2. **Existing Installation:**
   ```bash
   ./start_https.sh       # Start with existing database
   ```
   Result: ✅ Database tables verified, no errors

3. **Multiple Workers:**
   ```bash
   # Edit gunicorn_config.py: workers = 4
   ./start_https.sh
   ```
   Result: ✅ No race conditions, all workers start correctly

## Migration Path

For existing installations:

1. **No action required** - The fix is backward compatible
2. The database will be verified/created on next startup
3. Existing data is preserved

For new installations:

1. Use `./start_https.sh` for easiest setup
2. Or follow manual steps in README.md

## Files Modified

1. **`app.py`:**
   - Added `init_database()` function
   - Moved initialization logic from `if __name__ == '__main__':` block
   - Added call to `init_database()` at module level

2. **`gunicorn_config.py`:**
   - Added `preload_app = True`
   - Reduced workers to 1 (can be increased after first run)
   - Added comments explaining the configuration

3. **`start_https.sh`:** (NEW)
   - Automated startup script
   - Handles SSL certificate generation
   - Checks for virtual environment
   - Provides user feedback

4. **`README.md`:**
   - Updated deployment instructions
   - Added notes about database initialization
   - Documented the startup script

5. **`docs/TROUBLESHOOTING.md`:** (NEW)
   - Comprehensive troubleshooting guide
   - Documents this specific issue and solution
   - Includes other common issues

## Best Practices Going Forward

1. **Always use `preload_app = True` with Gunicorn** when the app has initialization logic
2. **Initialize database at module level** for both dev and production compatibility
3. **Use proper app context** (`with app.app_context():`) for database operations
4. **Log initialization steps** for debugging
5. **Make initialization idempotent** - safe to run multiple times

## Related Issues

This fix also resolves:
- Race conditions with multiple Gunicorn workers
- Missing default admin user on first startup
- Scheduler not starting in production
- Inconsistent behavior between dev and production

## References

- Flask Application Context: https://flask.palletsprojects.com/en/2.3.x/appcontext/
- Gunicorn Configuration: https://docs.gunicorn.org/en/stable/settings.html
- SQLAlchemy with Flask: https://flask-sqlalchemy.palletsprojects.com/

