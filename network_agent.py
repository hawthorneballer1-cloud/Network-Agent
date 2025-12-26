import os
import random
from typing import Annotated, TypedDict
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END, START

# --- 1. CONFIGURATION & MODELS ---
# Using the environment variable you successfully retrieved
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    google_api_key=os.getenv("GEMINI_API_KEY")
)

# --- 2. STATE DEFINITION ---
class AgentState(TypedDict):
    target_ip: str
    status: str
    attempts: int
    history: list

# --- 3. TOOLS (Industrial Simulation) ---
@tool
def ping_server(hostname: str):
    """Checks if a server is reachable. Returns 'Online' or 'Offline'."""
    # Simulating a 50/50 failure rate for testing
    return "Offline" if random.random() > 0.5 else "Online"

@tool
def restart_service(service_name: str):
    """Simulates restarting a network service or Docker container."""
    return f"SUCCESS: Service {service_name} has been restarted."

# --- 4. NODES (The Brain Logic) ---
def monitor_node(state: AgentState):
    print(f"\n[Monitor] Checking status for {state['target_ip']}...")
    current_status = ping_server.invoke(state['target_ip'])
    return {"status": current_status, "attempts": state['attempts'] + 1}

def analyzer_node(state: AgentState):
    print(f"[Analyzer] Asking Gemini to evaluate the {state['status']} status...")
    prompt = (
        f"The server {state['target_ip']} is {state['status']}. "
        f"This is attempt number {state['attempts']}. "
        "Should we attempt a restart? Provide a brief reasoning."
    )
    response = llm.invoke(prompt)
    print(f"--- Gemini's Analysis: {response.content} ---")
    return {"history": state['history'] + [response.content]}

def repair_node(state: AgentState):
    print(f"[Repair] Executing automated recovery...")
    result = restart_service.invoke("nginx_gateway")
    return {"history": state['history'] + [result]}

# --- 5. GRAPH CONSTRUCTION ---
workflow = StateGraph(AgentState)

# Add our nodes to the graph
workflow.add_node("monitor", monitor_node)
workflow.add_node("analyzer", analyzer_node)
workflow.add_node("repair", repair_node)

# Set the flow
workflow.add_edge(START, "monitor")

# Routing Logic: If offline, go to Gemini. If online, we are finished.
workflow.add_conditional_edges(
    "monitor",
    lambda x: "analyzer" if x["status"] == "Offline" and x["attempts"] < 3 else END
)

# After Gemini analyzes, go to repair
workflow.add_edge("analyzer", "repair")

# After repair, loop back to monitor to verify the fix
workflow.add_edge("repair", "monitor")

# Compile the final application
app = workflow.compile()

# --- 6. EXECUTION ---
if __name__ == "__main__":
    print("Starting Autonomous Network Agent...")
    
    # Initial input data
    initial_input = {
        "target_ip": "192.168.1.105", 
        "status": "Unknown", 
        "attempts": 0, 
        "history": []
    }
    
    # Stream the steps so you can see the agent "thinking" in the terminal
    for output in app.stream(initial_input):
        for key, value in output.items():
            print(f"Step '{key}' finished.")