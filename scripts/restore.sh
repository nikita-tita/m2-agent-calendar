#!/bin/bash

# RealEstate Calendar Bot Restore Script
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKUP_DIR="./backups"
LOG_FILE="./restore.log"

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

# Check arguments
if [ $# -eq 0 ]; then
    echo "Usage: $0 <backup_file>"
    echo "Available backups:"
    ls -la "$BACKUP_DIR"/*.tar.gz 2>/dev/null || echo "No backup files found"
    exit 1
fi

BACKUP_FILE="$1"

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    error "Backup file not found: $BACKUP_FILE"
fi

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   error "This script should not be run as root"
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    error "Docker is not running"
fi

# Start restore
log "Starting restore process from: $BACKUP_FILE"

# 1. Create temporary directory
TEMP_DIR=$(mktemp -d)
log "Created temporary directory: $TEMP_DIR"

# 2. Extract backup
log "Extracting backup file..."
tar -xzf "$BACKUP_FILE" -C "$TEMP_DIR" || error "Failed to extract backup"

# 3. Stop services
log "Stopping services..."
docker-compose down || warning "Failed to stop some services"

# 4. Restore database
log "Restoring database..."
DB_FILE=$(find "$TEMP_DIR" -name "database_*.sql" | head -1)
if [ -n "$DB_FILE" ]; then
    docker-compose up -d postgres
    sleep 10
    docker-compose exec -T postgres psql -U postgres -d realestate_bot -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;" || warning "Failed to clear database"
    docker-compose exec -T postgres psql -U postgres realestate_bot < "$DB_FILE" || error "Failed to restore database"
    success "Database restored from: $(basename "$DB_FILE")"
else
    warning "No database backup found"
fi

# 5. Restore Redis
log "Restoring Redis..."
REDIS_FILE=$(find "$TEMP_DIR" -name "redis_*.rdb" | head -1)
if [ -n "$REDIS_FILE" ]; then
    docker-compose up -d redis
    sleep 5
    docker cp "$REDIS_FILE" realestate_redis:/data/dump.rdb || warning "Failed to restore Redis"
    docker-compose restart redis
    success "Redis restored from: $(basename "$REDIS_FILE")"
else
    warning "No Redis backup found"
fi

# 6. Restore configuration
log "Restoring configuration..."
CONFIG_FILE=$(find "$TEMP_DIR" -name "config_*.tar.gz" | head -1)
if [ -n "$CONFIG_FILE" ]; then
    tar -xzf "$CONFIG_FILE" -C . || warning "Failed to restore configuration"
    success "Configuration restored from: $(basename "$CONFIG_FILE")"
else
    warning "No configuration backup found"
fi

# 7. Restore application data
log "Restoring application data..."
APP_DATA_FILE=$(find "$TEMP_DIR" -name "app_data_*.tar.gz" | head -1)
if [ -n "$APP_DATA_FILE" ]; then
    tar -xzf "$APP_DATA_FILE" -C . || warning "Failed to restore application data"
    success "Application data restored from: $(basename "$APP_DATA_FILE")"
else
    warning "No application data backup found"
fi

# 8. Start services
log "Starting services..."
docker-compose up -d || error "Failed to start services"

# 9. Wait for services to be healthy
log "Waiting for services to be healthy..."
sleep 30

# 10. Run migrations
log "Running database migrations..."
docker-compose exec -T api alembic upgrade head || warning "Failed to run migrations"

# 11. Health checks
log "Performing health checks..."

# Check API
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    success "API is healthy"
else
    error "API health check failed"
fi

# Check PostgreSQL
if docker-compose exec -T postgres pg_isready -U postgres > /dev/null 2>&1; then
    success "PostgreSQL is healthy"
else
    error "PostgreSQL health check failed"
fi

# Check Redis
if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    success "Redis is healthy"
else
    error "Redis health check failed"
fi

# 12. Cleanup
log "Cleaning up temporary files..."
rm -rf "$TEMP_DIR"

# 13. Show restore info
log "Restore completed successfully!"
echo ""
echo "Services are available at:"
echo "  - API: http://localhost:8000"
echo "  - API Docs: http://localhost:8000/docs"
echo ""
echo "To view logs:"
echo "  docker-compose logs -f"
echo ""
echo "To stop services:"
echo "  docker-compose down"
echo ""

success "Restore process completed successfully!" 