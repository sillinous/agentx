# DevOps Hub - Setup & Login Guide

## Quick Start

### 1. Start the Backend
```powershell
python service/api.py
```
- Runs on http://localhost:8100
- API docs at http://localhost:8100/docs
- Bootstrap admin key will be displayed (save it!)

### 2. Start the Frontend
```powershell
cd frontend
npm run dev
```
- Runs on http://localhost:3000

### 3. Login to the Application

When you visit http://localhost:3000, you'll see the login page:

#### Option 1: Guest Mode (Recommended for Testing)
1. Click **"Continue as Guest"**
2. Instant access to all features
3. Can view and fulfill HITL requests
4. Perfect for testing and demos

#### Option 2: API Key Authentication
1. Enter the bootstrap admin key from the backend console
2. Full admin access
3. Can create/modify all data

## Accessing HITL System

After logging in, navigate to:
- **Human Actions**: http://localhost:3000/human-actions

Or use the navigation menu: **Human Actions**

## Testing HITL

### Create Test Requests
```powershell
python test_hitl.py
```

This creates sample requests you can view and fulfill in the UI.

### Via API
```powershell
# Create a request
$body = @{
    agent_id = "test-agent"
    request_type = "api_key"
    title = "Stripe API Key Needed"
    description = "Need production Stripe credentials"
    required_fields = @{
        api_key = "Stripe API Key"
        webhook_secret = "Webhook Secret"
    }
    priority = "high"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8100/hitl/requests" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body

# List requests
Invoke-RestMethod -Uri "http://localhost:8100/hitl/requests"
```

## Troubleshooting

### "Sign-in redirect" issue
- Click **"Continue as Guest"** button on the login page
- Guest mode provides full access in development

### Port already in use
```powershell
# Backend (8100)
netstat -ano | findstr :8100
taskkill /PID <process_id> /F

# Frontend (3000)
netstat -ano | findstr :3000
taskkill /PID <process_id> /F
```

### Backend errors
```powershell
# Reinstall dependencies
pip install -r requirements.txt

# Fresh database
Remove-Item -Force data/devops.db
python service/api.py
```

### Frontend errors
```powershell
cd frontend
npm install
npm run dev
```

## Features Available

- ✅ Dashboard - Operations overview
- ✅ Portfolio - Project analysis
- ✅ Agents - Browse and execute agents
- ✅ Workflows - Multi-agent orchestration
- ✅ **Human Actions** - HITL request management (NEW!)
- ✅ Handbook - Documentation
- ✅ Evaluations - Agent validation

## Documentation

- **HITL System**: [HITL_IMPLEMENTATION_SUMMARY.md](./HITL_IMPLEMENTATION_SUMMARY.md)
- **Codebase**: [CODEBASE_ASSESSMENT.md](./CODEBASE_ASSESSMENT.md)
- **API Docs**: http://localhost:8100/docs (when running)

## Next Steps

1. **Start both servers** (backend + frontend)
2. **Login** using "Continue as Guest"
3. **Navigate** to Human Actions
4. **Test** by running `python test_hitl.py`
5. **Explore** the UI and fulfill test requests

---

**Quick Links:**
- Frontend: http://localhost:3000
- Backend: http://localhost:8100
- API Docs: http://localhost:8100/docs
- Human Actions: http://localhost:3000/human-actions
