import json
from datetime import datetime
import streamlit as st

def log_api_interaction(input_data: dict, response: str, files: list = None):
    """Log API interaction with Vertex"""
    if 'api_logs' not in st.session_state:
        st.session_state.api_logs = []
    
    timestamp = datetime.now().isoformat()
    
    log_entry = {
        "timestamp": timestamp,
        "input": input_data,
        "files": files or [],
        "response": response
    }
    
    st.session_state.api_logs.insert(0, log_entry)  # Add to beginning of list

def format_json(data):
    """Format JSON data for display"""
    return json.dumps(data, indent=2, ensure_ascii=False) 