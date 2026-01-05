# ===========================================
# SYNAPSE CORE - Setup Script (Windows PowerShell)
# ===========================================

Write-Host "🚀 Setting up Synapse Core..." -ForegroundColor Blue
Write-Host ""

# Check prerequisites
Write-Host "📋 Checking prerequisites..." -ForegroundColor Blue

# Check Docker
try {
    docker --version | Out-Null
    Write-Host "✓ Docker found" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not installed. Please install Docker Desktop first." -ForegroundColor Red
    Write-Host "   Download from: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    exit 1
}

# Check Docker Compose
try {
    docker-compose --version | Out-Null
    Write-Host "✓ Docker Compose found" -ForegroundColor Green
} catch {
    try {
        docker compose version | Out-Null
        Write-Host "✓ Docker Compose found" -ForegroundColor Green
    } catch {
        Write-Host "❌ Docker Compose is not installed." -ForegroundColor Red
        exit 1
    }
}

# Create .env file if it doesn't exist
if (-not (Test-Path .env)) {
    Write-Host "📝 Creating .env file from template..." -ForegroundColor Yellow
    Copy-Item .env.example .env
    Write-Host "✓ Created .env file" -ForegroundColor Green
    Write-Host "⚠️  Please edit .env and add your OPENAI_API_KEY" -ForegroundColor Yellow
} else {
    Write-Host "✓ .env file already exists" -ForegroundColor Green
}

# Create frontend .env.local if it doesn't exist
if (-not (Test-Path apps/web/.env.local)) {
    Write-Host "📝 Creating frontend .env.local file..." -ForegroundColor Yellow
    Copy-Item apps/web/.env.example apps/web/.env.local
    Write-Host "✓ Created apps/web/.env.local" -ForegroundColor Green
} else {
    Write-Host "✓ Frontend .env.local already exists" -ForegroundColor Green
}

# Create backend .env if it doesn't exist
if (-not (Test-Path packages/marketing-agent/.env)) {
    Write-Host "📝 Creating backend .env file..." -ForegroundColor Yellow

    # Read OPENAI_API_KEY from root .env if it exists
    $openaiKey = "your_openai_api_key"
    if (Test-Path .env) {
        $envContent = Get-Content .env
        foreach ($line in $envContent) {
            if ($line -match "^OPENAI_API_KEY=(.+)$") {
                $openaiKey = $matches[1]
            }
        }
    }

    @"
OPENAI_API_KEY=$openaiKey
DATABASE_URL=postgresql://synapse:synapse_dev_password_change_in_production@postgres:5432/synapse
FASTAPI_BASE_URL=http://backend:8000
"@ | Out-File -FilePath packages/marketing-agent/.env -Encoding UTF8

    Write-Host "✓ Created packages/marketing-agent/.env" -ForegroundColor Green
} else {
    Write-Host "✓ Backend .env already exists" -ForegroundColor Green
}

Write-Host ""
Write-Host "🐳 Building Docker containers..." -ForegroundColor Blue
docker-compose build

Write-Host ""
Write-Host "🚀 Starting services..." -ForegroundColor Blue
docker-compose up -d

Write-Host ""
Write-Host "✅ Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📍 Access points:"
Write-Host "   - Frontend:  http://localhost:3000"
Write-Host "   - Backend:   http://localhost:8000"
Write-Host "   - Database:  localhost:5432"
Write-Host ""
Write-Host "📊 Optional: PgAdmin (database UI)"
Write-Host "   Run: docker-compose --profile tools up -d"
Write-Host "   Access: http://localhost:5050"
Write-Host ""
Write-Host "📝 Next steps:"
Write-Host "   1. Make sure you've added your OPENAI_API_KEY to .env"
Write-Host "   2. Initialize the database:"
Write-Host "      docker-compose exec backend python init_db.py"
Write-Host "   3. Visit http://localhost:3000 to see the app"
Write-Host ""
Write-Host "🔧 Useful commands:"
Write-Host "   - View logs:        docker-compose logs -f"
Write-Host "   - Stop services:    docker-compose down"
Write-Host "   - Restart:          docker-compose restart"
Write-Host "   - Clean everything: docker-compose down -v"
Write-Host ""
