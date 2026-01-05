#!/bin/bash

# ===========================================
# SYNAPSE CORE - Setup Script (Unix/Linux/Mac)
# ===========================================

set -e

echo "🚀 Setting up Synapse Core..."
echo ""

# Color codes for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check prerequisites
echo -e "${BLUE}📋 Checking prerequisites...${NC}"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed. Please install Docker Desktop first.${NC}"
    echo "   Download from: https://www.docker.com/products/docker-desktop"
    exit 1
fi
echo -e "${GREEN}✓ Docker found${NC}"

# Check Docker Compose
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker Compose found${NC}"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo -e "${YELLOW}📝 Creating .env file from template...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✓ Created .env file${NC}"
    echo -e "${YELLOW}⚠️  Please edit .env and add your OPENAI_API_KEY${NC}"
else
    echo -e "${GREEN}✓ .env file already exists${NC}"
fi

# Create frontend .env.local if it doesn't exist
if [ ! -f apps/web/.env.local ]; then
    echo -e "${YELLOW}📝 Creating frontend .env.local file...${NC}"
    cp apps/web/.env.example apps/web/.env.local
    echo -e "${GREEN}✓ Created apps/web/.env.local${NC}"
else
    echo -e "${GREEN}✓ Frontend .env.local already exists${NC}"
fi

# Create backend .env if it doesn't exist
if [ ! -f packages/marketing-agent/.env ]; then
    echo -e "${YELLOW}📝 Creating backend .env file...${NC}"
    # Source the root .env for OPENAI_API_KEY
    if [ -f .env ]; then
        source .env
    fi
    cat > packages/marketing-agent/.env << EOF
OPENAI_API_KEY=${OPENAI_API_KEY:-your_openai_api_key}
DATABASE_URL=postgresql://synapse:synapse_dev_password_change_in_production@postgres:5432/synapse
FASTAPI_BASE_URL=http://backend:8000
EOF
    echo -e "${GREEN}✓ Created packages/marketing-agent/.env${NC}"
else
    echo -e "${GREEN}✓ Backend .env already exists${NC}"
fi

echo ""
echo -e "${BLUE}🐳 Building Docker containers...${NC}"
docker-compose build

echo ""
echo -e "${BLUE}🚀 Starting services...${NC}"
docker-compose up -d

echo ""
echo -e "${GREEN}✅ Setup complete!${NC}"
echo ""
echo "📍 Access points:"
echo "   - Frontend:  http://localhost:3000"
echo "   - Backend:   http://localhost:8000"
echo "   - Database:  localhost:5432"
echo ""
echo "📊 Optional: PgAdmin (database UI)"
echo "   Run: docker-compose --profile tools up -d"
echo "   Access: http://localhost:5050"
echo ""
echo "📝 Next steps:"
echo "   1. Make sure you've added your OPENAI_API_KEY to .env"
echo "   2. Initialize the database:"
echo "      docker-compose exec backend python init_db.py"
echo "   3. Visit http://localhost:3000 to see the app"
echo ""
echo "🔧 Useful commands:"
echo "   - View logs:        docker-compose logs -f"
echo "   - Stop services:    docker-compose down"
echo "   - Restart:          docker-compose restart"
echo "   - Clean everything: docker-compose down -v"
echo ""
