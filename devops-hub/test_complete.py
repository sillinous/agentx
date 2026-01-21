"""Complete API test suite."""
import requests
import json

BASE_URL = "http://127.0.0.1:8100"

def test_endpoint(name, url):
    """Test an endpoint and return result."""
    try:
        response = requests.get(url, timeout=10)
        return {
            "name": name,
            "status": response.status_code,
            "success": response.status_code == 200,
            "data": response.json() if response.status_code == 200 else None
        }
    except Exception as e:
        return {
            "name": name,
            "status": "ERROR",
            "success": False,
            "error": str(e)
        }

print("=" * 70)
print("COMPLETE API TEST SUITE")
print("=" * 70)

# Test all endpoints
endpoints = [
    ("Health Check", f"{BASE_URL}/health"),
    ("Portfolio Summary", f"{BASE_URL}/portfolio/summary"),
    ("All Projects", f"{BASE_URL}/portfolio/projects"),
    ("Recommendations", f"{BASE_URL}/portfolio/recommendations"),
    ("Automation Actions", f"{BASE_URL}/automation/actions"),
    ("Automation Workflows", f"{BASE_URL}/automation/workflows"),
]

results = []
for name, url in endpoints:
    print(f"\nTesting: {name}...")
    result = test_endpoint(name, url)
    results.append(result)
    
    if result["success"]:
        print(f"  ✓ Status: {result['status']}")
        if "summary" in name.lower():
            data = result["data"]
            print(f"    • Total Projects: {data.get('total_projects', 'N/A')}")
            print(f"    • High Potential: {data.get('by_potential', {}).get('high', 'N/A')}")
            print(f"    • Revenue Opportunities: {data.get('revenue_opportunities', 'N/A')}")
        elif "actions" in name.lower():
            data = result["data"]
            print(f"    • Total Actions: {data.get('total', 'N/A')}")
        elif "workflows" in name.lower():
            data = result["data"]
            print(f"    • Available Workflows: {len(data.get('workflows', []))}")
    else:
        print(f"  ✗ FAILED: {result.get('status', 'ERROR')}")
        if "error" in result:
            print(f"    Error: {result['error']}")

# Summary
print("\n" + "=" * 70)
print("TEST SUMMARY")
print("=" * 70)
passed = sum(1 for r in results if r["success"])
total = len(results)
print(f"Passed: {passed}/{total}")
print(f"Success Rate: {(passed/total*100):.1f}%")

if passed == total:
    print("\n✅ ALL TESTS PASSED - System fully operational!")
else:
    print(f"\n⚠️  {total - passed} endpoint(s) need attention")

# If automation works, show some actions
if any(r["name"] == "Automation Actions" and r["success"] for r in results):
    print("\n" + "=" * 70)
    print("REVENUE AUTOMATION STATUS")
    print("=" * 70)
    actions_result = next(r for r in results if r["name"] == "Automation Actions")
    data = actions_result["data"]
    auto_exec = sum(1 for a in data.get("actions", []) if a.get("auto_executable", False))
    print(f"✓ Executable Actions Found: {data.get('total', 0)}")
    print(f"✓ Safe Auto-Executable: {auto_exec}")
    print(f"✓ Revenue Automation: OPERATIONAL")
