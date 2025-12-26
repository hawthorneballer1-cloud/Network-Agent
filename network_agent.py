import os
import random
from typing import Annotated, TypedDict
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END, START

# --- 1. STATE DEFINITION ---
# This must be defined at the top level so it can be imported
class AgentState(TypedDict):
    target_ip: str
    status: str
    attempts: int
    history: list

# --- 2. TOOLS ---
@tool
def ping_server(hostname: str):
    """Checks if a server is reachable. Returns 'Online' or 'Offline'."""
    # Simulating a real network environment
    return "Offline" if random.random() > 0.5 else "Online"

# --- 3. NODES ---
def monitor_node(state: AgentState):
    # Retrieve target_ip from state safely
    ip = state.get("target_ip", "127.0.0.1")
    status = ping_server.invoke(ip)
    return {"status": status, "attempts": state['attempts'] + 1}

def analyzer_node(state: AgentState):
    # Access the API key from environment variables (synced from st.secrets)
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash", 
        google_api_key=api_key
    )
    
    prompt = f"The server {state['target_ip']} is {state['status']}. Should we restart? Explain why."
    response = llm.invoke(prompt)
    return {"history": state.get('history', []) + [response.content]}

# --- 4. GRAPH CONSTRUCTION ---
# We define the builder globally so app.py can import it
builder = StateGraph(AgentState)

builder.add_node("monitor", monitor_node)
builder.add_node("analyzer", analyzer_node)

builder.set_entry_point("monitor")

# Routing Logic: If offline, go to Gemini analysis
builder.add_conditional_edges(
    "monitor",
    lambda x: "analyzer" if x["status"] == "Offline" and x["attempts"] < 3 else END
)

builder.add_edge("analyzer", END)

# This global variable is what app.py imports
workflow = builder

# --- 5. LOCAL TESTING ---
# This block only runs if you execute THIS file directly in VS Code
if __name__ == "__main__":
    # For local testing, ensure your key is in the environment
    test_app = workflow.compile()
    print("--- Starting Local Test Run ---")
    
    test_input = {
        "target_ip": "127.0.0.1", 
        "attempts": 0, 
        "history": []
    }
    
    for output in test_app.stream(test_input):
        print(output)
