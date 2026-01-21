#!/bin/bash
#
# DevOps Hub - Backup Script
# Creates timestamped backups of database and configuration
#
# Usage:
#   ./scripts/backup.sh              # Full backup
#   ./scripts/backup.sh --db-only    # Database only
#   ./scripts/backup.sh --config-only # Config files only
#   ./scripts/backup.sh --to s3://bucket/path  # Upload to S3
#
# Environment variables:
#   BACKUP_DIR      - Backup destination (default: ./backups)
#   BACKUP_RETAIN   - Days to retain backups (default: 30)
#   DATABASE_PATH   - Database path (default: ./data/devops_hub.db)
#   AWS_PROFILE     - AWS profile for S3 uploads (optional)
#

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="${BACKUP_DIR:-$PROJECT_ROOT/backups}"
BACKUP_RETAIN="${BACKUP_RETAIN:-30}"
DATABASE_PATH="${DATABASE_PATH:-$PROJECT_ROOT/data/devops_hub.db}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="devops_hub_backup_$TIMESTAMP"

# Flags
DB_ONLY=false
CONFIG_ONLY=false
S3_DEST=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --db-only)
            DB_ONLY=true
            shift
            ;;
        --config-only)
            CONFIG_ONLY=true
            shift
            ;;
        --to)
            S3_DEST="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [--db-only] [--config-only] [--to s3://bucket/path]"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

create_backup_dir() {
    mkdir -p "$BACKUP_DIR"
    mkdir -p "$BACKUP_DIR/$BACKUP_NAME"
}

backup_database() {
    log_info "Backing up database..."

    if [[ ! -f "$DATABASE_PATH" ]]; then
        log_warn "Database not found at $DATABASE_PATH - skipping"
        return 0
    fi

    # Create SQLite backup using .backup command (safe for live databases)
    sqlite3 "$DATABASE_PATH" ".backup '$BACKUP_DIR/$BACKUP_NAME/devops_hub.db'"

    # Also create a SQL dump for portability
    sqlite3 "$DATABASE_PATH" ".dump" > "$BACKUP_DIR/$BACKUP_NAME/devops_hub.sql"

    # Get row counts for verification
    echo "Database Statistics:" > "$BACKUP_DIR/$BACKUP_NAME/db_stats.txt"
    sqlite3 "$DATABASE_PATH" "SELECT 'agents: ' || COUNT(*) FROM agents;" >> "$BACKUP_DIR/$BACKUP_NAME/db_stats.txt"
    sqlite3 "$DATABASE_PATH" "SELECT 'workflows: ' || COUNT(*) FROM workflows;" >> "$BACKUP_DIR/$BACKUP_NAME/db_stats.txt"
    sqlite3 "$DATABASE_PATH" "SELECT 'api_keys: ' || COUNT(*) FROM api_keys;" >> "$BACKUP_DIR/$BACKUP_NAME/db_stats.txt"
    sqlite3 "$DATABASE_PATH" "SELECT 'events: ' || COUNT(*) FROM events;" >> "$BACKUP_DIR/$BACKUP_NAME/db_stats.txt"

    log_success "Database backed up"
}

backup_config() {
    log_info "Backing up configuration..."

    CONFIG_DIR="$BACKUP_DIR/$BACKUP_NAME/config"
    mkdir -p "$CONFIG_DIR"

    # Backup environment files (without secrets - just structure)
    if [[ -f "$PROJECT_ROOT/.env" ]]; then
        # Remove actual secret values, keep structure
        grep -v "SECRET\|PASSWORD\|KEY=" "$PROJECT_ROOT/.env" > "$CONFIG_DIR/env_structure.txt" 2>/dev/null || true
        log_info "Environment structure saved (secrets excluded)"
    fi

    # Backup .env.example if it exists
    [[ -f "$PROJECT_ROOT/.env.example" ]] && cp "$PROJECT_ROOT/.env.example" "$CONFIG_DIR/"

    # Backup Docker configs
    [[ -f "$PROJECT_ROOT/docker-compose.yml" ]] && cp "$PROJECT_ROOT/docker-compose.yml" "$CONFIG_DIR/"
    [[ -f "$PROJECT_ROOT/docker-compose.prod.yml" ]] && cp "$PROJECT_ROOT/docker-compose.prod.yml" "$CONFIG_DIR/"

    # Backup Kubernetes configs
    if [[ -d "$PROJECT_ROOT/k8s" ]]; then
        cp -r "$PROJECT_ROOT/k8s" "$CONFIG_DIR/"
    fi

    # Backup nginx config
    [[ -f "$PROJECT_ROOT/frontend/nginx.conf" ]] && cp "$PROJECT_ROOT/frontend/nginx.conf" "$CONFIG_DIR/"

    # Backup alembic config
    [[ -f "$PROJECT_ROOT/alembic.ini" ]] && cp "$PROJECT_ROOT/alembic.ini" "$CONFIG_DIR/"

    log_success "Configuration backed up"
}

backup_api_keys() {
    log_info "Backing up API keys (hashes only)..."

    if [[ ! -f "$DATABASE_PATH" ]]; then
        log_warn "Database not found - skipping API key backup"
        return 0
    fi

    # Export API keys (hashed, not actual keys) for recovery
    sqlite3 -header -csv "$DATABASE_PATH" \
        "SELECT id, name, scopes, is_active, created_at, expires_at FROM api_keys;" \
        > "$BACKUP_DIR/$BACKUP_NAME/api_keys_metadata.csv"

    log_success "API key metadata backed up (hashes excluded for security)"
}

create_manifest() {
    log_info "Creating backup manifest..."

    cat > "$BACKUP_DIR/$BACKUP_NAME/MANIFEST.json" << EOF
{
    "backup_name": "$BACKUP_NAME",
    "timestamp": "$(date -Iseconds)",
    "hostname": "$(hostname)",
    "database_path": "$DATABASE_PATH",
    "contents": {
        "database": $([[ "$CONFIG_ONLY" == "false" ]] && echo "true" || echo "false"),
        "config": $([[ "$DB_ONLY" == "false" ]] && echo "true" || echo "false"),
        "api_keys_metadata": $([[ "$CONFIG_ONLY" == "false" ]] && echo "true" || echo "false")
    },
    "checksums": {}
}
EOF

    # Add checksums
    if command -v sha256sum &> /dev/null; then
        cd "$BACKUP_DIR/$BACKUP_NAME"
        find . -type f ! -name "MANIFEST.json" -exec sha256sum {} \; > checksums.sha256
        log_info "Checksums generated"
    fi
}

compress_backup() {
    log_info "Compressing backup..."

    cd "$BACKUP_DIR"
    tar -czf "$BACKUP_NAME.tar.gz" "$BACKUP_NAME"
    rm -rf "$BACKUP_NAME"

    BACKUP_SIZE=$(du -h "$BACKUP_NAME.tar.gz" | cut -f1)
    log_success "Backup compressed: $BACKUP_NAME.tar.gz ($BACKUP_SIZE)"
}

upload_to_s3() {
    if [[ -z "$S3_DEST" ]]; then
        return 0
    fi

    log_info "Uploading to S3: $S3_DEST"

    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI not found. Install it to enable S3 uploads."
        return 1
    fi

    aws s3 cp "$BACKUP_DIR/$BACKUP_NAME.tar.gz" "$S3_DEST/$BACKUP_NAME.tar.gz"
    log_success "Uploaded to S3"
}

cleanup_old_backups() {
    log_info "Cleaning up backups older than $BACKUP_RETAIN days..."

    find "$BACKUP_DIR" -name "devops_hub_backup_*.tar.gz" -type f -mtime +$BACKUP_RETAIN -delete 2>/dev/null || true

    REMAINING=$(find "$BACKUP_DIR" -name "devops_hub_backup_*.tar.gz" -type f | wc -l)
    log_info "$REMAINING backup(s) retained"
}

# Main execution
main() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  DevOps Hub Backup${NC}"
    echo -e "${BLUE}  $TIMESTAMP${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""

    create_backup_dir

    if [[ "$CONFIG_ONLY" == "false" ]]; then
        backup_database
        backup_api_keys
    fi

    if [[ "$DB_ONLY" == "false" ]]; then
        backup_config
    fi

    create_manifest
    compress_backup
    upload_to_s3
    cleanup_old_backups

    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  Backup Complete!${NC}"
    echo -e "${GREEN}  Location: $BACKUP_DIR/$BACKUP_NAME.tar.gz${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
}

main "$@"
