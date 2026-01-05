import os
from fastapi import FastAPI
from pydantic import BaseModel
from scribe import get_scribe_agent, ScribeState
from langchain_core.messages import HumanMessage

# --- FastAPI App ---
app = FastAPI(
    title="Synapse Agent Server",
    description="An API server to interact with the Synapse Agent Swarm.",
    version="1.0.0",
)


# --- API Models ---
class ScribeRequest(BaseModel):
    thread_id: str
    user_id: str  # Add user_id
    prompt: str


# --- Agent Initialization ---
# This is where we would configure the agent with API keys and other settings.
# For now, we'll use placeholders.


scribe_agent_app = get_scribe_agent()


@app.post("/invoke/scribe")
async def invoke_scribe_agent(request: ScribeRequest):
    """
    Invokes The Scribe agent with a given prompt, user_id, and thread_id.
    """
    config = {
        "configurable": {"thread_id": request.thread_id, "user_id": request.user_id}
    }  # Pass user_id in config

    input_message = HumanMessage(content=request.prompt)

    # Stream the agent's response
    # Note: For a production implementation, you might use WebSockets
    # or a different streaming response method.
    final_state = scribe_agent_app.invoke({"messages": [input_message]}, config=config)

    # Return the final message from the agent
    return {"response": final_state["messages"][-1].content}


@app.get("/")
def read_root():
    return {
        "message": "Synapse Agent Server is running. Visit /docs for API documentation."
    }


if __name__ == "__main__":
    import uvicorn

    print("--- Starting Synapse Agent Server ---")
    print("API documentation will be available at http://127.0.0.1:8000/docs")
    uvicorn.run(app, host="127.0.0.1", port=8000)
