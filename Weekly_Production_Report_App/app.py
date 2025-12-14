import streamlit as st
from auth import login
st.set_page_config(layout="wide")
if "user" not in st.session_state:
    login()
    st.stop()
st.write("Welcome", st.session_state.user)
