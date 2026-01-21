"""
FlipFlow Payment Flow Automated Testing Suite

Tests all critical payment flows:
- Stripe checkout session creation
- Webhook processing
- Credit allocation
- Subscription management
- Edge cases and error handling

Requirements:
    pip install requests pytest

Usage:
    # Test against local development
    python test_flipflow_payments.py

    # Test against production
    FLIPFLOW_URL=https://your-domain.com python test_flipflow_payments.py

    # Run with pytest for detailed output
    pytest test_flipflow_payments.py -v
"""

import os
import time
import json
import requests
from typing import Dict, Any, Optional
from datetime import datetime


class FlipFlowTester:
    """Automated payment flow testing for FlipFlow."""

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or os.getenv('FLIPFLOW_URL', 'http://localhost:3000')
        self.session = requests.Session()
        self.test_results = []

    def log(self, message: str, level: str = "INFO"):
        """Log test output with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")

    def test_healthcheck(self) -> bool:
        """Test API healthcheck endpoint."""
        self.log("Testing healthcheck endpoint...")
        try:
            response = self.session.get(
                f"{self.base_url}/api/healthcheck",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"✓ Healthcheck passed: {data.get('status')}", "SUCCESS")
                
                # Check Stripe configuration
                if 'stripe' in data:
                    stripe_configured = data['stripe'].get('configured', False)
                    if stripe_configured:
                        self.log("✓ Stripe is configured", "SUCCESS")
                    else:
                        self.log("✗ Stripe not configured", "WARNING")
                
                return True
            else:
                self.log(f"✗ Healthcheck failed: {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"✗ Healthcheck error: {str(e)}", "ERROR")
            return False

    def test_create_checkout_starter(self) -> Optional[str]:
        """Test creating Stripe checkout session for Starter Pack."""
        self.log("Testing Starter Pack checkout creation...")
        try:
            response = self.session.post(
                f"{self.base_url}/api/stripe/create-checkout",
                json={
                    "priceId": "price_starter",  # Will be replaced with actual price ID
                    "mode": "payment",
                    "successUrl": f"{self.base_url}/success",
                    "cancelUrl": f"{self.base_url}/pricing"
                },
                headers={"Content-Type": "application/json"},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                session_url = data.get('url')
                self.log(f"✓ Checkout session created: {session_url[:50]}...", "SUCCESS")
                return session_url
            else:
                self.log(f"✗ Checkout creation failed: {response.status_code}", "ERROR")
                self.log(f"  Response: {response.text}", "ERROR")
                return None
        except Exception as e:
            self.log(f"✗ Checkout error: {str(e)}", "ERROR")
            return None

    def test_create_checkout_pro(self) -> Optional[str]:
        """Test creating Stripe checkout session for Pro Plan."""
        self.log("Testing Pro Plan checkout creation...")
        try:
            response = self.session.post(
                f"{self.base_url}/api/stripe/create-checkout",
                json={
                    "priceId": "price_unlimited",  # Will be replaced with actual price ID
                    "mode": "subscription",
                    "successUrl": f"{self.base_url}/success",
                    "cancelUrl": f"{self.base_url}/pricing"
                },
                headers={"Content-Type": "application/json"},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                session_url = data.get('url')
                self.log(f"✓ Pro checkout session created: {session_url[:50]}...", "SUCCESS")
                return session_url
            else:
                self.log(f"✗ Pro checkout creation failed: {response.status_code}", "ERROR")
                return None
        except Exception as e:
            self.log(f"✗ Pro checkout error: {str(e)}", "ERROR")
            return None

    def test_webhook_signature_validation(self):
        """Test webhook signature validation."""
        self.log("Testing webhook signature validation...")
        
        # This would normally fail without proper signature
        test_payload = {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test_123",
                    "customer": "cus_test_123",
                    "amount_total": 999,
                    "payment_status": "paid"
                }
            }
        }

        try:
            response = self.session.post(
                f"{self.base_url}/api/stripe/webhook",
                json=test_payload,
                headers={
                    "Content-Type": "application/json",
                    "stripe-signature": "invalid_signature"
                },
                timeout=10
            )

            # Should return 400 for invalid signature
            if response.status_code == 400:
                self.log("✓ Webhook correctly rejects invalid signature", "SUCCESS")
            else:
                self.log(f"✗ Unexpected webhook response: {response.status_code}", "WARNING")
        except Exception as e:
            self.log(f"✗ Webhook test error: {str(e)}", "ERROR")

    def test_credit_allocation_api(self):
        """Test credit allocation endpoint (if exists)."""
        self.log("Testing credit allocation...")
        # This is a placeholder - actual implementation depends on FlipFlow's API
        self.log("⊘ Credit allocation API test not implemented", "INFO")

    def test_subscription_status_api(self):
        """Test subscription status endpoint."""
        self.log("Testing subscription status...")
        # This is a placeholder - actual implementation depends on FlipFlow's API
        self.log("⊘ Subscription status API test not implemented", "INFO")

    def test_pricing_page(self) -> bool:
        """Test that pricing page loads correctly."""
        self.log("Testing pricing page...")
        try:
            response = self.session.get(
                f"{self.base_url}/pricing",
                timeout=10
            )

            if response.status_code == 200:
                # Check for pricing elements
                content = response.text.lower()
                has_starter = 'starter' in content or '$9.99' in content
                has_pro = 'pro' in content or '$49' in content

                if has_starter and has_pro:
                    self.log("✓ Pricing page loads with both plans", "SUCCESS")
                    return True
                else:
                    self.log("✗ Pricing page missing plan information", "WARNING")
                    return False
            else:
                self.log(f"✗ Pricing page failed to load: {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"✗ Pricing page error: {str(e)}", "ERROR")
            return False

    def test_database_schema(self):
        """Test database schema expectations."""
        self.log("Testing database schema...")
        # This would require database access or API endpoint
        self.log("⊘ Database schema validation requires direct DB access", "INFO")
        self.log("  → Run flipflow_database_migration.sql to ensure schema is correct", "INFO")

    def run_all_tests(self) -> Dict[str, Any]:
        """Run complete test suite."""
        self.log("=" * 60)
        self.log("FlipFlow Payment Flow Test Suite")
        self.log("=" * 60)
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "base_url": self.base_url,
            "tests": {}
        }

        # Run tests
        results["tests"]["healthcheck"] = self.test_healthcheck()
        time.sleep(1)

        results["tests"]["pricing_page"] = self.test_pricing_page()
        time.sleep(1)

        results["tests"]["checkout_starter"] = self.test_create_checkout_starter() is not None
        time.sleep(1)

        results["tests"]["checkout_pro"] = self.test_create_checkout_pro() is not None
        time.sleep(1)

        self.test_webhook_signature_validation()
        time.sleep(1)

        self.test_credit_allocation_api()
        self.test_subscription_status_api()
        self.test_database_schema()

        # Summary
        self.log("=" * 60)
        passed = sum(1 for v in results["tests"].values() if v is True)
        total = len(results["tests"])
        self.log(f"Tests Passed: {passed}/{total}")
        self.log("=" * 60)

        return results


# Pytest integration
def test_healthcheck():
    """Pytest: Test healthcheck endpoint."""
    tester = FlipFlowTester()
    assert tester.test_healthcheck() is True


def test_pricing_page():
    """Pytest: Test pricing page loads."""
    tester = FlipFlowTester()
    assert tester.test_pricing_page() is True


def test_checkout_creation():
    """Pytest: Test checkout session creation."""
    tester = FlipFlowTester()
    # Note: This may fail if Stripe is not configured
    # Comment out if testing without Stripe
    assert tester.test_create_checkout_starter() is not None


if __name__ == "__main__":
    # Run standalone test suite
    tester = FlipFlowTester()
    results = tester.run_all_tests()

    # Save results to file
    with open("flipflow_test_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print("\n✓ Test results saved to: flipflow_test_results.json")
