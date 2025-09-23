#!/bin/bash

# RUDE.AI Bot Monitoring Script
# Usage: ./scripts/monitor.sh [health|logs|metrics|status]

set -e

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}"
SERVICE_NAME="rudeai-bot"

function show_health() {
    echo "🏥 Health Check"
    echo "==============="

    # Check if service is running
    if docker-compose -f $COMPOSE_FILE ps $SERVICE_NAME | grep -q "Up"; then
        echo "✅ Service is running"

        # Try health endpoint
        if curl -s -f http://localhost:8000/health > /dev/null; then
            echo "✅ Health endpoint responding"
            curl -s http://localhost:8000/health | jq '.'
        else
            echo "❌ Health endpoint not responding"
        fi
    else
        echo "❌ Service is not running"
    fi

    echo ""
}

function show_logs() {
    echo "📋 Recent Logs"
    echo "=============="

    # Show last 50 lines of logs
    docker-compose -f $COMPOSE_FILE logs --tail=50 $SERVICE_NAME

    echo ""
    echo "📊 Log Summary (last 1000 lines):"
    echo "=================================="

    # Count different log levels
    logs=$(docker-compose -f $COMPOSE_FILE logs --tail=1000 $SERVICE_NAME 2>/dev/null || echo "")

    if [ -n "$logs" ]; then
        echo "INFO:     $(echo "$logs" | grep -c "INFO" || echo "0")"
        echo "WARNING:  $(echo "$logs" | grep -c "WARNING" || echo "0")"
        echo "ERROR:    $(echo "$logs" | grep -c "ERROR" || echo "0")"
        echo "CRITICAL: $(echo "$logs" | grep -c "CRITICAL" || echo "0")"
    else
        echo "No logs available"
    fi

    echo ""
}

function show_metrics() {
    echo "📈 Metrics"
    echo "=========="

    # Try metrics endpoint
    if curl -s -f http://localhost:8000/metrics > /dev/null; then
        echo "✅ Metrics endpoint responding"
        curl -s http://localhost:8000/metrics | jq '.'
    else
        echo "❌ Metrics endpoint not responding"
    fi

    echo ""
    echo "🐳 Docker Stats:"
    echo "================"

    # Show docker stats for our service
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}" | grep -E "(NAMES|$SERVICE_NAME)" || echo "Service not found"

    echo ""
}

function show_status() {
    echo "🤖 RUDE.AI Bot Status"
    echo "===================="
    echo "Timestamp: $(date)"
    echo ""

    show_health

    echo "🐳 Container Status"
    echo "=================="
    docker-compose -f $COMPOSE_FILE ps
    echo ""

    echo "💾 Disk Usage"
    echo "============="
    echo "Logs directory:"
    du -sh logs/ 2>/dev/null || echo "No logs directory"
    echo ""
    echo "Database size:"
    if [ -f "rudeai_bot.db" ]; then
        ls -lh rudeai_bot.db
    else
        echo "Database file not found"
    fi
    echo ""

    echo "🌐 Network Connectivity"
    echo "======================"

    # Test external connectivity
    if curl -s -m 5 https://api.openai.com > /dev/null; then
        echo "✅ OpenAI API reachable"
    else
        echo "❌ OpenAI API not reachable"
    fi

    if curl -s -m 5 https://api.telegram.org > /dev/null; then
        echo "✅ Telegram API reachable"
    else
        echo "❌ Telegram API not reachable"
    fi

    echo ""
}

function show_help() {
    echo "RUDE.AI Bot Monitoring Script"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  health   - Check service health"
    echo "  logs     - Show recent logs and log summary"
    echo "  metrics  - Show performance metrics"
    echo "  status   - Show comprehensive status (default)"
    echo "  help     - Show this help message"
    echo ""
    echo "Environment variables:"
    echo "  COMPOSE_FILE - Docker compose file to use (default: docker-compose.yml)"
    echo ""
}

# Main script logic
case "${1:-status}" in
    "health")
        show_health
        ;;
    "logs")
        show_logs
        ;;
    "metrics")
        show_metrics
        ;;
    "status")
        show_status
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    *)
        echo "Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac