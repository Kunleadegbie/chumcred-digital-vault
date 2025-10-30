# auth.py
# -*- coding: utf-8 -*-

import streamlit as st
from typing import Optional, Dict, Any

from db import (
    verify_user,
    get_user_by_id,
    get_user_by_email,
)


def login_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Verify credentials and store the user in session.
    Returns the user dict on success, else None.
    """
    user = verify_user(email, password)
    if user:
        st.session_state.user = user
        return user
    return None


def logout_user() -> None:
    """Clear user session."""
    if "user" in st.session_state:
        st.session_state.pop("user", None)


def get_current_user() -> Optional[Dict[str, Any]]:
    """Return the currently signed-in user (if any)."""
    return st.session_state.get("user")


def require_login() -> Dict[str, Any]:
    """
    Guard for pages that need authentication.
    Stops the app if no user is signed in.
    """
    user = get_current_user()
    if not user:
        st.error("Please sign in to continue.")
        st.stop()
    return user
