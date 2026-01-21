#!/bin/bash
#
# DevOps Hub - Restore Script
# Restores from a backup created by backup.sh
#
# Usage:
#   ./scripts/restore.sh <backup_file>
#   ./scripts/restore.sh backups/devops_hub_backup_20260112_120000.tar.gz
#   ./scripts/restore.sh --from-s3 s3://bucket/path/backup.tar.gz
#
# Options:
#   --db-only       Restore only the database
#   --config-only   Restore only config files
#   --dry-run       Show what would be restored without making changes
#   --force         Skip confirmation prompts
#

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DATABASE_PATH="${DATABASE_PATH:-$PROJECT_ROOT/data/devops_hub.db}"
TEMP_DIR=$(mktemp -d)

# Flags
DB_ONLY=false
CONFIG_ONLY=false
DRY_RUN=false
FORCE=false
FROM_S3=""
BACKUP_FILE=""

# Cleanup on exit
cleanup() {
    rm -rf "$TEMP_DIR"
}
trap cleanup EXIT

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
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --force)
            FORCE=true
            shift
            ;;
        --from-s3)
            FROM_S3="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [options] <backup_file>"
            echo ""
            echo "Options:"
            echo "  --db-only       Restore only the database"
            echo "  --config-only   Restore only config files"
            echo "  --dry-run       Show what would be restored"
            echo "  --force         Skip confirmation prompts"
            echo "  --from-s3 URL   Download backup from S3 first"
            exit 0
            ;;
        *)
            BACKUP_FILE="$1"
            shift
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

download_from_s3() {
    if [[ -z "$FROM_S3" ]]; then
        return 0
    fi

    log_info "Downloading backup from S3: $FROM_S3"

    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI not found. Install it to enable S3 downloads."
        exit 1
    fi

    BACKUP_FILE="$TEMP_DIR/backup.tar.gz"
    aws s3 cp "$FROM_S3" "$BACKUP_FILE"
    log_success "Downloaded from S3"
}

validate_backup() {
    if [[ -z "$BACKUP_FILE" ]]; then
        log_error "No backup file specified"
        echo "Usage: $0 <backup_file>"
        exit 1
    fi

    if [[ ! -f "$BACKUP_FILE" ]]; then
        log_error "Backup file not found: $BACKUP_FILE"
        exit 1
    fi

    log_info "Validating backup: $BACKUP_FILE"

    # Extract to temp directory
    tar -xzf "$BACKUP_FILE" -C "$TEMP_DIR"

    # Find the backup directory
    BACKUP_DIR=$(find "$TEMP_DIR" -maxdepth 1 -type d -name "devops_hub_backup_*" | head -1)

    if [[ -z "$BACKUP_DIR" ]]; then
        log_error "Invalid backup format - no backup directory found"
        exit 1
    fi

    # Verify checksums if available
    if [[ -f "$BACKUP_DIR/checksums.sha256" ]]; then
        log_info "Verifying checksums..."
        cd "$BACKUP_DIR"
        if sha256sum -c checksums.sha256 > /dev/null 2>&1; then
            log_success "Checksums verified"
        else
            log_error "Checksum verification failed!"
            exit 1
        fi
        cd - > /dev/null
    fi

    # Show manifest
    if [[ -f "$BACKUP_DIR/MANIFEST.json" ]]; then
        log_info "Backup manifest:"
        cat "$BACKUP_DIR/MANIFEST.json"
        echo ""
    fi

    # Show database stats
    if [[ -f "$BACKUP_DIR/db_stats.txt" ]]; then
        log_info "Database statistics:"
        cat "$BACKUP_DIR/db_stats.txt"
        echo ""
    fi
}

confirm_restore() {
    if [[ "$FORCE" == "true" ]] || [[ "$DRY_RUN" == "true" ]]; then
        return 0
    fi

    echo ""
    log_warn "This will overwrite existing data!"
    read -p "Are you sure you want to restore? [y/N] " -n 1 -r
    echo ""

    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Restore cancelled"
        exit 0
    fi
}

restore_database() {
    if [[ "$CONFIG_ONLY" == "true" ]]; then
        return 0
    fi

    log_info "Restoring database..."

    DB_BACKUP="$BACKUP_DIR/devops_hub.db"

    if [[ ! -f "$DB_BACKUP" ]]; then
        log_warn "Database backup not found - skipping"
        return 0
    fi

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY-RUN] Would restore database to: $DATABASE_PATH"
        return 0
    fi

    # Create backup of current database
    if [[ -f "$DATABASE_PATH" ]]; then
        CURRENT_BACKUP="${DATABASE_PATH}.pre_restore_$(date +%Y%m%d_%H%M%S)"
        cp "$DATABASE_PATH" "$CURRENT_BACKUP"
        log_info "Current database backed up to: $CURRENT_BACKUP"
    fi

    # Ensure directory exists
    mkdir -p "$(dirname "$DATABASE_PATH")"

    # Restore database
    cp "$DB_BACKUP" "$DATABASE_PATH"

    log_success "Database restored"
}

restore_config() {
    if [[ "$DB_ONLY" == "true" ]]; then
        return 0
    fi

    log_info "Restoring configuration..."

    CONFIG_BACKUP="$BACKUP_DIR/config"

    if [[ ! -d "$CONFIG_BACKUP" ]]; then
        log_warn "Config backup not found - skipping"
        return 0
    fi

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY-RUN] Would restore config files:"
        find "$CONFIG_BACKUP" -type f | while read f; do
            echo "  - $(basename "$f")"
        done
        return 0
    fi

    # Restore docker-compose files
    [[ -f "$CONFIG_BACKUP/docker-compose.yml" ]] && cp "$CONFIG_BACKUP/docker-compose.yml" "$PROJECT_ROOT/"
    [[ -f "$CONFIG_BACKUP/docker-compose.prod.yml" ]] && cp "$CONFIG_BACKUP/docker-compose.prod.yml" "$PROJECT_ROOT/"

    # Restore Kubernetes configs
    if [[ -d "$CONFIG_BACKUP/k8s" ]]; then
        mkdir -p "$PROJECT_ROOT/k8s"
        cp -r "$CONFIG_BACKUP/k8s/"* "$PROJECT_ROOT/k8s/"
    fi

    # Restore nginx config
    if [[ -f "$CONFIG_BACKUP/nginx.conf" ]]; then
        mkdir -p "$PROJECT_ROOT/frontend"
        cp "$CONFIG_BACKUP/nginx.conf" "$PROJECT_ROOT/frontend/"
    fi

    log_success "Configuration restored"
    log_warn "Note: .env file was NOT restored for security. Recreate it manually."
}

show_api_keys_info() {
    if [[ "$CONFIG_ONLY" == "true" ]]; then
        return 0
    fi

    API_KEYS_BACKUP="$BACKUP_DIR/api_keys_metadata.csv"

    if [[ -f "$API_KEYS_BACKUP" ]]; then
        echo ""
        log_info "API Keys in backup (metadata only):"
        cat "$API_KEYS_BACKUP"
        echo ""
        log_warn "Note: API key hashes were restored. The original key values cannot be recovered."
        log_warn "You may need to regenerate API keys for affected services."
    fi
}

# Main execution
main() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  DevOps Hub Restore${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""

    download_from_s3
    validate_backup
    confirm_restore
    restore_database
    restore_config
    show_api_keys_info

    if [[ "$DRY_RUN" == "true" ]]; then
        echo ""
        log_info "Dry run complete - no changes made"
    else
        echo ""
        echo -e "${GREEN}========================================${NC}"
        echo -e "${GREEN}  Restore Complete!${NC}"
        echo -e "${GREEN}========================================${NC}"
        echo ""
        log_info "Next steps:"
        echo "  1. Verify the application starts correctly"
        echo "  2. Check database connectivity"
        echo "  3. Regenerate API keys if needed"
        echo "  4. Update .env file with correct values"
    fi
}

main "$@"
