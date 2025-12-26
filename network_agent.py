import os
import random
from typing import Annotated, TypedDict
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END, START

# --- 1. STATE DEFINITION ---
class AgentState(TypedDict):
    target_ip: str
    status: str
    attempts: int
    history: list

# --- 2. TOOLS ---
@tool
def ping_server(hostname: str):
    """Checks if a server is reachable."""
    return "Offline" if random.random() > 0.5 else "Online"

# --- 3. NODES ---
def monitor_node(state: AgentState):
    ip = state.get("target_ip", "127.0.0.1")
    status = ping_server.invoke(ip)
    return {"status": status, "attempts": state['attempts'] + 1}

def analyzer_node(state: AgentState):
    # Retrieve key from environment (synced from st.secrets)
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash", 
        google_api_key=api_key
    )
    
    prompt = f"The server {state['target_ip']} is {state['status']}. Should we restart? Explain why."
    response = llm.invoke(prompt)
    return {"history": state.get('history', []) + [response.content]}

# --- 4. GRAPH CONSTRUCTION ---
builder = StateGraph(AgentState)
builder.add_node("monitor", monitor_node)
builder.add_node("analyzer", analyzer_node)
builder.add_edge(START, "monitor")

builder.add_conditional_edges(
    "monitor",
    lambda x: "analyzer" if x["status"] == "Offline" and x["attempts"] < 3 else END
)
builder.add_edge("analyzer", END)

workflow = builder
