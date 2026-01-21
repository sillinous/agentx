"""
The Architect - UI Component Generation Agent
Handles React/Next.js component creation and code generation.
"""

import os
import json
import logging
from typing import Annotated, TypedDict, Literal

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver

logger = logging.getLogger(__name__)


# --- State Definition ---
class ArchitectState(TypedDict):
    """State for The Architect agent."""

    messages: Annotated[list, add_messages]
    component_type: str
    framework: str
    user_id: str
    thread_id: str


# --- Tools for The Architect ---
@tool
def analyze_component_structure(description: str) -> dict:
    """
    Analyze a component description and suggest structure.

    Args:
        description: Description of the desired component

    Returns:
        Suggested component structure with intelligent analysis
    """
    description_lower = description.lower()

    # Analyze keywords to determine component characteristics
    props = ["className"]
    hooks = []
    imports = ["react"]
    complexity = "simple"
    suggested_name = "Component"

    # Detect component type from description
    if any(word in description_lower for word in ["form", "input", "field", "submit"]):
        suggested_name = "FormComponent"
        props.extend(["onSubmit", "initialValues", "validation"])
        hooks.extend(["useState", "useCallback"])
        imports.append("@/components/ui/form")
        complexity = "medium"

    elif any(word in description_lower for word in ["button", "click", "action"]):
        suggested_name = "ActionButton"
        props.extend(["onClick", "disabled", "loading", "variant"])
        hooks.append("useState")
        imports.append("@/components/ui/button")
        complexity = "simple"

    elif any(word in description_lower for word in ["list", "table", "grid", "items"]):
        suggested_name = "DataDisplay"
        props.extend(["data", "columns", "onRowClick", "loading"])
        hooks.extend(["useState", "useMemo"])
        imports.append("@/components/ui/table")
        complexity = "medium"

    elif any(word in description_lower for word in ["modal", "dialog", "popup"]):
        suggested_name = "ModalDialog"
        props.extend(["isOpen", "onClose", "title", "children"])
        hooks.extend(["useState", "useEffect", "useCallback"])
        imports.append("@/components/ui/dialog")
        complexity = "medium"

    elif any(word in description_lower for word in ["card", "panel", "container"]):
        suggested_name = "ContentCard"
        props.extend(["title", "children", "footer", "actions"])
        hooks.append("useState")
        imports.append("@/components/ui/card")
        complexity = "simple"

    elif any(word in description_lower for word in ["nav", "menu", "sidebar", "header"]):
        suggested_name = "NavigationComponent"
        props.extend(["items", "activeItem", "onSelect"])
        hooks.extend(["useState", "useCallback"])
        imports.append("@/components/ui/navigation")
        complexity = "medium"

    elif any(word in description_lower for word in ["chart", "graph", "visualization", "analytics"]):
        suggested_name = "DataVisualization"
        props.extend(["data", "type", "options", "loading"])
        hooks.extend(["useState", "useEffect", "useMemo"])
        imports.extend(["recharts", "@/components/ui/chart"])
        complexity = "complex"

    elif any(word in description_lower for word in ["animation", "transition", "motion"]):
        suggested_name = "AnimatedComponent"
        props.extend(["children", "animate", "duration"])
        hooks.extend(["useState", "useRef"])
        imports.append("framer-motion")
        complexity = "medium"

    # Add common defaults
    if "children" not in props:
        props.append("children")

    return {
        "suggested_name": suggested_name,
        "props": props,
        "hooks": hooks,
        "imports": imports,
        "estimated_complexity": complexity,
        "analysis": {
            "detected_type": suggested_name,
            "accessibility_notes": [
                "Include proper ARIA labels",
                "Ensure keyboard navigation support",
                "Use semantic HTML elements",
            ],
            "performance_tips": [
                "Memoize callbacks with useCallback",
                "Use useMemo for expensive computations",
                "Consider lazy loading for complex components",
            ] if complexity in ["medium", "complex"] else [],
        },
    }


@tool
def validate_react_syntax(code: str) -> dict:
    """
    Validate React/JSX syntax for common issues.

    Args:
        code: React component code to validate

    Returns:
        Comprehensive validation results with fixes
    """
    issues = []
    warnings = []
    suggestions = []

    # JSX attribute checks
    if "class=" in code and "className=" not in code:
        issues.append({
            "type": "error",
            "message": "Use 'className' instead of 'class' in JSX",
            "fix": "Replace 'class=' with 'className='",
        })

    # Event handler casing
    event_handlers = ["onclick", "onchange", "onsubmit", "onfocus", "onblur", "onmouseover"]
    for handler in event_handlers:
        if handler + "=" in code.lower() and handler.replace("on", "on").title().replace("O", "o", 1) + "=" not in code:
            camel_case = "on" + handler[2:].capitalize()
            issues.append({
                "type": "error",
                "message": f"Use '{camel_case}' (camelCase) for event handlers",
                "fix": f"Replace '{handler}=' with '{camel_case}='",
            })

    # Fragment checks
    if "<>" in code and "</>" not in code:
        issues.append({
            "type": "error",
            "message": "Missing closing fragment tag",
            "fix": "Add '</>' to close the fragment",
        })

    # Self-closing tag checks
    void_elements = ["img", "input", "br", "hr", "meta", "link"]
    for elem in void_elements:
        pattern = f"<{elem} "
        if pattern in code.lower() and f"<{elem}" in code.lower() and "/>" not in code:
            warnings.append({
                "type": "warning",
                "message": f"'{elem}' should be self-closing in JSX",
                "fix": f"Use '<{elem} ... />' instead of '<{elem} ...>'",
            })

    # Hook usage checks
    if "useState" in code and "import" in code and "useState" not in code.split("import")[0]:
        if "'react'" not in code and '"react"' not in code:
            warnings.append({
                "type": "warning",
                "message": "useState used but React import not detected",
                "fix": "Add: import { useState } from 'react'",
            })

    # Key prop in lists
    if ".map(" in code and "key=" not in code and "key:" not in code:
        warnings.append({
            "type": "warning",
            "message": "Array .map() detected without 'key' prop",
            "fix": "Add a unique 'key' prop to mapped elements",
        })

    # Inline styles check
    if 'style="' in code:
        issues.append({
            "type": "error",
            "message": "Use style objects instead of string styles in JSX",
            "fix": "Change style=\"...\" to style={{...}}",
        })

    # Accessibility checks
    if "<img" in code.lower() and "alt=" not in code.lower():
        warnings.append({
            "type": "accessibility",
            "message": "Image element missing 'alt' attribute",
            "fix": "Add alt='description' to <img> tags",
        })

    if "<button" in code.lower() and "type=" not in code.lower():
        suggestions.append("Consider adding type='button' or type='submit' to buttons")

    # TypeScript suggestions
    if "props" in code.lower() and ": " not in code and "interface" not in code:
        suggestions.append("Consider adding TypeScript interfaces for props")

    if "useState<" not in code and "useState(" in code:
        suggestions.append("Consider adding type annotations to useState: useState<Type>()")

    # Performance suggestions
    if "useEffect" in code and "[]" not in code:
        suggestions.append("Verify useEffect dependency array is correctly specified")

    if code.count("useState") > 3:
        suggestions.append("Consider using useReducer for complex state management")

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "warnings": warnings,
        "suggestions": suggestions,
        "summary": {
            "errors": len(issues),
            "warnings": len(warnings),
            "suggestions": len(suggestions),
        },
    }


@tool
def get_ui_components_library() -> dict:
    """
    Get available UI components from the design system.

    Returns:
        Comprehensive dictionary of available components with usage details
    """
    return {
        "primitives": {
            "Button": {
                "import": "@/components/ui/button",
                "variants": ["default", "destructive", "outline", "secondary", "ghost", "link"],
                "sizes": ["default", "sm", "lg", "icon"],
                "props": ["variant", "size", "disabled", "loading", "onClick"],
            },
            "Input": {
                "import": "@/components/ui/input",
                "types": ["text", "password", "email", "number", "search"],
                "props": ["type", "placeholder", "value", "onChange", "disabled", "error"],
            },
            "Card": {
                "import": "@/components/ui/card",
                "subcomponents": ["CardHeader", "CardTitle", "CardDescription", "CardContent", "CardFooter"],
                "props": ["className", "children"],
            },
            "Badge": {
                "import": "@/components/ui/badge",
                "variants": ["default", "secondary", "destructive", "outline"],
                "props": ["variant", "children"],
            },
            "Avatar": {
                "import": "@/components/ui/avatar",
                "subcomponents": ["AvatarImage", "AvatarFallback"],
                "props": ["src", "alt", "fallback"],
            },
        },
        "layout": {
            "Container": {
                "import": "@/components/ui/container",
                "props": ["maxWidth", "className", "children"],
            },
            "Grid": {
                "import": "@/components/ui/grid",
                "props": ["cols", "gap", "className", "children"],
            },
            "Flex": {
                "import": "@/components/ui/flex",
                "props": ["direction", "justify", "align", "gap", "wrap", "children"],
            },
            "Stack": {
                "import": "@/components/ui/stack",
                "props": ["direction", "spacing", "children"],
            },
            "Separator": {
                "import": "@/components/ui/separator",
                "props": ["orientation", "className"],
            },
        },
        "navigation": {
            "Navbar": {
                "import": "@/components/ui/navbar",
                "props": ["items", "logo", "actions"],
            },
            "Sidebar": {
                "import": "@/components/ui/sidebar",
                "props": ["items", "collapsed", "onToggle"],
            },
            "Breadcrumb": {
                "import": "@/components/ui/breadcrumb",
                "props": ["items", "separator"],
            },
            "Tabs": {
                "import": "@/components/ui/tabs",
                "subcomponents": ["TabsList", "TabsTrigger", "TabsContent"],
                "props": ["defaultValue", "value", "onValueChange"],
            },
        },
        "feedback": {
            "Alert": {
                "import": "@/components/ui/alert",
                "variants": ["default", "destructive", "warning", "success"],
                "subcomponents": ["AlertTitle", "AlertDescription"],
            },
            "Toast": {
                "import": "@/components/ui/toast",
                "usage": "useToast() hook",
                "variants": ["default", "destructive", "success"],
            },
            "Progress": {
                "import": "@/components/ui/progress",
                "props": ["value", "max", "className"],
            },
            "Skeleton": {
                "import": "@/components/ui/skeleton",
                "props": ["className", "width", "height"],
            },
        },
        "overlay": {
            "Modal": {
                "import": "@/components/ui/modal",
                "props": ["isOpen", "onClose", "title", "children"],
            },
            "Dialog": {
                "import": "@/components/ui/dialog",
                "subcomponents": ["DialogTrigger", "DialogContent", "DialogHeader", "DialogTitle", "DialogDescription", "DialogFooter"],
            },
            "Popover": {
                "import": "@/components/ui/popover",
                "subcomponents": ["PopoverTrigger", "PopoverContent"],
            },
            "Tooltip": {
                "import": "@/components/ui/tooltip",
                "subcomponents": ["TooltipTrigger", "TooltipContent"],
            },
        },
        "forms": {
            "Form": {
                "import": "@/components/ui/form",
                "usage": "react-hook-form integration",
                "subcomponents": ["FormField", "FormItem", "FormLabel", "FormControl", "FormMessage"],
            },
            "Select": {
                "import": "@/components/ui/select",
                "subcomponents": ["SelectTrigger", "SelectValue", "SelectContent", "SelectItem"],
                "props": ["value", "onValueChange", "placeholder"],
            },
            "Checkbox": {
                "import": "@/components/ui/checkbox",
                "props": ["checked", "onCheckedChange", "disabled"],
            },
            "Radio": {
                "import": "@/components/ui/radio-group",
                "subcomponents": ["RadioGroup", "RadioGroupItem"],
            },
            "Switch": {
                "import": "@/components/ui/switch",
                "props": ["checked", "onCheckedChange", "disabled"],
            },
        },
        "data_display": {
            "Table": {
                "import": "@/components/ui/table",
                "subcomponents": ["Table", "TableHeader", "TableBody", "TableRow", "TableHead", "TableCell"],
            },
            "DataTable": {
                "import": "@/components/ui/data-table",
                "features": ["sorting", "filtering", "pagination", "selection"],
                "props": ["columns", "data", "onRowClick"],
            },
        },
        "theme": {
            "colors": {
                "primary": "cyan-400",
                "background": "slate-950",
                "surface": "slate-900",
                "text": "slate-200",
                "accent": "cyan-500",
            },
            "spacing": ["0", "1", "2", "3", "4", "6", "8", "12", "16", "24"],
            "borderRadius": ["none", "sm", "md", "lg", "xl", "2xl", "full"],
        },
    }


@tool
def generate_component_tests(component_code: str, component_name: str) -> str:
    """
    Generate comprehensive test cases for a React component.

    Args:
        component_code: The component source code
        component_name: Name of the component

    Returns:
        Complete test file content with multiple test scenarios
    """
    code_lower = component_code.lower()

    # Detect component characteristics to generate appropriate tests
    has_click = "onclick" in code_lower
    has_form = "onsubmit" in code_lower or "<form" in code_lower
    has_input = "<input" in code_lower or "onchange" in code_lower
    has_loading = "loading" in code_lower or "isloading" in code_lower
    has_async = "async" in code_lower or "await" in code_lower
    has_state = "usestate" in code_lower
    has_effect = "useeffect" in code_lower
    has_children = "children" in code_lower

    # Build test imports
    imports = ["render", "screen"]
    if has_click or has_form:
        imports.append("fireEvent")
    if has_async:
        imports.append("waitFor")

    imports_str = ", ".join(imports)

    # Generate test cases
    tests = []

    # Basic render test
    tests.append(f'''  it('renders without crashing', () => {{
    render(<{component_name} />);
  }});''')

    # Snapshot test
    tests.append(f'''  it('matches snapshot', () => {{
    const {{ container }} = render(<{component_name} />);
    expect(container).toMatchSnapshot();
  }});''')

    # ClassName test
    tests.append(f'''  it('applies custom className', () => {{
    render(<{component_name} className="custom-class" data-testid="{component_name.lower()}" />);
    const element = screen.getByTestId('{component_name.lower()}');
    expect(element).toHaveClass('custom-class');
  }});''')

    # Children test
    if has_children:
        tests.append(f'''  it('renders children correctly', () => {{
    render(
      <{component_name}>
        <span data-testid="child">Child Content</span>
      </{component_name}>
    );
    expect(screen.getByTestId('child')).toBeInTheDocument();
  }});''')

    # Click handler test
    if has_click:
        tests.append(f'''  it('calls onClick handler when clicked', () => {{
    const handleClick = jest.fn();
    render(<{component_name} onClick={{handleClick}} data-testid="{component_name.lower()}" />);
    fireEvent.click(screen.getByTestId('{component_name.lower()}'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  }});''')

    # Form submission test
    if has_form:
        tests.append(f'''  it('handles form submission', () => {{
    const handleSubmit = jest.fn((e) => e.preventDefault());
    render(<{component_name} onSubmit={{handleSubmit}} />);
    const form = screen.getByRole('form');
    fireEvent.submit(form);
    expect(handleSubmit).toHaveBeenCalled();
  }});''')

    # Input change test
    if has_input:
        tests.append(f'''  it('handles input changes', () => {{
    const handleChange = jest.fn();
    render(<{component_name} onChange={{handleChange}} />);
    const input = screen.getByRole('textbox');
    fireEvent.change(input, {{ target: {{ value: 'test value' }} }});
    expect(handleChange).toHaveBeenCalled();
  }});''')

    # Loading state test
    if has_loading:
        tests.append(f'''  it('displays loading state correctly', () => {{
    render(<{component_name} loading={{true}} />);
    expect(screen.getByTestId('loading-indicator')).toBeInTheDocument();
  }});

  it('hides loading state when not loading', () => {{
    render(<{component_name} loading={{false}} />);
    expect(screen.queryByTestId('loading-indicator')).not.toBeInTheDocument();
  }});''')

    # Disabled state test
    tests.append(f'''  it('applies disabled styles when disabled', () => {{
    render(<{component_name} disabled={{true}} data-testid="{component_name.lower()}" />);
    const element = screen.getByTestId('{component_name.lower()}');
    expect(element).toBeDisabled();
  }});''')

    # Async test
    if has_async:
        tests.append(f'''  it('handles async operations correctly', async () => {{
    render(<{component_name} />);
    await waitFor(() => {{
      expect(screen.getByTestId('async-content')).toBeInTheDocument();
    }});
  }});''')

    # Accessibility test
    tests.append(f'''  it('meets accessibility requirements', () => {{
    const {{ container }} = render(<{component_name} />);
    // Basic accessibility checks
    expect(container.querySelector('[aria-label]') || container.querySelector('[role]')).toBeTruthy();
  }});''')

    tests_str = "\n\n".join(tests)

    return f'''import {{ {imports_str} }} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {{ {component_name} }} from './{component_name}';

// Mock any external dependencies
jest.mock('@/lib/api', () => ({{
  synapseAPI: {{
    invokeAgent: jest.fn(),
  }},
}}));

describe('{component_name}', () => {{
{tests_str}
}});

// Integration tests
describe('{component_name} Integration', () => {{
  it('integrates correctly with parent components', () => {{
    const ParentComponent = () => (
      <div>
        <{component_name} data-testid="{component_name.lower()}" />
      </div>
    );
    render(<ParentComponent />);
    expect(screen.getByTestId('{component_name.lower()}')).toBeInTheDocument();
  }});
}});
'''


# --- Agent Node Functions ---
def create_architect_agent():
    """Create and return The Architect agent graph."""

    model = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview"),
        temperature=0.3,  # Lower temperature for code generation
    )

    tools = [
        analyze_component_structure,
        validate_react_syntax,
        get_ui_components_library,
        generate_component_tests,
    ]
    model_with_tools = model.bind_tools(tools)

    system_prompt = """You are The Architect, an expert React/Next.js component generation agent for Synapse Core.

Your responsibilities:
1. Generate high-quality, reusable React components
2. Follow modern React best practices (hooks, functional components)
3. Use TypeScript when appropriate
4. Create accessible, responsive components
5. Follow the project's design system

You have access to tools for:
- Analyzing component structure requirements
- Validating React/JSX syntax
- Getting available UI components from the design system
- Generating component tests

Component Guidelines:
- Use functional components with hooks
- Prefer composition over inheritance
- Include proper TypeScript types/interfaces
- Add JSDoc comments for props
- Follow accessibility best practices (ARIA labels, keyboard navigation)
- Use Tailwind CSS for styling

Format your code responses as JSON:
{
    "type": "component",
    "name": "ComponentName",
    "code": "// component code here",
    "styles": "// optional styles",
    "tests": "// optional test code",
    "usage": "// example usage"
}

For questions or clarifications, use:
{
    "type": "text",
    "content": "your message"
}
"""

    def agent_node(state: ArchitectState) -> dict:
        """Main agent decision node."""
        messages = state["messages"]

        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=system_prompt)] + list(messages)

        response = model_with_tools.invoke(messages)
        return {"messages": [response]}

    def should_continue(state: ArchitectState) -> Literal["tools", END]:
        """Determine if we should continue to tools or end."""
        messages = state["messages"]
        last_message = messages[-1]

        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return END

    # Build the graph
    graph = StateGraph(ArchitectState)

    graph.add_node("agent", agent_node)
    graph.add_node("tools", ToolNode(tools))

    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", should_continue)
    graph.add_edge("tools", "agent")

    memory = MemorySaver()
    return graph.compile(checkpointer=memory)


# Create the agent app
architect_agent_app = create_architect_agent()


# --- Convenience Functions ---
def invoke_architect(
    prompt: str,
    user_id: str,
    thread_id: str,
    component_type: str = "functional",
    framework: str = "react",
) -> dict:
    """
    Convenience function to invoke The Architect agent.

    Args:
        prompt: The user's component request
        user_id: User identifier
        thread_id: Thread/conversation identifier
        component_type: Type of component (functional, class, server)
        framework: Target framework (react, nextjs)

    Returns:
        Agent response as a dictionary
    """
    config = {"configurable": {"thread_id": thread_id, "user_id": user_id}}

    result = architect_agent_app.invoke(
        {
            "messages": [HumanMessage(content=prompt)],
            "component_type": component_type,
            "framework": framework,
            "user_id": user_id,
            "thread_id": thread_id,
        },
        config=config,
    )

    last_message = result["messages"][-1]
    return {
        "response": last_message.content,
        "thread_id": thread_id,
        "agent": "architect",
    }
