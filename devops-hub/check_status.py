"""Check HITL system status and statistics"""
import requests
import json

print("=" * 70)
print("🎉 DEVOPS HUB - HITL SYSTEM STATUS")
print("=" * 70)

# Check backend health
try:
    health = requests.get("http://localhost:8100/health")
    if health.status_code == 200:
        print("\n✅ Backend API: RUNNING")
        print(f"   URL: http://localhost:8100")
        print(f"   Docs: http://localhost:8100/docs")
    else:
        print("\n❌ Backend API: ERROR")
except:
    print("\n❌ Backend API: NOT RUNNING")

# Get HITL statistics
try:
    stats = requests.get("http://localhost:8100/hitl/statistics").json()
    print("\n📊 HITL STATISTICS:")
    print(f"   Total Requests: {stats['total_requests']}")
    print(f"   Pending: {stats['pending_requests']}")
    print(f"   By Status: {stats['by_status']}")
    print(f"   By Priority: {stats['by_priority']}")
    print(f"   By Type: {stats['by_type']}")
    print(f"   Avg Response Time: {stats['average_response_time_hours']:.1f} hours")
except Exception as e:
    print(f"\n❌ Statistics Error: {e}")

# List all pending requests
try:
    pending = requests.get("http://localhost:8100/hitl/requests?status=pending").json()
    print(f"\n📋 PENDING REQUESTS ({len(pending)}):")
    for req in pending:
        print(f"\n   🔸 {req['title']}")
        print(f"      ID: {req['id']}")
        print(f"      Type: {req['request_type']}")
        print(f"      Priority: {req['priority']}")
        print(f"      Agent: {req['agent_id']}")
        print(f"      Required Fields: {len(req['required_fields'])}")
except Exception as e:
    print(f"\n❌ Requests Error: {e}")

print("\n" + "=" * 70)
print("🌐 ACCESS POINTS:")
print("=" * 70)
print("\n   Frontend UI: http://localhost:5173")
print("   Human Actions: http://localhost:5173/human-actions")
print("   Backend API: http://localhost:8100")
print("   API Documentation: http://localhost:8100/docs")

print("\n" + "=" * 70)
print("✨ NEXT STEPS:")
print("=" * 70)
print("""
1. Open http://localhost:5173 in your browser
2. Click "Continue as Guest" to login
3. Navigate to "Human Actions" in the menu
4. View and fulfill the pending requests
5. Test the full HITL workflow!
""")

print("=" * 70)
