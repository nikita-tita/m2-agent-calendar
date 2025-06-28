#!/bin/bash

# RealEstate Calendar Bot Backup Script
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="realestate_bot"
BACKUP_DIR="./backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="${PROJECT_NAME}_backup_${DATE}"
LOG_FILE="./backup.log"

# Functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}✓${NC} $1" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}⚠${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}✗${NC} $1" | tee -a "$LOG_FILE"
    exit 1
}

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Start backup
log "Starting backup process..."

# 1. Database backup
log "Creating database backup..."
if docker-compose ps postgres | grep -q "Up"; then
    docker-compose exec -T postgres pg_dump -U postgres realestate_bot > "$BACKUP_DIR/database_${DATE}.sql"
    success "Database backup created: database_${DATE}.sql"
else
    warning "PostgreSQL is not running, skipping database backup"
fi

# 2. Redis backup
log "Creating Redis backup..."
if docker-compose ps redis | grep -q "Up"; then
    docker-compose exec -T redis redis-cli BGSAVE
    sleep 5
    docker cp realestate_redis:/data/dump.rdb "$BACKUP_DIR/redis_${DATE}.rdb"
    success "Redis backup created: redis_${DATE}.rdb"
else
    warning "Redis is not running, skipping Redis backup"
fi

# 3. Configuration files backup
log "Creating configuration backup..."
tar -czf "$BACKUP_DIR/config_${DATE}.tar.gz" \
    .env \
    docker-compose.yml \
    docker-compose.prod.yml \
    docker/ \
    alembic.ini \
    requirements.txt \
    pyproject.toml \
    --exclude='*.pyc' \
    --exclude='__pycache__' \
    --exclude='.git' \
    --exclude='temp' \
    --exclude='backups' \
    --exclude='logs' \
    2>/dev/null || warning "Some files could not be backed up"
success "Configuration backup created: config_${DATE}.tar.gz"

# 4. Application data backup
log "Creating application data backup..."
if [ -d "temp" ]; then
    tar -czf "$BACKUP_DIR/app_data_${DATE}.tar.gz" temp/ 2>/dev/null || warning "Application data backup failed"
    success "Application data backup created: app_data_${DATE}.tar.gz"
else
    warning "No application data directory found"
fi

# 5. Create backup manifest
log "Creating backup manifest..."
cat > "$BACKUP_DIR/manifest_${DATE}.txt" << EOF
RealEstate Calendar Bot Backup Manifest
Generated: $(date)
Backup ID: ${DATE}

Files included:
- database_${DATE}.sql (Database dump)
- redis_${DATE}.rdb (Redis dump)
- config_${DATE}.tar.gz (Configuration files)
- app_data_${DATE}.tar.gz (Application data)

System Information:
- Docker version: $(docker --version)
- Docker Compose version: $(docker-compose --version)
- Project directory: $(pwd)

Services status:
$(docker-compose ps 2>/dev/null || echo "Docker Compose not available")

Backup size:
$(du -sh "$BACKUP_DIR"/*_${DATE}.* 2>/dev/null || echo "Size calculation failed")
EOF

success "Backup manifest created: manifest_${DATE}.txt"

# 6. Compress all backups
log "Compressing backup files..."
tar -czf "$BACKUP_DIR/${BACKUP_NAME}.tar.gz" \
    -C "$BACKUP_DIR" \
    database_${DATE}.sql \
    redis_${DATE}.rdb \
    config_${DATE}.tar.gz \
    app_data_${DATE}.tar.gz \
    manifest_${DATE}.txt \
    2>/dev/null || warning "Some files could not be compressed"

success "Complete backup created: ${BACKUP_NAME}.tar.gz"

# 7. Cleanup old backups (keep last 7 days)
log "Cleaning up old backups..."
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +7 -delete 2>/dev/null || warning "Failed to cleanup old backups"

# 8. Show backup summary
log "Backup completed successfully!"
echo ""
echo "Backup files created:"
ls -la "$BACKUP_DIR"/*_${DATE}.* 2>/dev/null || echo "No backup files found"
echo ""
echo "Total backup size:"
du -sh "$BACKUP_DIR" 2>/dev/null || echo "Size calculation failed"
echo ""
echo "To restore from backup:"
echo "  1. Extract the backup: tar -xzf ${BACKUP_NAME}.tar.gz"
echo "  2. Restore database: docker-compose exec -T postgres psql -U postgres realestate_bot < database_${DATE}.sql"
echo "  3. Restore Redis: docker cp redis_${DATE}.rdb realestate_redis:/data/dump.rdb"
echo "  4. Restore config: tar -xzf config_${DATE}.tar.gz"
echo ""

success "Backup process completed successfully!" 