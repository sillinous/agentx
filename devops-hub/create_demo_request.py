"""Create a demo HITL request for testing the UI"""
import requests
import json

# Create a realistic Stripe API key request
request_data = {
    "agent_id": "stripe-integration-agent",
    "request_type": "api_key",
    "title": "Stripe Production API Keys Required",
    "description": "Need production Stripe API credentials to enable payment processing for FlipFlow SaaS platform. This will allow us to accept customer payments and subscriptions.",
    "required_fields": {
        "publishable_key": "Stripe Publishable Key (starts with pk_live_...)",
        "secret_key": "Stripe Secret Key (starts with sk_live_...)",
        "webhook_secret": "Webhook Signing Secret (starts with whsec_...)"
    },
    "priority": "high",
    "context": {
        "service": "stripe",
        "environment": "production",
        "project": "FlipFlow",
        "purpose": "Payment processing and subscription management",
        "documentation": "https://stripe.com/docs/keys"
    }
}

# Create the request
response = requests.post(
    "http://localhost:8100/hitl/requests",
    json=request_data
)

if response.status_code == 200:
    request = response.json()
    print("✅ Demo HITL request created successfully!")
    print(f"\nRequest ID: {request['id']}")
    print(f"Title: {request['title']}")
    print(f"Priority: {request['priority']}")
    print(f"Status: {request['status']}")
    print(f"\nRequired fields:")
    for field, desc in request['required_fields'].items():
        print(f"  - {field}: {desc}")
    print(f"\n🌐 View in UI: http://localhost:5173/human-actions")
else:
    print(f"❌ Error: {response.status_code}")
    print(response.text)
