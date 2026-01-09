#!/bin/bash
# DevOps Hub Deployment Script
# Usage: ./scripts/deploy.sh [dev|prod|docker]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
MODE="${1:-dev}"

cd "$PROJECT_ROOT"

echo "============================================"
echo "DevOps Hub - Agent Library Service"
echo "Deployment Mode: $MODE"
echo "============================================"
echo ""

case "$MODE" in
    dev)
        echo "Starting in development mode..."
        echo ""

        # Check dependencies
        if ! command -v python3 &> /dev/null; then
            echo "Error: python3 is required"
            exit 1
        fi

        # Install dependencies
        echo "Installing dependencies..."
        pip install -r requirements.txt

        # Start with auto-reload
        echo ""
        echo "Starting service on http://localhost:8100"
        echo "API docs: http://localhost:8100/docs"
        echo ""
        python3 -m uvicorn service.api:app --host 0.0.0.0 --port 8100 --reload
        ;;

    prod)
        echo "Starting in production mode..."
        echo ""

        # Install dependencies
        pip install -r requirements.txt

        # Use gunicorn for production
        echo "Starting with Gunicorn..."
        gunicorn service.api:app \
            --bind 0.0.0.0:8100 \
            --workers 4 \
            --worker-class uvicorn.workers.UvicornWorker \
            --access-logfile - \
            --error-logfile - \
            --capture-output
        ;;

    docker)
        echo "Building and starting Docker containers..."
        echo ""

        docker-compose up --build -d

        echo ""
        echo "Containers started. Checking health..."
        sleep 5

        if curl -s http://localhost:8100/health | grep -q "healthy"; then
            echo "Service is healthy!"
        else
            echo "Warning: Service may not be ready yet"
        fi

        echo ""
        echo "View logs: docker-compose logs -f agent-library"
        ;;

    stop)
        echo "Stopping services..."
        docker-compose down
        pkill -f "uvicorn service.api" 2>/dev/null || true
        echo "Services stopped."
        ;;

    *)
        echo "Usage: $0 [dev|prod|docker|stop]"
        echo ""
        echo "  dev    - Start in development mode with auto-reload"
        echo "  prod   - Start in production mode with Gunicorn"
        echo "  docker - Build and start Docker containers"
        echo "  stop   - Stop all services"
        exit 1
        ;;
esac
