# VCF Credentials Manager - Architecture

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Web Browser                              │
│                    (Clarity UI Interface)                        │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTPS
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                      Flask Application                           │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Authentication Layer                         │  │
│  │              (Flask-Login)                                │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Route Handlers                               │  │
│  │  • Dashboard        • Environment View                    │  │
│  │  • Login/Logout     • API Endpoints                       │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Business Logic                               │  │
│  │  • VCF Fetcher      • Export Utils                        │  │
│  │  • Scheduler        • Credential Parser                   │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
┌───────────────┐ ┌──────────────┐ ┌──────────────┐
│   SQLite DB   │ │ VCF Installer│ │ SDDC Manager │
│               │ │              │ │              │
│ • Users       │ │   REST API   │ │   REST API   │
│ • Environments│ │              │ │              │
│ • Credentials │ │              │ │              │
└───────────────┘ └──────────────┘ └──────────────┘
```

## Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend Layer                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────┐    │
│  │  login.html │  │dashboard.html│  │environment.html    │    │
│  │             │  │              │  │                    │    │
│  │ • Auth Form │  │ • Env Cards  │  │ • Cred Table       │    │
│  │             │  │ • Add/Edit   │  │ • Search/Filter    │    │
│  │             │  │ • Quick Sync │  │ • Export Buttons   │    │
│  └─────────────┘  └──────────────┘  └────────────────────┘    │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Clarity UI Components                        │  │
│  │  • Cards  • Modals  • Tables  • Forms  • Alerts         │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              JavaScript (dashboard.js)                    │  │
│  │  • API Calls  • Modal Management  • Event Handlers       │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                         Backend Layer                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                      app.py                               │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │  Route Handlers                                     │  │  │
│  │  │  • /login, /logout, /dashboard                      │  │  │
│  │  │  • /api/environments/*                              │  │  │
│  │  │  • /api/environments/<id>/credentials               │  │  │
│  │  │  • /api/environments/<id>/export/*                  │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │  Background Scheduler (APScheduler)                 │  │  │
│  │  │  • Periodic credential sync                         │  │  │
│  │  │  • Per-environment job management                   │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                   vcf_fetcher.py                          │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │  VCFCredentialFetcher                               │  │  │
│  │  │  • fetch_from_installer()                           │  │  │
│  │  │  • fetch_from_manager()                             │  │  │
│  │  │  • _parse_installer_spec()                          │  │  │
│  │  │  • _get_token()                                     │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                   export_utils.py                         │  │
│  │  • export_to_csv()                                        │  │
│  │  • export_to_excel()                                      │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                         Data Layer                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                   database.py                             │  │
│  │  ┌────────────┐  ┌──────────────┐  ┌────────────────┐   │  │
│  │  │   User     │  │ Environment  │  │  Credential    │   │  │
│  │  │            │  │              │  │                │   │  │
│  │  │ • id       │  │ • id         │  │ • id           │   │  │
│  │  │ • username │  │ • name       │  │ • environment  │   │  │
│  │  │ • password │  │ • installer* │  │ • hostname     │   │  │
│  │  │ • is_admin │  │ • manager*   │  │ • username     │   │  │
│  │  │            │  │ • sync_*     │  │ • password     │   │  │
│  │  └────────────┘  └──────────────┘  └────────────────┘   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              SQLite Database File                         │  │
│  │              (vcf_credentials.db)                         │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow Diagrams

### 1. User Login Flow

```
User → Login Page → POST /login → Flask-Login
                                      ↓
                              Verify Credentials
                                      ↓
                              Create Session
                                      ↓
                              Redirect to Dashboard
```

### 2. Environment Creation Flow

```
User → Dashboard → Add Environment Modal
                         ↓
                   Fill Form Data
                         ↓
                   POST /api/environments
                         ↓
                   Validate Data
                         ↓
                   Save to Database
                         ↓
                   Schedule Sync Job (if enabled)
                         ↓
                   Return Success
                         ↓
                   Reload Dashboard
```

### 3. Credential Sync Flow

```
Trigger (Manual/Scheduled)
         ↓
fetch_credentials_for_environment()
         ↓
    ┌────┴────┐
    ▼         ▼
Installer  Manager
  API       API
    │         │
    └────┬────┘
         ▼
  Parse Credentials
         ↓
  Clear Old Credentials
         ↓
  Insert New Credentials
         ↓
  Update last_sync
         ↓
    Complete
```

### 4. Credential Export Flow

```
User → Environment View → Click Export
                              ↓
                    GET /api/environments/<id>/export/csv
                              ↓
                    Fetch Credentials from DB
                              ↓
                    Generate CSV/Excel
                              ↓
                    Return File Download
                              ↓
                    Browser Downloads File
```

## Scheduler Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   APScheduler                                │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Background Scheduler (BackgroundScheduler)                 │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Job: env_1  │  │  Job: env_2  │  │  Job: env_N  │     │
│  │              │  │              │  │              │     │
│  │ Interval:    │  │ Interval:    │  │ Interval:    │     │
│  │ 60 minutes   │  │ 30 minutes   │  │ 120 minutes  │     │
│  │              │  │              │  │              │     │
│  │ Function:    │  │ Function:    │  │ Function:    │     │
│  │ fetch_creds  │  │ fetch_creds  │  │ fetch_creds  │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                              │
│  Jobs are dynamically added/removed based on                │
│  environment configuration                                   │
└─────────────────────────────────────────────────────────────┘
```

## Security Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Security Layers                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Layer 1: Transport Security                                │
│  ┌────────────────────────────────────────────────────┐    │
│  │  HTTPS (TLS/SSL)                                    │    │
│  │  • Certificate validation                           │    │
│  │  • Encrypted communication                          │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  Layer 2: Authentication                                    │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Flask-Login                                        │    │
│  │  • Session management                               │    │
│  │  • Login required decorators                        │    │
│  │  • Secure cookies                                   │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  Layer 3: Password Security                                 │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Werkzeug Security                                  │    │
│  │  • Password hashing (PBKDF2)                        │    │
│  │  • Salt generation                                  │    │
│  │  • Secure password verification                     │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  Layer 4: Data Protection                                   │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Database Security                                  │    │
│  │  • File permissions (600)                           │    │
│  │  • Encrypted credentials storage                    │    │
│  │  • SQL injection prevention (ORM)                   │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  Layer 5: API Security                                      │
│  ┌────────────────────────────────────────────────────┐    │
│  │  VCF API Calls                                      │    │
│  │  • Token-based authentication                       │    │
│  │  • SSL verification (configurable)                  │    │
│  │  • Request timeout handling                         │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## Deployment Architectures

### Development Deployment

```
┌─────────────────────────────────────┐
│         Developer Machine            │
│                                      │
│  ┌────────────────────────────────┐ │
│  │   Flask Development Server     │ │
│  │   (python app.py)              │ │
│  │   Port: 5000                   │ │
│  └────────────────────────────────┘ │
│                                      │
│  ┌────────────────────────────────┐ │
│  │   SQLite Database              │ │
│  │   (vcf_credentials.db)         │ │
│  └────────────────────────────────┘ │
└─────────────────────────────────────┘
```

### Production Deployment (Single Server)

```
┌─────────────────────────────────────────────────────────┐
│                    Production Server                     │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │              Nginx (Reverse Proxy)                  │ │
│  │              Port: 443 (HTTPS)                      │ │
│  │              • SSL Termination                      │ │
│  │              • Rate Limiting                        │ │
│  │              • Static File Serving                  │ │
│  └──────────────────────┬─────────────────────────────┘ │
│                         │                                │
│  ┌──────────────────────▼─────────────────────────────┐ │
│  │         Gunicorn (WSGI Server)                      │ │
│  │         Port: 8000 (localhost)                      │ │
│  │         Workers: 4                                  │ │
│  └──────────────────────┬─────────────────────────────┘ │
│                         │                                │
│  ┌──────────────────────▼─────────────────────────────┐ │
│  │         Flask Application                           │ │
│  │         • Route Handlers                            │ │
│  │         • Business Logic                            │ │
│  │         • Background Scheduler                      │ │
│  └──────────────────────┬─────────────────────────────┘ │
│                         │                                │
│  ┌──────────────────────▼─────────────────────────────┐ │
│  │         SQLite Database                             │ │
│  │         (vcf_credentials.db)                        │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### Docker Deployment

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Host                           │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │           Nginx Container                           │ │
│  │           Port: 80, 443                             │ │
│  └──────────────────────┬─────────────────────────────┘ │
│                         │                                │
│  ┌──────────────────────▼─────────────────────────────┐ │
│  │      VCF Credentials Container                      │ │
│  │      • Flask App                                    │ │
│  │      • Gunicorn                                     │ │
│  │      • Python Dependencies                          │ │
│  └──────────────────────┬─────────────────────────────┘ │
│                         │                                │
│  ┌──────────────────────▼─────────────────────────────┐ │
│  │      Volume: Database                               │ │
│  │      (Persistent Storage)                           │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## Technology Stack

```
┌─────────────────────────────────────────────────────────┐
│                    Technology Stack                      │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Frontend                                               │
│  ├─ HTML5                                               │
│  ├─ CSS3                                                │
│  ├─ JavaScript (ES6+)                                   │
│  └─ Clarity UI (v15.11.1)                               │
│     ├─ Clarity Core (v6.9.2)                            │
│     └─ Web Components                                   │
│                                                          │
│  Backend                                                │
│  ├─ Python 3.8+                                         │
│  ├─ Flask 3.0.0                                         │
│  ├─ Flask-Login 0.6.3                                   │
│  ├─ Flask-SQLAlchemy 3.1.1                              │
│  └─ APScheduler 3.10.4                                  │
│                                                          │
│  Database                                               │
│  └─ SQLite 3                                            │
│                                                          │
│  Data Processing                                        │
│  ├─ requests 2.31.0                                     │
│  ├─ openpyxl 3.1.2                                      │
│  └─ PyYAML 6.0.1                                        │
│                                                          │
│  Security                                               │
│  ├─ Werkzeug 3.0.1                                      │
│  └─ urllib3 2.1.0                                       │
│                                                          │
│  Production Server                                      │
│  ├─ Gunicorn 21.2.0                                     │
│  └─ Nginx (external)                                    │
└─────────────────────────────────────────────────────────┘
```

## Performance Characteristics

```
┌─────────────────────────────────────────────────────────┐
│                  Performance Metrics                     │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Response Times (typical)                               │
│  ├─ Login: < 100ms                                      │
│  ├─ Dashboard Load: < 200ms                             │
│  ├─ Credential View: < 300ms                            │
│  ├─ Manual Sync: 2-10s (depends on VCF)                │
│  └─ Export: < 500ms                                     │
│                                                          │
│  Resource Usage                                         │
│  ├─ Memory: ~50-100 MB                                  │
│  ├─ CPU: < 5% (idle), 10-30% (syncing)                 │
│  └─ Disk: ~10 MB + credentials data                    │
│                                                          │
│  Scalability                                            │
│  ├─ Environments: 100+ supported                        │
│  ├─ Credentials: 10,000+ per environment               │
│  ├─ Concurrent Users: 10-50 (single server)            │
│  └─ Background Jobs: Limited by scheduler               │
│                                                          │
│  Database Performance                                   │
│  ├─ SQLite: Suitable for < 1M records                  │
│  ├─ Query Time: < 50ms (typical)                       │
│  └─ Write Time: < 100ms (typical)                      │
└─────────────────────────────────────────────────────────┘
```

## Error Handling Flow

```
┌─────────────────────────────────────────────────────────┐
│                    Error Handling                        │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Frontend Errors                                        │
│  ├─ Network Errors → Alert User                         │
│  ├─ Validation Errors → Form Feedback                   │
│  └─ API Errors → Display Error Message                  │
│                                                          │
│  Backend Errors                                         │
│  ├─ Authentication Errors → Redirect to Login           │
│  ├─ Database Errors → Rollback + Log                    │
│  ├─ VCF API Errors → Log + Return Error                 │
│  └─ Validation Errors → Return 400 + Message            │
│                                                          │
│  Scheduler Errors                                       │
│  ├─ Job Failure → Log Error                             │
│  ├─ Connection Timeout → Retry Logic                    │
│  └─ Credential Invalid → Mark Environment               │
│                                                          │
│  Logging                                                │
│  ├─ Level: INFO (default)                               │
│  ├─ Output: Console/File                                │
│  └─ Format: Timestamp + Level + Message                 │
└─────────────────────────────────────────────────────────┘
```

---

This architecture is designed to be:
- **Scalable**: Can handle multiple environments and users
- **Secure**: Multiple layers of security
- **Maintainable**: Clean separation of concerns
- **Extensible**: Easy to add new features
- **Reliable**: Error handling and logging throughout

