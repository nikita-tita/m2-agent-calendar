#!/bin/bash

# RealEstate Calendar Bot Production Deployment Script
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
LOG_FILE="./deploy.log"

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

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   error "This script should not be run as root"
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    error "Docker is not running"
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null; then
    error "Docker Compose is not installed"
fi

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Start deployment
log "Starting production deployment..."

# 1. Backup current database
log "Creating database backup..."
if docker-compose ps postgres | grep -q "Up"; then
    docker-compose exec -T postgres pg_dump -U postgres realestate_bot > "$BACKUP_DIR/backup_$(date +%Y%m%d_%H%M%S).sql"
    success "Database backup created"
else
    warning "PostgreSQL is not running, skipping backup"
fi

# 2. Pull latest changes
log "Pulling latest changes..."
git pull origin main || error "Failed to pull latest changes"

# 3. Check for environment file
if [ ! -f ".env" ]; then
    error "Environment file .env not found. Please create it from env.example"
fi

# 4. Stop current services
log "Stopping current services..."
docker-compose down || warning "Failed to stop some services"

# 5. Build new images
log "Building new Docker images..."
docker-compose -f docker-compose.prod.yml build --no-cache || error "Failed to build images"

# 6. Start services
log "Starting services..."
docker-compose -f docker-compose.prod.yml up -d || error "Failed to start services"

# 7. Wait for services to be healthy
log "Waiting for services to be healthy..."
sleep 30

# 8. Run database migrations
log "Running database migrations..."
docker-compose -f docker-compose.prod.yml exec -T api alembic upgrade head || error "Failed to run migrations"

# 9. Initialize database if needed
log "Initializing database..."
docker-compose -f docker-compose.prod.yml exec -T api python scripts/init_db.py || warning "Database initialization failed or not needed"

# 10. Health checks
log "Performing health checks..."

# Check API
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    success "API is healthy"
else
    error "API health check failed"
fi

# Check PostgreSQL
if docker-compose -f docker-compose.prod.yml exec -T postgres pg_isready -U postgres > /dev/null 2>&1; then
    success "PostgreSQL is healthy"
else
    error "PostgreSQL health check failed"
fi

# Check Redis
if docker-compose -f docker-compose.prod.yml exec -T redis redis-cli ping > /dev/null 2>&1; then
    success "Redis is healthy"
else
    error "Redis health check failed"
fi

# 11. Check service status
log "Checking service status..."
docker-compose -f docker-compose.prod.yml ps

# 12. Cleanup old images
log "Cleaning up old Docker images..."
docker image prune -f

# 13. Show deployment info
log "Deployment completed successfully!"
echo ""
echo "Services are available at:"
echo "  - API: https://localhost"
echo "  - API Docs: https://localhost/docs"
echo "  - Grafana: http://localhost:3000 (admin/admin)"
echo "  - Prometheus: http://localhost:9090"
echo ""
echo "To view logs:"
echo "  docker-compose -f docker-compose.prod.yml logs -f"
echo ""
echo "To stop services:"
echo "  docker-compose -f docker-compose.prod.yml down"
echo ""

success "Production deployment completed successfully!" 