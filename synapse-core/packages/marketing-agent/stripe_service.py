"""
Stripe Payment Service for Synapse Core
Handles subscription management, checkout sessions, and webhooks.
"""

import os
import logging
from typing import Optional, Literal
from datetime import datetime, UTC
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Stripe configuration
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
STRIPE_PUBLIC_KEY = os.getenv("STRIPE_PUBLIC_KEY", "")

# Price IDs for subscription tiers (set in environment)
STRIPE_PRICE_STANDARD_MONTHLY = os.getenv("STRIPE_PRICE_STANDARD_MONTHLY", "")
STRIPE_PRICE_STANDARD_YEARLY = os.getenv("STRIPE_PRICE_STANDARD_YEARLY", "")
STRIPE_PRICE_ENTERPRISE_MONTHLY = os.getenv("STRIPE_PRICE_ENTERPRISE_MONTHLY", "")
STRIPE_PRICE_ENTERPRISE_YEARLY = os.getenv("STRIPE_PRICE_ENTERPRISE_YEARLY", "")

# Frontend URLs for redirects
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
CHECKOUT_SUCCESS_URL = f"{FRONTEND_URL}/billing/success?session_id={{CHECKOUT_SESSION_ID}}"
CHECKOUT_CANCEL_URL = f"{FRONTEND_URL}/billing/cancel"

# Initialize Stripe if key is available
stripe = None
if STRIPE_SECRET_KEY:
    try:
        import stripe as stripe_lib
        stripe_lib.api_key = STRIPE_SECRET_KEY
        stripe = stripe_lib
        logger.info("Stripe SDK initialized successfully")
    except ImportError:
        logger.warning("Stripe SDK not installed")
else:
    logger.warning("STRIPE_SECRET_KEY not configured - payment features disabled")


# =============================================================================
# Pydantic Models
# =============================================================================

class PricingTier(BaseModel):
    """Pricing tier information."""
    tier: Literal["standard", "enterprise"]
    name: str
    description: str
    price_monthly: int  # cents
    price_yearly: int   # cents
    features: list[str]
    stripe_price_monthly: str
    stripe_price_yearly: str


class CheckoutSessionRequest(BaseModel):
    """Request to create a checkout session."""
    tier: Literal["standard", "enterprise"] = Field(..., description="Subscription tier")
    billing_period: Literal["monthly", "yearly"] = Field(
        default="monthly", description="Billing period"
    )
    success_url: Optional[str] = Field(None, description="Custom success URL")
    cancel_url: Optional[str] = Field(None, description="Custom cancel URL")


class CheckoutSessionResponse(BaseModel):
    """Response with checkout session details."""
    session_id: str
    checkout_url: str
    tier: str
    billing_period: str


class SubscriptionStatus(BaseModel):
    """Current subscription status."""
    user_id: str
    tier: Literal["standard", "enterprise", "free"]
    status: Literal["active", "canceled", "past_due", "trialing", "none"]
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    current_period_start: Optional[str] = None
    current_period_end: Optional[str] = None
    cancel_at_period_end: bool = False


class SubscriptionUpdate(BaseModel):
    """Request to update subscription."""
    new_tier: Literal["standard", "enterprise"]
    billing_period: Literal["monthly", "yearly"] = "monthly"


class BillingPortalRequest(BaseModel):
    """Request for Stripe billing portal."""
    return_url: Optional[str] = None


class Invoice(BaseModel):
    """Invoice information."""
    id: str
    amount_paid: int
    currency: str
    status: str
    invoice_pdf: Optional[str]
    created: str
    period_start: str
    period_end: str


class WebhookEvent(BaseModel):
    """Processed webhook event."""
    event_type: str
    customer_id: Optional[str]
    subscription_id: Optional[str]
    data: dict


# =============================================================================
# Pricing Configuration
# =============================================================================

PRICING_TIERS: dict[str, PricingTier] = {
    "standard": PricingTier(
        tier="standard",
        name="Standard",
        description="Perfect for individuals and small teams",
        price_monthly=2900,  # $29/month
        price_yearly=29000,  # $290/year (save ~17%)
        features=[
            "All 3 AI Agents (Scribe, Architect, Sentry)",
            "60 requests/minute rate limit",
            "10GB context memory",
            "Email support",
            "API access",
        ],
        stripe_price_monthly=STRIPE_PRICE_STANDARD_MONTHLY,
        stripe_price_yearly=STRIPE_PRICE_STANDARD_YEARLY,
    ),
    "enterprise": PricingTier(
        tier="enterprise",
        name="Enterprise",
        description="For growing businesses and power users",
        price_monthly=9900,  # $99/month
        price_yearly=99000,  # $990/year (save ~17%)
        features=[
            "All 3 AI Agents (Scribe, Architect, Sentry)",
            "600 requests/minute rate limit (10x)",
            "100GB context memory",
            "Priority support",
            "Custom integrations",
            "Advanced analytics",
            "Team collaboration",
            "SSO (coming soon)",
        ],
        stripe_price_monthly=STRIPE_PRICE_ENTERPRISE_MONTHLY,
        stripe_price_yearly=STRIPE_PRICE_ENTERPRISE_YEARLY,
    ),
}


def get_pricing_tiers() -> list[PricingTier]:
    """Get all available pricing tiers."""
    return list(PRICING_TIERS.values())


def get_price_id(tier: str, billing_period: str) -> str:
    """Get the Stripe price ID for a tier and billing period."""
    pricing = PRICING_TIERS.get(tier)
    if not pricing:
        raise ValueError(f"Invalid tier: {tier}")

    if billing_period == "monthly":
        return pricing.stripe_price_monthly
    elif billing_period == "yearly":
        return pricing.stripe_price_yearly
    else:
        raise ValueError(f"Invalid billing period: {billing_period}")


# =============================================================================
# Stripe Service Functions
# =============================================================================

def is_stripe_configured() -> bool:
    """Check if Stripe is properly configured."""
    return stripe is not None and STRIPE_SECRET_KEY is not None


def create_customer(user_id: str, email: str, name: Optional[str] = None) -> str:
    """
    Create a Stripe customer for a user.

    Args:
        user_id: Internal user ID
        email: User's email
        name: User's name

    Returns:
        Stripe customer ID
    """
    if not is_stripe_configured():
        raise RuntimeError("Stripe is not configured")

    customer = stripe.Customer.create(
        email=email,
        name=name,
        metadata={"synapse_user_id": user_id},
    )

    logger.info(
        "Stripe customer created",
        extra={"user_id": user_id, "stripe_customer_id": customer.id},
    )

    return customer.id


def get_or_create_customer(
    user_id: str,
    email: str,
    name: Optional[str] = None,
    existing_customer_id: Optional[str] = None,
) -> str:
    """
    Get existing Stripe customer or create a new one.

    Args:
        user_id: Internal user ID
        email: User's email
        name: User's name
        existing_customer_id: Existing Stripe customer ID if known

    Returns:
        Stripe customer ID
    """
    if not is_stripe_configured():
        raise RuntimeError("Stripe is not configured")

    # If we have an existing customer ID, verify it exists
    if existing_customer_id:
        try:
            customer = stripe.Customer.retrieve(existing_customer_id)
            if not customer.deleted:
                return customer.id
        except stripe.error.InvalidRequestError:
            logger.warning(
                "Existing customer ID invalid, creating new",
                extra={"old_customer_id": existing_customer_id},
            )

    # Search for existing customer by email
    customers = stripe.Customer.list(email=email, limit=1)
    if customers.data:
        return customers.data[0].id

    # Create new customer
    return create_customer(user_id, email, name)


def create_checkout_session(
    customer_id: str,
    price_id: str,
    success_url: Optional[str] = None,
    cancel_url: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> CheckoutSessionResponse:
    """
    Create a Stripe Checkout session for subscription.

    Args:
        customer_id: Stripe customer ID
        price_id: Stripe price ID
        success_url: URL to redirect on success
        cancel_url: URL to redirect on cancel
        metadata: Additional metadata to attach

    Returns:
        CheckoutSessionResponse with session details
    """
    if not is_stripe_configured():
        raise RuntimeError("Stripe is not configured")

    # Determine tier and billing period from price ID
    tier = "standard"
    billing_period = "monthly"
    for t, pricing in PRICING_TIERS.items():
        if price_id == pricing.stripe_price_monthly:
            tier = t
            billing_period = "monthly"
            break
        elif price_id == pricing.stripe_price_yearly:
            tier = t
            billing_period = "yearly"
            break

    session = stripe.checkout.Session.create(
        customer=customer_id,
        payment_method_types=["card"],
        line_items=[{"price": price_id, "quantity": 1}],
        mode="subscription",
        success_url=success_url or CHECKOUT_SUCCESS_URL,
        cancel_url=cancel_url or CHECKOUT_CANCEL_URL,
        metadata=metadata or {},
        subscription_data={
            "metadata": metadata or {},
        },
        allow_promotion_codes=True,
    )

    logger.info(
        "Checkout session created",
        extra={
            "session_id": session.id,
            "customer_id": customer_id,
            "tier": tier,
        },
    )

    return CheckoutSessionResponse(
        session_id=session.id,
        checkout_url=session.url,
        tier=tier,
        billing_period=billing_period,
    )


def get_subscription_status(customer_id: str, user_id: str) -> SubscriptionStatus:
    """
    Get current subscription status for a customer.

    Args:
        customer_id: Stripe customer ID
        user_id: Internal user ID

    Returns:
        SubscriptionStatus with current subscription details
    """
    if not is_stripe_configured():
        return SubscriptionStatus(
            user_id=user_id,
            tier="free",
            status="none",
        )

    try:
        subscriptions = stripe.Subscription.list(
            customer=customer_id,
            status="all",
            limit=1,
        )

        if not subscriptions.data:
            return SubscriptionStatus(
                user_id=user_id,
                tier="free",
                status="none",
                stripe_customer_id=customer_id,
            )

        sub = subscriptions.data[0]

        # Determine tier from price ID
        price_id = sub["items"]["data"][0]["price"]["id"] if sub["items"]["data"] else ""
        tier = "standard"
        for t, pricing in PRICING_TIERS.items():
            if price_id in [pricing.stripe_price_monthly, pricing.stripe_price_yearly]:
                tier = t
                break

        return SubscriptionStatus(
            user_id=user_id,
            tier=tier,
            status=sub.status,
            stripe_customer_id=customer_id,
            stripe_subscription_id=sub.id,
            current_period_start=datetime.fromtimestamp(
                sub.current_period_start, UTC
            ).isoformat(),
            current_period_end=datetime.fromtimestamp(
                sub.current_period_end, UTC
            ).isoformat(),
            cancel_at_period_end=sub.cancel_at_period_end,
        )

    except Exception as e:
        logger.error(f"Error getting subscription status: {e}")
        return SubscriptionStatus(
            user_id=user_id,
            tier="free",
            status="none",
            stripe_customer_id=customer_id,
        )


def update_subscription(
    subscription_id: str,
    new_price_id: str,
    proration_behavior: str = "create_prorations",
) -> dict:
    """
    Update an existing subscription to a new plan.

    Args:
        subscription_id: Stripe subscription ID
        new_price_id: New Stripe price ID
        proration_behavior: How to handle prorations

    Returns:
        Updated subscription data
    """
    if not is_stripe_configured():
        raise RuntimeError("Stripe is not configured")

    subscription = stripe.Subscription.retrieve(subscription_id)

    updated = stripe.Subscription.modify(
        subscription_id,
        items=[{
            "id": subscription["items"]["data"][0].id,
            "price": new_price_id,
        }],
        proration_behavior=proration_behavior,
    )

    logger.info(
        "Subscription updated",
        extra={
            "subscription_id": subscription_id,
            "new_price_id": new_price_id,
        },
    )

    return {"subscription_id": updated.id, "status": updated.status}


def cancel_subscription(
    subscription_id: str,
    cancel_immediately: bool = False,
) -> dict:
    """
    Cancel a subscription.

    Args:
        subscription_id: Stripe subscription ID
        cancel_immediately: If True, cancel now; otherwise at period end

    Returns:
        Cancellation details
    """
    if not is_stripe_configured():
        raise RuntimeError("Stripe is not configured")

    if cancel_immediately:
        subscription = stripe.Subscription.delete(subscription_id)
        logger.info(
            "Subscription canceled immediately",
            extra={"subscription_id": subscription_id},
        )
    else:
        subscription = stripe.Subscription.modify(
            subscription_id,
            cancel_at_period_end=True,
        )
        logger.info(
            "Subscription set to cancel at period end",
            extra={"subscription_id": subscription_id},
        )

    return {
        "subscription_id": subscription.id,
        "status": subscription.status,
        "cancel_at_period_end": subscription.cancel_at_period_end,
    }


def reactivate_subscription(subscription_id: str) -> dict:
    """
    Reactivate a subscription that was set to cancel at period end.

    Args:
        subscription_id: Stripe subscription ID

    Returns:
        Reactivation details
    """
    if not is_stripe_configured():
        raise RuntimeError("Stripe is not configured")

    subscription = stripe.Subscription.modify(
        subscription_id,
        cancel_at_period_end=False,
    )

    logger.info(
        "Subscription reactivated",
        extra={"subscription_id": subscription_id},
    )

    return {
        "subscription_id": subscription.id,
        "status": subscription.status,
        "cancel_at_period_end": False,
    }


def create_billing_portal_session(
    customer_id: str,
    return_url: Optional[str] = None,
) -> str:
    """
    Create a Stripe billing portal session for self-service management.

    Args:
        customer_id: Stripe customer ID
        return_url: URL to return to after portal session

    Returns:
        Portal session URL
    """
    if not is_stripe_configured():
        raise RuntimeError("Stripe is not configured")

    session = stripe.billing_portal.Session.create(
        customer=customer_id,
        return_url=return_url or f"{FRONTEND_URL}/billing",
    )

    logger.info(
        "Billing portal session created",
        extra={"customer_id": customer_id},
    )

    return session.url


def get_invoices(customer_id: str, limit: int = 10) -> list[Invoice]:
    """
    Get invoices for a customer.

    Args:
        customer_id: Stripe customer ID
        limit: Maximum number of invoices to return

    Returns:
        List of Invoice objects
    """
    if not is_stripe_configured():
        return []

    try:
        invoices = stripe.Invoice.list(customer=customer_id, limit=limit)

        return [
            Invoice(
                id=inv.id,
                amount_paid=inv.amount_paid,
                currency=inv.currency,
                status=inv.status,
                invoice_pdf=inv.invoice_pdf,
                created=datetime.fromtimestamp(inv.created, UTC).isoformat(),
                period_start=datetime.fromtimestamp(
                    inv.period_start, UTC
                ).isoformat() if inv.period_start else "",
                period_end=datetime.fromtimestamp(
                    inv.period_end, UTC
                ).isoformat() if inv.period_end else "",
            )
            for inv in invoices.data
        ]
    except Exception as e:
        logger.error(f"Error fetching invoices: {e}")
        return []


# =============================================================================
# Webhook Handling
# =============================================================================

def verify_webhook_signature(payload: bytes, signature: str) -> dict:
    """
    Verify Stripe webhook signature and return event data.

    Args:
        payload: Raw request body
        signature: Stripe-Signature header value

    Returns:
        Verified event data

    Raises:
        ValueError: If signature verification fails
    """
    if not is_stripe_configured():
        raise RuntimeError("Stripe is not configured")

    if not STRIPE_WEBHOOK_SECRET:
        raise RuntimeError("STRIPE_WEBHOOK_SECRET not configured")

    try:
        event = stripe.Webhook.construct_event(
            payload,
            signature,
            STRIPE_WEBHOOK_SECRET,
        )
        return event
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Webhook signature verification failed: {e}")
        raise ValueError("Invalid webhook signature")


def process_webhook_event(event: dict) -> WebhookEvent:
    """
    Process a verified Stripe webhook event.

    Args:
        event: Verified Stripe event

    Returns:
        Processed WebhookEvent
    """
    event_type = event["type"]
    data = event["data"]["object"]

    customer_id = None
    subscription_id = None

    # Extract relevant IDs based on event type
    if event_type.startswith("customer.subscription"):
        subscription_id = data.get("id")
        customer_id = data.get("customer")
    elif event_type.startswith("invoice"):
        customer_id = data.get("customer")
        subscription_id = data.get("subscription")
    elif event_type.startswith("customer"):
        customer_id = data.get("id")

    logger.info(
        "Processing webhook event",
        extra={
            "event_type": event_type,
            "customer_id": customer_id,
            "subscription_id": subscription_id,
        },
    )

    return WebhookEvent(
        event_type=event_type,
        customer_id=customer_id,
        subscription_id=subscription_id,
        data=data,
    )


# Event type constants for webhook handling
class StripeEvents:
    """Stripe webhook event types."""
    CHECKOUT_COMPLETED = "checkout.session.completed"
    SUBSCRIPTION_CREATED = "customer.subscription.created"
    SUBSCRIPTION_UPDATED = "customer.subscription.updated"
    SUBSCRIPTION_DELETED = "customer.subscription.deleted"
    INVOICE_PAID = "invoice.paid"
    INVOICE_PAYMENT_FAILED = "invoice.payment_failed"
    CUSTOMER_UPDATED = "customer.updated"
    CUSTOMER_DELETED = "customer.deleted"
