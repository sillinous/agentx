#!/usr/bin/env pwsh
# Test script to verify Unified Media Ecosystem setup

Write-Host "🧪 Unified Media Ecosystem - Structure Verification" -ForegroundColor Cyan
Write-Host "=" * 60

# Test 1: Check junctions
Write-Host "`n📁 Test 1: Verifying junctions..." -ForegroundColor Yellow
$junctions = @{
    "apps/media-manager/backend" = "backend"
    "apps/media-manager/frontend" = "frontend"
    "apps/story-forge" = "../StoryBiblePortfolioApp"
}

$junctionsPassed = $true
foreach ($junction in $junctions.GetEnumerator()) {
    $exists = Test-Path $junction.Key
    $item = Get-Item $junction.Key -ErrorAction SilentlyContinue
    $isJunction = $item.LinkType -eq "Junction"
    
    if ($exists -and $isJunction) {
        Write-Host "  ✅ $($junction.Key) → $($junction.Value)" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $($junction.Key) - FAILED" -ForegroundColor Red
        $junctionsPassed = $false
    }
}

# Test 2: Check package structure
Write-Host "`n📦 Test 2: Verifying shared packages..." -ForegroundColor Yellow
$packages = @(
    "packages/shared/package.json",
    "packages/shared-ui/package.json",
    "packages/shared-utils/package.json"
)

$packagesPassed = $true
foreach ($pkg in $packages) {
    if (Test-Path $pkg) {
        Write-Host "  ✅ $pkg" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $pkg - MISSING" -ForegroundColor Red
        $packagesPassed = $false
    }
}

# Test 3: Check critical files
Write-Host "`n📄 Test 3: Verifying critical files..." -ForegroundColor Yellow
$criticalFiles = @(
    "package.json",
    "docker-compose.yml",
    "README.md",
    "START_HERE.md"
)

$filesPassed = $true
foreach ($file in $criticalFiles) {
    if (Test-Path $file) {
        Write-Host "  ✅ $file" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $file - MISSING" -ForegroundColor Red
        $filesPassed = $false
    }
}

# Test 4: Check backend/frontend dependencies
Write-Host "`n🔧 Test 4: Checking dependencies..." -ForegroundColor Yellow

$frontendNodeModules = Test-Path "frontend/node_modules"
$storyForgeBackendNodeModules = Test-Path "apps/story-forge/backend/node_modules"
$storyForgeFrontendNodeModules = Test-Path "apps/story-forge/frontend/node_modules"

if ($frontendNodeModules) {
    Write-Host "  ✅ Media Manager frontend dependencies installed" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  Media Manager frontend dependencies missing (run: cd frontend && npm install)" -ForegroundColor Yellow
}

if ($storyForgeBackendNodeModules) {
    Write-Host "  ✅ StoryForge backend dependencies installed" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  StoryForge backend dependencies missing (run: cd apps/story-forge/backend && npm install)" -ForegroundColor Yellow
}

if ($storyForgeFrontendNodeModules) {
    Write-Host "  ✅ StoryForge frontend dependencies installed" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  StoryForge frontend dependencies missing (run: cd apps/story-forge/frontend && npm install)" -ForegroundColor Yellow
}

# Test 5: Check environment files
Write-Host "`n🔐 Test 5: Checking environment configuration..." -ForegroundColor Yellow

$backendEnv = Test-Path "backend/.env"
$storyForgeEnv = Test-Path "apps/story-forge/backend/.env"

if ($backendEnv) {
    Write-Host "  ✅ Media Manager backend .env exists" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  Media Manager backend .env missing (copy from backend/.env.example)" -ForegroundColor Yellow
}

if ($storyForgeEnv) {
    Write-Host "  ✅ StoryForge backend .env exists" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  StoryForge backend .env missing (see ENV_TEMPLATE.md)" -ForegroundColor Yellow
}

# Summary
Write-Host "`n" + "=" * 60
Write-Host "📊 Summary" -ForegroundColor Cyan

if ($junctionsPassed -and $packagesPassed -and $filesPassed) {
    Write-Host "✅ All critical tests PASSED!" -ForegroundColor Green
    Write-Host "`n🚀 Next steps:" -ForegroundColor Yellow
    Write-Host "  1. Ensure environment variables are set (see ENV_TEMPLATE.md)"
    Write-Host "  2. Start with Docker: docker compose up"
    Write-Host "  3. Or start individual apps (see START_HERE.md)"
} else {
    Write-Host "❌ Some tests FAILED. Please review the errors above." -ForegroundColor Red
    exit 1
}

Write-Host "`n📚 Documentation:" -ForegroundColor Cyan
Write-Host "  - Quick Start: START_HERE.md"
Write-Host "  - Full Docs: README.md"
Write-Host "  - Merge Details: MONOREPO_MERGE_COMPLETE.md"
