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
        Suggested component structure
    """
    return {
        "suggested_name": "CustomComponent",
        "props": ["className", "children", "onClick"],
        "hooks": ["useState", "useEffect"],
        "imports": ["react", "@/components/ui"],
        "estimated_complexity": "medium",
    }


@tool
def validate_react_syntax(code: str) -> dict:
    """
    Validate React/JSX syntax for common issues.

    Args:
        code: React component code to validate

    Returns:
        Validation results
    """
    issues = []

    # Basic checks
    if "className=" not in code and "class=" in code:
        issues.append("Use 'className' instead of 'class' in JSX")

    if "onclick=" in code.lower() and "onClick=" not in code:
        issues.append("Use 'onClick' (camelCase) for event handlers")

    if "<>" in code and "</>" not in code:
        issues.append("Missing closing fragment tag")

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "suggestions": [
            "Consider using TypeScript for type safety",
            "Add PropTypes or TypeScript interfaces",
        ],
    }


@tool
def get_ui_components_library() -> dict:
    """
    Get available UI components from the design system.

    Returns:
        Dictionary of available components
    """
    return {
        "primitives": ["Button", "Input", "Card", "Badge", "Avatar"],
        "layout": ["Container", "Grid", "Flex", "Stack", "Separator"],
        "navigation": ["Navbar", "Sidebar", "Breadcrumb", "Tabs"],
        "feedback": ["Alert", "Toast", "Progress", "Skeleton"],
        "overlay": ["Modal", "Dialog", "Popover", "Tooltip"],
        "forms": ["Form", "Select", "Checkbox", "Radio", "Switch"],
    }


@tool
def generate_component_tests(component_code: str, component_name: str) -> str:
    """
    Generate basic test cases for a React component.

    Args:
        component_code: The component source code
        component_name: Name of the component

    Returns:
        Test file content
    """
    return f"""import {{ render, screen }} from '@testing-library/react';
import {{ {component_name} }} from './{component_name}';

describe('{component_name}', () => {{
  it('renders without crashing', () => {{
    render(<{component_name} />);
  }});

  it('applies custom className', () => {{
    render(<{component_name} className="custom-class" />);
    // Add assertions based on component structure
  }});

  it('handles click events', () => {{
    const handleClick = jest.fn();
    render(<{component_name} onClick={{handleClick}} />);
    // Add click simulation
  }});
}});
"""


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
