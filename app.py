# app.py

import streamlit as st
from auth import authenticate, logout, check_role
from data_loader import data_loader_page
from dashboard import dashboard_page
from editor import editor_page
from audit_logger import audit_log_page
from reports import reports_page
from export_utils import export_page
from chatbot import chatbot_page # NEW: Import the chatbot module

# --- Configuration ---
st.set_page_config(
    page_title="Weekly Production Report Generator",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CRITICAL FIX: Initialize Session State Keys at App Start ---
if 'page' not in st.session_state:
    st.session_state['page'] = 'Login'
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user_info' not in st.session_state:
    st.session_state['user_info'] = None

# Set Dark Theme (Visual styles)
st.markdown("""
<style>
    /* Dark Theme Setup for a Modern UI */
    .stApp {
        background-color: #1E1E1E;
        color: #F0F2F6;
    }
    .main .block-container {
        padding-top: 2rem;
        padding-right: 2rem;
        padding-left: 2rem;
        padding-bottom: 2rem;
    }
    /* Streamlit Sidebar Customization */
    [data-testid="stSidebar"] {
        background-color: #2D2D2D;
    }
    /* Metric Cards */
    [data-testid="stMetric"], .css-1r6dm7m { /* Targeting the custom metric card container */
        background-color: #3C3C3C;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #4D4D4D;
        box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2);
    }
</style>
""", unsafe_allow_html=True)


# --- Page Routing Dictionary ---
PAGES = {
    "Login": authenticate,
    "Dashboard": dashboard_page,
    "AI Chatbot (Beta)": chatbot_page, # NEW: Added Chatbot page
    "Load & Manage Dataset": data_loader_page,
    "Data Editor": editor_page,
    "Reports": reports_page,
    "Audit Logs": audit_log_page,
    "Export Database": export_page
}

# --- Sidebar Navigation ---
with st.sidebar:
    st.header("🏭 Chips Factory App")
    st.markdown("---")
    
    if not st.session_state['logged_in']:
        if st.button("Login", width='stretch'):
            st.session_state['page'] = 'Login'
    
    else:
        user_info = st.session_state.get('user_info', {})
        st.success(f"User: {user_info.get('full_name', 'N/A')} ({user_info.get('role', 'N/A')})")
        st.markdown("---")

        # Dynamic Navigation based on Role
        nav_buttons = {
            "Dashboard": "Viewer",
            "AI Chatbot (Beta)": "Analyst", # NEW: Added Chatbot to Analyst/Admin view
            "Load & Manage Dataset": "Analyst",
            "Data Editor": "Admin",
            "Reports": "Analyst",
            "Audit Logs": "Admin",
            "Export Database": "Analyst",
        }
        
        st.subheader("Menu")
        for label, required_role in nav_buttons.items():
            if check_role(required_role):
                if st.button(label, key=f"nav_{label}", width='stretch', help=f"Requires {required_role} role"):
                    st.session_state['page'] = label

        st.markdown("---")
        if st.button("Logout", key="logout_btn", width='stretch'):
            logout()
            
# --- Page Rendering ---
page_func = PAGES.get(st.session_state['page'])
if page_func:
    page_func()
else:
    st.error("Application Error: Navigation page not found.")