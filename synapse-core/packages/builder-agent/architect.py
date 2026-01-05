import logging
from typing import List, TypedDict, Annotated, Dict, Any
from langchain_core.messages import AnyMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langchain_core.tools import tool
import json
import re

# --- Logger Configuration ---
logger = logging.getLogger(__name__)
if not logger.handlers:
    logHandler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    logHandler.setFormatter(formatter)
    logger.addHandler(logHandler)
logger.setLevel(logging.INFO)


# --- Agent State ---
class ArchitectState(TypedDict):
    messages: Annotated[List[AnyMessage], lambda x, y: x + y]


# --- Tools for The Architect ---


@tool
def analyze_component_structure(description: str) -> str:
    """
    Analyzes a component description and suggests the optimal React component structure.
    Returns recommended component hierarchy and props.
    """
    logger.info(f"TOOL: Analyzing component structure for: '{description[:50]}...'")

    # Basic heuristic analysis
    suggestions = {
        "component_type": "functional",
        "hooks_needed": [],
        "props": [],
        "structure": "Simple single-component structure"
    }

    desc_lower = description.lower()

    # Detect complexity
    if any(word in desc_lower for word in ["form", "input", "submit"]):
        suggestions["hooks_needed"].append("useState")
        suggestions["props"].append("onSubmit: (data) => void")

    if any(word in desc_lower for word in ["fetch", "api", "load", "data"]):
        suggestions["hooks_needed"].append("useEffect")
        suggestions["hooks_needed"].append("useState")

    if any(word in desc_lower for word in ["animate", "transition", "motion"]):
        suggestions["props"].append("animated: boolean")

    if len(suggestions["hooks_needed"]) > 2:
        suggestions["structure"] = "Complex component - consider breaking into smaller components"

    result = f"""
Component Analysis:
- Type: {suggestions['component_type']}
- Hooks needed: {', '.join(suggestions['hooks_needed']) if suggestions['hooks_needed'] else 'None'}
- Recommended props: {', '.join(suggestions['props']) if suggestions['props'] else 'Basic props only'}
- Structure: {suggestions['structure']}
"""
    logger.info("Component structure analysis complete", extra=suggestions)
    return result


@tool
def validate_react_syntax(code: str) -> str:
    """
    Validates React component syntax and checks for common issues.
    Returns validation report with any errors or warnings.
    """
    logger.info("TOOL: Validating React syntax")

    issues = []
    warnings = []

    # Check for basic React patterns
    if "export default" not in code and "export const" not in code:
        issues.append("Component should be exported (use 'export default' or 'export const')")

    if "return" not in code:
        issues.append("Component must return JSX")

    # Check for common mistakes
    if "class=" in code:
        warnings.append("Found 'class=' instead of 'className=' (HTML syntax in React)")

    if re.search(r'<[A-Z]\w+[^/>]*>[^<]*</[A-Z]\w+>', code):
        # Has JSX tags - good
        pass
    else:
        warnings.append("No JSX elements detected - ensure component returns valid JSX")

    # Check for useState without import
    if "useState" in code and "import" not in code:
        issues.append("useState used but no imports detected")

    if not issues and not warnings:
        return "✓ Syntax validation passed - no issues detected"

    report = "Validation Report:\n"
    if issues:
        report += "ERRORS:\n" + "\n".join(f"  - {issue}" for issue in issues) + "\n"
    if warnings:
        report += "WARNINGS:\n" + "\n".join(f"  - {warning}" for warning in warnings)

    logger.info("Validation complete", extra={"issues": len(issues), "warnings": len(warnings)})
    return report


@tool
def suggest_tailwind_classes(design_intent: str) -> str:
    """
    Suggests Tailwind CSS classes based on design intent description.
    Returns a list of recommended Tailwind utility classes.
    """
    logger.info(f"TOOL: Suggesting Tailwind classes for: '{design_intent[:50]}...'")

    classes = []
    intent_lower = design_intent.lower()

    # Layout suggestions
    if any(word in intent_lower for word in ["center", "centered", "middle"]):
        classes.extend(["flex", "items-center", "justify-center"])

    if "card" in intent_lower or "box" in intent_lower:
        classes.extend(["rounded-lg", "shadow-lg", "p-6", "bg-white"])

    # Spacing
    if "padding" in intent_lower or "space" in intent_lower:
        classes.append("p-4")
    if "margin" in intent_lower:
        classes.append("m-4")

    # Colors
    if "blue" in intent_lower:
        classes.append("bg-blue-500")
    if "dark" in intent_lower:
        classes.extend(["bg-gray-900", "text-white"])
    if "light" in intent_lower:
        classes.extend(["bg-gray-50", "text-gray-900"])

    # Typography
    if "heading" in intent_lower or "title" in intent_lower:
        classes.extend(["text-2xl", "font-bold"])
    if "small" in intent_lower and "text" in intent_lower:
        classes.append("text-sm")

    # Effects
    if "hover" in intent_lower:
        classes.append("hover:opacity-80")
    if "button" in intent_lower:
        classes.extend(["px-6", "py-3", "rounded-md", "font-semibold", "transition-colors"])

    if not classes:
        classes = ["p-4", "rounded-lg"]  # Defaults

    result = f"Suggested Tailwind classes:\n{' '.join(classes)}"
    logger.info("Tailwind suggestions generated", extra={"class_count": len(classes)})
    return result


@tool
def optimize_component_performance(code: str) -> str:
    """
    Analyzes component code for performance optimization opportunities.
    Returns suggestions for React.memo, useMemo, useCallback usage.
    """
    logger.info("TOOL: Analyzing component performance")

    suggestions = []

    # Check for potential memo opportunities
    if "props" in code and "React.memo" not in code and "memo(" not in code:
        suggestions.append(
            "Consider wrapping component with React.memo if props don't change frequently"
        )

    # Check for expensive computations
    if ".map(" in code or ".filter(" in code or ".reduce(" in code:
        if "useMemo" not in code:
            suggestions.append(
                "Found array operations - consider using useMemo for expensive computations"
            )

    # Check for function definitions inside component
    if "const handle" in code or "function handle" in code:
        if "useCallback" not in code:
            suggestions.append(
                "Found event handlers - consider using useCallback to prevent unnecessary re-renders"
            )

    if not suggestions:
        return "✓ No obvious performance issues detected"

    report = "Performance Optimization Suggestions:\n" + "\n".join(
        f"  - {suggestion}" for suggestion in suggestions
    )

    logger.info("Performance analysis complete", extra={"suggestion_count": len(suggestions)})
    return report


# --- Agent Class ---
class ArchitectAgent:
    def __init__(self, model):
        self.model = model

    def design_component(self, state: ArchitectState, config: dict):
        """
        The first step: The Architect analyzes the request and designs the component structure.
        """
        logger.info("NODE: Designing Component")

        user_id = config["configurable"]["user_id"]

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    (
                        "You are 'The Architect', an expert React/Next.js component builder. "
                        "Your mission is to create modern, responsive, accessible UI components. "
                        "First, analyze the component structure using available tools. "
                        "Then generate clean, functional React code using TypeScript and Tailwind CSS. "
                        "Use the suggest_tailwind_classes tool to get styling recommendations. "
                        "After generating code, validate it using the validation tool. "
                        "Finally, return your output as a JSON object with: "
                        '{"type": "component", "code": "your React component code here", '
                        '"description": "brief description of the component"}. '
                        "Use modern React patterns (functional components, hooks) and "
                        "follow best practices for accessibility and performance."
                    ),
                ),
                ("human", "{request}"),
            ]
        )

        chain = prompt | self.model.bind_tools(
            [
                analyze_component_structure,
                suggest_tailwind_classes,
                validate_react_syntax,
                optimize_component_performance,
            ]
        )

        user_request = state["messages"][-1].content
        response = chain.invoke({"request": user_request})

        return {"messages": [response]}

    def build_and_validate(self, state: ArchitectState):
        """
        The second step: Execute tools and refine the component based on analysis.
        """
        logger.info("NODE: Building and Validating Component")

        assistant_message = state["messages"][-1]

        # Execute tool calls
        tool_outputs = []
        for tool_call in assistant_message.tool_calls:
            try:
                tool_output = globals()[tool_call["name"]].invoke(tool_call["args"])
                tool_outputs.append(
                    ToolMessage(content=str(tool_output), tool_call_id=tool_call["id"])
                )
                logger.info(
                    f"Tool '{tool_call['name']}' executed successfully",
                    extra={"tool_call_id": tool_call["id"]},
                )
            except Exception as e:
                error_message = f"Error executing tool '{tool_call['name']}': {e}"
                logger.error(
                    error_message,
                    extra={"tool_call_id": tool_call["id"], "error": str(e)},
                )
                tool_outputs.append(
                    ToolMessage(
                        content=f"Error: {error_message}", tool_call_id=tool_call["id"]
                    )
                )

        new_messages = state["messages"] + tool_outputs
        response = self.model.invoke(new_messages)

        return {"messages": [response]}


# --- Graph Definition ---
def get_architect_agent():
    """
    Initializes and compiles The Architect agent graph.
    """
    llm = ChatOpenAI(model="gpt-4-turbo")
    architect_agent = ArchitectAgent(model=llm)

    workflow = StateGraph(ArchitectState)

    # Add nodes
    workflow.add_node("design", architect_agent.design_component)
    workflow.add_node("build", architect_agent.build_and_validate)

    # Define edges
    workflow.set_entry_point("design")
    workflow.add_edge("design", "build")
    workflow.add_edge("build", END)

    # Compile
    app = workflow.compile()

    return app


# --- Example Usage ---
if __name__ == "__main__":
    logger.info("This is a blueprint for The Architect agent.")
    logger.info("To run it as a service, integrate with main.py and uvicorn server.")
