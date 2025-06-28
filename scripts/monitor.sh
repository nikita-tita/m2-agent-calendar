#!/bin/bash

# RealEstate Calendar Bot Monitoring Script
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
LOG_FILE="./monitor.log"

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
}

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    error "Docker is not running"
    exit 1
fi

# Start monitoring
log "Starting system monitoring..."

echo ""
echo "=== System Status ==="

# 1. Docker services status
log "Checking Docker services status..."
if docker-compose ps | grep -q "Up"; then
    success "Docker services are running"
    docker-compose ps
else
    error "No Docker services are running"
fi

echo ""

# 2. API health check
log "Checking API health..."
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    success "API is healthy"
    
    # Get API response time
    RESPONSE_TIME=$(curl -w "%{time_total}" -o /dev/null -s http://localhost:8000/health)
    log "API response time: ${RESPONSE_TIME}s"
else
    error "API health check failed"
fi

echo ""

# 3. Database health check
log "Checking database health..."
if docker-compose exec -T postgres pg_isready -U postgres > /dev/null 2>&1; then
    success "PostgreSQL is healthy"
    
    # Get database size
    DB_SIZE=$(docker-compose exec -T postgres psql -U postgres -d realestate_bot -t -c "SELECT pg_size_pretty(pg_database_size('realestate_bot'));" | xargs)
    log "Database size: $DB_SIZE"
    
    # Get table counts
    TABLE_COUNTS=$(docker-compose exec -T postgres psql -U postgres -d realestate_bot -t -c "
        SELECT 
            schemaname,
            tablename,
            n_tup_ins as inserts,
            n_tup_upd as updates,
            n_tup_del as deletes
        FROM pg_stat_user_tables 
        ORDER BY n_tup_ins + n_tup_upd + n_tup_del DESC;
    " | head -10)
    log "Top tables by activity:"
    echo "$TABLE_COUNTS"
else
    error "PostgreSQL health check failed"
fi

echo ""

# 4. Redis health check
log "Checking Redis health..."
if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    success "Redis is healthy"
    
    # Get Redis info
    REDIS_INFO=$(docker-compose exec -T redis redis-cli info memory | grep -E "(used_memory|used_memory_peak|connected_clients)" | head -3)
    log "Redis memory usage:"
    echo "$REDIS_INFO"
else
    error "Redis health check failed"
fi

echo ""

# 5. Disk usage
log "Checking disk usage..."
DISK_USAGE=$(df -h . | tail -1)
log "Disk usage: $DISK_USAGE"

echo ""

# 6. Memory usage
log "Checking memory usage..."
MEMORY_USAGE=$(free -h | grep Mem)
log "Memory usage: $MEMORY_USAGE"

echo ""

# 7. Docker resource usage
log "Checking Docker resource usage..."
DOCKER_STATS=$(docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}")
log "Docker resource usage:"
echo "$DOCKER_STATS"

echo ""

# 8. Log analysis
log "Checking recent logs for errors..."
ERROR_LOGS=$(docker-compose logs --tail=100 2>&1 | grep -i error | tail -5)
if [ -n "$ERROR_LOGS" ]; then
    warning "Recent errors found:"
    echo "$ERROR_LOGS"
else
    success "No recent errors found"
fi

echo ""

# 9. Performance metrics
log "Checking performance metrics..."

# API response time trend
API_TIMES=$(for i in {1..5}; do curl -w "%{time_total}" -o /dev/null -s http://localhost:8000/health; echo; done | sort -n)
AVG_TIME=$(echo "$API_TIMES" | awk '{sum+=$1} END {print sum/NR}')
log "Average API response time: ${AVG_TIME}s"

# Database connection count
DB_CONNECTIONS=$(docker-compose exec -T postgres psql -U postgres -d realestate_bot -t -c "SELECT count(*) FROM pg_stat_activity WHERE datname = 'realestate_bot';" | xargs)
log "Active database connections: $DB_CONNECTIONS"

# Redis memory usage percentage
REDIS_MEMORY=$(docker-compose exec -T redis redis-cli info memory | grep used_memory_human | cut -d: -f2 | xargs)
log "Redis memory usage: $REDIS_MEMORY"

echo ""

# 10. Recommendations
log "Generating recommendations..."

# Check if disk usage is high
DISK_PERCENT=$(df . | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_PERCENT" -gt 80 ]; then
    warning "High disk usage detected (${DISK_PERCENT}%). Consider cleaning up old logs and backups."
fi

# Check if memory usage is high
MEMORY_PERCENT=$(free | grep Mem | awk '{printf("%.0f", $3/$2 * 100.0)}')
if [ "$MEMORY_PERCENT" -gt 80 ]; then
    warning "High memory usage detected (${MEMORY_PERCENT}%). Consider increasing memory or optimizing applications."
fi

# Check if API response time is slow
if (( $(echo "$AVG_TIME > 1.0" | bc -l) )); then
    warning "Slow API response time detected (${AVG_TIME}s). Consider optimizing database queries or increasing resources."
fi

# Check if database connections are high
if [ "$DB_CONNECTIONS" -gt 50 ]; then
    warning "High number of database connections ($DB_CONNECTIONS). Consider connection pooling optimization."
fi

echo ""

# 11. Summary
log "Monitoring completed!"
echo ""
echo "=== Summary ==="
echo "✓ System monitoring completed"
echo "✓ Health checks performed"
echo "✓ Performance metrics collected"
echo "✓ Recommendations generated"
echo ""
echo "For detailed monitoring, visit:"
echo "  - Grafana: http://localhost:3000"
echo "  - Prometheus: http://localhost:9090"
echo "  - API Docs: http://localhost:8000/docs"
echo ""

success "Monitoring process completed successfully!" 