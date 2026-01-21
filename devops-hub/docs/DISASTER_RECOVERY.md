# Disaster Recovery Guide

> **Last Updated:** 2026-01-12
> **Version:** 1.0.0

This guide covers backup procedures, recovery scenarios, and disaster recovery planning for DevOps Hub.

---

## Table of Contents

1. [Overview](#overview)
2. [Backup Strategy](#backup-strategy)
3. [Recovery Procedures](#recovery-procedures)
4. [Disaster Scenarios](#disaster-scenarios)
5. [Automated Backups](#automated-backups)
6. [Testing Recovery](#testing-recovery)
7. [Checklist](#checklist)

---

## Overview

### Critical Components

| Component | Data Type | Recovery Priority | RTO | RPO |
|-----------|-----------|-------------------|-----|-----|
| SQLite Database | Agents, workflows, API keys | Critical | 15 min | 1 hour |
| Configuration | Docker, K8s, nginx configs | High | 30 min | 24 hours |
| Application Code | Git repository | Medium | 1 hour | N/A |
| Logs | Operational data | Low | N/A | N/A |

**RTO** = Recovery Time Objective (how quickly we need to recover)
**RPO** = Recovery Point Objective (how much data loss is acceptable)

### Backup Location Recommendations

| Environment | Primary | Secondary |
|-------------|---------|-----------|
| Development | Local `./backups/` | None |
| Staging | S3 bucket | Local |
| Production | S3 bucket (versioned) | Cross-region S3 |

---

## Backup Strategy

### Using the Backup Script

```bash
# Full backup (database + config)
./scripts/backup.sh

# Database only
./scripts/backup.sh --db-only

# Config only
./scripts/backup.sh --config-only

# Backup and upload to S3
./scripts/backup.sh --to s3://your-bucket/backups/

# Using Makefile
make backup
```

### What Gets Backed Up

| Item | Included | Notes |
|------|----------|-------|
| SQLite database | ✅ | Binary + SQL dump |
| Database statistics | ✅ | Row counts for verification |
| API key metadata | ✅ | IDs, names, scopes (not hashes) |
| Docker Compose files | ✅ | docker-compose*.yml |
| Kubernetes manifests | ✅ | All k8s/*.yaml files |
| Nginx configuration | ✅ | frontend/nginx.conf |
| Environment variables | ⚠️ | Structure only, not secrets |
| Application code | ❌ | Use git for this |
| Logs | ❌ | Use log aggregation |

### Backup Retention

Default retention: **30 days**

Configure with:
```bash
export BACKUP_RETAIN=60  # Keep 60 days
./scripts/backup.sh
```

---

## Recovery Procedures

### Standard Recovery

```bash
# List available backups
ls -la backups/

# Restore from local backup
./scripts/restore.sh backups/devops_hub_backup_20260112_120000.tar.gz

# Restore from S3
./scripts/restore.sh --from-s3 s3://bucket/backups/devops_hub_backup_20260112.tar.gz

# Dry run (see what would be restored)
./scripts/restore.sh --dry-run backups/devops_hub_backup_20260112_120000.tar.gz
```

### Recovery Steps

1. **Stop the application**
   ```bash
   docker-compose down
   # or
   kubectl scale deployment backend --replicas=0 -n devops-hub
   ```

2. **Restore from backup**
   ```bash
   ./scripts/restore.sh <backup_file>
   ```

3. **Verify database integrity**
   ```bash
   sqlite3 data/devops_hub.db "PRAGMA integrity_check;"
   ```

4. **Recreate .env file** (not restored for security)
   ```bash
   cp .env.example .env
   # Edit with correct values
   ```

5. **Restart application**
   ```bash
   docker-compose up -d
   # or
   kubectl scale deployment backend --replicas=2 -n devops-hub
   ```

6. **Verify functionality**
   ```bash
   curl http://localhost:8100/health
   curl http://localhost:8100/api/agents
   ```

### API Key Recovery

API keys are hashed in the database and **cannot be recovered**. If keys are lost:

1. Check `api_keys_metadata.csv` in backup for key names/IDs
2. Generate new keys for affected services:
   ```bash
   # Via API (requires admin key)
   curl -X POST http://localhost:8100/api/keys \
     -H "Authorization: Bearer $ADMIN_KEY" \
     -H "Content-Type: application/json" \
     -d '{"name": "service-name", "scopes": ["read", "write"]}'
   ```
3. Update client applications with new keys

---

## Disaster Scenarios

### Scenario 1: Database Corruption

**Symptoms:** Application errors, integrity check failures, unexpected behavior

**Recovery:**
```bash
# 1. Stop application
docker-compose down

# 2. Check integrity
sqlite3 data/devops_hub.db "PRAGMA integrity_check;"

# 3. If corrupted, restore from backup
./scripts/restore.sh --db-only <latest_backup>

# 4. Restart
docker-compose up -d
```

### Scenario 2: Accidental Data Deletion

**Recovery:**
```bash
# 1. Stop application immediately to prevent further changes
docker-compose down

# 2. Restore database from most recent backup
./scripts/restore.sh --db-only <backup_file>

# 3. If backup is too old, check for SQL dump
sqlite3 data/devops_hub.db < backup/devops_hub.sql

# 4. Restart
docker-compose up -d
```

### Scenario 3: Server/VM Failure

**Recovery:**
```bash
# 1. Provision new server with same specs

# 2. Install prerequisites
apt-get update && apt-get install -y docker.io docker-compose

# 3. Clone repository
git clone https://github.com/your-org/devops-hub.git
cd devops-hub

# 4. Download backup from S3
./scripts/restore.sh --from-s3 s3://bucket/backups/latest.tar.gz

# 5. Create .env file
cp .env.example .env
# Edit with production values

# 6. Start application
docker-compose -f docker-compose.prod.yml up -d
```

### Scenario 4: Kubernetes Cluster Failure

**Recovery:**
```bash
# 1. Provision new cluster or use backup cluster

# 2. Restore secrets
kubectl create secret generic devops-hub-secrets \
  --from-literal=secret-key=$(cat /secure/secret-key) \
  -n devops-hub

# 3. Apply manifests
kubectl apply -f k8s/ -n devops-hub

# 4. Restore database from S3
kubectl exec -it deployment/backend -n devops-hub -- \
  ./scripts/restore.sh --from-s3 s3://bucket/backups/latest.tar.gz

# 5. Verify
kubectl get pods -n devops-hub
kubectl logs deployment/backend -n devops-hub
```

### Scenario 5: Security Breach / Compromised Keys

**Recovery:**
```bash
# 1. Rotate all API keys immediately
# Delete compromised keys
sqlite3 data/devops_hub.db "UPDATE api_keys SET is_active = 0;"

# 2. Generate new admin key (restart application)
docker-compose restart backend

# 3. Save new bootstrap key and regenerate service keys

# 4. Update all client applications with new keys

# 5. Review audit logs for unauthorized access
sqlite3 data/devops_hub.db \
  "SELECT * FROM events WHERE type LIKE '%auth%' ORDER BY timestamp DESC LIMIT 100;"

# 6. Consider restoring from pre-breach backup if data was modified
```

---

## Automated Backups

### Cron Job Setup

```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * /path/to/devops-hub/scripts/backup.sh --to s3://bucket/backups/ >> /var/log/devops-hub-backup.log 2>&1

# Add weekly full backup on Sundays
0 3 * * 0 /path/to/devops-hub/scripts/backup.sh --to s3://bucket/backups/weekly/ >> /var/log/devops-hub-backup.log 2>&1
```

### Kubernetes CronJob

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: devops-hub-backup
  namespace: devops-hub
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: devops-hub-backend:latest
            command: ["/app/scripts/backup.sh"]
            args: ["--to", "s3://bucket/backups/"]
            env:
            - name: AWS_ACCESS_KEY_ID
              valueFrom:
                secretKeyRef:
                  name: aws-credentials
                  key: access-key-id
            - name: AWS_SECRET_ACCESS_KEY
              valueFrom:
                secretKeyRef:
                  name: aws-credentials
                  key: secret-access-key
            volumeMounts:
            - name: data
              mountPath: /app/data
          restartPolicy: OnFailure
          volumes:
          - name: data
            persistentVolumeClaim:
              claimName: devops-hub-data
```

### Backup Monitoring

Add to your monitoring:

```yaml
# Prometheus alert rule
- alert: BackupMissing
  expr: time() - devops_hub_last_backup_timestamp > 86400
  for: 1h
  labels:
    severity: warning
  annotations:
    summary: "No backup in 24 hours"
```

---

## Testing Recovery

### Monthly Recovery Test

1. **Create test environment**
   ```bash
   docker-compose -f docker-compose.test.yml up -d
   ```

2. **Restore to test environment**
   ```bash
   DATABASE_PATH=./data/test_restore.db ./scripts/restore.sh <latest_backup>
   ```

3. **Verify data integrity**
   ```bash
   sqlite3 data/test_restore.db "PRAGMA integrity_check;"
   sqlite3 data/test_restore.db "SELECT COUNT(*) FROM agents;"
   ```

4. **Test application functionality**
   ```bash
   curl http://localhost:8101/health
   curl http://localhost:8101/api/agents
   ```

5. **Document results**
   - Recovery time
   - Any issues encountered
   - Data completeness

### Recovery Test Checklist

- [ ] Backup file downloads successfully
- [ ] Checksum verification passes
- [ ] Database restores without errors
- [ ] Application starts successfully
- [ ] Health checks pass
- [ ] Agent count matches backup stats
- [ ] API endpoints respond correctly
- [ ] WebSocket connections work

---

## Checklist

### Before Disaster Strikes

- [ ] Automated backups configured
- [ ] Backups uploading to off-site storage (S3)
- [ ] Backup monitoring/alerting set up
- [ ] Recovery procedures documented
- [ ] Recovery tested within last 30 days
- [ ] Team trained on recovery procedures
- [ ] .env file stored securely (password manager, secrets vault)
- [ ] Bootstrap API key stored securely

### During Recovery

- [ ] Incident documented (time, cause, impact)
- [ ] Stakeholders notified
- [ ] Most recent backup identified
- [ ] Backup integrity verified
- [ ] Application stopped
- [ ] Data restored
- [ ] Configuration verified
- [ ] Application restarted
- [ ] Functionality verified
- [ ] Users notified of resolution

### After Recovery

- [ ] Root cause analysis completed
- [ ] Preventive measures identified
- [ ] Documentation updated
- [ ] Recovery procedure improvements noted
- [ ] Fresh backup taken after recovery

---

## Quick Reference

```bash
# Create backup
./scripts/backup.sh

# Create backup and upload to S3
./scripts/backup.sh --to s3://bucket/backups/

# Restore from backup
./scripts/restore.sh <backup_file>

# Restore from S3
./scripts/restore.sh --from-s3 s3://bucket/backups/backup.tar.gz

# Dry run restore
./scripts/restore.sh --dry-run <backup_file>

# Check database integrity
sqlite3 data/devops_hub.db "PRAGMA integrity_check;"

# List backups
ls -la backups/*.tar.gz
```

---

## Related Documentation

- [DEPLOYMENT.md](./DEPLOYMENT.md) - Deployment procedures
- [DATABASE_MIGRATION.md](./DATABASE_MIGRATION.md) - Database migration guide
- [../PRODUCTION_ROADMAP.md](../PRODUCTION_ROADMAP.md) - Project roadmap
