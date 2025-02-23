import streamlit as st
import requests

from agentic.events import SSEDecoder

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

def generate_agentic_response(prompt):
    sse_decoder = SSEDecoder()

    byte_stream_iterator = requests.post(
        f"{BASE_URL}/{selected_agent}/stream_request",
        json={"prompt": prompt},
        stream=True,
        headers={'Accept': 'text/event-stream'}
    )

    for sse in sse_decoder.iter_bytes(byte_stream_iterator):
        yield sse.data



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
        response = generate_agentic_response(prompt)
        full_response = st.write_stream(response)

            
    
    message = {"role": "assistant", "content": full_response}
    st.session_state.messages.append(message)
