# FlipFlow Deployment Guide

Complete step-by-step guide to deploy FlipFlow Phase 1 (Analyzer) to production.

## Prerequisites

- Node.js 18+ installed
- npm or yarn
- Anthropic API key (get from https://console.anthropic.com)
- Vercel account (free tier works)
- Git installed

## Phase 1: Local Development Setup

### Step 1: Install Dependencies

```bash
cd FlipFlow
npm install
```

### Step 2: Set Up Environment Variables

```bash
# Copy the example env file
cp .env.example .env.local

# Edit .env.local and add your API key
```

Required variables for Phase 1:
```env
ANTHROPIC_API_KEY=sk-ant-your-key-here
NEXT_PUBLIC_APP_URL=http://localhost:3000
NODE_ENV=development
```

### Step 3: Test Locally

```bash
# Start development server
npm run dev

# Open http://localhost:3000
```

### Step 4: Test the Analyzer

1. Visit `http://localhost:3000`
2. Click "Start Analyzing" or go to `/analyze`
3. Use the sample data button or paste a real Flippa listing
4. Click "Analyze Deal"
5. Verify you get results in 10-20 seconds

## Phase 1: Production Deployment (Vercel)

### Step 1: Prepare for Deployment

```bash
# Ensure everything is committed
git add .
git commit -m "Initial FlipFlow setup - Phase 1"

# Create GitHub repository (if not already created)
gh repo create FlipFlow --private --source=.
git push -u origin main
```

### Step 2: Deploy to Vercel

**Option A: Using Vercel CLI**

```bash
# Install Vercel CLI
npm install -g vercel

# Login to Vercel
vercel login

# Deploy
vercel

# Follow prompts:
# - Link to existing project? No
# - Project name? FlipFlow
# - Directory? ./
# - Override settings? No
```

**Option B: Using Vercel Dashboard**

1. Go to https://vercel.com/new
2. Import your GitHub repository
3. Configure project:
   - Framework Preset: Next.js
   - Root Directory: ./
   - Build Command: `npm run build` (default)
   - Output Directory: `.next` (default)

### Step 3: Add Environment Variables in Vercel

In Vercel Dashboard → Your Project → Settings → Environment Variables:

Add:
```
ANTHROPIC_API_KEY = sk-ant-your-key-here
NEXT_PUBLIC_APP_URL = https://your-project.vercel.app
NODE_ENV = production
```

### Step 4: Redeploy

```bash
# Trigger new deployment with env vars
vercel --prod
```

### Step 5: Test Production

1. Visit your Vercel URL (e.g., `https://flipflow.vercel.app`)
2. Test the analyzer with sample data
3. Verify everything works

## Phase 2: Adding Supabase (Scout Agent)

### Step 1: Create Supabase Project

1. Go to https://supabase.com/dashboard
2. Click "New Project"
3. Fill in:
   - Name: FlipFlow
   - Database Password: (save this securely)
   - Region: (choose closest to your users)
   - Pricing Plan: Free (for MVP)

### Step 2: Set Up Database Schema

```bash
# In your FlipFlow directory
npm run db:setup
```

Or manually in Supabase SQL Editor:

```sql
# Copy contents from supabase/schema.sql
# Run in Supabase SQL Editor
```

### Step 3: Get Supabase Credentials

In Supabase Dashboard → Settings → API:

Copy:
- Project URL
- `anon` public key
- `service_role` secret key

### Step 4: Add to Environment Variables

Local (.env.local):
```env
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJxxx
SUPABASE_SERVICE_KEY=eyJxxx
```

Vercel:
Add the same variables in Vercel Dashboard → Settings → Environment Variables

### Step 5: Deploy Updates

```bash
git add .
git commit -m "Add Supabase integration"
git push
# Vercel auto-deploys
```

## Phase 2: Adding n8n Automation

### Step 1: Create n8n Account

1. Go to https://n8n.io/cloud
2. Sign up for free trial
3. Create new workflow

### Step 2: Import Workflows

In n8n:
1. Click "Add Workflow" → "Import from File"
2. Import workflows from `/n8n/` directory:
   - `scraper-workflow.json`
   - `analyzer-workflow.json`
   - `alerts-workflow.json`
   - `digest-workflow.json`

### Step 3: Configure Credentials

In each workflow, add:
- Supabase credentials
- Resend API key (for emails)
- Your app's webhook URLs

### Step 4: Activate Workflows

1. Test each workflow manually
2. Once verified, click "Activate" on each
3. Scraper will run every 6 hours automatically

## Phase 2: Adding Email (Resend)

### Step 1: Create Resend Account

1. Go to https://resend.com
2. Sign up (free tier: 100 emails/day)
3. Verify your domain (optional, recommended for production)

### Step 2: Get API Key

1. In Resend Dashboard → API Keys
2. Create new API key
3. Copy key

### Step 3: Add to Environment

```env
RESEND_API_KEY=re_xxx
RESEND_FROM_EMAIL=noreply@yourdomain.com
```

## Cost Breakdown

### Free Tier (MVP Testing)
- Vercel: Free (Hobby plan)
- Supabase: Free (500MB database, 50MB file storage)
- Anthropic: $5 free credit (~100-250 analyses)
- Resend: Free (100 emails/day)
- n8n: Free trial (then $20/mo)

**Total**: $0/month initially

### Production (100 users)
- Vercel Pro: $20/mo (better performance)
- Supabase Pro: $25/mo (better limits)
- Anthropic API: ~$50-100/mo (depending on usage)
- Resend: $20/mo (10,000 emails)
- n8n: $20/mo (automation)
- Bright Data: $50-200/mo (scraping, optional)

**Total**: ~$185-385/month

**Break-even**: 4 Pro subscribers at $99/mo = $396/mo revenue

## Monitoring & Maintenance

### Analytics

Add to Vercel:
```bash
# Vercel Analytics is automatic for Pro plan
# Or add Google Analytics
```

### Error Tracking

Add Sentry (optional):
```bash
npm install @sentry/nextjs
```

### Logs

- Vercel: Check deployment logs in dashboard
- Supabase: Check database logs
- n8n: Check workflow execution logs
- Anthropic: Monitor usage in console

### Backups

Supabase automatic backups:
- Free tier: 7 days point-in-time recovery
- Pro tier: 30 days

### Updates

```bash
# Pull latest dependencies
npm update

# Test locally
npm run dev

# Deploy
git push
```

## Troubleshooting

### "Analysis failed" Error

**Check:**
1. Anthropic API key is correct
2. API key has credits remaining
3. Request isn't too large (check listing data length)

**Fix:**
```bash
# Verify API key
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01"
```

### Deployment Fails

**Check:**
1. All environment variables are set in Vercel
2. No build errors: `npm run build`
3. TypeScript passes: `npm run type-check`

**Fix:**
```bash
# Clear cache and rebuild
rm -rf .next node_modules
npm install
npm run build
```

### Scraper Not Working (Phase 2)

**Check:**
1. n8n workflow is activated
2. Supabase credentials are correct
3. Webhook URLs are correct

**Fix:**
- Run workflow manually in n8n
- Check execution logs for errors

### Database Connection Issues

**Check:**
1. Supabase project is active
2. API keys are correct
3. Row Level Security policies allow access

**Fix:**
```sql
-- Disable RLS for testing (re-enable in production)
ALTER TABLE listings DISABLE ROW LEVEL SECURITY;
```

## Security Checklist

- [ ] Environment variables in Vercel (not in code)
- [ ] Supabase RLS policies enabled
- [ ] API rate limiting enabled
- [ ] HTTPS only (Vercel automatic)
- [ ] Sensitive data encrypted
- [ ] Regular dependency updates
- [ ] Error messages don't leak secrets

## Next Steps After Phase 1 Deployment

1. **Get Users**: Share on Twitter, ProductHunt, Indie Hackers
2. **Collect Feedback**: Add feedback form, track usage
3. **Add Analytics**: See which features users love
4. **Build Phase 2**: Automated deal finding based on demand
5. **Monetize**: Add Stripe payment integration

## Support

- **Documentation**: Check README.md and code comments
- **Issues**: Use GitHub Issues for bug reports
- **Updates**: Follow deployment logs in Vercel

---

**Ready to launch?** Follow the steps above in order. Each phase builds on the previous one.

**Estimated Time**:
- Phase 1 Local Setup: 30 minutes
- Phase 1 Production Deploy: 1 hour
- Phase 2 Full Stack: 2-3 hours

Good luck! 🚀
