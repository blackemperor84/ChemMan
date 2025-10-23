# Chem-Man Deployment Guide

Complete guide for deploying the Chem-Man chemical substance management application to production.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Server Setup](#server-setup)
3. [Database Installation (PostgreSQL)](#database-installation-postgresql)
4. [Application Installation](#application-installation)
5. [Configuration](#configuration)
6. [Data Import](#data-import)
7. [Production Deployment (WSGI Server)](#production-deployment-wsgi-server)
8. [Reverse Proxy Setup (nginx/Apache)](#reverse-proxy-setup)
9. [SSL/TLS Configuration](#ssltls-configuration)
10. [Backup Strategy](#backup-strategy)
11. [Monitoring & Maintenance](#monitoring--maintenance)
12. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Server Requirements

- **OS:** Windows Server 2019/2022 or Linux (Ubuntu 20.04/22.04, CentOS 8+)
- **RAM:** 4GB minimum, 8GB recommended
- **Storage:** 20GB minimum (including database and logs)
- **CPU:** 2 cores minimum, 4 cores recommended

### Software Requirements

- **Python:** 3.11 or higher
- **PostgreSQL:** 14 or higher (18 recommended)
- **pip:** Latest version
- **virtualenv:** For Python environment isolation

### Network Requirements

- **Port 5432:** PostgreSQL database (internal only)
- **Port 80:** HTTP (redirects to HTTPS)
- **Port 443:** HTTPS (public access)
- **Port 5000:** Flask development server (internal only, not for production)

---

## Server Setup

### 1. Update System (Linux)

```bash
sudo apt update && sudo apt upgrade -y  # Ubuntu/Debian
# OR
sudo yum update -y  # CentOS/RHEL
```

### 2. Install System Dependencies

#### Ubuntu/Debian:
```bash
sudo apt install -y python3 python3-pip python3-venv postgresql postgresql-contrib nginx
```

#### CentOS/RHEL:
```bash
sudo yum install -y python3 python3-pip postgresql-server postgresql-contrib nginx
```

#### Windows Server:
- Download and install Python 3.13+ from [python.org](https://www.python.org/downloads/)
- Download and install PostgreSQL 18 from [postgresql.org](https://www.postgresql.org/download/windows/)
- Download and install nginx from [nginx.org](http://nginx.org/en/download.html)

---

## Database Installation (PostgreSQL)

### Linux Installation

#### 1. Initialize PostgreSQL (first time only)

```bash
# Ubuntu/Debian - already initialized during installation
sudo systemctl start postgresql
sudo systemctl enable postgresql

# CentOS/RHEL - manual initialization required
sudo postgresql-setup --initdb
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

#### 2. Create Database and User

```bash
sudo -u postgres psql

# Inside PostgreSQL prompt:
CREATE DATABASE chemman_prod;
CREATE USER chemman_user WITH PASSWORD 'STRONG_PASSWORD_HERE';
GRANT ALL PRIVILEGES ON DATABASE chemman_prod TO chemman_user;
\q
```

### Windows Installation

#### 1. Install PostgreSQL

- Run the PostgreSQL installer
- Set a strong password for the `postgres` superuser
- Accept default port (5432)

#### 2. Create Database and User

Using pgAdmin or command line:

```sql
-- Open SQL Query window and run:
CREATE DATABASE chemman_prod;
CREATE USER chemman_user WITH PASSWORD 'STRONG_PASSWORD_HERE';
GRANT ALL PRIVILEGES ON DATABASE chemman_prod TO chemman_user;
```

### Database Security

Edit `postgresql.conf` and `pg_hba.conf`:

```bash
# Linux:
sudo nano /etc/postgresql/18/main/postgresql.conf

# Set:
listen_addresses = 'localhost'  # Only accept local connections
max_connections = 100
```

Edit `pg_hba.conf`:
```
# TYPE  DATABASE        USER            ADDRESS                 METHOD
local   chemman_prod    chemman_user                            md5
host    chemman_prod    chemman_user    127.0.0.1/32            md5
```

Restart PostgreSQL:
```bash
sudo systemctl restart postgresql  # Linux
# Windows: Restart service via Services panel
```

---

## Application Installation

### 1. Create Application User (Linux only)

```bash
sudo useradd -m -s /bin/bash chemman
sudo su - chemman
```

### 2. Clone/Copy Application Files

```bash
# Create directory
mkdir -p /opt/chemman  # Linux
# OR
mkdir C:\chemman  # Windows

# Copy all application files to this directory
cd /opt/chemman  # Linux
cd C:\chemman  # Windows
```

### 3. Create Python Virtual Environment

```bash
python3 -m venv venv

# Activate environment
source venv/bin/activate  # Linux
venv\Scripts\activate  # Windows
```

### 4. Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## Configuration

### 1. Create Production Configuration File

Create `.env` file in application root:

```bash
# Database Configuration
DATABASE_URL=postgresql://chemman_user:STRONG_PASSWORD_HERE@localhost:5432/chemman_prod

# Flask Configuration
FLASK_ENV=production
SECRET_KEY=GENERATE_RANDOM_SECRET_KEY_HERE
FLASK_DEBUG=0

# Admin User (first login)
DEFAULT_PASSWORD=CHANGE_THIS_IMMEDIATELY

# Rate Limiting
RATELIMIT_STORAGE_URL=redis://localhost:6379

# Security Headers
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax
```

### 2. Generate Secret Key

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Copy the output to `SECRET_KEY` in `.env` file.

### 3. Set File Permissions (Linux)

```bash
chmod 600 .env  # Only owner can read
chown chemman:chemman .env
```

---

## Data Import

### 1. Create Database Tables

```bash
python -c "from app import create_app; from models import db; from config import ProductionConfig; app = create_app(ProductionConfig); app.app_context().push(); db.create_all(); print('Tables created')"
```

### 2. Import CLP Database (4400 substances)

```bash
python import_excel.py
```

Expected output: `Gotowe! Zaimportowano 4400 substancji!`

### 3. Import SVHC Database (492 substances)

```bash
python import_svhc.py
```

Expected output: `Gotowe! Zaimportowano 492 substancji SVHC!`

### 4. Create Admin User

```bash
python create_admin.py
```

Expected output: `Admin user created successfully!`

### 5. Verify Import

```bash
python -c "from app import create_app; from models import db, ExcelSourceSubstance, SVHCSubstance, User; from config import ProductionConfig; app = create_app(ProductionConfig); app.app_context().push(); print(f'CLP: {ExcelSourceSubstance.query.count()}'); print(f'SVHC: {SVHCSubstance.query.count()}'); print(f'Users: {User.query.count()}')"
```

Expected output:
```
CLP: 4400
SVHC: 492
Users: 1
```

---

## Production Deployment (WSGI Server)

### Option 1: Gunicorn (Linux - Recommended)

#### 1. Install Gunicorn

```bash
pip install gunicorn
```

#### 2. Create Gunicorn Configuration

Create `gunicorn_config.py`:

```python
# Gunicorn configuration file
bind = "127.0.0.1:8000"
workers = 4  # (2 x CPU cores) + 1
worker_class = "sync"
worker_connections = 1000
timeout = 120
keepalive = 5

# Logging
accesslog = "/var/log/chemman/access.log"
errorlog = "/var/log/chemman/error.log"
loglevel = "info"

# Security
limit_request_line = 4096
limit_request_fields = 100
limit_request_field_size = 8190
```

#### 3. Create Systemd Service

Create `/etc/systemd/system/chemman.service`:

```ini
[Unit]
Description=Chem-Man Chemical Management Application
After=network.target postgresql.service

[Service]
Type=notify
User=chemman
Group=chemman
WorkingDirectory=/opt/chemman
Environment="PATH=/opt/chemman/venv/bin"
ExecStart=/opt/chemman/venv/bin/gunicorn -c gunicorn_config.py "app:create_app()"
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=always

[Install]
WantedBy=multi-user.target
```

#### 4. Start and Enable Service

```bash
sudo systemctl daemon-reload
sudo systemctl start chemman
sudo systemctl enable chemman
sudo systemctl status chemman
```

### Option 2: Waitress (Windows - Recommended)

#### 1. Install Waitress

```bash
pip install waitress
```

#### 2. Create Startup Script

Create `start_production.py`:

```python
"""Production server startup script using Waitress"""
from waitress import serve
from app import create_app
from config import ProductionConfig

app = create_app(ProductionConfig)

if __name__ == '__main__':
    print("Starting Chem-Man on http://localhost:8000")
    serve(app, host='127.0.0.1', port=8000, threads=4)
```

#### 3. Create Windows Service

Install NSSM (Non-Sucking Service Manager):
```bash
# Download from https://nssm.cc/download
nssm install ChemMan "C:\chemman\venv\Scripts\python.exe" "C:\chemman\start_production.py"
nssm set ChemMan AppDirectory "C:\chemman"
nssm start ChemMan
```

---

## Reverse Proxy Setup

### nginx Configuration (Linux & Windows)

#### 1. Create nginx Configuration

Create `/etc/nginx/sites-available/chemman` (Linux) or `C:\nginx\conf\chemman.conf` (Windows):

```nginx
# HTTP to HTTPS redirect
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    return 301 https://$server_name$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    # SSL Configuration (update paths for your certificates)
    ssl_certificate /etc/ssl/certs/your-domain.crt;
    ssl_certificate_key /etc/ssl/private/your-domain.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Logging
    access_log /var/log/nginx/chemman_access.log;
    error_log /var/log/nginx/chemman_error.log;

    # Max upload size (for SDS files)
    client_max_body_size 20M;

    # Proxy to Gunicorn/Waitress
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Static files (if served separately)
    location /static/ {
        alias /opt/chemman/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

#### 2. Enable Site (Linux)

```bash
sudo ln -s /etc/nginx/sites-available/chemman /etc/nginx/sites-enabled/
sudo nginx -t  # Test configuration
sudo systemctl restart nginx
```

#### 3. Start nginx (Windows)

```bash
cd C:\nginx
start nginx
```

### Apache Configuration (Alternative)

Create `/etc/apache2/sites-available/chemman.conf`:

```apache
<VirtualHost *:80>
    ServerName your-domain.com
    Redirect permanent / https://your-domain.com/
</VirtualHost>

<VirtualHost *:443>
    ServerName your-domain.com

    SSLEngine on
    SSLCertificateFile /etc/ssl/certs/your-domain.crt
    SSLCertificateKeyFile /etc/ssl/private/your-domain.key

    ProxyPreserveHost On
    ProxyPass / http://127.0.0.1:8000/
    ProxyPassReverse / http://127.0.0.1:8000/
</VirtualHost>
```

Enable modules and site:
```bash
sudo a2enmod proxy proxy_http ssl
sudo a2ensite chemman
sudo systemctl restart apache2
```

---

## SSL/TLS Configuration

### Option 1: Let's Encrypt (Free, Linux only)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Auto-renewal (already enabled by certbot)
sudo systemctl status certbot.timer
```

### Option 2: Commercial Certificate

1. Purchase SSL certificate from a CA (Comodo, DigiCert, etc.)
2. Generate CSR: `openssl req -new -newkey rsa:2048 -nodes -keyout your-domain.key -out your-domain.csr`
3. Submit CSR to CA, receive certificate
4. Install certificate in nginx/Apache configuration (see above)

---

## Backup Strategy

### 1. Database Backups

Create `/opt/chemman/backup_db.sh`:

```bash
#!/bin/bash
# PostgreSQL backup script

BACKUP_DIR="/backups/chemman"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="chemman_prod"
DB_USER="chemman_user"

mkdir -p $BACKUP_DIR

# Create backup
PGPASSWORD="STRONG_PASSWORD_HERE" pg_dump -U $DB_USER -h localhost $DB_NAME | gzip > $BACKUP_DIR/chemman_$DATE.sql.gz

# Keep only last 30 days
find $BACKUP_DIR -name "chemman_*.sql.gz" -mtime +30 -delete

echo "Backup completed: chemman_$DATE.sql.gz"
```

Make executable and schedule:
```bash
chmod +x /opt/chemman/backup_db.sh

# Add to cron (daily at 2 AM)
sudo crontab -e
# Add line:
0 2 * * * /opt/chemman/backup_db.sh >> /var/log/chemman/backup.log 2>&1
```

### 2. Application Files Backup

```bash
#!/bin/bash
# Application files backup

BACKUP_DIR="/backups/chemman"
DATE=$(date +%Y%m%d)
APP_DIR="/opt/chemman"

tar -czf $BACKUP_DIR/chemman_files_$DATE.tar.gz $APP_DIR --exclude='venv' --exclude='__pycache__' --exclude='*.pyc'

# Keep only last 7 days
find $BACKUP_DIR -name "chemman_files_*.tar.gz" -mtime +7 -delete
```

### 3. Restore from Backup

```bash
# Restore database
gunzip -c /backups/chemman/chemman_20251022.sql.gz | PGPASSWORD="PASSWORD" psql -U chemman_user -h localhost chemman_prod

# Restore files
tar -xzf /backups/chemman/chemman_files_20251022.tar.gz -C /
```

---

## Monitoring & Maintenance

### 1. Log Monitoring

Application logs:
- **Location:** `/var/log/chemman/` (Linux) or `C:\chemman\logs\` (Windows)
- **Files:** `chem_man.log`, `access.log`, `error.log`

Monitor logs:
```bash
tail -f /var/log/chemman/chem_man.log
tail -f /var/log/chemman/error.log
```

### 2. Health Check Script

Create `health_check.py`:

```python
"""Health check script for Chem-Man application"""
import requests
import sys
from datetime import datetime

def check_health():
    try:
        # Check if app responds
        response = requests.get('http://localhost:8000/', timeout=5)
        if response.status_code in [200, 302]:  # 302 = redirect to login
            print(f"[{datetime.now()}] OK: Application is responding")
            return 0
        else:
            print(f"[{datetime.now()}] ERROR: Unexpected status code {response.status_code}")
            return 1
    except Exception as e:
        print(f"[{datetime.now()}] ERROR: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(check_health())
```

Schedule health checks:
```bash
# Add to cron (every 5 minutes)
*/5 * * * * /opt/chemman/venv/bin/python /opt/chemman/health_check.py >> /var/log/chemman/health.log 2>&1
```

### 3. Disk Space Monitoring

```bash
# Check disk space weekly
df -h | grep -E 'Filesystem|/$' | mail -s "Disk Space Report" admin@your-domain.com
```

### 4. Performance Monitoring

Install and configure:
- **PostgreSQL:** pg_stat_statements for query monitoring
- **nginx:** Monitor response times via access logs
- **Application:** Use Flask-Monitor or custom metrics

---

## Troubleshooting

### Application Won't Start

1. **Check logs:**
   ```bash
   tail -50 /var/log/chemman/error.log
   sudo journalctl -u chemman -n 50
   ```

2. **Verify database connection:**
   ```bash
   python -c "from app import create_app; from config import ProductionConfig; app = create_app(ProductionConfig); print('DB connection OK')"
   ```

3. **Check permissions:**
   ```bash
   ls -la /opt/chemman
   # Ensure chemman user owns files
   ```

### Database Connection Errors

1. **Verify PostgreSQL is running:**
   ```bash
   sudo systemctl status postgresql
   ```

2. **Check connection string in `.env`:**
   ```bash
   grep DATABASE_URL .env
   ```

3. **Test connection manually:**
   ```bash
   PGPASSWORD="PASSWORD" psql -U chemman_user -h localhost chemman_prod -c "SELECT version();"
   ```

### nginx/Apache Errors

1. **Check configuration:**
   ```bash
   sudo nginx -t
   # OR
   sudo apache2ctl configtest
   ```

2. **Check error logs:**
   ```bash
   tail -50 /var/log/nginx/error.log
   ```

3. **Verify proxy is working:**
   ```bash
   curl -I http://localhost:8000
   ```

### Import Failures

1. **Check Excel file permissions:**
   ```bash
   ls -la substancje_baza.xlsx svhc.xlsx
   ```

2. **Verify database tables exist:**
   ```bash
   python -c "from app import create_app; from models import db; from config import ProductionConfig; app = create_app(ProductionConfig); app.app_context().push(); print(db.engine.table_names())"
   ```

---

## Security Checklist

- [ ] PostgreSQL only accepts local connections
- [ ] Strong passwords for database user and admin account
- [ ] SECRET_KEY is random and kept secret
- [ ] HTTPS is enforced (HTTP redirects to HTTPS)
- [ ] SSL certificate is valid and up to date
- [ ] Security headers are configured in nginx
- [ ] File permissions are restrictive (600 for .env, 644 for code)
- [ ] Application runs as non-root user (Linux)
- [ ] Database backups are configured and tested
- [ ] Logs are monitored regularly
- [ ] Rate limiting is enabled
- [ ] Firewall rules are configured (only 80/443 open)

---

## Maintenance Schedule

### Daily
- Monitor logs for errors
- Check disk space

### Weekly
- Review access logs
- Check backup integrity
- Update system packages

### Monthly
- Update Python dependencies (`pip list --outdated`)
- Review user accounts
- Test restore from backup

### Quarterly
- Security audit
- Performance review
- Update SSL certificates (if not auto-renewed)

---

## Support & Updates

### Updating the Application

```bash
# Stop application
sudo systemctl stop chemman  # Linux
nssm stop ChemMan  # Windows

# Backup current version
cd /opt/chemman
tar -czf ../chemman_backup_$(date +%Y%m%d).tar.gz .

# Pull/copy new code
git pull  # if using git

# Update dependencies
source venv/bin/activate
pip install -r requirements.txt --upgrade

# Run migrations (if any)
# python migrate.py

# Restart application
sudo systemctl start chemman  # Linux
nssm start ChemMan  # Windows
```

### Getting Help

- **Application logs:** `/var/log/chemman/chem_man.log`
- **PostgreSQL logs:** `/var/log/postgresql/`
- **nginx logs:** `/var/log/nginx/`

---

## Production Checklist

Before going live, verify:

- [ ] Database is PostgreSQL (not SQLite)
- [ ] 4400 CLP substances imported
- [ ] 492 SVHC substances imported
- [ ] Admin user created
- [ ] HTTPS is working
- [ ] Backups are configured
- [ ] Logs are being written
- [ ] Health checks are scheduled
- [ ] All tests passing (`pytest tests/`)
- [ ] Application accessible via domain name
- [ ] Login works with admin credentials
- [ ] Search functionality works
- [ ] Export functionality works
- [ ] SDS file upload works

---

**End of Deployment Guide**

For questions or issues, review logs and consult this guide's troubleshooting section.
