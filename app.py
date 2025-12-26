import streamlit as st
import os
from network_agent import workflow  # Correctly importing the global variable

st.set_page_config(page_title="Autonomous SRE Dashboard")
st.title("🤖 Autonomous Network SRE Agent")

# Sync Streamlit Secrets to Environment Variables for LangChain
if "GEMINI_API_KEY" in st.secrets:
    os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]

# PERSISTENCE: Compile the app once and save it in session state
if "agent_app" not in st.session_state:
    st.session_state.agent_app = workflow.compile()

target_ip = st.text_input("Target Node IP", value="192.168.1.105")

if st.button("🚀 Start Monitoring Run"):
    # Initial state for the run
    initial_input = {
        "target_ip": target_ip, 
        "status": "Unknown", 
        "attempts": 0, 
        "history": []
    }
    
    # Run the compiled graph from session state
    for output in st.session_state.agent_app.stream(initial_input):
        for key, value in output.items():
            st.write(f"**Node Finished:** `{key}`")
            if "status" in value:
                st.success(f"Network Status: {value['status']}")
            if "history" in value:
                st.info(f"Gemini Analysis: {value['history'][-1]}")

