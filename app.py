import streamlit as st
import os
import random
from typing import Annotated, TypedDict
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END, START

# --- 1. SETUP & SECRETS ---
# Access the key you saved in the Streamlit Cloud "Secrets" dashboard
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
    os.environ["GOOGLE_API_KEY"] = api_key # LangChain looks for this env var
else:
    st.error("Please add GEMINI_API_KEY to your Streamlit Secrets.")
    st.stop()

# Initialize Gemini 2.0 Flash
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    google_api_key=api_key,
    temperature=0.7
)

# --- 2. AGENT DEFINITION ---
class AgentState(TypedDict):
    target_ip: str
    status: str
    attempts: int
    history: list

@tool
def ping_server(hostname: str):
    """Checks if a server is reachable."""
    # Simulating random network behavior for the demo
    return "Offline" if random.random() > 0.5 else "Online"

def monitor_node(state: AgentState):
    status = ping_server.invoke(state['target_ip'])
    return {"status": status, "attempts": state['attempts'] + 1}

def analyzer_node(state: AgentState):
    prompt = f"The server {state['target_ip']} is {state['status']}. Should we restart it? Why?"
    response = llm.invoke(prompt)
    return {"history": state.get('history', []) + [response.content]}

# --- 3. GRAPH CONSTRUCTION ---
# Defining the workflow globally ensures it is available for every rerun
builder = StateGraph(AgentState)
builder.add_node("monitor", monitor_node)
builder.add_node("analyzer", analyzer_node)

builder.add_edge(START, "monitor")

# Routing Logic: If offline, analyze. If online or too many attempts, finish.
builder.add_conditional_edges(
    "monitor",
    lambda x: "analyzer" if x["status"] == "Offline" and x["attempts"] < 3 else END
)
builder.add_edge("analyzer", END)

# Use st.session_state to persist the compiled agent
if "agent_app" not in st.session_state:
    st.session_state.agent_app = builder.compile()

# --- 4. STREAMLIT UI ---
st.set_page_config(page_title="Autonomous SRE", page_icon="🤖")
st.title("🤖 Autonomous Network SRE Agent")
st.markdown("Monitoring system powered by **LangGraph** and **Gemini 2.0 Flash**.")

target_ip = st.text_input("Enter Target IP to Monitor", value="192.168.1.105")

if st.button("🚀 Run Diagnostic"):
    # Initial state for the workflow
    initial_input = {
        "target_ip": target_ip, 
        "status": "Unknown", 
        "attempts": 0, 
        "history": []
    }
    
    # Run the compiled graph and stream output to the UI
    with st.status("Agent is working...", expanded=True) as status:
        for output in st.session_state.agent_app.stream(initial_input):
            for node_name, state_update in output.items():
                st.write(f"✅ **Step Finished:** `{node_name}`")
                
                if "status" in state_update:
                    st.write(f"Current Status: **{state_update['status']}**")
                
                if "history" in state_update:
                    with st.expander("View Gemini Reasoning"):
                        st.info(state_update['history'][-1])
        status.update(label="Diagnostic Complete!", state="complete")


