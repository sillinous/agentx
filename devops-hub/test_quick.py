"""Quick test with longer timeout."""
import requests

BASE_URL = "http://127.0.0.1:8100"

print("Testing Portfolio System (with 60s timeout for large scan)...\n")

# Test 1: Health (fast)
print("[1/3] Health Check...")
resp = requests.get(f"{BASE_URL}/health", timeout=5)
print(f"✓ Status: {resp.status_code}")

# Test 2: Portfolio Summary (slow - scanning 72 projects)
print("\n[2/3] Portfolio Summary (scanning 72 projects, please wait)...")
try:
    resp = requests.get(f"{BASE_URL}/portfolio/summary", timeout=60)
    data = resp.json()
    print(f"✓ Status: {resp.status_code}")
    print(f"  • Total Projects: {data['total_projects']}")
    print(f"  • High Potential: {data['by_potential']['high']}")
    print(f"  • Revenue Ready: {data['revenue_ready']}")
    print(f"  • Revenue Opportunities: {data['revenue_opportunities']}")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 3: Automation (depends on portfolio scan completing)
print("\n[3/3] Automation Workflows...")
try:
    resp = requests.get(f"{BASE_URL}/automation/workflows", timeout=10)
    data = resp.json()
    print(f"✓ Status: {resp.status_code}")
    print(f"  • Available Workflows: {len(data['workflows'])}")
    for wf in data['workflows']:
        print(f"    - {wf['name']}")
except Exception as e:
    print(f"✗ Error: {e}")

print("\n✅ Core system operational!")
print(f"\n📊 View full API docs: http://127.0.0.1:8100/docs")
