# data_loader.py

import streamlit as st
import pandas as pd
import json
from auth import load_users, save_users

DEFAULT_DATASET = "potato_chips_factory_30days_400rows.csv"
USERS_FILE = 'users.json'

def save_last_dataset(username, file_name):
    """Stores the last used dataset name for a user."""
    users = load_users()
    if username in users:
        users[username]['last_dataset'] = file_name
        save_users(users)

@st.cache_data(show_spinner="Loading data and parsing columns...")
def load_data(file_path):
    """Loads the production data from a given CSV file path."""
    try:
        df = pd.read_csv(file_path)
        
        # Data Cleaning and Preparation
        df['Date'] = pd.to_datetime(df['Date'])
        
        # Create unique ID for row tracking in audit log
        df.insert(0, 'Row_ID', df.index)
        
        return df
    except Exception as e:
        st.error(f"Error loading data from {file_path}: {e}")
        return pd.DataFrame()

def data_loader_page():
    """Streamlit page for loading and managing the dataset."""
    st.title("🗄️ Load & Manage Dataset")
    st.markdown("---")
    
    user_info = st.session_state['user_info']
    username = user_info['username']
    users = load_users()
    last_dataset = users[username].get('last_dataset')

    # Option 1: Load Last Used Dataset
    if last_dataset and last_dataset != 'None':
        st.subheader("Load Last Used Dataset")
        if st.button(f"Reload: {last_dataset}", width='stretch'):
            st.session_state['df'] = load_data(last_dataset)
            st.success(f"Successfully loaded {last_dataset}.")
    
    # Option 2: Upload New CSV
    st.subheader("Upload New Production Data (CSV)")
    uploaded_file = st.file_uploader("Choose a CSV file", type=['csv'])

    if uploaded_file is not None:
        file_name = uploaded_file.name
        
        # Save file locally (Streamlit handles temporary file on rerun, but we need a fixed path to reload)
        # For simplicity in this demo, we assume the file name maps to a file in the app directory.
        # In a real app, you would save this file to a persistent storage path.
        
        # Load the uploaded file content directly
        st.session_state['df'] = load_data(uploaded_file)
        
        # Update metadata
        save_last_dataset(username, file_name)
        st.success(f"Successfully uploaded and loaded '{file_name}'.")

    # Option 3: Load Default
    if st.button(f"Load Default Dataset: {DEFAULT_DATASET}", width='stretch'):
        st.session_state['df'] = load_data(DEFAULT_DATASET)
        save_last_dataset(username, DEFAULT_DATASET)
        st.success(f"Successfully loaded default dataset: {DEFAULT_DATASET}.")

    # Display current dataset info
    if 'df' in st.session_state and not st.session_state['df'].empty:
        df = st.session_state['df']
        st.markdown("### Current Dataset Preview")
        st.info(f"Loaded {len(df)} rows and {len(df.columns)} columns.")
        st.dataframe(df.head(), width='stretch')