"""
Database models for VCF Credentials Fetch application
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, timezone

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """User model for authentication"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    role = db.Column(db.String(20), default='admin')  # 'admin' or 'readonly'
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    def __repr__(self):
        return f'<User {self.username}>'


class Environment(db.Model):
    """Environment model for VCF installations"""
    __tablename__ = 'environments'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    
    # VCF Installer configuration
    installer_host = db.Column(db.String(255))
    installer_username = db.Column(db.String(100))
    installer_password = db.Column(db.String(255))
    
    # SDDC Manager configuration
    manager_host = db.Column(db.String(255))
    manager_username = db.Column(db.String(100))
    manager_password = db.Column(db.String(255))
    
    # SSL verification settings (separate for installer and manager)
    installer_ssl_verify = db.Column(db.Boolean, default=True)
    manager_ssl_verify = db.Column(db.Boolean, default=True)
    
    # Legacy field for backward compatibility
    ssl_verify = db.Column(db.Boolean, default=True)
    
    # Sync configuration
    sync_enabled = db.Column(db.Boolean, default=False)
    sync_interval_minutes = db.Column(db.Integer, default=60)
    last_sync = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    credentials = db.relationship('Credential', backref='environment', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Environment {self.name}>'


class Credential(db.Model):
    """Credential model for storing fetched passwords"""
    __tablename__ = 'credentials'
    
    id = db.Column(db.Integer, primary_key=True)
    environment_id = db.Column(db.Integer, db.ForeignKey('environments.id'), nullable=False)
    
    hostname = db.Column(db.String(255))
    username = db.Column(db.String(100))
    password = db.Column(db.String(255))
    
    credential_type = db.Column(db.String(50))  # SSH, API, SSO, etc.
    account_type = db.Column(db.String(50))     # USER, SERVICE, SYSTEM, etc.
    resource_type = db.Column(db.String(50))    # ESXI, VCENTER, NSX_MANAGER, etc.
    domain_name = db.Column(db.String(100))
    source = db.Column(db.String(50), default='SDDC_MANAGER')  # VCF_INSTALLER or SDDC_MANAGER
    
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    password_history = db.relationship('PasswordHistory', backref='credential', lazy=True, cascade='all, delete-orphan', order_by='PasswordHistory.changed_at.desc()')
    
    def __repr__(self):
        return f'<Credential {self.hostname}:{self.username}>'


class PasswordHistory(db.Model):
    """Password history for tracking credential changes"""
    __tablename__ = 'password_history'
    
    id = db.Column(db.Integer, primary_key=True)
    credential_id = db.Column(db.Integer, db.ForeignKey('credentials.id'), nullable=False)
    
    password = db.Column(db.String(255), nullable=False)
    changed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    changed_by = db.Column(db.String(50), default='SYSTEM')  # SYSTEM, SYNC, MANUAL
    
    def __repr__(self):
        return f'<PasswordHistory {self.credential_id} at {self.changed_at}>'


class ScheduleConfig(db.Model):
    """Configuration for scheduled tasks"""
    __tablename__ = 'schedule_configs'
    
    id = db.Column(db.Integer, primary_key=True)
    environment_id = db.Column(db.Integer, db.ForeignKey('environments.id'), nullable=False)
    
    enabled = db.Column(db.Boolean, default=True)
    interval_minutes = db.Column(db.Integer, default=60)
    last_run = db.Column(db.DateTime)
    next_run = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<ScheduleConfig env={self.environment_id} interval={self.interval_minutes}m>'

