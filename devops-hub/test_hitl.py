"""
Test script for HITL (Human-in-the-Loop) system.
Run this to verify the HITL implementation works correctly.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from service.hitl_service import get_hitl_service
import json


def test_hitl_system():
    """Test the complete HITL system workflow."""
    
    print("🧪 Testing HITL System\n")
    print("=" * 60)
    
    # Initialize service
    print("\n1️⃣  Initializing HITL service...")
    hitl = get_hitl_service()
    print("✅ HITL service initialized")
    
    # Create a test request
    print("\n2️⃣  Creating test request...")
    request = hitl.create_request(
        agent_id="test-agent",
        request_type="api_key",
        title="Test API Key Request",
        description="Testing the HITL system end-to-end",
        required_fields={
            "api_key": "Your API key",
            "api_secret": "Your API secret"
        },
        priority="medium",
        context={
            "service": "test-service",
            "environment": "development",
            "purpose": "integration testing"
        }
    )
    print(f"✅ Request created with ID: {request.id}")
    print(f"   Status: {request.status}")
    print(f"   Priority: {request.priority}")
    
    # List all requests
    print("\n3️⃣  Listing all requests...")
    all_requests = hitl.list_requests()
    print(f"✅ Found {len(all_requests)} total request(s)")
    
    # List pending requests
    print("\n4️⃣  Listing pending requests...")
    pending = hitl.list_requests(status="pending")
    print(f"✅ Found {len(pending)} pending request(s)")
    
    # Get request details
    print("\n5️⃣  Retrieving request details...")
    retrieved = hitl.get_request(request.id)
    assert retrieved is not None, "Failed to retrieve request"
    assert retrieved.id == request.id
    print(f"✅ Retrieved request: {retrieved.title}")
    print(f"   Required fields: {json.dumps(retrieved.required_fields, indent=2)}")
    
    # Fulfill the request
    print("\n6️⃣  Fulfilling request...")
    fulfilled = hitl.fulfill_request(
        request_id=request.id,
        fulfilled_by="test-user",
        response_data={
            "api_key": "test_key_12345",
            "api_secret": "test_secret_67890"
        },
        notes="Test fulfillment - all fields provided"
    )
    assert fulfilled is not None, "Failed to fulfill request"
    assert fulfilled.status == "fulfilled"
    assert fulfilled.fulfilled_by == "test-user"
    print(f"✅ Request fulfilled by: {fulfilled.fulfilled_by}")
    print(f"   Status: {fulfilled.status}")
    print(f"   Response data: {json.dumps(fulfilled.response_data, indent=2)}")
    
    # Get statistics
    print("\n7️⃣  Getting statistics...")
    stats = hitl.get_statistics()
    print(f"✅ Statistics:")
    print(f"   Total requests: {stats['total_requests']}")
    print(f"   Pending: {stats['pending_requests']}")
    print(f"   By status: {stats['by_status']}")
    print(f"   By priority: {stats['by_priority']}")
    print(f"   By type: {stats['by_type']}")
    
    # Test rejection flow
    print("\n8️⃣  Testing rejection flow...")
    reject_request = hitl.create_request(
        agent_id="test-agent",
        request_type="payment_authorization",
        title="Test Rejection Request",
        description="This request will be rejected",
        required_fields={"amount": "Amount to authorize"},
        priority="low"
    )
    
    rejected = hitl.reject_request(
        request_id=reject_request.id,
        rejected_by="test-admin",
        reason="Test rejection - insufficient information"
    )
    assert rejected is not None, "Failed to reject request"
    assert rejected.status == "rejected"
    print(f"✅ Request rejected by: {rejected.fulfilled_by}")
    print(f"   Reason: {rejected.notes}")
    
    # Final statistics
    print("\n9️⃣  Final statistics...")
    final_stats = hitl.get_statistics()
    print(f"✅ Final counts:")
    print(f"   Total: {final_stats['total_requests']}")
    print(f"   Fulfilled: {final_stats['by_status'].get('fulfilled', 0)}")
    print(f"   Rejected: {final_stats['by_status'].get('rejected', 0)}")
    print(f"   Pending: {final_stats['pending_requests']}")
    
    print("\n" + "=" * 60)
    print("🎉 All tests passed! HITL system is working correctly.")
    print("\n💡 Next steps:")
    print("   1. Start the backend: python service/api.py")
    print("   2. Start the frontend: cd frontend && npm run dev")
    print("   3. Visit: http://localhost:3000/human-actions")
    print("   4. Test the UI by fulfilling/rejecting requests")
    print("=" * 60)


if __name__ == "__main__":
    try:
        test_hitl_system()
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
