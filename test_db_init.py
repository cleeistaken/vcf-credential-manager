#!/usr/bin/env python3
"""
Test script to verify database initialization works correctly
This simulates what happens when Gunicorn loads the app
"""

import os
import sys

# Remove existing database to test fresh initialization
if os.path.exists('vcf_credentials.db'):
    print("Removing existing database for clean test...")
    os.remove('vcf_credentials.db')

print("Importing app module (simulating Gunicorn import)...")
try:
    from app import app, db, User
    print("✅ App imported successfully")
except Exception as e:
    print(f"❌ Failed to import app: {e}")
    sys.exit(1)

print("\nChecking database initialization...")
with app.app_context():
    try:
        # Check if tables exist
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        print(f"✅ Found {len(tables)} tables: {', '.join(tables)}")
        
        # Check if admin user exists
        admin = User.query.filter_by(username='admin').first()
        if admin:
            print("✅ Default admin user exists")
        else:
            print("❌ Default admin user not found")
            sys.exit(1)
        
        # Check all expected tables
        expected_tables = ['user', 'environment', 'credential', 'schedule_config', 'password_history']
        missing_tables = [t for t in expected_tables if t not in tables]
        
        if missing_tables:
            print(f"❌ Missing tables: {', '.join(missing_tables)}")
            sys.exit(1)
        else:
            print(f"✅ All expected tables present")
        
        print("\n" + "="*60)
        print("✅ DATABASE INITIALIZATION TEST PASSED")
        print("="*60)
        print("\nThe database was successfully initialized when the app")
        print("module was imported, which means Gunicorn will work correctly!")
        print("\nDefault credentials:")
        print("  Username: admin")
        print("  Password: admin")
        
    except Exception as e:
        print(f"❌ Database check failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

