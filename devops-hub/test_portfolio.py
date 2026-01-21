#!/usr/bin/env python
"""Test portfolio analyzer and revenue automation."""

import sys
from pathlib import Path

sys.path.insert(0, 'service')

print("=" * 60)
print("PORTFOLIO INTELLIGENCE TEST")
print("=" * 60)

# Test Portfolio Analyzer
print("\n[1/3] Testing Portfolio Analyzer...")
from portfolio_analyzer import ProjectAnalyzer

analyzer = ProjectAnalyzer(Path.cwd())
summary = analyzer.get_portfolio_summary()

print(f"✓ Portfolio Analyzer operational")
print(f"  • Total projects: {summary['total_projects']}")
print(f"  • High potential: {summary['by_potential']['high']}")
print(f"  • Medium potential: {summary['by_potential']['medium']}")
print(f"  • Low potential: {summary['by_potential']['low']}")
print(f"  • Revenue ready: {summary['revenue_ready']}")
print(f"  • Revenue opportunities: {summary['revenue_opportunities']}")
print(f"  • Critical actions: {summary['critical_actions']}")

# Test Revenue Automation
print("\n[2/3] Testing Revenue Automation...")
from revenue_automation import RevenueActionExecutor

executor = RevenueActionExecutor(Path.cwd())
actions = executor.get_executable_actions()

print(f"✓ Revenue Automation operational")
print(f"  • Executable actions found: {len(actions)}")
print(f"  • Auto-executable (low risk): {sum(1 for a in actions if a['auto_executable'])}")
print(f"  • High impact actions: {sum(1 for a in actions if a['estimated_impact'] >= 70)}")

# Show top 5 projects
print("\n[3/3] Top 5 Revenue Projects:")
for i, project in enumerate(summary['top_projects'][:5], 1):
    print(f"\n  {i}. {project['name']}")
    print(f"     Score: {project['monetization']['score']} | Type: {project['type']}")
    print(f"     Revenue Streams: {', '.join(project['monetization']['revenue_streams']) if project['monetization']['revenue_streams'] else 'None identified'}")
    print(f"     Health: {project['health']['status']} ({project['health']['score']}/100)")
    if project['git']['is_repo']:
        print(f"     Git: {project['git']['modified']} modified, {project['git']['ahead']} ahead, {project['git']['behind']} behind")

print("\n" + "=" * 60)
print("ALL TESTS PASSED ✓")
print("=" * 60)
