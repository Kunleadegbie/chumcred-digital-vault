# auth.py
import streamlit as st
from db import verify_user

def login_user(email, password):
    user = verify_user(email, password)
    if user:
        return user
    return None

def get_current_user():
    return st.session_state.get("user")

def logout_user():
    st.session_state.user = None


