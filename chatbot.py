# chatbot.py

import streamlit as st
import pandas as pd
from auth import check_role, load_users
from google import genai
from google.genai.errors import APIError
import os

# --- 1. Model Initialization ---
# Using gemini-2.5-flash for better availability and cost-efficiency
AI_MODEL = 'gemini-2.5-flash-lite'
MAX_DATASET_BYTES = 1_500_000

def init_ai_client():
    """Initializes the Gemini client, retrieving API key from Streamlit secrets."""
    try:
        # Fetching API key from secrets.toml or Streamlit Cloud UI secrets
        api_key = st.secrets["gemini"]["api_key"]
        if not api_key:
             st.error("Gemini API Key not found. Please set it in .streamlit/secrets.toml or Streamlit Cloud Secrets.")
             return None
        
        client = genai.Client(api_key=api_key)
        return client
    except KeyError:
        st.error("Gemini API Key not found. Please set it in .streamlit/secrets.toml or Streamlit Cloud Secrets.")
        return None
    except Exception as e:
        st.error(f"Error initializing Gemini client: {e}")
        return None

# --- 2. Data Condensation Function ---

def get_last_dataset_path():
    """Returns the last dataset file path for the logged-in user."""
    user_info = st.session_state.get('user_info', {})
    username = user_info.get('username')
    if not username:
        return None

    users = load_users()
    last_dataset = users.get(username, {}).get('last_dataset')
    if not last_dataset or last_dataset == 'None':
        return None

    if not os.path.exists(last_dataset):
        return None

    return last_dataset


def read_dataset_text(file_path):
    """Reads the dataset file as UTF-8 text with a size guard."""
    file_size = os.path.getsize(file_path)
    if file_size > MAX_DATASET_BYTES:
        return None, f"Dataset is too large ({file_size:,} bytes). Please use a smaller file."

    with open(file_path, 'rb') as f:
        raw_bytes = f.read()
    return raw_bytes.decode('utf-8', errors='replace'), None


# --- 3. Chatbot Page Function ---

def chatbot_page():
    """Streamlit page for the AI Production Analyst Chatbot."""
    st.title("🤖 AI Production Analyst Chatbot")
    st.markdown("---")

    if not check_role('Analyst'):
        st.error("Access Denied: You must be an Analyst or Admin to use the AI Chatbot.")
        return

    # Check for dataset presence on disk
    dataset_path = get_last_dataset_path()
    if not dataset_path:
        st.warning("No dataset file found. Please load a dataset on the 'Load & Manage Dataset' page first.")
        return

    client = init_ai_client()
    if not client:
        return

    st.info(f"Using **{AI_MODEL}**. Ask for summaries, suggestions, or feel free to chat casually!")
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state["messages"] = [{"role": "model", "content": "Hello! I am your AI Production Analyst. I have the data summary ready. How can I help you?"}]

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Accept user input
    if prompt := st.chat_input("Enter your question..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        normalized_prompt = prompt.lower()
        
        # --- LOGIC: DETERMINE PROMPT TYPE AND CONSTRUCT CONTEXT ---
        
        is_data_query = False
        
        # Keywords for analytical questions
        data_keywords = ["summary", "kpi", "waste", "downtime", "product", "efficiency", "suggest", "data", "analyze"]
        
        # 1. Handle Capabilities Query (Highest Priority for specific persona)
        if any(word in normalized_prompt for word in ["capabilities", "what can you do", "functionalities", "what are you"]):
            
            # --- STRONGER, MORE RESTRICTIVE SYSTEM INSTRUCTION for Capabilities ---
            system_instruction = (
                "You are the AI Production Analyst embedded within the Chips Factory Report Generator app. "
                "Your primary function is to analyze the production dataset currently loaded into the app. "
                "You MUST NOT give a generic LLM capabilities list. You MUST ONLY state your capabilities "
                "strictly in the context of analyzing the manufacturing data. "
            )
            
            # Forcing the structured response directly in the prompt
            full_prompt = (
                f"{system_instruction}\n\n"
                "Begin your response with: 'My capabilities are specifically tailored to the analysis of the loaded manufacturing data.' "
                "Provide a detailed response that includes: "
                "1. Data Summarization (e.g., total production, waste, downtime). "
                "2. Trend and Anomaly Detection. "
                "3. Root Cause Analysis (e.g., top downtime reasons). "
                "4. Actionable Recommendations for improvement. "
                "5. Conversational ability for non-analytical, general questions.\n\n"
                f"--- USER QUESTION: What are your capabilities in this app?"
            )
            
        # 2. Handle Data Query
        elif any(word in normalized_prompt for word in data_keywords):
            dataset_text, dataset_error = read_dataset_text(dataset_path)
            if dataset_error:
                st.error(dataset_error)
                return

            system_instruction = (
                "You are an expert Senior Production Data Analyst. Your primary task is to analyze the provided "
                "manufacturing dataset file content and answer the user's analytical question. "
                "Do not invent data. If the dataset is missing information, state that clearly. "
                "Avoid dumping large raw tables in the response."
            )
            full_prompt = (
                f"{system_instruction}\n\n"
                f"--- DATASET FILE (CSV) ---\n"
                f"File name: {os.path.basename(dataset_path)}\n"
                f"File contents:\n{dataset_text}\n\n"
                f"--- USER QUESTION: {prompt}"
            )
            is_data_query = True
        
        # 3. Handle Casual Conversation
        else:
            full_prompt = prompt
            system_instruction = "You are a friendly, conversational AI assistant. Do not mention manufacturing or production data unless the user asks specifically about it."

        # --- Generate model response ---
        
        with st.chat_message("model"):
            with st.spinner(f"Processing {'data analysis' if is_data_query else 'response'}..."):
                try:
                    # FIX: Removed the explicit 'system_instruction' parameter to resolve the "unexpected keyword argument" error.
                    # The system instruction text is now correctly prepended to the 'full_prompt'.
                    response = client.models.generate_content(
                        model=AI_MODEL,
                        contents=full_prompt,
                        config={'temperature': 0.7 if not is_data_query else 0.0}
                    )
                    
                    st.markdown(response.text)
                    st.session_state.messages.append({"role": "model", "content": response.text})
                
                except APIError as e:
                    error_message = f"AI API Error: Could not process request. Details: {e}. Please try again later."
                    st.error(error_message)
                    st.session_state.messages.append({"role": "model", "content": error_message})
                except Exception as e:
                    error_message = f"An unexpected error occurred: {e}"
                    st.error(error_message)
                    st.session_state.messages.append({"role": "model", "content": error_message})