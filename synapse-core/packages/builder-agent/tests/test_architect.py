"""
Tests for The Architect - UI Component Generation Agent

These tests verify the tool functions work correctly without requiring
an actual OpenAI API key. The agent creation and invocation are tested
separately via the marketing-agent's integration tests.
"""

import pytest
from unittest.mock import patch, MagicMock

import sys
import os

# Set up test environment before imports
os.environ["TESTING"] = "1"
os.environ["OPENAI_API_KEY"] = "test-key-for-testing"

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock ChatOpenAI before importing architect
with patch("langchain_openai.ChatOpenAI"):
    from architect import (
        analyze_component_structure,
        validate_react_syntax,
        get_ui_components_library,
        generate_component_tests,
        ArchitectState,
    )


class TestAnalyzeComponentStructure:
    """Tests for the analyze_component_structure tool."""

    def test_returns_structure(self):
        """Test that component structure analysis returns expected fields."""
        result = analyze_component_structure.invoke({"description": "A button with icon"})

        assert "suggested_name" in result
        assert "props" in result
        assert "hooks" in result
        assert "imports" in result
        assert "estimated_complexity" in result

    def test_suggests_component_name(self):
        """Test that a component name is suggested."""
        result = analyze_component_structure.invoke({"description": "A modal dialog"})

        assert result["suggested_name"] is not None
        assert len(result["suggested_name"]) > 0

    def test_props_is_list(self):
        """Test that props is a list."""
        result = analyze_component_structure.invoke({"description": "A form input"})

        assert isinstance(result["props"], list)

    def test_hooks_is_list(self):
        """Test that hooks is a list."""
        result = analyze_component_structure.invoke({"description": "A stateful widget"})

        assert isinstance(result["hooks"], list)

    def test_imports_is_list(self):
        """Test that imports is a list."""
        result = analyze_component_structure.invoke({"description": "A component"})

        assert isinstance(result["imports"], list)

    def test_complexity_is_valid(self):
        """Test that estimated complexity is a valid value."""
        result = analyze_component_structure.invoke({"description": "Simple button"})

        valid_complexities = ["low", "medium", "high"]
        assert result["estimated_complexity"] in valid_complexities


class TestValidateReactSyntax:
    """Tests for the validate_react_syntax tool."""

    def test_detects_class_instead_of_classname(self):
        """Test that using 'class' instead of 'className' is detected."""
        code = '<div class="container">Hello</div>'
        result = validate_react_syntax.invoke({"code": code})

        assert result["valid"] is False
        assert any("className" in issue for issue in result["issues"])

    def test_detects_lowercase_onclick(self):
        """Test that lowercase onclick is detected."""
        code = '<button onclick={handleClick}>Click</button>'
        result = validate_react_syntax.invoke({"code": code})

        assert result["valid"] is False
        assert any("onClick" in issue for issue in result["issues"])

    def test_detects_unclosed_fragment(self):
        """Test that unclosed fragments are detected."""
        code = "<><div>Hello</div>"
        result = validate_react_syntax.invoke({"code": code})

        assert result["valid"] is False
        assert any("fragment" in issue.lower() for issue in result["issues"])

    def test_valid_jsx_passes(self):
        """Test that valid JSX passes validation."""
        code = '<div className="container"><button onClick={handleClick}>Click</button></div>'
        result = validate_react_syntax.invoke({"code": code})

        assert result["valid"] is True
        assert len(result["issues"]) == 0

    def test_includes_suggestions(self):
        """Test that validation includes suggestions."""
        code = "<div>Hello</div>"
        result = validate_react_syntax.invoke({"code": code})

        assert "suggestions" in result
        assert isinstance(result["suggestions"], list)

    def test_proper_fragment_is_valid(self):
        """Test that properly closed fragments are valid."""
        code = "<><div>Hello</div></>"
        result = validate_react_syntax.invoke({"code": code})

        assert result["valid"] is True


class TestGetUIComponentsLibrary:
    """Tests for the get_ui_components_library tool."""

    def test_returns_categories(self):
        """Test that component library returns categories."""
        result = get_ui_components_library.invoke({})

        assert "primitives" in result
        assert "layout" in result
        assert "navigation" in result
        assert "feedback" in result
        assert "overlay" in result
        assert "forms" in result

    def test_primitives_include_common_components(self):
        """Test that primitives include common UI components."""
        result = get_ui_components_library.invoke({})

        primitives = result["primitives"]
        assert "Button" in primitives
        assert "Input" in primitives
        assert "Card" in primitives

    def test_layout_includes_common_components(self):
        """Test that layout includes common components."""
        result = get_ui_components_library.invoke({})

        layout = result["layout"]
        assert "Container" in layout
        assert "Grid" in layout
        assert "Flex" in layout

    def test_navigation_includes_common_components(self):
        """Test that navigation includes common components."""
        result = get_ui_components_library.invoke({})

        nav = result["navigation"]
        assert "Navbar" in nav
        assert "Tabs" in nav

    def test_feedback_includes_common_components(self):
        """Test that feedback includes common components."""
        result = get_ui_components_library.invoke({})

        feedback = result["feedback"]
        assert "Alert" in feedback
        assert "Toast" in feedback

    def test_overlay_includes_common_components(self):
        """Test that overlay includes common components."""
        result = get_ui_components_library.invoke({})

        overlay = result["overlay"]
        assert "Modal" in overlay
        assert "Dialog" in overlay

    def test_forms_include_common_components(self):
        """Test that forms include common components."""
        result = get_ui_components_library.invoke({})

        forms = result["forms"]
        assert "Form" in forms
        assert "Select" in forms
        assert "Checkbox" in forms


class TestGenerateComponentTests:
    """Tests for the generate_component_tests tool."""

    def test_generates_test_file_content(self):
        """Test that test file content is generated."""
        code = "const Button = () => <button>Click</button>"
        result = generate_component_tests.invoke({
            "component_code": code,
            "component_name": "Button",
        })

        assert isinstance(result, str)
        assert len(result) > 0

    def test_includes_import_statements(self):
        """Test that test file includes import statements."""
        code = "const Card = () => <div>Card</div>"
        result = generate_component_tests.invoke({
            "component_code": code,
            "component_name": "Card",
        })

        assert "import" in result
        assert "@testing-library/react" in result

    def test_includes_describe_block(self):
        """Test that test file includes describe block."""
        code = "const Modal = () => <div>Modal</div>"
        result = generate_component_tests.invoke({
            "component_code": code,
            "component_name": "Modal",
        })

        assert "describe(" in result
        assert "'Modal'" in result

    def test_includes_render_test(self):
        """Test that test file includes render test."""
        code = "const Alert = () => <div>Alert</div>"
        result = generate_component_tests.invoke({
            "component_code": code,
            "component_name": "Alert",
        })

        assert "renders without crashing" in result
        assert "render(" in result

    def test_includes_classname_test(self):
        """Test that test file includes className test."""
        code = "const Badge = () => <span>Badge</span>"
        result = generate_component_tests.invoke({
            "component_code": code,
            "component_name": "Badge",
        })

        assert "className" in result
        assert "custom-class" in result

    def test_includes_click_handler_test(self):
        """Test that test file includes click handler test."""
        code = "const Link = () => <a>Link</a>"
        result = generate_component_tests.invoke({
            "component_code": code,
            "component_name": "Link",
        })

        assert "handleClick" in result or "onClick" in result
        assert "jest.fn()" in result

    def test_uses_component_name_in_imports(self):
        """Test that component name is used in import path."""
        code = "const Header = () => <header>Header</header>"
        result = generate_component_tests.invoke({
            "component_code": code,
            "component_name": "Header",
        })

        assert "./Header" in result


class TestArchitectState:
    """Tests for the ArchitectState TypedDict."""

    def test_state_has_required_keys(self):
        """Test that ArchitectState has all required keys."""
        state: ArchitectState = {
            "messages": [],
            "component_type": "functional",
            "framework": "react",
            "user_id": "user-123",
            "thread_id": "thread-456",
        }

        assert "messages" in state
        assert "component_type" in state
        assert "framework" in state
        assert "user_id" in state
        assert "thread_id" in state


class TestValidationEdgeCases:
    """Tests for edge cases in validation."""

    def test_empty_code_is_valid(self):
        """Test that empty code is considered valid."""
        result = validate_react_syntax.invoke({"code": ""})
        assert result["valid"] is True

    def test_whitespace_only_is_valid(self):
        """Test that whitespace-only code is valid."""
        result = validate_react_syntax.invoke({"code": "   \n\t  "})
        assert result["valid"] is True

    def test_mixed_valid_invalid_jsx(self):
        """Test code with only 'class' (not 'className') triggers validation."""
        # Note: The validator only flags when className= is absent entirely
        # If className= exists alongside class=, it doesn't flag (transitional code)
        code = '<div class="bad"><span class="also-bad">Text</span></div>'
        result = validate_react_syntax.invoke({"code": code})

        assert result["valid"] is False
        assert len(result["issues"]) >= 1

    def test_multiple_onclick_handlers(self):
        """Test code with multiple onclick issues."""
        code = '<button onclick={a}><span onclick={b}>Text</span></button>'
        result = validate_react_syntax.invoke({"code": code})

        assert result["valid"] is False
