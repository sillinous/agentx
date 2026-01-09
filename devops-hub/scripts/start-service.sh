#!/bin/bash
# Start the Agent Library Service

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo "Starting Agent Library Service..."
echo "Project Root: $PROJECT_ROOT"
echo ""

# Check if uvicorn is installed
if ! command -v uvicorn &> /dev/null; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

# Start the service
echo "Starting service on http://localhost:8100"
echo "API docs: http://localhost:8100/docs"
echo ""

python -m uvicorn service.api:app --host 0.0.0.0 --port 8100 --reload
