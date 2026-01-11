# Unified Media Ecosystem Environment Variables Template
# Copy this to .env and fill in your actual values

# ============================================
# Media Manager (FastAPI + Next.js)
# ============================================

# AI Providers
ANTHROPIC_API_KEY=your_anthropic_api_key_here
LTX_API_KEY=your_ltx_api_key_here
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here

# Database
DATABASE_URL=sqlite:///./sql_app.db
# For production, use PostgreSQL:
# DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# Authentication
DISABLE_AUTH=true
JWT_SECRET=your_jwt_secret_here
JWT_ALGORITHM=HS256

# CORS
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173

# Celery (Task Queue)
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Storage
STORAGE_TYPE=local
# For S3 storage:
# STORAGE_TYPE=s3
# AWS_ACCESS_KEY_ID=your_access_key
# AWS_SECRET_ACCESS_KEY=your_secret_key
# S3_BUCKET_NAME=your_bucket_name
# S3_REGION=us-east-1

# ============================================
# StoryForge (Node.js + React + Firebase)
# ============================================

# Google Gemini AI
GEMINI_API_KEY=your_gemini_api_key_here

# Firebase Admin (Backend)
FIREBASE_PROJECT_ID=your_firebase_project_id
FIREBASE_PRIVATE_KEY=your_firebase_private_key
FIREBASE_CLIENT_EMAIL=your_firebase_client_email

# Firebase Web (Frontend)
VITE_FIREBASE_API_KEY=your_firebase_api_key
VITE_FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your_firebase_project_id
VITE_FIREBASE_STORAGE_BUCKET=your_project.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=your_sender_id
VITE_FIREBASE_APP_ID=your_app_id

# Backend URL
VITE_BACKEND_URL=http://localhost:3001

# App ID
APP_ID=story-forge-default

# ============================================
# Development Settings
# ============================================
NODE_ENV=development
PYTHONUNBUFFERED=1
