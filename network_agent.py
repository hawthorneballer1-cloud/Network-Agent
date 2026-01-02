from tenacity import retry, stop_after_attempt, wait_exponential

# REPLACE your old analyzer_node with this one:
@retry(
    stop=stop_after_attempt(5), 
    wait=wait_exponential(multiplier=1, min=4, max=60),
    reraise=True
)
def analyzer_node(state: AgentState):
    """Analyzes network issues with built-in retry logic for API limits."""
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash", 
        google_api_key=api_key
    )
    
    prompt = f"The server {state['target_ip']} is {state['status']}. Should we restart? Explain why."
    
    # This call is now protected by the @retry decorator above
    response = llm.invoke(prompt)
    return {"history": state.get('history', []) + [response.content]}


