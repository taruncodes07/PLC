import json, bcrypt, streamlit as st
def load_users():
    return json.load(open("users.json"))
def verify_password(p, h):
    return bcrypt.checkpw(p.encode(), h.encode())
def login():
    st.title("Login")
    u=st.text_input("Username")
    p=st.text_input("Password",type="password")
    if st.button("Login"):
        users=load_users()
        if u in users and verify_password(p,users[u]["password"]):
            st.session_state.user=u
            st.session_state.role=users[u]["role"]
            st.rerun()
        st.error("Invalid credentials")
