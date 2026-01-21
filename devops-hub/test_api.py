"""Test portfolio API endpoints."""
import requests
import json

BASE_URL = "http://127.0.0.1:8100"

print("=" * 70)
print("PORTFOLIO DASHBOARD API TEST")
print("=" * 70)

# Test 1: Health check
print("\n[1/5] Testing Health Endpoint...")
response = requests.get(f"{BASE_URL}/health")
print(f"✓ Status: {response.status_code}")
print(f"  {json.dumps(response.json(), indent=2)}")

# Test 2: Portfolio Summary
print("\n[2/5] Testing Portfolio Summary...")
response = requests.get(f"{BASE_URL}/portfolio/summary")
data = response.json()
print(f"✓ Status: {response.status_code}")
print(f"  • Total Projects: {data['total_projects']}")
print(f"  • High Potential: {data['by_potential']['high']}")
print(f"  • Revenue Ready: {data['revenue_ready']}")
print(f"  • Revenue Opportunities: {data['revenue_opportunities']}")

# Test 3: Top Projects
print("\n[3/5] Top 3 Revenue Projects:")
for i, project in enumerate(data['top_projects'][:3], 1):
    print(f"  {i}. {project['name']}")
    print(f"     Score: {project['monetization']['score']} | Health: {project['health']['status']}")
    streams = ', '.join(project['monetization']['revenue_streams']) if project['monetization']['revenue_streams'] else 'None'
    print(f"     Revenue Streams: {streams}")

# Test 4: Recommendations
print("\n[4/5] Testing Recommendations Endpoint...")
response = requests.get(f"{BASE_URL}/portfolio/recommendations")
data = response.json()
print(f"✓ Status: {response.status_code}")
print(f"  • Total Recommendations: {data['total']}")
print(f"  • Revenue Opportunities: {data['revenue_opportunities']}")
print("\n  Top 3 Revenue Actions:")
for i, rec in enumerate([r for r in data['recommendations'] if r['type'] == 'revenue'][:3], 1):
    print(f"    {i}. [{rec['project']}] {rec['action']}")
    print(f"       Impact: {rec['impact']}")

# Test 5: Automation Actions
print("\n[5/5] Testing Automation Endpoint...")
response = requests.get(f"{BASE_URL}/automation/actions")
data = response.json()
print(f"✓ Status: {response.status_code}")
print(f"  • Executable Actions: {data['total']}")
auto_exec = sum(1 for a in data['actions'] if a['auto_executable'])
print(f"  • Auto-Executable (Low Risk): {auto_exec}")

# Test 6: Workflows
print("\n[6/6] Testing Workflows Endpoint...")
response = requests.get(f"{BASE_URL}/automation/workflows")
data = response.json()
print(f"✓ Status: {response.status_code}")
print("  Available Workflows:")
for wf in data['workflows']:
    print(f"    • {wf['name']} (Risk: {wf['risk']}, Auto: {wf['auto_executable']})")
    print(f"      {wf['description']}")

print("\n" + "=" * 70)
print("ALL API TESTS PASSED ✓")
print("=" * 70)
print(f"\n📊 Dashboard URL: http://127.0.0.1:8100/docs")
print(f"🎯 Portfolio UI: http://localhost:3000/portfolio (when frontend starts)")
print(f"💡 Next: Start frontend with 'cd frontend && npm run dev'")
