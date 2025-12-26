import streamlit as st
import os
# ... (Import your existing AgentState, monitor_node, analyzer_node, repair_node, and workflow here)

st.set_page_config(page_title="Autonomous SRE Dashboard", layout="wide")
st.title("🤖 Autonomous Network SRE Agent")
st.write("Real-time monitoring and self-healing automation powered by Gemini 2.0 Flash.")

# Initialize Session State for logs
if "agent_logs" not in st.session_state:
    st.session_state.agent_logs = []

# --- Sidebar Configuration ---
with st.sidebar:
    st.header("Settings")
    target_ip = st.text_input("Target Node IP", value="192.168.1.105")
    if st.button("Clear Dashboard"):
        st.session_state.agent_logs = []

# --- Main Dashboard ---
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Activity Log")
    log_container = st.container(height=400)
    
    if st.button("🚀 Start Monitoring Run"):
        # Setup initial state
        initial_input = {"target_ip": target_ip, "status": "Unknown", "attempts": 0, "history": []}
        
        # Compile and Run
        app = workflow.compile()
        
        for output in app.stream(initial_input):
            for key, value in output.items():
                log_entry = f"Step '{key}' finished. Status: {value.get('status', 'N/A')}"
                st.session_state.agent_logs.append(log_entry)
                log_container.write(log_entry)
                
                # If Gemini analyzed, show the reasoning
                if "history" in value:
                    st.session_state.agent_logs.append(f"🧠 Gemini: {value['history'][-1]}")
                    log_container.info(value['history'][-1])

with col2:
    st.subheader("System Health")
    # Display the most recent status in a big metric
    if st.session_state.agent_logs:
        last_status = "Healthy" if "Online" in str(st.session_state.agent_logs) else "Issue Detected"
        st.metric(label="Network Status", value=last_status)
    else:
        st.metric(label="Network Status", value="Idle")