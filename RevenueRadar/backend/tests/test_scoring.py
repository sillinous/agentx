"""Comprehensive tests for the monetization scoring engine."""
import pytest
from scanner.scoring import (
    calculate_maturity_score,
    calculate_revenue_score,
    calculate_effort_score,
    calculate_overall_score,
    determine_tier,
    get_revenue_potential,
    get_project_status,
    score_project,
    generate_opportunities,
    TIER1_PROJECTS,
    TIER2_PROJECTS,
    TIER3_PROJECTS,
)


class TestMaturityScore:
    """Tests for maturity score calculation."""

    def test_empty_metadata_returns_zero(self):
        """Empty metadata should return 0."""
        assert calculate_maturity_score({}) == 0

    def test_has_tests_adds_20_points(self):
        """Projects with tests get +20 points."""
        metadata = {"has_tests": True}
        assert calculate_maturity_score(metadata) == 20

    def test_has_docker_adds_15_points(self):
        """Projects with Docker get +15 points."""
        metadata = {"has_docker": True}
        assert calculate_maturity_score(metadata) == 15

    def test_has_readme_adds_10_points(self):
        """Projects with README get +10 points."""
        metadata = {"has_readme": True}
        assert calculate_maturity_score(metadata) == 10

    def test_has_ci_cd_adds_15_points(self):
        """Projects with CI/CD get +15 points."""
        metadata = {"has_ci_cd": True}
        assert calculate_maturity_score(metadata) == 15

    def test_loc_over_1000_adds_10_points(self):
        """Projects with >1000 LOC get +10 points."""
        metadata = {"loc_estimate": 1001}
        assert calculate_maturity_score(metadata) == 10

    def test_loc_under_1000_adds_nothing(self):
        """Projects with <1000 LOC get no bonus."""
        metadata = {"loc_estimate": 999}
        assert calculate_maturity_score(metadata) == 0

    def test_has_typescript_adds_10_points(self):
        """Projects with TypeScript get +10 points."""
        metadata = {"has_typescript": True}
        assert calculate_maturity_score(metadata) == 10

    def test_has_package_json_adds_10_points(self):
        """Projects with package.json get +10 points."""
        metadata = {"has_package_json": True}
        assert calculate_maturity_score(metadata) == 10

    def test_has_requirements_adds_10_points(self):
        """Projects with requirements.txt get +10 points."""
        metadata = {"has_requirements": True}
        assert calculate_maturity_score(metadata) == 10

    def test_fullstack_project_bonus(self):
        """Projects with both frontend and backend tech get +10 points."""
        metadata = {"tech_stack": ["Next.js", "FastAPI"]}
        assert calculate_maturity_score(metadata) == 10

    def test_frontend_only_no_bonus(self):
        """Frontend-only projects don't get fullstack bonus."""
        metadata = {"tech_stack": ["React", "Vue"]}
        assert calculate_maturity_score(metadata) == 0

    def test_backend_only_no_bonus(self):
        """Backend-only projects don't get fullstack bonus."""
        metadata = {"tech_stack": ["FastAPI", "Django"]}
        assert calculate_maturity_score(metadata) == 0

    def test_all_features_gives_maximum_score(self):
        """Project with all features should approach max score."""
        metadata = {
            "has_tests": True,
            "has_docker": True,
            "has_readme": True,
            "has_ci_cd": True,
            "loc_estimate": 5000,
            "has_typescript": True,
            "has_package_json": True,
            "tech_stack": ["Next.js", "Express"],
        }
        # 20 + 15 + 10 + 15 + 10 + 10 + 10 + 10 = 100
        assert calculate_maturity_score(metadata) == 100

    def test_score_capped_at_100(self):
        """Score should not exceed 100."""
        metadata = {
            "has_tests": True,
            "has_docker": True,
            "has_readme": True,
            "has_ci_cd": True,
            "loc_estimate": 5000,
            "has_typescript": True,
            "has_package_json": True,
            "has_requirements": True,  # Both package managers
            "tech_stack": ["Next.js", "FastAPI"],
        }
        assert calculate_maturity_score(metadata) <= 100


class TestRevenueScore:
    """Tests for revenue readiness score calculation."""

    def test_empty_metadata_returns_zero(self):
        """Empty metadata should return 0."""
        assert calculate_revenue_score({}) == 0

    def test_has_stripe_adds_30_points(self):
        """Projects with Stripe get +30 points (highest value)."""
        metadata = {"has_stripe": True}
        assert calculate_revenue_score(metadata) == 30

    def test_has_auth_adds_15_points(self):
        """Projects with auth get +15 points."""
        metadata = {"has_auth": True}
        assert calculate_revenue_score(metadata) == 15

    def test_has_api_adds_20_points(self):
        """Projects with API get +20 points."""
        metadata = {"has_api": True}
        assert calculate_revenue_score(metadata) == 20

    def test_has_database_adds_15_points(self):
        """Projects with database get +15 points."""
        metadata = {"has_database": True}
        assert calculate_revenue_score(metadata) == 15

    def test_has_docker_adds_10_points(self):
        """Projects with Docker (deployment ready) get +10 points."""
        metadata = {"has_docker": True}
        assert calculate_revenue_score(metadata) == 10

    def test_ai_tech_bonus(self):
        """Projects with AI/ML tech get +10 bonus points."""
        metadata = {"tech_stack": ["OpenAI"]}
        assert calculate_revenue_score(metadata) == 10

    def test_anthropic_claude_ai_bonus(self):
        """Projects using Anthropic Claude get AI bonus."""
        metadata = {"tech_stack": ["Anthropic Claude"]}
        assert calculate_revenue_score(metadata) == 10

    def test_pytorch_ai_bonus(self):
        """Projects using PyTorch get AI bonus."""
        metadata = {"tech_stack": ["PyTorch"]}
        assert calculate_revenue_score(metadata) == 10

    def test_tensorflow_ai_bonus(self):
        """Projects using TensorFlow get AI bonus."""
        metadata = {"tech_stack": ["TensorFlow"]}
        assert calculate_revenue_score(metadata) == 10

    def test_non_ai_tech_no_bonus(self):
        """Non-AI tech should not trigger bonus."""
        metadata = {"tech_stack": ["React", "Node.js"]}
        assert calculate_revenue_score(metadata) == 0

    def test_maximum_revenue_score(self):
        """Full revenue-ready project should score 100."""
        metadata = {
            "has_stripe": True,  # 30
            "has_auth": True,  # 15
            "has_api": True,  # 20
            "has_database": True,  # 15
            "has_docker": True,  # 10
            "tech_stack": ["OpenAI"],  # 10
        }
        # 30 + 15 + 20 + 15 + 10 + 10 = 100
        assert calculate_revenue_score(metadata) == 100

    def test_score_capped_at_100(self):
        """Score should not exceed 100."""
        metadata = {
            "has_stripe": True,
            "has_auth": True,
            "has_api": True,
            "has_database": True,
            "has_docker": True,
            "tech_stack": ["OpenAI", "PyTorch", "TensorFlow"],  # Multiple AI
        }
        assert calculate_revenue_score(metadata) <= 100


class TestEffortScore:
    """Tests for effort score calculation (100 = easy)."""

    def test_full_featured_project_keeps_100(self):
        """Fully featured project should keep score of 100."""
        metadata = {
            "has_tests": True,
            "has_readme": True,
            "has_auth": True,
            "has_stripe": True,
            "has_docker": True,
            "has_database": True,
        }
        assert calculate_effort_score(metadata) == 100

    def test_no_tests_deducts_10(self):
        """Missing tests deducts 10 points."""
        metadata = {"has_tests": False, "has_readme": True, "has_auth": True,
                    "has_stripe": True, "has_docker": True, "has_database": True}
        assert calculate_effort_score(metadata) == 90

    def test_no_readme_deducts_5(self):
        """Missing README deducts 5 points."""
        metadata = {"has_tests": True, "has_readme": False, "has_auth": True,
                    "has_stripe": True, "has_docker": True, "has_database": True}
        assert calculate_effort_score(metadata) == 95

    def test_no_auth_deducts_15(self):
        """Missing auth deducts 15 points."""
        metadata = {"has_tests": True, "has_readme": True, "has_auth": False,
                    "has_stripe": True, "has_docker": True, "has_database": True}
        assert calculate_effort_score(metadata) == 85

    def test_no_stripe_deducts_20(self):
        """Missing Stripe deducts 20 points (highest penalty)."""
        metadata = {"has_tests": True, "has_readme": True, "has_auth": True,
                    "has_stripe": False, "has_docker": True, "has_database": True}
        assert calculate_effort_score(metadata) == 80

    def test_no_docker_deducts_10(self):
        """Missing Docker deducts 10 points."""
        metadata = {"has_tests": True, "has_readme": True, "has_auth": True,
                    "has_stripe": True, "has_docker": False, "has_database": True}
        assert calculate_effort_score(metadata) == 90

    def test_no_database_deducts_10(self):
        """Missing database deducts 10 points."""
        metadata = {"has_tests": True, "has_readme": True, "has_auth": True,
                    "has_stripe": True, "has_docker": True, "has_database": False}
        assert calculate_effort_score(metadata) == 90

    def test_empty_project_gets_minimum_viable(self):
        """Empty project loses all points but doesn't go negative."""
        metadata = {}
        # 100 - 10 - 5 - 15 - 20 - 10 - 10 = 30
        assert calculate_effort_score(metadata) == 30

    def test_score_minimum_is_zero(self):
        """Score should not go below 0."""
        # Even with all penalties, score should be >= 0
        metadata = {}
        assert calculate_effort_score(metadata) >= 0


class TestOverallScore:
    """Tests for overall score calculation."""

    def test_equal_scores_gives_weighted_average(self):
        """Equal input scores should give weighted average."""
        # 50 * 0.25 + 50 * 0.40 + 50 * 0.35 = 50
        assert calculate_overall_score(50, 50, 50) == 50

    def test_revenue_has_highest_weight(self):
        """Revenue score should have 40% weight (highest)."""
        # Only revenue = 100, others = 0
        # 0 * 0.25 + 100 * 0.40 + 0 * 0.35 = 40
        assert calculate_overall_score(0, 100, 0) == 40

    def test_effort_has_second_highest_weight(self):
        """Effort score should have 35% weight."""
        # Only effort = 100, others = 0
        # 0 * 0.25 + 0 * 0.40 + 100 * 0.35 = 35
        assert calculate_overall_score(0, 0, 100) == 35

    def test_maturity_has_lowest_weight(self):
        """Maturity score should have 25% weight (lowest)."""
        # Only maturity = 100, others = 0
        # 100 * 0.25 + 0 * 0.40 + 0 * 0.35 = 25
        assert calculate_overall_score(100, 0, 0) == 25

    def test_perfect_scores_gives_100(self):
        """All perfect scores should give 100."""
        # 100 * 0.25 + 100 * 0.40 + 100 * 0.35 = 100
        assert calculate_overall_score(100, 100, 100) == 100

    def test_returns_integer(self):
        """Overall score should be an integer."""
        result = calculate_overall_score(33, 67, 81)
        assert isinstance(result, int)


class TestDetermineTier:
    """Tests for tier determination."""

    def test_manual_override_tier1(self):
        """Known Tier 1 projects should always be Tier 1."""
        for project_name in TIER1_PROJECTS:
            assert determine_tier(project_name, 0) == "tier1"
            assert determine_tier(project_name, 30) == "tier1"
            assert determine_tier(project_name, 100) == "tier1"

    def test_manual_override_tier2(self):
        """Known Tier 2 projects should always be Tier 2."""
        for project_name in TIER2_PROJECTS:
            assert determine_tier(project_name, 0) == "tier2"
            assert determine_tier(project_name, 100) == "tier2"

    def test_manual_override_tier3(self):
        """Known Tier 3 projects should always be Tier 3."""
        for project_name in TIER3_PROJECTS:
            assert determine_tier(project_name, 0) == "tier3"
            assert determine_tier(project_name, 100) == "tier3"

    def test_high_score_auto_tier1(self):
        """Unknown projects with score >= 70 get Tier 1."""
        assert determine_tier("UnknownProject", 70) == "tier1"
        assert determine_tier("UnknownProject", 85) == "tier1"
        assert determine_tier("UnknownProject", 100) == "tier1"

    def test_medium_score_auto_tier2(self):
        """Unknown projects with score 50-69 get Tier 2."""
        assert determine_tier("UnknownProject", 50) == "tier2"
        assert determine_tier("UnknownProject", 60) == "tier2"
        assert determine_tier("UnknownProject", 69) == "tier2"

    def test_low_score_auto_tier3(self):
        """Unknown projects with score < 50 get Tier 3."""
        assert determine_tier("UnknownProject", 0) == "tier3"
        assert determine_tier("UnknownProject", 25) == "tier3"
        assert determine_tier("UnknownProject", 49) == "tier3"


class TestGetRevenuePotential:
    """Tests for revenue potential estimation."""

    def test_tier1_project_uses_override(self):
        """Tier 1 projects use their manual revenue estimates."""
        for name, data in TIER1_PROJECTS.items():
            min_rev, max_rev = get_revenue_potential(name, 50)
            assert min_rev == data["min"]
            assert max_rev == data["max"]

    def test_tier2_project_uses_override(self):
        """Tier 2 projects use their manual revenue estimates."""
        for name, data in TIER2_PROJECTS.items():
            min_rev, max_rev = get_revenue_potential(name, 50)
            assert min_rev == data["min"]
            assert max_rev == data["max"]

    def test_tier3_project_uses_override(self):
        """Tier 3 projects use their manual revenue estimates."""
        for name, data in TIER3_PROJECTS.items():
            min_rev, max_rev = get_revenue_potential(name, 50)
            assert min_rev == data["min"]
            assert max_rev == data["max"]

    def test_unknown_project_calculates_from_score(self):
        """Unknown projects calculate revenue from score."""
        min_rev, max_rev = get_revenue_potential("UnknownProject", 50)
        # base_min = 50 * 30 = 1500
        # base_max = 50 * 150 = 7500
        assert min_rev == 1500
        assert max_rev == 7500

    def test_zero_score_gives_zero_revenue(self):
        """Projects with 0 revenue score get 0 revenue potential."""
        min_rev, max_rev = get_revenue_potential("UnknownProject", 0)
        assert min_rev == 0
        assert max_rev == 0

    def test_max_score_gives_high_revenue(self):
        """Projects with max revenue score get high potential."""
        min_rev, max_rev = get_revenue_potential("UnknownProject", 100)
        assert min_rev == 3000  # 100 * 30
        assert max_rev == 15000  # 100 * 150


class TestGetProjectStatus:
    """Tests for project status determination."""

    def test_manual_override_status(self):
        """Known projects use their manual status."""
        for tier_dict in [TIER1_PROJECTS, TIER2_PROJECTS, TIER3_PROJECTS]:
            for name, data in tier_dict.items():
                status = get_project_status(name, {})
                assert status == data["status"]

    def test_stripe_and_docker_means_ready(self):
        """Projects with Stripe and Docker are ready."""
        metadata = {"has_stripe": True, "has_docker": True}
        assert get_project_status("UnknownProject", metadata) == "ready"

    def test_api_means_development(self):
        """Projects with API are in development."""
        metadata = {"has_api": True}
        assert get_project_status("UnknownProject", metadata) == "development"

    def test_database_means_development(self):
        """Projects with database are in development."""
        metadata = {"has_database": True}
        assert get_project_status("UnknownProject", metadata) == "development"

    def test_empty_project_is_discovery(self):
        """Projects without indicators are in discovery."""
        assert get_project_status("UnknownProject", {}) == "discovery"


class TestScoreProject:
    """Tests for full project scoring."""

    def test_returns_all_score_fields(self):
        """score_project should return all required fields."""
        result = score_project("TestProject", {})
        required_fields = [
            "maturity_score",
            "revenue_score",
            "effort_score",
            "overall_score",
            "tier",
            "status",
            "revenue_potential_min",
            "revenue_potential_max",
        ]
        for field in required_fields:
            assert field in result

    def test_scores_are_integers(self):
        """All scores should be integers."""
        result = score_project("TestProject", {"has_tests": True})
        assert isinstance(result["maturity_score"], int)
        assert isinstance(result["revenue_score"], int)
        assert isinstance(result["effort_score"], int)
        assert isinstance(result["overall_score"], int)

    def test_tier_is_valid(self):
        """Tier should be one of the valid values."""
        result = score_project("TestProject", {})
        assert result["tier"] in ["tier1", "tier2", "tier3"]

    def test_status_is_valid(self):
        """Status should be one of the valid values."""
        result = score_project("TestProject", {})
        assert result["status"] in ["discovery", "development", "ready", "launched"]


class TestGenerateOpportunities:
    """Tests for opportunity generation."""

    def test_no_stripe_generates_payment_opportunity(self):
        """Projects without Stripe but good revenue score get payment opportunity."""
        metadata = {"has_stripe": False}
        scores = {"revenue_score": 40, "maturity_score": 40, "tier": "tier2", "status": "development"}
        opps = generate_opportunities("TestProject", metadata, scores)

        payment_opps = [o for o in opps if o["category"] == "payment"]
        assert len(payment_opps) == 1
        assert payment_opps[0]["priority"] == "high"

    def test_with_stripe_no_payment_opportunity(self):
        """Projects with Stripe should not get payment opportunity."""
        metadata = {"has_stripe": True}
        scores = {"revenue_score": 70, "maturity_score": 70, "tier": "tier1", "status": "ready"}
        opps = generate_opportunities("TestProject", metadata, scores)

        payment_opps = [o for o in opps if o["category"] == "payment"]
        assert len(payment_opps) == 0

    def test_no_auth_generates_auth_opportunity(self):
        """Projects without auth but good maturity get auth opportunity."""
        metadata = {"has_auth": False}
        scores = {"revenue_score": 30, "maturity_score": 40, "tier": "tier2", "status": "development"}
        opps = generate_opportunities("TestProject", metadata, scores)

        feature_opps = [o for o in opps if "authentication" in o["title"].lower()]
        assert len(feature_opps) == 1

    def test_no_docker_generates_deployment_opportunity(self):
        """Projects without Docker but good maturity get deployment opportunity."""
        metadata = {"has_docker": False}
        scores = {"revenue_score": 30, "maturity_score": 50, "tier": "tier2", "status": "development"}
        opps = generate_opportunities("TestProject", metadata, scores)

        docker_opps = [o for o in opps if "docker" in o["title"].lower()]
        assert len(docker_opps) == 1

    def test_tier1_not_launched_gets_deploy_opportunity(self):
        """Tier 1 projects not yet launched get deployment opportunity."""
        metadata = {"has_stripe": True, "has_docker": True}
        scores = {"revenue_score": 80, "maturity_score": 80, "tier": "tier1", "status": "ready"}
        opps = generate_opportunities("TestProject", metadata, scores)

        deploy_opps = [o for o in opps if "production" in o["title"].lower()]
        assert len(deploy_opps) == 1

    def test_opportunities_sorted_by_roi(self):
        """Opportunities should be sorted by ROI (revenue_impact / effort_hours)."""
        metadata = {}
        scores = {"revenue_score": 50, "maturity_score": 60, "tier": "tier1", "status": "development"}
        opps = generate_opportunities("TestProject", metadata, scores)

        if len(opps) > 1:
            for i in range(len(opps) - 1):
                roi_current = opps[i]["revenue_impact"] / max(opps[i]["effort_hours"], 1)
                roi_next = opps[i + 1]["revenue_impact"] / max(opps[i + 1]["effort_hours"], 1)
                assert roi_current >= roi_next

    def test_opportunity_has_required_fields(self):
        """Each opportunity should have all required fields."""
        metadata = {}
        scores = {"revenue_score": 50, "maturity_score": 50, "tier": "tier2", "status": "development"}
        opps = generate_opportunities("TestProject", metadata, scores)

        required_fields = ["title", "description", "category", "priority", "effort_hours", "revenue_impact"]
        for opp in opps:
            for field in required_fields:
                assert field in opp


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_case_insensitive_tech_detection(self):
        """Tech stack detection should be case-insensitive."""
        metadata = {"tech_stack": ["NEXT.JS", "fastapi"]}
        assert calculate_maturity_score(metadata) == 10  # Fullstack bonus

    def test_empty_tech_stack(self):
        """Empty tech stack should not cause errors."""
        metadata = {"tech_stack": []}
        assert calculate_maturity_score(metadata) == 0
        assert calculate_revenue_score(metadata) == 0

    def test_none_values_handled(self):
        """None values in metadata should be handled gracefully."""
        metadata = {"has_tests": None, "tech_stack": None}
        # Should not raise exception
        calculate_maturity_score(metadata)
        calculate_revenue_score(metadata)
        calculate_effort_score(metadata)

    def test_extra_metadata_fields_ignored(self):
        """Unknown metadata fields should be ignored."""
        metadata = {"unknown_field": True, "another_unknown": "value"}
        # Should not raise exception
        score_project("TestProject", metadata)
