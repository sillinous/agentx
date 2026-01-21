# Portfolio Dashboard Deployment Guide

## 🚀 Deploy to Vercel (5 Minutes)

### Prerequisites
- GitHub account
- Vercel account (free tier works)
- DevOps Hub API deployed and accessible

### Step 1: Push to GitHub

```bash
cd portfolio-dashboard

# Initialize git if not already done
git init
git add .
git commit -m "Initial commit: Portfolio dashboard"

# Create GitHub repo and push
gh repo create portfolio-dashboard --public --source=. --remote=origin --push
# OR manually:
# 1. Create repo on GitHub
# 2. git remote add origin https://github.com/YOUR_USERNAME/portfolio-dashboard.git
# 3. git push -u origin main
```

### Step 2: Import to Vercel

1. Go to [https://vercel.com](https://vercel.com)
2. Click "New Project"
3. Import your `portfolio-dashboard` repository
4. Configure:
   - **Framework Preset**: Next.js (auto-detected)
   - **Root Directory**: `./` (or leave blank)
   - **Build Command**: `npm run build` (auto-filled)
   - **Output Directory**: `.next` (auto-filled)

### Step 3: Set Environment Variables

In Vercel project settings → Environment Variables, add:

```
NEXT_PUBLIC_API_URL = https://your-devops-hub-api-url.com
```

**Important:** Replace with your actual DevOps Hub API URL (e.g., deployed on Render, Railway, or your own server).

### Step 4: Deploy

Click "Deploy" and wait ~2-3 minutes.

### Step 5: Get Your URL

Vercel will provide:
- **Production URL**: `https://portfolio-dashboard-xxx.vercel.app`
- **Custom Domain** (optional): Add your own domain in settings

---

## 🌐 Custom Domain Setup (Optional)

### Add Custom Domain to Vercel

1. Go to project → Settings → Domains
2. Add domain (e.g., `dashboard.yourdomain.com`)
3. Follow DNS instructions:
   - Add CNAME record: `dashboard.yourdomain.com` → `cname.vercel-dns.com`
4. Wait for DNS propagation (~5-60 minutes)

---

## 🔧 Alternative Deployment Options

### Deploy to Netlify

```bash
# Install Netlify CLI
npm install -g netlify-cli

# Deploy
cd portfolio-dashboard
netlify deploy --prod

# Follow prompts to connect to Netlify account
```

### Deploy to Your Own Server

```bash
# Build for production
npm run build

# Start production server
npm start

# OR use PM2 for process management
npm install -g pm2
pm2 start npm --name "portfolio-dashboard" -- start
pm2 save
```

---

## 📊 Post-Deployment Checklist

- [ ] Dashboard loads successfully
- [ ] API connection working (green status indicator)
- [ ] Projects displayed correctly
- [ ] Revenue metrics showing
- [ ] Next actions listed
- [ ] Data updates every 30 seconds
- [ ] Mobile responsive
- [ ] Dark theme looks good

---

## 🐛 Troubleshooting

### Dashboard shows "API: OFFLINE"
- Check `NEXT_PUBLIC_API_URL` environment variable
- Verify DevOps Hub API is running and accessible
- Check CORS settings on API (should allow your dashboard domain)

### Data not updating
- Verify API endpoint returns correct format
- Check browser console for errors
- Confirm API `/portfolio/dashboard` endpoint exists

### Build fails on Vercel
- Check Node.js version (should be 18.x or higher)
- Verify all dependencies in package.json
- Check build logs for specific errors

---

## 🔐 Security Notes

1. **API Authentication**: Currently dashboard uses public endpoints. For production:
   - Add API key authentication to DevOps Hub
   - Store API key in Vercel environment variables
   - Add auth header to fetch requests

2. **Rate Limiting**: API should have rate limiting enabled to prevent abuse

3. **CORS**: DevOps Hub API should allow your dashboard domain:
   ```env
   CORS_ORIGINS=https://your-dashboard.vercel.app,https://dashboard.yourdomain.com
   ```

---

## 📈 Monitoring

### Vercel Analytics
Enable in project settings → Analytics for:
- Page views
- Load times
- Geographic distribution

### API Health Monitoring
Dashboard checks API health every 30 seconds. Monitor:
- API uptime
- Response times
- Error rates

---

## 🔄 Updates & Redeployment

### Automatic Deployments
Vercel auto-deploys on every push to `main` branch:
```bash
git add .
git commit -m "Update dashboard data"
git push origin main
# Vercel deploys automatically
```

### Manual Deployment
```bash
vercel --prod
```

---

## 🎨 Customization

### Change Theme Colors
Edit `tailwind.config.ts`:
```typescript
colors: {
  primary: "#00ff88",  // Change accent color
  danger: "#ff0055",
  warning: "#ffaa00",
}
```

### Update Fonts
Edit `src/app/layout.tsx` to change Google Fonts import.

### Modify Data Refresh Rate
Edit `src/app/page.tsx`:
```typescript
export const revalidate = 30; // Change from 30 seconds
```

---

**Deployment Time**: ~5 minutes  
**Cost**: $0 (Vercel free tier)  
**Result**: Public dashboard accessible 24/7
