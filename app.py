#!/usr/bin/env python3
"""
VCF Credentials Fetch Web Application
Main Flask application with HTTPS support and authentication
"""

import os
import sys
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_file
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
import io

from web.models import db, User, Environment, Credential, PasswordHistory, ScheduleConfig
from web.services import VCFCredentialFetcher, export_to_csv, export_to_excel

# Configure comprehensive logging
def setup_logging(app):
    """Setup comprehensive logging for the application"""
    
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Set logging level based on environment
    log_level = logging.DEBUG if app.debug else logging.INFO
    
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

# Use app logger throughout the application
logger = None

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(24).hex())
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vcf_credentials.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Setup logging
setup_logging(app)

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize scheduler
scheduler = BackgroundScheduler()
scheduler.start()
app.logger.info("Background scheduler started")


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def fetch_credentials_for_environment(env_id):
    """Background task to fetch credentials for an environment"""
    with app.app_context():
        try:
            environment = Environment.query.get(env_id)
            if not environment:
                app.logger.error(f"Environment {env_id} not found")
                return

            app.logger.info(f"Fetching credentials for environment: {environment.name} (ID: {env_id})")
            fetcher = VCFCredentialFetcher()
            
            credentials = []
            
            # Fetch from installer if configured
            if environment.installer_host:
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
                except Exception as e:
                    app.logger.error(f"Failed to fetch from installer {environment.installer_host}: {e}", exc_info=True)
            
            # Fetch from manager if configured
            if environment.manager_host:
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
                except Exception as e:
                    app.logger.error(f"Failed to fetch from manager {environment.manager_host}: {e}", exc_info=True)
            
            # Update database with new credentials and track password changes
            app.logger.debug(f"Updating database with {len(credentials)} credentials")
            
            # Get existing credentials for comparison
            existing_creds = {
                (c.hostname, c.username): c 
                for c in Credential.query.filter_by(environment_id=env_id).all()
            }
            
            # Track changes
            updated_count = 0
            new_count = 0
            password_changes = 0
            
            for cred_data in credentials:
                hostname = cred_data.get('hostname', cred_data.get('resourceName', ''))
                username = cred_data.get('username', '')
                new_password = cred_data.get('password', '')
                key = (hostname, username)
                
                if key in existing_creds:
                    # Update existing credential
                    existing_cred = existing_creds[key]
                    
                    # Check if password changed
                    if existing_cred.password != new_password:
                        # Save old password to history
                        history_entry = PasswordHistory(
                            credential_id=existing_cred.id,
                            password=existing_cred.password,
                            changed_at=existing_cred.last_updated or datetime.utcnow(),
                            changed_by='SYNC'
                        )
                        db.session.add(history_entry)
                        password_changes += 1
                        app.logger.info(f"Password changed for {hostname}:{username}")
                    
                    # Update credential
                    existing_cred.password = new_password
                    existing_cred.credential_type = cred_data.get('credentialType', 'USER')
                    existing_cred.account_type = cred_data.get('accountType', 'USER')
                    existing_cred.resource_type = cred_data.get('resourceType', '')
                    existing_cred.domain_name = cred_data.get('domainName', '')
                    existing_cred.source = cred_data.get('source', 'SDDC_MANAGER')
                    existing_cred.last_updated = datetime.utcnow()
                    updated_count += 1
                    
                    # Remove from dict so we know it still exists
                    del existing_creds[key]
                else:
                    # Add new credential
                    new_cred = Credential(
                        environment_id=env_id,
                        hostname=hostname,
                        username=username,
                        password=new_password,
                        credential_type=cred_data.get('credentialType', 'USER'),
                        account_type=cred_data.get('accountType', 'USER'),
                        resource_type=cred_data.get('resourceType', ''),
                        domain_name=cred_data.get('domainName', ''),
                        source=cred_data.get('source', 'SDDC_MANAGER'),
                        last_updated=datetime.utcnow()
                    )
                    db.session.add(new_cred)
                    new_count += 1
            
            # Remove credentials that no longer exist
            removed_count = 0
            for old_cred in existing_creds.values():
                db.session.delete(old_cred)
                removed_count += 1
            
            environment.last_sync = datetime.utcnow()
            db.session.commit()
            
            app.logger.info(
                f"Sync complete for {environment.name}: "
                f"{new_count} new, {updated_count} updated, {removed_count} removed, "
                f"{password_changes} password changes"
            )
            
        except Exception as e:
            app.logger.error(f"Error fetching credentials for environment {env_id}: {e}", exc_info=True)
            db.session.rollback()


def schedule_environment_sync(environment):
    """Schedule periodic credential sync for an environment"""
    job_id = f"env_sync_{environment.id}"
    
    # Remove existing job if any
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
    
    if environment.sync_enabled and environment.sync_interval_minutes > 0:
        scheduler.add_job(
            func=fetch_credentials_for_environment,
            trigger=IntervalTrigger(minutes=environment.sync_interval_minutes),
            id=job_id,
            args=[environment.id],
            replace_existing=True
        )
        app.logger.info(f"Scheduled sync for {environment.name} every {environment.sync_interval_minutes} minutes")


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
                app.logger.info("Created default admin user (username: admin, password: admin)")
            
            # Schedule all enabled environments
            environments = Environment.query.filter_by(sync_enabled=True).all()
            for env in environments:
                schedule_environment_sync(env)
                
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
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('dashboard'))
        else:
            app.logger.warning(f"Failed login attempt for user: {username}")
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    app.logger.info(f"User logged out: {current_user.username}")
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
            'sync_enabled': env.sync_enabled,
            'sync_interval_minutes': env.sync_interval_minutes,
            'last_sync': env.last_sync.isoformat() if env.last_sync else None,
            'credential_count': Credential.query.filter_by(environment_id=env.id).count()
        } for env in environments])
    
    elif request.method == 'POST':
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
            sync_enabled=data.get('sync_enabled', False),
            sync_interval_minutes=data.get('sync_interval_minutes', 60)
        )
        
        db.session.add(environment)
        db.session.commit()
        
        app.logger.info(f"Environment created: {environment.name} (ID: {environment.id})")
        
        # Schedule sync if enabled
        if environment.sync_enabled:
            schedule_environment_sync(environment)
            app.logger.info(f"Scheduled sync for environment: {environment.name}")
        
        return jsonify({'id': environment.id, 'message': 'Environment created successfully'}), 201


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
            'sync_enabled': environment.sync_enabled,
            'sync_interval_minutes': environment.sync_interval_minutes,
            'last_sync': environment.last_sync.isoformat() if environment.last_sync else None
        })
    
    elif request.method == 'PUT':
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
        environment.sync_enabled = data.get('sync_enabled', environment.sync_enabled)
        environment.sync_interval_minutes = data.get('sync_interval_minutes', environment.sync_interval_minutes)
        
        db.session.commit()
        
        # Update schedule
        schedule_environment_sync(environment)
        
        return jsonify({'message': 'Environment updated successfully'})
    
    elif request.method == 'DELETE':
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
    environment = Environment.query.get_or_404(env_id)
    
    app.logger.info(f"Manual sync triggered for environment: {environment.name} (ID: {env_id})")
    try:
        fetch_credentials_for_environment(env_id)
        app.logger.info(f"Manual sync completed for environment: {environment.name}")
        return jsonify({'message': 'Credentials synced successfully'})
    except Exception as e:
        app.logger.error(f"Error syncing environment {env_id}: {e}", exc_info=True)
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


@app.route('/environment/<int:env_id>')
@login_required
def environment_view(env_id):
    """View credentials for a specific environment"""
    environment = Environment.query.get_or_404(env_id)
    return render_template('environment.html', environment=environment)


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
        
        # Schedule all enabled environments
        environments = Environment.query.filter_by(sync_enabled=True).all()
        for env in environments:
            schedule_environment_sync(env)
    
    # For development - use a proper WSGI server with SSL cert for production
    # Example: gunicorn --certfile=cert.pem --keyfile=key.pem app:app
    app.run(host='0.0.0.0', port=5000, debug=True)

