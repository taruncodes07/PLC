# auth.py

import streamlit as st
import json
import hashlib # NOTE: For production, use a library like 'bcrypt' for stronger hashing.

USERS_FILE = 'users.json'

def load_users():
    """Loads user data from the JSON file."""
    try:
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error(f"Error: {USERS_FILE} not found.")
        return {}

def save_users(users_data):
    """Saves user data back to the JSON file."""
    try:
        with open(USERS_FILE, 'w') as f:
            json.dump(users_data, f, indent=4)
    except Exception as e:
        st.error(f"Error saving user data: {e}")

def hash_password(password):
    """Hashes a password using SHA-256 (for demonstration)."""
    return hashlib.sha256(password.encode()).hexdigest()

# NOTE: The redundant check_password function has been removed.
# The authentication is performed directly in the authenticate() function
# by comparing the hash of the input password with the stored hash.

def authenticate():
    """Implements the Streamlit login page."""
    
    st.title("🔐 Production Report Generator Login")
    
    users = load_users()

    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
        st.session_state['user_info'] = None

    if st.session_state['logged_in']:
        # User is logged in, show a simple welcome and main app button
        st.success(f"Welcome back, {st.session_state['user_info']['full_name']}!")
        st.session_state['page'] = 'Dashboard'
        return True

    # Login Form
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")

        if submitted:
            if username in users:
                user_data = users[username]
                
                # CORRECTED LOGIC: Direct comparison of the HASHED input password 
                # with the stored hashed password.
                if user_data['hashed_password'] == hash_password(password):
                    st.session_state['logged_in'] = True
                    st.session_state['user_info'] = user_data
                    st.session_state['page'] = 'Dashboard' # Redirect to dashboard upon successful login
                    st.rerun()
                else:
                    st.error("Incorrect username or password.")
            else:
                st.error("Incorrect username or password.")
    return False

def logout():
    """Resets session state to log the user out."""
    st.session_state['logged_in'] = False
    st.session_state['user_info'] = None
    st.session_state.pop('df', None) # Clear dataset from memory
    st.session_state.pop('page', None)
    st.success("Logged out successfully.")
    st.rerun()

def check_role(required_role):
    """Checks if the current user has the required role for access."""
    if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
        st.warning("Please log in to access this page.")
        return False
    
    user_role = st.session_state['user_info']['role']
    
    if required_role == 'Admin':
        return user_role == 'Admin'
    elif required_role == 'Analyst':
        return user_role in ['Admin', 'Analyst']
    elif required_role == 'Viewer':
        return user_role in ['Admin', 'Analyst', 'Viewer']
    
    return False