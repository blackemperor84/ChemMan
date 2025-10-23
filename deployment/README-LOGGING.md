# ChemMan - Log Rotation Setup

This directory contains configuration files for log rotation in production environments.

## Overview

ChemMan uses a multi-layered approach to log rotation:

### 1. Application-Level Rotation (Python RotatingFileHandler)

**Automatic** - Already configured in `config.py`

- **Development**: Logs rotate at 5 MB, keeps 5 backups
  - Location: `logs/chem_man_dev.log`
  - Format: Includes filename and line numbers for debugging

- **Production**: Logs rotate at 10 MB, keeps 10 backups
  - Location: `logs/chem_man.log`
  - Format: Standard timestamp, level, and message

**How it works:**
- Python's `RotatingFileHandler` automatically creates new log files when size limit is reached
- Old logs are renamed: `chem_man.log.1`, `chem_man.log.2`, etc.
- Oldest logs are automatically deleted when backup count is exceeded

**Benefits:**
- Works on all operating systems (Windows, Linux, Mac)
- No external dependencies
- Prevents logs from growing forever

### 2. System-Level Rotation (Linux logrotate)

**For production Linux servers only**

The `logrotate-chemman` file provides system-level log rotation for Linux production deployments.

## Installation (Linux Production)

### Step 1: Copy the logrotate configuration

```bash
sudo cp deployment/logrotate-chemman /etc/logrotate.d/chemman
sudo chmod 644 /etc/logrotate.d/chemman
```

### Step 2: Verify the configuration

```bash
# Test configuration (dry run)
sudo logrotate -d /etc/logrotate.d/chemman

# Check for errors
sudo logrotate -v /etc/logrotate.d/chemman
```

### Step 3: Test rotation

```bash
# Force rotation (for testing)
sudo logrotate -f /etc/logrotate.d/chemman

# Check rotated files
ls -lh /var/www/chemman/logs/
```

## Log Rotation Schedule

- **Frequency**: Daily (runs at ~3 AM via cron)
- **Retention**: 30 days of logs
- **Compression**: Yes (gzip)
- **Delay Compression**: Yes (keeps today's rotated log uncompressed)

## Log File Locations

### Development (Windows/Local)
```
chemman/
├── logs/
│   ├── chem_man_dev.log          # Current log
│   ├── chem_man_dev.log.1        # Yesterday (most recent backup)
│   ├── chem_man_dev.log.2        # 2 days ago
│   └── ...
```

### Production (Linux Server)
```
/var/www/chemman/logs/
├── chem_man.log                   # Current log
├── chem_man.log-20231015.gz      # Oct 15 (compressed)
├── chem_man.log-20231014.gz      # Oct 14 (compressed)
└── ...

/var/log/chemman/
├── access.log                     # Gunicorn access log
├── error.log                      # Gunicorn error log
├── access.log-20231015.gz        # Rotated access logs
└── error.log-20231015.gz         # Rotated error logs
```

## Log Levels

Configure via `LOG_LEVEL` in `.env`:

- `DEBUG` - Detailed information for debugging (development only)
- `INFO` - General informational messages (default)
- `WARNING` - Warning messages (recommended for production)
- `ERROR` - Error messages only
- `CRITICAL` - Critical errors only

## Monitoring Log Files

### View current logs (Linux)
```bash
# Application logs
tail -f /var/www/chemman/logs/chem_man.log

# Gunicorn access logs
tail -f /var/log/chemman/access.log

# Gunicorn error logs
tail -f /var/log/chemman/error.log
```

### View current logs (Windows/Development)
```powershell
# PowerShell
Get-Content logs\chem_man_dev.log -Wait -Tail 50

# Or open in text editor
notepad logs\chem_man_dev.log
```

### Search logs
```bash
# Find errors from last 24 hours
grep "ERROR" /var/www/chemman/logs/chem_man.log

# Find specific user actions
grep "username" /var/www/chemman/logs/chem_man.log

# Search in compressed logs
zgrep "ERROR" /var/www/chemman/logs/chem_man.log-*.gz
```

## Disk Space Management

### Current Configuration

**Development:**
- Max size per log: 5 MB
- Backups kept: 5
- **Total max disk usage**: ~25 MB

**Production (Application):**
- Max size per log: 10 MB
- Backups kept: 10
- **Total max disk usage**: ~100 MB

**Production (System logrotate):**
- Rotation: Daily
- Retention: 30 days
- Compression: Yes (~10x reduction)
- **Estimated disk usage**: 50-200 MB (depends on activity)

### Adjusting Retention

**To keep more/fewer days** (edit `/etc/logrotate.d/chemman`):
```bash
rotate 30    # Change to desired number of days
```

**To change rotation frequency**:
```bash
daily       # Options: daily, weekly, monthly
```

## Troubleshooting

### Logs not rotating
1. Check if logrotate is installed: `which logrotate`
2. Check logrotate status: `sudo systemctl status logrotate`
3. Check for errors: `sudo cat /var/lib/logrotate/status`
4. Verify configuration: `sudo logrotate -d /etc/logrotate.d/chemman`

### Disk space issues
```bash
# Check log disk usage
du -h /var/www/chemman/logs/
du -h /var/log/chemman/

# Find large log files
find /var/www/chemman/logs/ -type f -size +50M

# Manually delete old logs (if needed)
sudo rm /var/www/chemman/logs/*.log.*.gz
```

### Application not writing to logs
1. Check log directory permissions: `ls -ld logs/`
2. Check log file permissions: `ls -l logs/`
3. Ensure directory exists: `mkdir -p logs/`
4. Check `LOG_LEVEL` in `.env`
5. Restart application: `sudo systemctl restart chemman`

## Best Practices

1. **Monitor disk space regularly** in production
2. **Set up alerts** for disk usage >80%
3. **Review logs periodically** for errors and warnings
4. **Archive important logs** before they expire (30 days)
5. **Test log rotation** after deployment
6. **Don't commit logs to git** (already in .gitignore)

## References

- Python RotatingFileHandler: https://docs.python.org/3/library/logging.handlers.html#rotatingfilehandler
- Linux logrotate: `man logrotate`
- Flask Logging: https://flask.palletsprojects.com/en/latest/logging/
