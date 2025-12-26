import streamlit as st
import os
import random
from typing import Annotated, TypedDict
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END, START

# --- 1. SETUP & SECRETS ---
# Streamlit Cloud reads from the "Secrets" box you filled earlier
api_key = st.secrets["GEMINI_API_KEY"]

llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    google_api_key=api_key
)

# --- 2. AGENT LOGIC (Nodes & Tools) ---
class AgentState(TypedDict):
    target_ip: str
    status: str
    attempts: int
    history: list

@tool
def ping_server(hostname: str):
    """Checks if a server is reachable."""
    return "Offline" if random.random() > 0.5 else "Online"

def monitor_node(state: AgentState):
    status = ping_server.invoke(state['target_ip'])
    return {"status": status, "attempts": state['attempts'] + 1}

def analyzer_node(state: AgentState):
    prompt = f"The server {state['target_ip']} is {state['status']}. Should we restart?"
    response = llm.invoke(prompt)
    return {"history": state['history'] + [response.content]}

# --- 3. GRAPH CONSTRUCTION ---
# We define the workflow globally so the UI can always see it
workflow = StateGraph(AgentState)
workflow.add_node("monitor", monitor_node)
workflow.add_node("analyzer", analyzer_node)
workflow.set_entry_point("monitor")

workflow.add_conditional_edges(
    "monitor",
    lambda x: "analyzer" if x["status"] == "Offline" and x["attempts"] < 3 else END
)
workflow.add_edge("analyzer", END)

# Compile the app once and store it in session state to prevent NameErrors
if "agent_app" not in st.session_state:
    st.session_state.agent_app = workflow.compile()

# --- 4. STREAMLIT UI ---
st.title("🤖 Autonomous SRE Agent")

target_ip = st.text_input("Target IP", "192.168.1.105")

if st.button("Run Diagnostic"):
    initial_state = {"target_ip": target_ip, "status": "Unknown", "attempts": 0, "history": []}
    
    # Use the app from session state
    for output in st.session_state.agent_app.stream(initial_input=initial_state):
        for key, value in output.items():
            st.write(f"**Step:** {key}")
            if "status" in value:
                st.write(f"Status detected: {value['status']}")
            if "history" in value:
                st.info(value['history'][-1])
