# FlipFlow 30-Minute Launch Checklist

**Total Time**: ~30 minutes  
**Result**: FlipFlow accepting real payments  
**Revenue**: First $ in 7-10 days

---

## ✅ STEP 1: Database Migration (5 minutes)

### Actions:
1. Open browser → https://app.supabase.com
2. Select FlipFlow project
3. Click "SQL Editor" in left sidebar
4. Click "New Query"
5. Copy entire contents of `flipflow_database_migration.sql`
6. Paste into query editor
7. Click "Run" button
8. Verify results show in bottom panel

### Success Criteria:
✅ Query executes without errors  
✅ Verification query shows all users have credits  
✅ No NULL values in credits column  

**Time**: 5 minutes

---

## ✅ STEP 2: Create Stripe Live Products (10 minutes)

### Actions:
1. Open browser → https://dashboard.stripe.com
2. Toggle to **"Live mode"** (top right - switch from Test to Live)
3. Click "Products" in left sidebar
4. Click "+ Create product"

### Product 1: Starter Pack
- **Name**: `Starter Pack`
- **Description**: `10 FlipFlow analyses that never expire`
- **Pricing**:
  - Price: `$9.99`
  - Billing: `One time`
  - Currency: `USD`
- Click "Save product"
- **⚠️ COPY THE PRICE ID** (format: `price_xxxxxxxxxxxxx`)
  - Save as: `STRIPE_PRICE_STARTER`

### Product 2: Pro Plan
- **Name**: `Pro Plan`
- **Description**: `Unlimited FlipFlow analyses per month`
- **Pricing**:
  - Price: `$49.00`
  - Billing: `Recurring - Monthly`
  - Currency: `USD`
- Click "Save product"
- **⚠️ COPY THE PRICE ID** (format: `price_xxxxxxxxxxxxx`)
  - Save as: `STRIPE_PRICE_UNLIMITED`

### Get API Keys:
1. Click "Developers" in left sidebar
2. Click "API keys"
3. **⚠️ COPY THESE VALUES**:
   - Publishable key (starts with `pk_live_`)
   - Secret key (click "Reveal" then copy, starts with `sk_live_`)

**Time**: 10 minutes

---

## ✅ STEP 3: Set Up Webhook (5 minutes)

### Actions:
1. Still in Stripe Dashboard → Developers → Webhooks
2. Click "+ Add endpoint"
3. **Endpoint URL**: `https://your-flipflow-domain.com/api/stripe/webhook`
   - (Replace with actual domain)
4. **Description**: `FlipFlow Production Webhook`
5. **Events to send**:
   - Click "Select events"
   - Search and select:
     - ✅ `checkout.session.completed`
     - ✅ `customer.subscription.created`
     - ✅ `customer.subscription.updated`
     - ✅ `customer.subscription.deleted`
     - ✅ `invoice.paid`
     - ✅ `invoice.payment_failed`
6. Click "Add endpoint"
7. **⚠️ COPY THE SIGNING SECRET** (starts with `whsec_`)
   - Save as: `STRIPE_WEBHOOK_SECRET`

**Time**: 5 minutes

---

## ✅ STEP 4: Update Vercel Environment Variables (5 minutes)

### Actions:
1. Open browser → https://vercel.com
2. Select FlipFlow project
3. Click "Settings" tab
4. Click "Environment Variables" in left sidebar
5. Add/Update these variables (use values from Step 2 & 3):

```
STRIPE_SECRET_KEY=sk_live_xxxxxxxxxxxxx
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_xxxxxxxxxxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxx
STRIPE_PRICE_STARTER=price_xxxxxxxxxxxxx
STRIPE_PRICE_UNLIMITED=price_xxxxxxxxxxxxx
```

6. **IMPORTANT**: Set for "Production" environment
7. Click "Save"

**Time**: 5 minutes

---

## ✅ STEP 5: Deploy to Production (5 minutes)

### Actions:
1. Still in Vercel → Click "Deployments" tab
2. Click "Redeploy" on latest deployment
3. OR: Push any small change to main branch to trigger deploy
4. Wait for deployment to complete (~2-3 minutes)
5. Click "Visit" to open production site

### Verification:
1. Open `/api/healthcheck` endpoint
2. Verify Stripe environment variables show as configured
3. Check console for any errors

**Time**: 5 minutes

---

## ✅ STEP 6: Test Payment Flow (5 minutes - CRITICAL)

### Test Mode First:
1. Open your FlipFlow site
2. Click "Sign Up" → Create test account
3. Go to "/pricing" page
4. Click "Get Started" on Starter Pack
5. Use Stripe test card: `4242 4242 4242 4242`
   - Expiry: Any future date
   - CVC: Any 3 digits
   - ZIP: Any 5 digits
6. Complete checkout
7. Verify:
   - Redirected back to success page
   - Credits added to account
   - Can perform analysis

### Go Live:
Once test works:
1. Update env vars to use LIVE keys (Step 4)
2. Redeploy
3. Test with REAL card (your own)
4. Verify payment appears in Stripe Dashboard → Payments

**Time**: 5 minutes

---

## 🎉 LAUNCH CHECKLIST

After all steps above:

- [ ] Database migration successful
- [ ] Stripe products created (2 products)
- [ ] Webhook endpoint configured
- [ ] Vercel env vars updated
- [ ] Production deployment successful
- [ ] Test payment completed successfully
- [ ] Webhook delivered successfully (check Stripe logs)
- [ ] Credits added to user account
- [ ] Email confirmation sent (if configured)

---

## 📊 Post-Launch Monitoring (First 24 Hours)

### What to Watch:
1. **Stripe Dashboard**:
   - Payments → Monitor successful charges
   - Webhooks → Check delivery status
   - Customers → See new sign-ups

2. **Vercel Logs**:
   - Check for any errors in `/api/stripe/*` endpoints
   - Monitor webhook processing

3. **Supabase**:
   - Watch users table for subscription updates
   - Monitor credits column updates

### Success Metrics (Week 1):
- [ ] 10+ signups
- [ ] 1+ paying customer
- [ ] $0 → $X MRR
- [ ] Zero critical errors
- [ ] All webhooks processing successfully

---

## 🚨 TROUBLESHOOTING

### "Webhook failed to deliver"
- Check endpoint URL is correct
- Verify STRIPE_WEBHOOK_SECRET matches
- Check Vercel logs for errors

### "Payment succeeded but credits not added"
- Check webhook delivery in Stripe
- Verify database migration ran
- Check Vercel function logs

### "Test card declined"
- Ensure using test mode keys
- Use test card: 4242 4242 4242 4242
- Check Stripe Dashboard for decline reason

---

## 📞 SUPPORT RESOURCES

- **Stripe Docs**: https://stripe.com/docs
- **Supabase Docs**: https://supabase.com/docs
- **Vercel Docs**: https://vercel.com/docs
- **FlipFlow Code**: Check `lib/stripe.ts` for implementation

---

**TOTAL TIME**: ~30 minutes  
**RESULT**: FlipFlow live and accepting payments 💰  
**NEXT**: Monitor metrics and optimize conversion!
