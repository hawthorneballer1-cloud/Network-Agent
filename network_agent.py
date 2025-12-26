import os
import random
from typing import Annotated, TypedDict
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END, START

# 1. Define the State globally
class AgentState(TypedDict):
    target_ip: str
    status: str
    attempts: int
    history: list

# 2. Define Tools
@tool
def ping_server(hostname: str):
    """Checks if a server is reachable."""
    return "Offline" if random.random() > 0.5 else "Online"

# 3. Define Nodes
def monitor_node(state: AgentState):
    # Retrieve target_ip from the state
    ip = state.get("target_ip", "127.0.0.1")
    status = ping_server.invoke(ip)
    return {"status": status, "attempts": state['attempts'] + 1}

def analyzer_node(state: AgentState):
    # Initialize LLM here to ensure it uses the latest secret
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=api_key)
    
    prompt = f"The server {state['target_ip']} is {state['status']}. Should we restart? Explain."
    response = llm.invoke(prompt)
    return {"history": state['history'] + [response.content]}

# 4. Build the Graph structure
builder = StateGraph(AgentState)
builder.add_node("monitor", monitor_node)
builder.add_node("analyzer", analyzer_node)

builder.add_edge(START, "monitor")

# Routing Logic
builder.add_conditional_edges(
    "monitor",
    lambda x: "analyzer" if x["status"] == "Offline" and x["attempts"] < 3 else END
)
builder.add_edge("analyzer", END)

# Export the builder so app.py can compile it
workflow = builder
    # Stream the steps so you can see the agent "thinking" in the terminal
    for output in app.stream(initial_input):
        for key, value in output.items():

            print(f"Step '{key}' finished.")
