#!/usr/bin/env python3
"""
VCF Credentials Fetch Web Application
Main Flask application with HTTPS support and authentication
"""

import os
import sys
import json
import requests
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_file
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler import events
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime, timezone
import io

from web.models import db, User, Environment, Credential, PasswordHistory, ScheduleConfig
from web.services import VCFCredentialFetcher, export_to_csv, export_to_excel

# Configure comprehensive logging
def setup_logging(app):
    """Setup comprehensive logging for the application"""
    
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Set logging level based on environment and DEBUG_MODE
    if DEBUG_MODE or app.debug:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler for all logs (rotating)
    file_handler = RotatingFileHandler(
        'logs/vcf_credentials.log',
        maxBytes=10485760,  # 10MB
        backupCount=10
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(detailed_formatter)
    
    # File handler for errors only
    error_handler = RotatingFileHandler(
        'logs/vcf_credentials_errors.log',
        maxBytes=10485760,  # 10MB
        backupCount=10
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    
    # Console handler (only in development)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(simple_formatter)
    
    # Clear any existing handlers to prevent duplicates
    app.logger.handlers.clear()
    
    # Add handlers to app logger only (not root logger to avoid duplicates)
    app.logger.addHandler(file_handler)
    app.logger.addHandler(error_handler)
    app.logger.addHandler(console_handler)
    app.logger.setLevel(log_level)
    
    # Prevent propagation to root logger to avoid duplicate messages
    app.logger.propagate = False
    
    # Log startup
    app.logger.info("="*60)
    app.logger.info("VCF Credentials Manager Starting")
    app.logger.info(f"Log level: {logging.getLevelName(log_level)}")
    app.logger.info("="*60)
    
    return app.logger


def setup_access_logging(app):
    """Setup separate user access logging"""
    
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Create access logger
    access_logger = logging.getLogger('access')
    access_logger.setLevel(logging.INFO)
    access_logger.handlers.clear()
    
    # Access log formatter
    access_formatter = logging.Formatter(
        '%(asctime)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler for access logs (rotating)
    access_handler = RotatingFileHandler(
        'logs/user_access.log',
        maxBytes=10485760,  # 10MB
        backupCount=10
    )
    access_handler.setLevel(logging.INFO)
    access_handler.setFormatter(access_formatter)
    
    access_logger.addHandler(access_handler)
    access_logger.propagate = False
    
    return access_logger


def log_user_access(username, action, details=None):
    """Log user access to the access log file"""
    ip_address = request.remote_addr or 'unknown'
    user_agent = request.headers.get('User-Agent', 'unknown')
    
    # Truncate user agent if too long
    if len(user_agent) > 150:
        user_agent = user_agent[:150] + '...'
    
    log_message = f"USER={username} | IP={ip_address} | ACTION={action}"
    if details:
        log_message += f" | {details}"
    log_message += f" | AGENT={user_agent}"
    
    access_logger.info(log_message)


def get_version_info():
    """Read version information from static/json/version.json file"""
    version_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'json', 'version.json')
    
    default_version = {
        "version": "dev",
        "build_type": "development",
        "branch": "unknown",
        "commit": "unknown",
        "commit_short": "unknown",
        "build_date": "unknown",
        "build_timestamp": "unknown"
    }
    
    try:
        if os.path.exists(version_file):
            with open(version_file, 'r') as f:
                version_info = json.load(f)
                # Merge with defaults to ensure all fields exist
                return {**default_version, **version_info}
    except Exception as e:
        # Log error but don't fail - return default version
        print(f"Warning: Could not read static/json/version.json: {e}")
    
    return default_version


# Use app logger throughout the application
logger = None
access_logger = None

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(24).hex())
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vcf_credentials.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Debug mode - set via environment variable
# DEBUG_MODE=true for verbose logging
DEBUG_MODE = os.environ.get('DEBUG_MODE', 'false').lower() == 'true'

# Setup logging
setup_logging(app)
access_logger = setup_access_logging(app)

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'warning'  # Use warning style for login required message

# Initialize scheduler with error logging
def scheduler_error_listener(event):
    """Log scheduler job errors"""
    if event.exception:
        app.logger.error(f"Scheduler job {event.job_id} failed with exception: {event.exception}")
    else:
        app.logger.info(f"Scheduler job {event.job_id} executed successfully")

def scheduler_job_submitted(event):
    """Log when a job is submitted for execution"""
    app.logger.info(f"Scheduler job {event.job_id} submitted for execution")

scheduler = BackgroundScheduler(
    job_defaults={
        'coalesce': True,  # Combine multiple missed runs into one
        'max_instances': 1,  # Only one instance of each job at a time
        'misfire_grace_time': 60 * 60  # Allow jobs to run up to 1 hour late
    }
)
scheduler.add_listener(scheduler_error_listener, events.EVENT_JOB_ERROR | events.EVENT_JOB_EXECUTED)
scheduler.add_listener(scheduler_job_submitted, events.EVENT_JOB_SUBMITTED)
scheduler.start()
app.logger.info("Background scheduler started")


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        if not current_user.is_admin and current_user.role != 'admin':
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function


def check_readonly():
    """Check if current user is readonly and return error if trying to modify"""
    if current_user.role == 'readonly':
        return jsonify({'error': 'Read-only users cannot modify data'}), 403
    return None


def _get_friendly_error_message(exception):
    """Extract a friendly error message from an exception without full traceback"""
    if isinstance(exception, requests.exceptions.Timeout):
        return "Connection timed out"
    elif isinstance(exception, requests.exceptions.ConnectionError):
        # Extract the most relevant part of the connection error
        error_str = str(exception)
        if "Connection refused" in error_str:
            return "Connection refused - server may be down"
        elif "Name or service not known" in error_str or "getaddrinfo failed" in error_str:
            return "Host not found - check hostname"
        elif "Network is unreachable" in error_str:
            return "Network unreachable"
        else:
            return "Connection failed - check network connectivity"
    elif isinstance(exception, requests.exceptions.SSLError):
        return "SSL certificate error - try disabling SSL verification"
    elif isinstance(exception, requests.exceptions.HTTPError):
        response = getattr(exception, 'response', None)
        if response is not None:
            if response.status_code == 401:
                return "Authentication failed - check credentials"
            elif response.status_code == 403:
                return "Access denied - insufficient permissions"
            elif response.status_code == 404:
                return "API endpoint not found - check host"
            else:
                return f"HTTP error {response.status_code}"
        return "HTTP request failed"
    else:
        # For other exceptions, return a truncated message
        error_msg = str(exception)
        if len(error_msg) > 100:
            error_msg = error_msg[:100] + "..."
        return error_msg or "Unknown error"


def fetch_credentials_for_environment(env_id, source=None):
    """Background task to fetch credentials for an environment
    
    Args:
        env_id: Environment ID to sync
        source: Optional - 'installer', 'manager', or None for both
    """
    source_desc = f" ({source})" if source else ""
    app.logger.info(f"Scheduled sync starting for environment ID: {env_id}{source_desc}")
    
    with app.app_context():
        try:
            environment = db.session.get(Environment, env_id)
            if not environment:
                app.logger.error(f"Environment {env_id} not found")
                return

            app.logger.info(f"Fetching credentials for environment: {environment.name} (ID: {env_id}){source_desc}")
            fetcher = VCFCredentialFetcher()
            
            credentials = []
            installer_error = environment.installer_error  # Preserve existing errors
            manager_error = environment.manager_error
            installer_success = False
            manager_success = False
            
            # Fetch from installer if configured and requested
            fetch_installer = (source is None or source == 'installer') and environment.installer_host
            if fetch_installer:
                try:
                    app.logger.debug(f"Fetching from installer: {environment.installer_host}")
                    installer_creds = fetcher.fetch_from_installer(
                        host=environment.installer_host,
                        username=environment.installer_username,
                        password=environment.installer_password,
                        ssl_verify=environment.installer_ssl_verify
                    )
                    credentials.extend(installer_creds)
                    app.logger.info(f"Fetched {len(installer_creds)} credentials from installer")
                    installer_success = True
                    installer_error = None
                except Exception as e:
                    installer_error = _get_friendly_error_message(e)
                    app.logger.error(f"Failed to fetch from installer {environment.installer_host}: {installer_error}")
            
            # Fetch from manager if configured and requested
            fetch_manager = (source is None or source == 'manager') and environment.manager_host
            if fetch_manager:
                try:
                    app.logger.debug(f"Fetching from manager: {environment.manager_host}")
                    manager_creds = fetcher.fetch_from_manager(
                        host=environment.manager_host,
                        username=environment.manager_username,
                        password=environment.manager_password,
                        ssl_verify=environment.manager_ssl_verify
                    )
                    credentials.extend(manager_creds)
                    app.logger.info(f"Fetched {len(manager_creds)} credentials from manager")
                    manager_success = True
                    manager_error = None
                except Exception as e:
                    manager_error = _get_friendly_error_message(e)
                    app.logger.error(f"Failed to fetch from manager {environment.manager_host}: {manager_error}")
            
            # Determine sync status based on what was fetched
            if source == 'installer':
                # Only installer was synced
                sync_status = 'success' if installer_success else 'failed'
            elif source == 'manager':
                # Only manager was synced
                sync_status = 'success' if manager_success else 'failed'
            else:
                # Both were synced (or attempted)
                has_installer = bool(environment.installer_host)
                has_manager = bool(environment.manager_host)
                
                if has_installer and has_manager:
                    if installer_success and manager_success:
                        sync_status = 'success'
                    elif installer_success or manager_success:
                        sync_status = 'partial'
                    else:
                        sync_status = 'failed'
                elif has_installer:
                    sync_status = 'success' if installer_success else 'failed'
                elif has_manager:
                    sync_status = 'success' if manager_success else 'failed'
                else:
                    sync_status = 'failed'
            
            # Update error fields (only update the source that was synced)
            if source is None or source == 'installer':
                environment.installer_error = installer_error
            if source is None or source == 'manager':
                environment.manager_error = manager_error
            environment.last_sync_status = sync_status
            app.logger.info(f"Setting sync status for {environment.name}: status={sync_status}, installer_error={installer_error}, manager_error={manager_error}")
            
            # Update database with new credentials and track password changes
            # Only process credentials if we got any
            if credentials:
                app.logger.debug(f"Updating database with {len(credentials)} credentials")
                
                # Get existing credentials for comparison
                # Key is (hostname, credential_type, username, source) - the unique identity
                # When syncing a single source, only load credentials from that source
                if source:
                    source_filter = 'VCF_INSTALLER' if source == 'installer' else 'SDDC_MANAGER'
                    existing_creds = {
                        (c.hostname, c.credential_type, c.username, c.source): c 
                        for c in Credential.query.filter_by(environment_id=env_id, source=source_filter).all()
                    }
                else:
                    existing_creds = {
                        (c.hostname, c.credential_type, c.username, c.source): c 
                        for c in Credential.query.filter_by(environment_id=env_id).all()
                    }
                
                # Track changes
                updated_count = 0
                new_count = 0
                password_changes = 0
                seen_keys = set()  # Track keys we've processed to avoid duplicates from API
                
                for cred_data in credentials:
                    hostname = cred_data.get('hostname', cred_data.get('resourceName', ''))
                    username = cred_data.get('username', '')
                    new_password = cred_data.get('password', '')
                    credential_type = cred_data.get('credentialType', 'USER')
                    cred_source = cred_data.get('source', 'SDDC_MANAGER')
                    
                    # Skip if missing required fields
                    if not hostname or not username or not credential_type:
                        app.logger.warning(f"Skipping credential with missing required fields: hostname={hostname}, username={username}, type={credential_type}")
                        continue
                    
                    # Unique key: hostname + credential_type + username + source
                    key = (hostname, credential_type, username, cred_source)
                    
                    # Skip duplicates from the API response
                    if key in seen_keys:
                        app.logger.debug(f"Skipping duplicate credential from API: {hostname}:{username} ({credential_type}) from {cred_source}")
                        continue
                    seen_keys.add(key)
                    
                    if key in existing_creds:
                        existing_cred = existing_creds[key]
                        
                        # Check if password changed - save old password to history
                        if existing_cred.password != new_password and existing_cred.password:
                            history_entry = PasswordHistory(
                                credential_id=existing_cred.id,
                                password=existing_cred.password,
                                changed_at=existing_cred.last_updated or datetime.now(timezone.utc),
                                changed_by='SYNC'
                            )
                            db.session.add(history_entry)
                            password_changes += 1
                            app.logger.info(f"Password changed for {hostname}:{username} ({credential_type}) from {cred_source}")
                        
                        # Update credential with new data
                        existing_cred.password = new_password
                        existing_cred.account_type = cred_data.get('accountType', 'USER')
                        existing_cred.resource_type = cred_data.get('resourceType', '')
                        existing_cred.domain_name = cred_data.get('domainName', '')
                        existing_cred.source = cred_source
                        existing_cred.last_updated = datetime.now(timezone.utc)
                        updated_count += 1
                        
                        del existing_creds[key]
                    else:
                        new_cred = Credential(
                            environment_id=env_id,
                            hostname=hostname,
                            username=username,
                            password=new_password,
                            credential_type=credential_type,
                            account_type=cred_data.get('accountType', 'USER'),
                            resource_type=cred_data.get('resourceType', ''),
                            domain_name=cred_data.get('domainName', ''),
                            source=cred_source,
                            last_updated=datetime.now(timezone.utc)
                        )
                        db.session.add(new_cred)
                        new_count += 1
                
                # Only remove credentials that are no longer present from the synced source(s)
                # For single-source sync: only remove credentials from that source
                # For full sync: only remove if sync was fully successful
                removed_count = 0
                if source:
                    # Single source sync - safe to remove credentials from this source that weren't returned
                    for old_cred in existing_creds.values():
                        db.session.delete(old_cred)
                        removed_count += 1
                elif sync_status == 'success':
                    # Full sync was successful - safe to remove all missing credentials
                    for old_cred in existing_creds.values():
                        db.session.delete(old_cred)
                        removed_count += 1
                # If sync_status is 'partial' or 'failed' for a full sync, don't remove anything
                
                app.logger.info(
                    f"Sync {sync_status} for {environment.name}: "
                    f"{new_count} new, {updated_count} updated, {removed_count} removed, "
                    f"{password_changes} password changes"
                )
            else:
                app.logger.warning(f"No credentials fetched for {environment.name} - sync status: {sync_status}")
            
            environment.last_sync = datetime.now(timezone.utc)
            db.session.commit()
            app.logger.info(f"Sync completed and committed for {environment.name}: status={sync_status}")
            
        except Exception as e:
            app.logger.error(f"Error fetching credentials for environment {env_id}: {_get_friendly_error_message(e)}")
            # Try to save the error status even if the main sync failed
            try:
                environment = db.session.get(Environment, env_id)
                if environment:
                    environment.last_sync_status = 'failed'
                    environment.installer_error = _get_friendly_error_message(e)
                    environment.last_sync = datetime.now(timezone.utc)
                    db.session.commit()
                    app.logger.info(f"Saved failed status for {environment.name}")
            except Exception as save_error:
                app.logger.error(f"Could not save error status: {save_error}")
                db.session.rollback()


def schedule_environment_sync(environment):
    """Schedule periodic credential sync for an environment (separate schedules for installer and manager)"""
    
    # Ensure scheduler is running
    if not scheduler.running:
        app.logger.warning(f"Scheduler not running when scheduling jobs for {environment.name}, starting it now")
        scheduler.start()
    
    # Schedule installer sync
    installer_job_id = f"env_sync_{environment.id}_installer"
    existing_installer_job = scheduler.get_job(installer_job_id)
    if existing_installer_job:
        app.logger.debug(f"Removing existing installer sync job: {installer_job_id}")
        scheduler.remove_job(installer_job_id)
    
    if (environment.installer_host and 
        environment.installer_sync_enabled and 
        environment.installer_sync_interval_minutes and 
        environment.installer_sync_interval_minutes > 0):
        scheduler.add_job(
            func=fetch_credentials_for_environment,
            trigger=IntervalTrigger(minutes=environment.installer_sync_interval_minutes),
            id=installer_job_id,
            args=[environment.id, 'installer'],
            replace_existing=True
        )
        job = scheduler.get_job(installer_job_id)
        if job:
            next_run = job.next_run_time.strftime('%Y-%m-%d %H:%M:%S') if job.next_run_time else 'Not scheduled'
            app.logger.info(f"Scheduled installer sync for {environment.name} every {environment.installer_sync_interval_minutes} minutes (next run: {next_run})")
    else:
        app.logger.debug(f"Installer sync not enabled for {environment.name}")
    
    # Schedule manager sync
    manager_job_id = f"env_sync_{environment.id}_manager"
    existing_manager_job = scheduler.get_job(manager_job_id)
    if existing_manager_job:
        app.logger.debug(f"Removing existing manager sync job: {manager_job_id}")
        scheduler.remove_job(manager_job_id)
    
    if (environment.manager_host and 
        environment.manager_sync_enabled and 
        environment.manager_sync_interval_minutes and 
        environment.manager_sync_interval_minutes > 0):
        scheduler.add_job(
            func=fetch_credentials_for_environment,
            trigger=IntervalTrigger(minutes=environment.manager_sync_interval_minutes),
            id=manager_job_id,
            args=[environment.id, 'manager'],
            replace_existing=True
        )
        job = scheduler.get_job(manager_job_id)
        if job:
            next_run = job.next_run_time.strftime('%Y-%m-%d %H:%M:%S') if job.next_run_time else 'Not scheduled'
            app.logger.info(f"Scheduled manager sync for {environment.name} every {environment.manager_sync_interval_minutes} minutes (next run: {next_run})")
    else:
        app.logger.debug(f"Manager sync not enabled for {environment.name}")
    
    # Also handle legacy sync_enabled field for backward compatibility
    legacy_job_id = f"env_sync_{environment.id}"
    existing_legacy_job = scheduler.get_job(legacy_job_id)
    if existing_legacy_job:
        scheduler.remove_job(legacy_job_id)


def _migrate_database():
    """Add any missing columns to existing database tables and clean up duplicates."""
    import sqlite3
    
    db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
    app.logger.info(f"Checking database migration for: {db_path}")
    
    if not os.path.exists(db_path):
        app.logger.info("Database does not exist yet, will be created with correct schema")
        return  # New database, will be created with correct schema
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check for missing columns in environments table
    cursor.execute("PRAGMA table_info(environments)")
    existing_columns = {row[1] for row in cursor.fetchall()}
    app.logger.info(f"Existing columns in environments table: {existing_columns}")
    
    columns_to_add = [
        ("last_sync_status", "VARCHAR(20) DEFAULT 'never'"),
        ("installer_error", "TEXT"),
        ("manager_error", "TEXT"),
        # Separate sync settings for installer and manager
        ("installer_sync_enabled", "BOOLEAN DEFAULT 0"),
        ("installer_sync_interval_minutes", "INTEGER DEFAULT 0"),
        ("manager_sync_enabled", "BOOLEAN DEFAULT 1"),
        ("manager_sync_interval_minutes", "INTEGER DEFAULT 60"),
    ]
    
    for column_name, column_def in columns_to_add:
        if column_name not in existing_columns:
            try:
                cursor.execute(f"ALTER TABLE environments ADD COLUMN {column_name} {column_def}")
                app.logger.info(f"Added missing column to environments table: {column_name}")
            except sqlite3.OperationalError as e:
                app.logger.warning(f"Could not add column {column_name}: {e}")
        else:
            app.logger.debug(f"Column {column_name} already exists")
    
    # Clean up duplicate credentials - keep only the most recent one for each unique key
    # Unique key: environment_id + hostname + credential_type + username + source
    app.logger.info("Checking for duplicate credentials...")
    
    # Find duplicates (including source in the unique key)
    cursor.execute("""
        SELECT environment_id, hostname, credential_type, username, source, COUNT(*) as cnt, GROUP_CONCAT(id) as ids
        FROM credentials
        GROUP BY environment_id, hostname, credential_type, username, source
        HAVING cnt > 1
    """)
    duplicates = cursor.fetchall()
    
    if duplicates:
        app.logger.info(f"Found {len(duplicates)} sets of duplicate credentials, cleaning up...")
        total_removed = 0
        
        for dup in duplicates:
            env_id, hostname, cred_type, username, source, count, id_list = dup
            ids = [int(x) for x in id_list.split(',')]
            
            # Keep the one with the most recent last_updated, or highest ID if no dates
            cursor.execute(f"""
                SELECT id FROM credentials 
                WHERE id IN ({','.join('?' * len(ids))})
                ORDER BY last_updated DESC NULLS LAST, id DESC
                LIMIT 1
            """, ids)
            keep_id = cursor.fetchone()[0]
            
            # Delete the others
            ids_to_delete = [i for i in ids if i != keep_id]
            if ids_to_delete:
                # First, move any password history to the credential we're keeping
                for old_id in ids_to_delete:
                    cursor.execute("""
                        UPDATE password_history SET credential_id = ? WHERE credential_id = ?
                    """, (keep_id, old_id))
                
                # Then delete the duplicate credentials
                cursor.execute(f"""
                    DELETE FROM credentials WHERE id IN ({','.join('?' * len(ids_to_delete))})
                """, ids_to_delete)
                total_removed += len(ids_to_delete)
                app.logger.debug(f"Removed {len(ids_to_delete)} duplicates for {hostname}:{username} ({cred_type})")
        
        app.logger.info(f"Removed {total_removed} duplicate credentials")
    else:
        app.logger.info("No duplicate credentials found")
    
    conn.commit()
    conn.close()
    app.logger.info("Database migration check complete")


def init_database():
    """Initialize database and create default admin user if needed"""
    with app.app_context():
        try:
            # Migrate existing database if needed
            _migrate_database()
            
            # Create all tables
            db.create_all()
            app.logger.info("Database tables created/verified")
            
            # Create default admin if no users exist
            if User.query.count() == 0:
                admin = User(
                    username='admin',
                    password_hash=generate_password_hash('admin'),
                    is_admin=True,
                    role='admin'
                )
                db.session.add(admin)
                db.session.commit()
                app.logger.info("Created default admin user (username: admin, password: admin)")
            
            # Schedule all environments with sync enabled (either installer or manager)
            environments = Environment.query.all()
            app.logger.info(f"Found {len(environments)} environment(s) in database")
            
            for env in environments:
                app.logger.info(f"Environment '{env.name}' (id={env.id}): "
                              f"installer_sync_enabled={env.installer_sync_enabled}, "
                              f"installer_host={env.installer_host}, "
                              f"installer_sync_interval={env.installer_sync_interval_minutes}, "
                              f"manager_sync_enabled={env.manager_sync_enabled}, "
                              f"manager_host={env.manager_host}, "
                              f"manager_sync_interval={env.manager_sync_interval_minutes}")
                
                # Check if scheduler is running before scheduling
                if not scheduler.running:
                    app.logger.warning("Scheduler is not running! Starting scheduler...")
                    scheduler.start()
                
                if env.installer_sync_enabled or env.manager_sync_enabled:
                    app.logger.info(f"Scheduling sync jobs for environment '{env.name}'")
                    schedule_environment_sync(env)
                else:
                    app.logger.info(f"Sync not enabled for environment '{env.name}'")
            
            # Log all scheduled jobs for debugging
            all_jobs = scheduler.get_jobs()
            if all_jobs:
                app.logger.info(f"Scheduler has {len(all_jobs)} job(s) scheduled:")
                for job in all_jobs:
                    next_run = job.next_run_time.strftime('%Y-%m-%d %H:%M:%S') if job.next_run_time else 'None'
                    app.logger.info(f"  - {job.id}: next run at {next_run}")
            else:
                app.logger.info("No jobs scheduled in scheduler")
            
            app.logger.info(f"Scheduler state: running={scheduler.running}, state={scheduler.state}")
            app.logger.info("Database initialization complete")
        except Exception as e:
            app.logger.error(f"Error initializing database: {e}", exc_info=True)
            raise


# Initialize database when app is created (works with both Flask dev server and Gunicorn)
init_database()


@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/test-clarity')
def test_clarity():
    """Test page to verify Clarity UI is loading"""
    return render_template('test_clarity.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        app.logger.info(f"Login attempt for user: {username}")
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            app.logger.info(f"Successful login for user: {username}")
            log_user_access(username, 'LOGIN', f"role={user.role}")
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('dashboard'))
        else:
            app.logger.warning(f"Failed login attempt for user: {username}")
            log_user_access(username, 'LOGIN_FAILED', 'invalid credentials')
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    username = current_user.username
    app.logger.info(f"User logged out: {username}")
    log_user_access(username, 'LOGOUT')
    logout_user()
    return redirect(url_for('login'))


@app.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change user password"""
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        app.logger.info(f"Password change attempt for user: {current_user.username}")
        
        # Validate current password
        if not check_password_hash(current_user.password_hash, current_password):
            app.logger.warning(f"Password change failed - invalid current password for user: {current_user.username}")
            flash('Current password is incorrect', 'error')
            return render_template('change_password.html')
        
        # Validate new password
        if len(new_password) < 8:
            flash('New password must be at least 8 characters long', 'error')
            return render_template('change_password.html')
        
        if new_password != confirm_password:
            flash('New passwords do not match', 'error')
            return render_template('change_password.html')
        
        # Update password
        current_user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        
        app.logger.info(f"Password changed successfully for user: {current_user.username}")
        flash('Password changed successfully', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('change_password.html')


@app.route('/settings')
@login_required
@admin_required
def settings():
    """Settings page - admin only"""
    return render_template('settings.html')


@app.route('/settings/users')
@login_required
@admin_required
def settings_users():
    """User management page - admin only"""
    users = User.query.all()
    return render_template('settings_users.html', users=users)


@app.route('/settings/ssl')
@login_required
@admin_required
def settings_ssl():
    """SSL certificate management page - admin only"""
    return render_template('settings_ssl.html')


@app.route('/settings/server')
@login_required
@admin_required
def settings_server():
    """Server management page - admin only"""
    import sys
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    return render_template('settings_server.html', python_version=python_version)


@app.route('/settings/users/add', methods=['POST'])
@login_required
@admin_required
def add_user():
    """Add a new user"""
    try:
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role', 'readonly')
        
        if not username or not password:
            flash('Username and password are required', 'error')
            return redirect(url_for('settings_users'))
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            flash(f'User {username} already exists', 'error')
            return redirect(url_for('settings_users'))
        
        # Validate password length
        if len(password) < 8:
            flash('Password must be at least 8 characters long', 'error')
            return redirect(url_for('settings_users'))
        
        # Create new user
        new_user = User(
            username=username,
            password_hash=generate_password_hash(password),
            is_admin=(role == 'admin'),
            role=role
        )
        db.session.add(new_user)
        db.session.commit()
        
        app.logger.info(f"New user created: {username} (role: {role})")
        flash(f'User {username} created successfully', 'success')
        
    except Exception as e:
        app.logger.error(f"Error creating user: {e}", exc_info=True)
        flash('Failed to create user', 'error')
        db.session.rollback()
    
    return redirect(url_for('settings_users'))


@app.route('/settings/users/<int:user_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_user(user_id):
    """Delete a user"""
    try:
        user = db.session.get(User, user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Prevent deleting yourself
        if user.id == current_user.id:
            return jsonify({'error': 'Cannot delete your own account'}), 400
        
        # Prevent deleting the last admin
        if user.is_admin or user.role == 'admin':
            admin_count = User.query.filter(
                (User.is_admin == True) | (User.role == 'admin')
            ).count()
            if admin_count <= 1:
                return jsonify({'error': 'Cannot delete the last admin user'}), 400
        
        username = user.username
        db.session.delete(user)
        db.session.commit()
        
        app.logger.info(f"User deleted: {username}")
        return jsonify({'message': f'User {username} deleted successfully'})
        
    except Exception as e:
        app.logger.error(f"Error deleting user: {e}", exc_info=True)
        db.session.rollback()
        return jsonify({'error': 'Failed to delete user'}), 500


@app.route('/settings/ssl/upload', methods=['POST'])
@login_required
@admin_required
def upload_ssl_certificates():
    """Upload and validate SSL certificates"""
    try:
        import ssl
        import tempfile
        import subprocess
        
        cert_file = request.files.get('cert_file')
        key_file = request.files.get('key_file')
        
        if not cert_file or not key_file:
            flash('Both certificate and key files are required', 'error')
            return redirect(url_for('settings_ssl'))
        
        # Save files temporarily for validation
        with tempfile.NamedTemporaryFile(delete=False, suffix='.crt') as cert_tmp:
            cert_file.save(cert_tmp.name)
            cert_path = cert_tmp.name
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.key') as key_tmp:
            key_file.save(key_tmp.name)
            key_path = key_tmp.name
        
        try:
            # Validate certificate
            result = subprocess.run(
                ['openssl', 'x509', '-in', cert_path, '-noout', '-text'],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                flash('Invalid certificate file', 'error')
                return redirect(url_for('settings_ssl'))
            
            # Validate private key
            result = subprocess.run(
                ['openssl', 'rsa', '-in', key_path, '-check', '-noout'],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                flash('Invalid private key file', 'error')
                return redirect(url_for('settings_ssl'))
            
            # Verify certificate and key match
            cert_modulus = subprocess.run(
                ['openssl', 'x509', '-noout', '-modulus', '-in', cert_path],
                capture_output=True,
                text=True
            ).stdout.strip()
            
            key_modulus = subprocess.run(
                ['openssl', 'rsa', '-noout', '-modulus', '-in', key_path],
                capture_output=True,
                text=True
            ).stdout.strip()
            
            if cert_modulus != key_modulus:
                flash('Certificate and private key do not match', 'error')
                return redirect(url_for('settings_ssl'))
            
            # Create ssl directory if it doesn't exist
            ssl_dir = os.path.join(os.getcwd(), 'ssl')
            os.makedirs(ssl_dir, exist_ok=True)
            
            # Backup existing certificates
            cert_dest = os.path.join(ssl_dir, 'server.crt')
            key_dest = os.path.join(ssl_dir, 'server.key')
            
            if os.path.exists(cert_dest):
                os.rename(cert_dest, cert_dest + '.backup')
            if os.path.exists(key_dest):
                os.rename(key_dest, key_dest + '.backup')
            
            # Copy new certificates
            import shutil
            shutil.copy2(cert_path, cert_dest)
            shutil.copy2(key_path, key_dest)
            
            # Set proper permissions
            os.chmod(cert_dest, 0o644)
            os.chmod(key_dest, 0o600)
            
            app.logger.info("SSL certificates updated successfully")
            flash('SSL certificates updated successfully. Please restart the server for changes to take effect.', 'success')
            
        finally:
            # Clean up temporary files
            os.unlink(cert_path)
            os.unlink(key_path)
            
    except Exception as e:
        app.logger.error(f"Error uploading SSL certificates: {e}", exc_info=True)
        flash('Failed to upload SSL certificates', 'error')
    
    return redirect(url_for('settings_ssl'))


@app.route('/dashboard')
@login_required
def dashboard():
    environments = Environment.query.order_by(Environment.name).all()
    return render_template('dashboard.html', environments=environments)


@app.route('/api/environments', methods=['GET', 'POST'])
@login_required
def api_environments():
    if request.method == 'GET':
        environments = Environment.query.order_by(Environment.name).all()
        return jsonify([{
            'id': env.id,
            'name': env.name,
            'description': env.description,
            'installer_host': env.installer_host,
            'manager_host': env.manager_host,
            # Separate sync settings
            'installer_sync_enabled': env.installer_sync_enabled or False,
            'installer_sync_interval_minutes': env.installer_sync_interval_minutes or 0,
            'manager_sync_enabled': env.manager_sync_enabled if env.manager_sync_enabled is not None else True,
            'manager_sync_interval_minutes': env.manager_sync_interval_minutes or 60,
            # Legacy fields
            'sync_enabled': env.sync_enabled,
            'sync_interval_minutes': env.sync_interval_minutes,
            'last_sync': env.last_sync.isoformat() if env.last_sync else None,
            'last_sync_status': env.last_sync_status or 'never',
            'installer_error': env.installer_error,
            'manager_error': env.manager_error,
            'credential_count': Credential.query.filter_by(environment_id=env.id).count()
        } for env in environments])
    
    elif request.method == 'POST':
        # Check if user is readonly
        readonly_check = check_readonly()
        if readonly_check:
            return readonly_check
        
        data = request.json
        
        app.logger.info(f"Creating new environment: {data.get('name')}")
        
        environment = Environment(
            name=data['name'],
            description=data.get('description', ''),
            installer_host=data.get('installer_host'),
            installer_username=data.get('installer_username'),
            installer_password=data.get('installer_password'),
            installer_ssl_verify=data.get('installer_ssl_verify', True),
            manager_host=data.get('manager_host'),
            manager_username=data.get('manager_username'),
            manager_password=data.get('manager_password'),
            manager_ssl_verify=data.get('manager_ssl_verify', True),
            ssl_verify=data.get('ssl_verify', True),  # Legacy
            # Separate sync settings (installer default: disabled, manager default: 60 min)
            installer_sync_enabled=data.get('installer_sync_enabled', False),
            installer_sync_interval_minutes=data.get('installer_sync_interval_minutes', 0),
            manager_sync_enabled=data.get('manager_sync_enabled', True),
            manager_sync_interval_minutes=data.get('manager_sync_interval_minutes', 60),
            # Legacy fields
            sync_enabled=data.get('sync_enabled', False),
            sync_interval_minutes=data.get('sync_interval_minutes', 60)
        )
        
        db.session.add(environment)
        db.session.commit()
        
        app.logger.info(f"Environment created: {environment.name} (ID: {environment.id})")
        
        # Schedule sync based on new settings
        schedule_environment_sync(environment)
        app.logger.info(f"Scheduled sync for environment: {environment.name}")
        
        return jsonify({'id': environment.id, 'message': 'Environment created successfully'}), 201


@app.route('/api/environments/import', methods=['POST'])
@login_required
def api_import_environment():
    """Import environment from JSON or YAML file"""
    import json
    
    # Check if user is readonly
    readonly_check = check_readonly()
    if readonly_check:
        return readonly_check
    
    if 'file' not in request.files:
        return jsonify({'success': False, 'errors': ['No file provided']}), 400
    
    file = request.files['file']
    if not file.filename:
        return jsonify({'success': False, 'errors': ['No file selected']}), 400
    
    # Check file extension
    filename = secure_filename(file.filename)
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    
    if ext not in ['json', 'yaml', 'yml']:
        return jsonify({'success': False, 'errors': ['Invalid file type. Supported: .json, .yaml, .yml']}), 400
    
    try:
        content = file.read().decode('utf-8')
        
        # Parse file based on extension
        if ext == 'json':
            try:
                data = json.loads(content)
            except json.JSONDecodeError as e:
                return jsonify({'success': False, 'errors': [f'Invalid JSON: {str(e)}']}), 400
        else:
            # YAML
            try:
                import yaml
                data = yaml.safe_load(content)
            except ImportError:
                return jsonify({'success': False, 'errors': ['YAML support not available. Install PyYAML: pip install pyyaml']}), 400
            except yaml.YAMLError as e:
                return jsonify({'success': False, 'errors': [f'Invalid YAML: {str(e)}']}), 400
        
        if not isinstance(data, dict):
            return jsonify({'success': False, 'errors': ['File must contain a single environment object']}), 400
        
        # Validate required fields
        errors = []
        
        if not data.get('name'):
            errors.append('Missing required field: name')
        elif Environment.query.filter_by(name=data['name']).first():
            errors.append(f'Environment with name "{data["name"]}" already exists')
        
        has_installer = data.get('installer_host') and data.get('installer_username') and data.get('installer_password')
        has_manager = data.get('manager_host') and data.get('manager_username') and data.get('manager_password')
        
        if not has_installer and not has_manager:
            errors.append('At least one complete configuration required (installer or manager with host, username, and password)')
        
        # Validate field types
        if data.get('sync_interval_minutes') is not None:
            try:
                interval = int(data['sync_interval_minutes'])
                if interval < 5:
                    errors.append('sync_interval_minutes must be at least 5')
            except (ValueError, TypeError):
                errors.append('sync_interval_minutes must be a number')
        
        if errors:
            return jsonify({'success': False, 'errors': errors}), 400
        
        # Test connections
        app.logger.info(f"Testing connections for imported environment: {data.get('name')}")
        connection_tests = {'installer': None, 'manager': None}
        fetcher = VCFCredentialFetcher()
        
        if has_installer:
            try:
                token = fetcher._get_token(
                    host=data['installer_host'],
                    username=data['installer_username'],
                    password=data['installer_password'],
                    ssl_verify=data.get('installer_ssl_verify', True)
                )
                if token:
                    connection_tests['installer'] = {'success': True, 'message': 'Connection successful'}
                    app.logger.info(f"Installer connection test passed: {data['installer_host']}")
                else:
                    connection_tests['installer'] = {'success': False, 'message': 'Failed to obtain token'}
                    app.logger.warning(f"Installer connection test failed: {data['installer_host']}")
            except Exception as e:
                connection_tests['installer'] = {'success': False, 'message': str(e)}
                app.logger.error(f"Installer connection test error: {e}")
        
        if has_manager:
            try:
                token = fetcher._get_token(
                    host=data['manager_host'],
                    username=data['manager_username'],
                    password=data['manager_password'],
                    ssl_verify=data.get('manager_ssl_verify', True)
                )
                if token:
                    connection_tests['manager'] = {'success': True, 'message': 'Connection successful'}
                    app.logger.info(f"Manager connection test passed: {data['manager_host']}")
                else:
                    connection_tests['manager'] = {'success': False, 'message': 'Failed to obtain token'}
                    app.logger.warning(f"Manager connection test failed: {data['manager_host']}")
            except Exception as e:
                connection_tests['manager'] = {'success': False, 'message': str(e)}
                app.logger.error(f"Manager connection test error: {e}")
        
        # Check if at least one connection succeeded
        installer_ok = connection_tests['installer'] and connection_tests['installer']['success']
        manager_ok = connection_tests['manager'] and connection_tests['manager']['success']
        
        if not installer_ok and not manager_ok:
            return jsonify({
                'success': False,
                'errors': ['All connection tests failed. Please verify credentials and network connectivity.'],
                'connection_tests': connection_tests
            }), 400
        
        # Create environment
        environment = Environment(
            name=data['name'],
            description=data.get('description', ''),
            installer_host=data.get('installer_host'),
            installer_username=data.get('installer_username'),
            installer_password=data.get('installer_password'),
            installer_ssl_verify=data.get('installer_ssl_verify', True),
            manager_host=data.get('manager_host'),
            manager_username=data.get('manager_username'),
            manager_password=data.get('manager_password'),
            manager_ssl_verify=data.get('manager_ssl_verify', True),
            sync_enabled=data.get('sync_enabled', False),
            sync_interval_minutes=int(data.get('sync_interval_minutes', 60))
        )
        
        db.session.add(environment)
        db.session.commit()
        
        app.logger.info(f"Environment imported successfully: {environment.name} (ID: {environment.id})")
        
        # Schedule sync if enabled
        if environment.sync_enabled:
            schedule_environment_sync(environment)
        
        return jsonify({
            'success': True,
            'environment': {
                'id': environment.id,
                'name': environment.name
            },
            'connection_tests': connection_tests
        }), 201
        
    except Exception as e:
        app.logger.error(f"Error importing environment: {e}", exc_info=True)
        db.session.rollback()
        return jsonify({'success': False, 'errors': [f'Import failed: {str(e)}']}), 500


@app.route('/api/environments/<int:env_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def api_environment(env_id):
    environment = Environment.query.get_or_404(env_id)
    
    if request.method == 'GET':
        return jsonify({
            'id': environment.id,
            'name': environment.name,
            'description': environment.description,
            'installer_host': environment.installer_host,
            'installer_username': environment.installer_username,
            'installer_ssl_verify': environment.installer_ssl_verify,
            'manager_host': environment.manager_host,
            'manager_username': environment.manager_username,
            'manager_ssl_verify': environment.manager_ssl_verify,
            'ssl_verify': environment.ssl_verify,  # Legacy
            # Separate sync settings
            'installer_sync_enabled': environment.installer_sync_enabled or False,
            'installer_sync_interval_minutes': environment.installer_sync_interval_minutes or 0,
            'manager_sync_enabled': environment.manager_sync_enabled if environment.manager_sync_enabled is not None else True,
            'manager_sync_interval_minutes': environment.manager_sync_interval_minutes or 60,
            # Legacy fields
            'sync_enabled': environment.sync_enabled,
            'sync_interval_minutes': environment.sync_interval_minutes,
            'last_sync': environment.last_sync.isoformat() if environment.last_sync else None
        })
    
    elif request.method == 'PUT':
        # Check if user is readonly
        readonly_check = check_readonly()
        if readonly_check:
            return readonly_check
        
        data = request.json
        
        environment.name = data.get('name', environment.name)
        environment.description = data.get('description', environment.description)
        environment.installer_host = data.get('installer_host', environment.installer_host)
        environment.installer_username = data.get('installer_username', environment.installer_username)
        if data.get('installer_password'):
            environment.installer_password = data['installer_password']
        environment.installer_ssl_verify = data.get('installer_ssl_verify', environment.installer_ssl_verify)
        environment.manager_host = data.get('manager_host', environment.manager_host)
        environment.manager_username = data.get('manager_username', environment.manager_username)
        if data.get('manager_password'):
            environment.manager_password = data['manager_password']
        environment.manager_ssl_verify = data.get('manager_ssl_verify', environment.manager_ssl_verify)
        environment.ssl_verify = data.get('ssl_verify', environment.ssl_verify)  # Legacy
        # Separate sync settings
        if 'installer_sync_enabled' in data:
            environment.installer_sync_enabled = data['installer_sync_enabled']
        if 'installer_sync_interval_minutes' in data:
            environment.installer_sync_interval_minutes = data['installer_sync_interval_minutes']
        if 'manager_sync_enabled' in data:
            environment.manager_sync_enabled = data['manager_sync_enabled']
        if 'manager_sync_interval_minutes' in data:
            environment.manager_sync_interval_minutes = data['manager_sync_interval_minutes']
        # Legacy fields
        environment.sync_enabled = data.get('sync_enabled', environment.sync_enabled)
        environment.sync_interval_minutes = data.get('sync_interval_minutes', environment.sync_interval_minutes)
        
        db.session.commit()
        
        # Update schedule
        schedule_environment_sync(environment)
        
        return jsonify({'message': 'Environment updated successfully'})
    
    elif request.method == 'DELETE':
        # Check if user is readonly
        readonly_check = check_readonly()
        if readonly_check:
            return readonly_check
        
        app.logger.info(f"Deleting environment: {environment.name} (ID: {env_id})")
        
        # Remove scheduled job
        job_id = f"env_sync_{env_id}"
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)
            app.logger.debug(f"Removed scheduled job: {job_id}")
        
        # Delete credentials
        cred_count = Credential.query.filter_by(environment_id=env_id).count()
        Credential.query.filter_by(environment_id=env_id).delete()
        app.logger.debug(f"Deleted {cred_count} credentials")
        
        # Delete environment
        db.session.delete(environment)
        db.session.commit()
        
        app.logger.info(f"Environment deleted: {environment.name}")
        
        return jsonify({'message': 'Environment deleted successfully'})


@app.route('/api/environments/<int:env_id>/sync', methods=['POST'])
@login_required
def api_sync_environment(env_id):
    """Manually trigger credential sync for an environment"""
    # Check if user is readonly
    readonly_check = check_readonly()
    if readonly_check:
        return readonly_check
    
    environment = Environment.query.get_or_404(env_id)
    
    app.logger.info(f"Manual sync triggered for environment: {environment.name} (ID: {env_id})")
    try:
        fetch_credentials_for_environment(env_id)
        
        # Refresh environment to get updated status
        db.session.refresh(environment)
        
        credential_count = Credential.query.filter_by(environment_id=env_id).count()
        
        response_data = {
            'message': 'Sync completed',
            'status': environment.last_sync_status,
            'credential_count': credential_count,
            'installer_error': environment.installer_error,
            'manager_error': environment.manager_error
        }
        
        if environment.last_sync_status == 'success':
            app.logger.info(f"Manual sync successful for environment: {environment.name}")
            return jsonify(response_data)
        elif environment.last_sync_status == 'partial':
            app.logger.warning(f"Manual sync partial for environment: {environment.name}")
            return jsonify(response_data)
        else:
            app.logger.error(f"Manual sync failed for environment: {environment.name}")
            return jsonify(response_data), 207  # 207 Multi-Status
            
    except Exception as e:
        error_msg = _get_friendly_error_message(e)
        app.logger.error(f"Error syncing environment {env_id}: {error_msg}")
        return jsonify({'error': error_msg, 'status': 'failed'}), 500


@app.route('/api/scheduler/status', methods=['GET'])
@login_required
@admin_required
def api_scheduler_status():
    """Get scheduler status and list of scheduled jobs (admin only)"""
    from datetime import datetime
    
    jobs = []
    now = datetime.now()
    for job in scheduler.get_jobs():
        next_run = job.next_run_time
        time_until = None
        if next_run:
            # Make both timezone-naive for comparison
            if next_run.tzinfo:
                next_run_naive = next_run.replace(tzinfo=None)
            else:
                next_run_naive = next_run
            delta = next_run_naive - now
            time_until = f"{int(delta.total_seconds() / 60)} minutes" if delta.total_seconds() > 0 else "overdue"
        
        jobs.append({
            'id': job.id,
            'name': job.name,
            'next_run_time': next_run.isoformat() if next_run else None,
            'next_run_time_local': next_run.strftime('%Y-%m-%d %H:%M:%S') if next_run else None,
            'time_until_next_run': time_until,
            'trigger': str(job.trigger),
            'func': str(job.func),
            'args': str(job.args)
        })
    
    return jsonify({
        'running': scheduler.running,
        'state': scheduler.state,
        'job_count': len(jobs),
        'current_time': now.strftime('%Y-%m-%d %H:%M:%S'),
        'jobs': jobs
    })


@app.route('/api/scheduler/reschedule', methods=['POST'])
@login_required
@admin_required
def api_scheduler_reschedule():
    """Reschedule all environment sync jobs (admin only)"""
    try:
        # Ensure scheduler is running
        if not scheduler.running:
            app.logger.warning("Scheduler was not running, starting it now")
            scheduler.start()
        
        environments = Environment.query.all()
        scheduled_count = 0
        
        for env in environments:
            app.logger.info(f"Rescheduling jobs for environment '{env.name}' (id={env.id})")
            schedule_environment_sync(env)
            
            # Check if any jobs were actually scheduled
            installer_job = scheduler.get_job(f"env_sync_{env.id}_installer")
            manager_job = scheduler.get_job(f"env_sync_{env.id}_manager")
            if installer_job or manager_job:
                scheduled_count += 1
        
        all_jobs = scheduler.get_jobs()
        
        return jsonify({
            'success': True,
            'message': f'Rescheduled jobs for {len(environments)} environment(s)',
            'environments_processed': len(environments),
            'environments_with_jobs': scheduled_count,
            'total_jobs_scheduled': len(all_jobs),
            'scheduler_running': scheduler.running
        })
    except Exception as e:
        app.logger.error(f"Error rescheduling jobs: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/test-credentials', methods=['POST'])
@login_required
def test_credentials():
    """Test VCF credentials before saving"""
    data = request.json
    
    app.logger.info("Testing credentials for new/updated environment")
    
    results = {
        'installer': {'success': False, 'message': ''},
        'manager': {'success': False, 'message': ''}
    }
    
    fetcher = VCFCredentialFetcher()
    
    # Test installer if provided
    if data.get('installer_host') and data.get('installer_username') and data.get('installer_password'):
        try:
            app.logger.info(f"Testing installer connection: {data['installer_host']}")
            # Try to get token
            token = fetcher._get_token(
                host=data['installer_host'],
                username=data['installer_username'],
                password=data['installer_password'],
                ssl_verify=data.get('installer_ssl_verify', True)
            )
            if token:
                results['installer']['success'] = True
                results['installer']['message'] = 'Connection successful'
                app.logger.info(f"Installer test successful: {data['installer_host']}")
            else:
                results['installer']['message'] = 'Failed to obtain authentication token'
                app.logger.warning(f"Installer test failed - no token: {data['installer_host']}")
        except Exception as e:
            results['installer']['message'] = f'Connection failed: {str(e)}'
            app.logger.error(f"Installer test failed: {data['installer_host']} - {e}")
    
    # Test manager if provided
    if data.get('manager_host') and data.get('manager_username') and data.get('manager_password'):
        try:
            app.logger.info(f"Testing manager connection: {data['manager_host']}")
            # Try to get token
            token = fetcher._get_token(
                host=data['manager_host'],
                username=data['manager_username'],
                password=data['manager_password'],
                ssl_verify=data.get('manager_ssl_verify', True)
            )
            if token:
                results['manager']['success'] = True
                results['manager']['message'] = 'Connection successful'
                app.logger.info(f"Manager test successful: {data['manager_host']}")
            else:
                results['manager']['message'] = 'Failed to obtain authentication token'
                app.logger.warning(f"Manager test failed - no token: {data['manager_host']}")
        except Exception as e:
            results['manager']['message'] = f'Connection failed: {str(e)}'
            app.logger.error(f"Manager test failed: {data['manager_host']} - {e}")
    
    # Check if at least one succeeded
    overall_success = results['installer']['success'] or results['manager']['success']
    
    return jsonify({
        'success': overall_success,
        'results': results
    })


@app.route('/api/environments/<int:env_id>/credentials', methods=['GET'])
@login_required
def api_credentials(env_id):
    """Get credentials for an environment"""
    credentials = Credential.query.filter_by(environment_id=env_id).all()
    
    return jsonify([{
        'id': cred.id,
        'hostname': cred.hostname,
        'username': cred.username,
        'password': cred.password,
        'credential_type': cred.credential_type,
        'account_type': cred.account_type,
        'resource_type': cred.resource_type,
        'domain_name': cred.domain_name,
        'source': cred.source,
        'last_updated': cred.last_updated.isoformat() if cred.last_updated else None,
        'has_history': len(cred.password_history) > 0
    } for cred in credentials])


@app.route('/api/credentials/<int:cred_id>/history', methods=['GET'])
@login_required
def api_credential_history(cred_id):
    """Get password history for a credential"""
    credential = Credential.query.get_or_404(cred_id)
    
    # Get password history
    history = PasswordHistory.query.filter_by(credential_id=cred_id).order_by(PasswordHistory.changed_at.desc()).all()
    
    return jsonify({
        'credential': {
            'id': credential.id,
            'hostname': credential.hostname,
            'username': credential.username,
            'current_password': credential.password,
            'last_updated': credential.last_updated.isoformat() if credential.last_updated else None
        },
        'history': [{
            'password': h.password,
            'changed_at': h.changed_at.isoformat() if h.changed_at else None,
            'changed_by': h.changed_by
        } for h in history]
    })


@app.route('/api/environments/<int:env_id>/export/csv')
@login_required
def export_csv(env_id):
    """Export credentials as CSV"""
    environment = Environment.query.get_or_404(env_id)
    credentials = Credential.query.filter_by(environment_id=env_id).all()
    
    csv_data = export_to_csv(credentials)
    
    return send_file(
        io.BytesIO(csv_data.encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'{environment.name}_credentials_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    )


@app.route('/api/environments/<int:env_id>/export/excel')
@login_required
def export_excel(env_id):
    """Export credentials as Excel"""
    environment = Environment.query.get_or_404(env_id)
    credentials = Credential.query.filter_by(environment_id=env_id).all()
    
    excel_data = export_to_excel(credentials, environment.name)
    
    return send_file(
        io.BytesIO(excel_data),
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'{environment.name}_credentials_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    )


@app.route('/api/environments/<int:env_id>/export/config')
@login_required
@admin_required
def export_environment_config(env_id):
    """Export environment configuration as JSON or YAML (admin only)"""
    import json
    
    environment = Environment.query.get_or_404(env_id)
    format_type = request.args.get('format', 'json').lower()
    
    # Build config data including passwords
    config = {
        'name': environment.name,
        'description': environment.description or '',
        'installer_host': environment.installer_host or '',
        'installer_username': environment.installer_username or '',
        'installer_password': environment.installer_password or '',
        'installer_ssl_verify': environment.installer_ssl_verify,
        'manager_host': environment.manager_host or '',
        'manager_username': environment.manager_username or '',
        'manager_password': environment.manager_password or '',
        'manager_ssl_verify': environment.manager_ssl_verify,
        # Separate sync settings
        'installer_sync_enabled': environment.installer_sync_enabled or False,
        'installer_sync_interval_minutes': environment.installer_sync_interval_minutes or 0,
        'manager_sync_enabled': environment.manager_sync_enabled if environment.manager_sync_enabled is not None else True,
        'manager_sync_interval_minutes': environment.manager_sync_interval_minutes or 60
    }
    
    # Remove empty optional fields for cleaner output
    if not config['installer_host']:
        del config['installer_host']
        del config['installer_username']
        del config['installer_password']
        del config['installer_ssl_verify']
    
    if not config['manager_host']:
        del config['manager_host']
        del config['manager_username']
        del config['manager_password']
        del config['manager_ssl_verify']
    
    app.logger.info(f"Environment config exported by {current_user.username}: {environment.name} (format: {format_type})")
    
    if format_type == 'yaml':
        try:
            import yaml
            content = yaml.dump(config, default_flow_style=False, sort_keys=False, allow_unicode=True)
            mimetype = 'text/yaml'
            extension = 'yaml'
        except ImportError:
            # Fallback to JSON if YAML not available
            content = json.dumps(config, indent=2)
            mimetype = 'application/json'
            extension = 'json'
    else:
        content = json.dumps(config, indent=2)
        mimetype = 'application/json'
        extension = 'json'
    
    # Sanitize filename
    safe_name = "".join(c for c in environment.name if c.isalnum() or c in (' ', '-', '_')).strip()
    safe_name = safe_name.replace(' ', '_')
    
    return send_file(
        io.BytesIO(content.encode('utf-8')),
        mimetype=mimetype,
        as_attachment=True,
        download_name=f'{safe_name}_config_{datetime.now().strftime("%Y%m%d_%H%M%S")}.{extension}'
    )


@app.route('/environment/<int:env_id>')
@login_required
def environment_view(env_id):
    """View credentials for a specific environment"""
    environment = Environment.query.get_or_404(env_id)
    return render_template('environment.html', environment=environment)


@app.route('/api/ssl-info')
@login_required
@admin_required
def api_ssl_info():
    """Get current SSL certificate information"""
    try:
        import subprocess
        
        ssl_dir = os.path.join(os.getcwd(), 'ssl')
        cert_path = os.path.join(ssl_dir, 'server.crt')
        
        if not os.path.exists(cert_path):
            return jsonify({'exists': False})
        
        # Get certificate information
        result = subprocess.run(
            ['openssl', 'x509', '-in', cert_path, '-noout', '-subject', '-issuer', '-dates'],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            return jsonify({'exists': False})
        
        # Parse output
        info = {}
        for line in result.stdout.strip().split('\n'):
            if line.startswith('subject='):
                info['subject'] = line.replace('subject=', '').strip()
            elif line.startswith('issuer='):
                info['issuer'] = line.replace('issuer=', '').strip()
            elif line.startswith('notBefore='):
                info['valid_from'] = line.replace('notBefore=', '').strip()
            elif line.startswith('notAfter='):
                info['valid_until'] = line.replace('notAfter=', '').strip()
        
        # Calculate days remaining
        try:
            from datetime import datetime
            valid_until_str = info.get('valid_until', '')
            if valid_until_str:
                valid_until = datetime.strptime(valid_until_str, '%b %d %H:%M:%S %Y %Z')
                days_remaining = (valid_until - datetime.now()).days
                info['days_remaining'] = days_remaining
        except:
            info['days_remaining'] = 'N/A'
        
        info['exists'] = True
        return jsonify(info)
        
    except Exception as e:
        app.logger.error(f"Error getting SSL info: {e}", exc_info=True)
        return jsonify({'exists': False, 'error': str(e)})


@app.route('/api/ssl/generate', methods=['POST'])
@login_required
@admin_required
def api_generate_ssl():
    """Generate a self-signed SSL certificate"""
    import subprocess
    import socket
    
    try:
        ssl_dir = os.path.join(os.getcwd(), 'ssl')
        os.makedirs(ssl_dir, exist_ok=True)
        
        cert_path = os.path.join(ssl_dir, 'server.crt')
        key_path = os.path.join(ssl_dir, 'server.key')
        
        # Backup existing certificates
        if os.path.exists(cert_path):
            backup_time = datetime.now().strftime('%Y%m%d_%H%M%S')
            os.rename(cert_path, f"{cert_path}.backup.{backup_time}")
        if os.path.exists(key_path):
            backup_time = datetime.now().strftime('%Y%m%d_%H%M%S')
            os.rename(key_path, f"{key_path}.backup.{backup_time}")
        
        # Get hostname and IP for SAN
        hostname = socket.gethostname()
        try:
            ip_address = socket.gethostbyname(hostname)
        except:
            ip_address = '127.0.0.1'
        
        # Create OpenSSL config for SAN
        config_content = f"""[req]
default_bits = 4096
prompt = no
default_md = sha256
distinguished_name = dn
x509_extensions = v3_req

[dn]
CN = {hostname}

[v3_req]
subjectAltName = @alt_names
basicConstraints = CA:FALSE
keyUsage = digitalSignature, keyEncipherment

[alt_names]
DNS.1 = {hostname}
DNS.2 = localhost
IP.1 = {ip_address}
IP.2 = 127.0.0.1
"""
        
        config_path = os.path.join(ssl_dir, 'openssl.cnf')
        with open(config_path, 'w') as f:
            f.write(config_content)
        
        # Generate certificate
        result = subprocess.run([
            'openssl', 'req', '-x509', '-newkey', 'rsa:4096', '-nodes',
            '-keyout', key_path,
            '-out', cert_path,
            '-days', '365',
            '-config', config_path,
            '-extensions', 'v3_req'
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            app.logger.error(f"OpenSSL error: {result.stderr}")
            return jsonify({'error': 'Failed to generate certificate', 'details': result.stderr}), 500
        
        # Set proper permissions
        os.chmod(cert_path, 0o644)
        os.chmod(key_path, 0o600)
        
        app.logger.info(f"Self-signed certificate generated by {current_user.username}")
        log_user_access(current_user.username, 'GENERATE_SSL_CERT')
        
        return jsonify({
            'message': 'Self-signed certificate generated successfully',
            'hostname': hostname,
            'ip': ip_address
        })
        
    except Exception as e:
        app.logger.error(f"Error generating SSL certificate: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/version')
@login_required
def api_version():
    """Get application version information"""
    return jsonify(get_version_info())


@app.route('/api/storage-info')
@login_required
@admin_required
def api_storage_info():
    """Get storage information for database and log files"""
    import shutil
    
    try:
        result = {}
        
        # Database info
        db_path = os.path.join(os.getcwd(), 'instance', 'vcf_credentials.db')
        if os.path.exists(db_path):
            db_size = os.path.getsize(db_path)
            result['database_size'] = _format_file_size(db_size)
            result['database_path'] = 'instance/'
        else:
            result['database_size'] = 'N/A'
            result['database_path'] = 'instance/'
        
        # Log files info
        logs_dir = os.path.join(os.getcwd(), 'logs')
        if os.path.exists(logs_dir):
            total_log_size = 0
            log_count = 0
            for filename in os.listdir(logs_dir):
                filepath = os.path.join(logs_dir, filename)
                if os.path.isfile(filepath):
                    total_log_size += os.path.getsize(filepath)
                    log_count += 1
            result['logs_size'] = _format_file_size(total_log_size)
            result['logs_count'] = log_count
        else:
            result['logs_size'] = 'N/A'
            result['logs_count'] = 0
        
        # Disk space info
        try:
            disk_usage = shutil.disk_usage(os.getcwd())
            result['disk_total'] = disk_usage.total
            result['disk_total_human'] = _format_file_size(disk_usage.total)
            result['disk_free'] = _format_file_size(disk_usage.free)
            result['disk_used'] = _format_file_size(disk_usage.used)
        except:
            result['disk_total'] = 0
            result['disk_total_human'] = 'N/A'
            result['disk_free'] = 'N/A'
            result['disk_used'] = 'N/A'
        
        return jsonify(result)
        
    except Exception as e:
        app.logger.error(f"Error getting storage info: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/restart-server', methods=['POST'])
@login_required
@admin_required
def api_restart_server():
    """Restart the Gunicorn server"""
    try:
        import signal
        
        app.logger.warning(f"Server restart initiated by user: {current_user.username}")
        
        # Get the current process ID
        current_pid = os.getpid()
        app.logger.debug(f"Current process PID: {current_pid}")
        
        # Method 1: Check for PID file (most reliable)
        pid_file = 'gunicorn.pid'
        gunicorn_pid = None
        
        if os.path.exists(pid_file):
            try:
                with open(pid_file, 'r') as f:
                    gunicorn_pid = int(f.read().strip())
                app.logger.info(f"Found Gunicorn PID from file: {gunicorn_pid}")
            except Exception as e:
                app.logger.debug(f"Could not read PID file: {e}")
        
        # Method 2: Check environment variable set by Gunicorn
        if not gunicorn_pid:
            # Check if we're running under Gunicorn by looking at parent process
            try:
                parent_pid = os.getppid()
                app.logger.debug(f"Parent process PID: {parent_pid}")
                
                # Try to read parent's process name from /proc (Linux) or use psutil
                try:
                    # Try Linux /proc filesystem
                    with open(f'/proc/{parent_pid}/comm', 'r') as f:
                        parent_name = f.read().strip()
                        if 'gunicorn' in parent_name.lower():
                            gunicorn_pid = parent_pid
                            app.logger.info(f"Found Gunicorn master via /proc: {gunicorn_pid}")
                except:
                    # /proc not available (macOS), try psutil if available
                    try:
                        import psutil
                        parent = psutil.Process(parent_pid)
                        if 'gunicorn' in parent.name().lower():
                            gunicorn_pid = parent_pid
                            app.logger.info(f"Found Gunicorn master via psutil: {gunicorn_pid}")
                    except ImportError:
                        app.logger.debug("psutil not available")
                    except Exception as e:
                        app.logger.debug(f"psutil check failed: {e}")
            except Exception as e:
                app.logger.debug(f"Parent process check failed: {e}")
        
        # Method 3: Use os.getppid() and assume parent is Gunicorn master
        if not gunicorn_pid:
            try:
                # If we're a Gunicorn worker, parent should be master
                # Check if SERVER_SOFTWARE or other Gunicorn indicators exist
                if 'gunicorn' in os.environ.get('SERVER_SOFTWARE', '').lower():
                    gunicorn_pid = os.getppid()
                    app.logger.info(f"Found Gunicorn master via SERVER_SOFTWARE: {gunicorn_pid}")
            except Exception as e:
                app.logger.debug(f"SERVER_SOFTWARE check failed: {e}")
        
        # Method 4: Last resort - try to signal parent and see if it works
        if not gunicorn_pid:
            try:
                parent_pid = os.getppid()
                # Try to send signal 0 (doesn't actually signal, just checks if process exists)
                os.kill(parent_pid, 0)
                # If we got here, parent exists - assume it's Gunicorn
                gunicorn_pid = parent_pid
                app.logger.info(f"Assuming parent is Gunicorn master: {gunicorn_pid}")
            except Exception as e:
                app.logger.debug(f"Parent signal test failed: {e}")
        
        # If we found a Gunicorn PID, send SIGHUP
        if gunicorn_pid:
            try:
                os.kill(gunicorn_pid, signal.SIGHUP)
                app.logger.info(f"Sent SIGHUP to Gunicorn process {gunicorn_pid}")
                return jsonify({
                    'message': 'Server restart initiated successfully',
                    'note': 'Please log in again after restart'
                })
            except ProcessLookupError:
                app.logger.error(f"Gunicorn process {gunicorn_pid} not found")
                return jsonify({
                    'error': 'Gunicorn process not found',
                    'note': 'Please restart manually: ./start_https.sh'
                }), 500
            except PermissionError:
                app.logger.error(f"Permission denied to signal process {gunicorn_pid}")
                return jsonify({
                    'error': 'Permission denied to restart server',
                    'note': 'Please restart manually: ./start_https.sh'
                }), 500
        else:
            # Not running under Gunicorn
            app.logger.warning("Not running under Gunicorn, cannot perform graceful restart")
            app.logger.debug(f"Environment: SERVER_SOFTWARE={os.environ.get('SERVER_SOFTWARE', 'not set')}")
            app.logger.debug(f"Parent PID: {os.getppid()}")
            return jsonify({
                'error': 'Server restart is only available when running under Gunicorn',
                'note': 'Please restart manually: ./start_https.sh'
            }), 400
                
    except Exception as e:
        app.logger.error(f"Error restarting server: {e}", exc_info=True)
        return jsonify({'error': 'Failed to restart server', 'details': str(e)}), 500


@app.route('/logs')
@login_required
@admin_required
def logs_view():
    """View log files (admin only)"""
    log_user_access(current_user.username, 'VIEW_LOGS')
    return render_template('logs.html')


@app.route('/api/logs')
@login_required
@admin_required
def api_logs():
    """Get list of available log files (admin only)"""
    import glob
    
    logs_dir = os.path.join(os.getcwd(), 'logs')
    if not os.path.exists(logs_dir):
        return jsonify({'logs': []})
    
    log_files = []
    for log_path in glob.glob(os.path.join(logs_dir, '*.log*')):
        filename = os.path.basename(log_path)
        stat = os.stat(log_path)
        log_files.append({
            'name': filename,
            'size': stat.st_size,
            'size_human': _format_file_size(stat.st_size),
            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            'modified_human': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        })
    
    # Sort by modification time (newest first)
    log_files.sort(key=lambda x: x['modified'], reverse=True)
    
    return jsonify({'logs': log_files})


def _format_file_size(size_bytes):
    """Format file size in human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


@app.route('/api/logs/<path:filename>')
@login_required
@admin_required
def api_log_content(filename):
    """Get content of a specific log file (admin only)"""
    import re
    
    # Security: only allow .log files from logs directory
    if not re.match(r'^[\w\-\.]+\.log(\.\d+)?$', filename):
        return jsonify({'error': 'Invalid filename'}), 400
    
    logs_dir = os.path.join(os.getcwd(), 'logs')
    log_path = os.path.join(logs_dir, filename)
    
    # Prevent directory traversal
    if not os.path.abspath(log_path).startswith(os.path.abspath(logs_dir)):
        return jsonify({'error': 'Invalid path'}), 400
    
    if not os.path.exists(log_path):
        return jsonify({'error': 'Log file not found'}), 404
    
    # Get optional parameters
    lines = request.args.get('lines', 500, type=int)
    lines = min(lines, 5000)  # Cap at 5000 lines
    
    try:
        with open(log_path, 'r', encoding='utf-8', errors='replace') as f:
            # Read last N lines
            all_lines = f.readlines()
            content = ''.join(all_lines[-lines:])
            total_lines = len(all_lines)
        
        log_user_access(current_user.username, 'READ_LOG', f"file={filename}")
        
        return jsonify({
            'filename': filename,
            'content': content,
            'total_lines': total_lines,
            'showing_lines': min(lines, total_lines)
        })
    except Exception as e:
        app.logger.error(f"Error reading log file {filename}: {e}")
        return jsonify({'error': 'Failed to read log file'}), 500


@app.route('/api/logs/export')
@login_required
@admin_required
def api_export_logs():
    """Export all log files as tar.gz archive (admin only)"""
    import tarfile
    import tempfile
    
    logs_dir = os.path.join(os.getcwd(), 'logs')
    if not os.path.exists(logs_dir):
        return jsonify({'error': 'No logs directory found'}), 404
    
    try:
        # Create tar.gz in memory
        output = io.BytesIO()
        
        with tarfile.open(fileobj=output, mode='w:gz') as tar:
            for filename in os.listdir(logs_dir):
                if filename.endswith('.log') or '.log.' in filename:
                    file_path = os.path.join(logs_dir, filename)
                    if os.path.isfile(file_path):
                        tar.add(file_path, arcname=filename)
        
        output.seek(0)
        
        log_user_access(current_user.username, 'EXPORT_LOGS', 'format=tar.gz')
        app.logger.info(f"Admin {current_user.username} exported log files")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return send_file(
            output,
            mimetype='application/gzip',
            as_attachment=True,
            download_name=f'vcf_credentials_logs_{timestamp}.tar.gz'
        )
    except Exception as e:
        app.logger.error(f"Error exporting logs: {e}")
        return jsonify({'error': 'Failed to export logs'}), 500


@app.route('/api/logs/<path:filename>/download')
@login_required
@admin_required
def api_download_log(filename):
    """Download a specific log file (admin only)"""
    import re
    
    # Security: only allow .log files from logs directory
    if not re.match(r'^[\w\-\.]+\.log(\.\d+)?$', filename):
        return jsonify({'error': 'Invalid filename'}), 400
    
    logs_dir = os.path.join(os.getcwd(), 'logs')
    log_path = os.path.join(logs_dir, filename)
    
    # Prevent directory traversal
    if not os.path.abspath(log_path).startswith(os.path.abspath(logs_dir)):
        return jsonify({'error': 'Invalid path'}), 400
    
    if not os.path.exists(log_path):
        return jsonify({'error': 'Log file not found'}), 404
    
    log_user_access(current_user.username, 'DOWNLOAD_LOG', f"file={filename}")
    
    return send_file(
        log_path,
        mimetype='text/plain',
        as_attachment=True,
        download_name=filename
    )


@app.cli.command()
def init_db():
    """Initialize the database"""
    db.create_all()
    print("Database initialized successfully")


@app.cli.command()
def create_admin():
    """Create an admin user"""
    username = input("Enter admin username: ")
    password = input("Enter admin password: ")
    
    user = User.query.filter_by(username=username).first()
    if user:
        print(f"User {username} already exists")
        return
    
    admin = User(
        username=username,
        password_hash=generate_password_hash(password),
        is_admin=True
    )
    
    db.session.add(admin)
    db.session.commit()
    print(f"Admin user {username} created successfully")


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Create default admin if no users exist
        if User.query.count() == 0:
            admin = User(
                username='admin',
                password_hash=generate_password_hash('admin'),
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()
            app.logger.info("Created default admin user (username: admin, password: admin)")
        
        # Schedule all environments with sync enabled (either installer or manager)
        environments = Environment.query.all()
        for env in environments:
            if env.installer_sync_enabled or env.manager_sync_enabled:
                schedule_environment_sync(env)
    
    # For development - use a proper WSGI server with SSL cert for production
    # Example: gunicorn --certfile=cert.pem --keyfile=key.pem app:app
    app.run(host='0.0.0.0', port=5000, debug=True)

