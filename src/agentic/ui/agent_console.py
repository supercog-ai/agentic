import json
import streamlit as st
import requests
import re

BASE_URL = "http://localhost:8086"

st.title("Agentic")

#======================
# Define Agent        #
#======================
def format_endpoint(endpoint: str) -> str:
    "Format endpoint for markdown display in UI"
    endpoint = endpoint.lstrip('/')
    return ' '.join(word.capitalize() for word in endpoint.split('_'))

@st.cache_data
def get_all_agents() -> list[str]:
    response = requests.get(f"{BASE_URL}/_discovery")
    response.raise_for_status()
    return response.json()

all_agents = get_all_agents()

selected_agent = st.selectbox(
    "Select an agent", all_agents, format_func=format_endpoint
)

#======================
# SSE Parsing Helpers #
#======================
def parse_sse(response_text):
    events = response_text.strip().split("\r\n\r\n")  # Split events by double newlines
    messages = []
    
    for event in events:
        lines = event.split("\r\n")
        data_lines = [line[6:] for line in lines if line.startswith("data: ")]  # Remove 'data: ' prefix

        if not data_lines:
            continue
        
        message = "".join(data_lines).strip()  # Reassemble split messages
        
        # Try parsing JSON if it's a structured message
        try:
            message_json = json.loads(message)
            messages.append(message_json)
        except json.JSONDecodeError:
            messages.append(message)  # If not JSON, treat as plain text

    return messages

#======================
# Create Session      #
#======================
if "messages" not in st.session_state:
    st.session_state.messages = []

#======================
# Chat Interface      #
#======================
if prompt := st.chat_input("Type your message here"):
    # Save and display the user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        try:
            # Send the POST request with stream enabled and proper SSE header
            response = requests.post(
                f"{BASE_URL}/{selected_agent}/stream_request",
                json={"prompt": prompt},
                stream=True,
                headers={'Accept': 'text/event-stream'}
            )
            
            # Manually iterate over the SSE event blocks
            for event in response.iter_lines():
                if event:
                    event_text = event.decode('utf-8')
                    parsed = parse_sse(event_text)
                    
                    # A None value signals the termination marker
                    if parsed is None:
                        break
                    
                    # Determine the content based on expected event structure
                    content = ""
                    for message in parsed:
                        if isinstance(message, dict):
                            if message.get("event_type") == "ChatOutput":
                                content = message.get("delta", {}).get("content", "")
                            elif message.get("event_type") == "FinishCompletion":
                                content = message.get("response", {}).get("content", "")
                            elif "content" in message:
                                content = message.get("content", "")
                            elif "raw" in message:
                                content = message.get("raw", "")
                    
                    if content:
                        full_response += content
                        response_placeholder.markdown(full_response + "▌")
        
        except Exception as e:
            full_response = f"Error communicating with agent: {str(e)}"
            response_placeholder.markdown(full_response)
        
        # Final display update once streaming completes
        response_placeholder.markdown(full_response)
    
    st.session_state.messages.append({"role": "assistant", "content": full_response})
