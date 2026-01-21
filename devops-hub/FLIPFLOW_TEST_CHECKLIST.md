
# FlipFlow Payment Testing Checklist

## Pre-Launch Testing (30 minutes)

### Environment Setup
- [ ] Stripe Test Mode enabled
- [ ] Test database/user created
- [ ] All environment variables set
- [ ] Webhook endpoint configured

### Basic Payment Flow
- [ ] Starter Pack ($9.99 one-time)
  - [ ] Checkout session created
  - [ ] Payment successful with test card
  - [ ] User redirected to success page
  - [ ] 10 credits allocated to user
  - [ ] Webhook delivered (200 OK)

- [ ] Pro Plan ($49/month subscription)
  - [ ] Checkout session created
  - [ ] Subscription activated
  - [ ] Unlimited credits set
  - [ ] Webhook delivered (200 OK)

### Credit Management
- [ ] Free user has 3 credits
- [ ] Starter user has 10 credits
- [ ] Pro user has unlimited credits
- [ ] Credits decrement on analysis
- [ ] Credits display correctly in UI

### Error Handling
- [ ] Declined card shows error
- [ ] Insufficient funds handled
- [ ] No credits allocated on failed payment
- [ ] User can retry payment

### Edge Cases
- [ ] User with 0 credits can't analyze
- [ ] Upgrade from Free to Starter works
- [ ] Upgrade from Starter to Pro works
- [ ] Subscription cancellation works
- [ ] Webhook retry on failure works

### Production Readiness
- [ ] Switch to Live Mode in Stripe
- [ ] Update environment variables with live keys
- [ ] Test with real card (small amount)
- [ ] Verify live webhook delivery
- [ ] Monitor first 24 hours for errors

## Test Card Numbers

✓ Success: 4242 4242 4242 4242
✗ Decline: 4000 0000 0000 0002
✗ Insufficient Funds: 4000 0000 0000 9995
✗ Expired: 4000 0000 0000 0069

---
Generated: 2026-01-11 11:14:41