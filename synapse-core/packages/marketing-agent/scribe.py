"""
SYNAPSE Agent 02: The Scribe (sys_scribe_v1)
Version: 1.0
Role: Content Generation & Brand Voice Guardian
Archetype: The Storyteller / The Diplomat
"""

import os
from typing import List, TypedDict, Annotated
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver

# Assume a LangChain compatible model is available
from langchain_openai import ChatOpenAI
from database_utils import retrieve_brand_dna


# --- Agent State ---
# This TypedDict defines the "memory" or "state" of our agent at each step.
class ScribeState(TypedDict):
    messages: Annotated[List[AnyMessage], lambda x, y: x + y]


# --- Placeholder Tools ---
# In a real scenario, these would be robust functions that might call external APIs
# or interact with the database (Context Lake).


@tool
def retrieve_brand_voice(query: str, user_id: str) -> str:
    """
    Retrieves key parameters about the brand voice for a given user from the Context Lake (database).
    """
    print("---TOOL: Retrieving Brand Voice---")
    brand_dna = retrieve_brand_dna(user_id)
    if brand_dna:
        # Format the retrieved JSON into a readable string for the LLM
        return f"Brand DNA parameters: {brand_dna}"
    else:
        return "No specific brand DNA found. Use a general professional and witty tone."


@tool
def sentiment_analyzer(text: str) -> str:
    """
    Analyzes the sentiment of the generated text.
    Returns 'Positive', 'Neutral', or 'Negative'.
    """
    print(f"---TOOL: Analyzing Sentiment for: '{text[:50]}...'---")
    text_lower = text.lower()

    positive_keywords = [
        "great",
        "excellent",
        "awesome",
        "good",
        "happy",
        "love",
        "fantastic",
        "superb",
    ]
    negative_keywords = [
        "bad",
        "terrible",
        "poor",
        "awful",
        "hate",
        "sad",
        "problem",
        "aggressive",
    ]

    positive_score = sum(text_lower.count(kw) for kw in positive_keywords)
    negative_score = sum(text_lower.count(kw) for kw in negative_keywords)

    if positive_score > negative_score:
        return "Positive"
    elif negative_score > positive_score:
        return "Negative"
    else:
        return "Neutral"


@tool
def seo_optimizer(text: str, keywords: List[str]) -> str:
    """
    Optimizes the text for SEO based on provided keywords.
    Returns an optimization report.
    """
    print(f"---TOOL: Optimizing for keywords: {keywords}---")
    report = []
    text_lower = text.lower()

    for keyword in keywords:
        if keyword.lower() not in text_lower:
            report.append(f"Keyword '{keyword}' is missing from the text.")
        else:
            report.append(f"Keyword '{keyword}' is present.")

    if not report:
        return "No keywords provided for SEO optimization."

    return "SEO Optimization Report:\n" + "\n".join(report)


# --- Agent Nodes ---
# Each node in our graph is a function that takes the current state and returns a
# dictionary to update that state.


class ScribeAgent:
    def __init__(self, model):
        self.model = model

    def draft_content(self, state: ScribeState, config: dict):  # Add config argument
        """
        The first step. The Scribe drafts content based on the user's request.
        """
        print("---NODE: Drafting Content---")

        user_id = config["configurable"]["user_id"]  # Extract user_id from config

        # Create a prompt that includes the tools
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are 'The Scribe', a world-class content generation agent. Your mission is to draft compelling text based on a user's request. First, you MUST retrieve the brand voice to understand the style guidelines. Then, write the content. After drafting, analyze the sentiment of the content and, if keywords are provided in the request, optimize the content for SEO using the available tools.",
                ),
                ("human", "{request}"),
            ]
        )

        # Bind all relevant tools with the user_id
        chain = prompt | self.model.bind_tools(
            [
                retrieve_brand_voice.partial(user_id=user_id),
                sentiment_analyzer,
                seo_optimizer,
            ]
        )

        # The user's request is the last message in the state
        user_request = state["messages"][-1].content

        response = chain.invoke({"request": user_request})

        return {"messages": [response]}

    def verify_and_refine(self, state: ScribeState):
        """
        The second step. The Scribe verifies the draft against its tools and refines it.
        """
        print("---NODE: Verifying and Refining---")

        # The model's last message should contain the tool calls
        assistant_message = state["messages"][-1]

        # Execute the tool calls
        tool_outputs = []
        for tool_call in assistant_message.tool_calls:
            tool_output = globals()[tool_call["name"]].invoke(tool_call["args"])
            tool_outputs.append(
                ToolMessage(content=str(tool_output), tool_call_id=tool_call["id"])
            )

        # The new state includes the tool outputs
        new_messages = state["messages"] + tool_outputs

        # Now, call the model again with the tool results to get the final, refined text
        response = self.model.invoke(new_messages)

        return {"messages": [response]}


# --- Graph Definition ---
def get_scribe_agent():
    """
    Initializes and compiles The Scribe agent graph.
    """
    # Initialize the model
    # IMPORTANT: This requires the OPENAI_API_KEY environment variable to be set.
    llm = ChatOpenAI(model="gpt-4-turbo")

    scribe_agent = ScribeAgent(model=llm)

    # Define the graph
    workflow = StateGraph(ScribeState)

    # Add the nodes
    workflow.add_node("draft", scribe_agent.draft_content)
    workflow.add_node("refine", scribe_agent.verify_and_refine)

    # Define the edges
    workflow.set_entry_point("draft")
    workflow.add_edge("draft", "refine")
    workflow.add_edge("refine", END)

    # Compile the graph with a memory saver
    memory = SqliteSaver.from_conn_string(":memory:")
    app = workflow.compile(checkpointer=memory)

    return app


# --- Example Usage ---
if __name__ == "__main__":
    print("This is a blueprint for The Scribe agent.")
    print("To run it as a service, use the 'main.py' file and a uvicorn server.")

    # Example of how to invoke the agent directly
    # os.environ["OPENAI_API_KEY"] = "YOUR_OPENAI_API_KEY"
    # agent_app = get_scribe_agent()
    #
    # config = {"configurable": {"thread_id": "scribe-thread-1"}}
    # user_input = "Write a short, punchy headline for a new course about 'Yoga for Programmers'."
    #
    # final_state = agent_app.invoke(
    #     {"messages": [HumanMessage(content=user_input)]},
    #     config=config
    # )
    #
    # print("\n--- FINAL OUTPUT ---")
    # print(final_state['messages'][-1].content)
