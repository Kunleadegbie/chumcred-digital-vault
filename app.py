# app.py
import os
import streamlit as st

# ──────────────────────────────────────────────────────────────────────────────
# Page config — must be the first Streamlit call
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Chumcred Digital Vault",
    page_icon="logo.png",   # or "🔐"
    layout="wide",
    initial_sidebar_state="expanded"
)

# Optional branding image
st.image("logo.png", width=240)

# ──────────────────────────────────────────────────────────────────────────────
# DB functions
# ──────────────────────────────────────────────────────────────────────────────
from db import (
    init_db,
    verify_user,
    create_user,
    get_user_by_email,
    DB_PATH,
    # has_admin,  # no longer needed for Option A (env-driven admin)
)

# ──────────────────────────────────────────────────────────────────────────────
# Admin via ENV — single source of truth
#   - Set ADMIN_EMAIL (single) or ADMIN_EMAILS (comma-separated) in Railway
# ──────────────────────────────────────────────────────────────────────────────
def _load_admin_emails_from_env() -> set:
    # Prefer ADMIN_EMAILS (comma-separated), fall back to ADMIN_EMAIL
    many = os.getenv("ADMIN_EMAILS", "")
    single = os.getenv("ADMIN_EMAIL", "")
    raw = many if many.strip() else single
    emails = [e.strip().lower() for e in raw.split(",") if e.strip()]
    return set(emails)

ADMIN_EMAILS = _load_admin_emails_from_env()

def is_admin_email(email: str | None) -> bool:
    if not email:
        return False
    return email.strip().lower() in ADMIN_EMAILS

# ──────────────────────────────────────────────────────────────────────────────
# Init DB once
# ──────────────────────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def _boot():
    init_db()
    return True

_boot()

# ──────────────────────────────────────────────────────────────────────────────
# Session helpers
# ──────────────────────────────────────────────────────────────────────────────
def login_user(user: dict):
    """Store the logged-in user in session and compute effective admin from ENV."""
    st.session_state.user = user or None
    email = (user or {}).get("email")
    st.session_state.is_admin = is_admin_email(email)

def logout_user():
    st.session_state.user = None
    st.session_state.is_admin = False

def get_current_user():
    return st.session_state.get("user")

def is_current_admin():
    return bool(st.session_state.get("is_admin", False))

def require_admin():
    if not is_current_admin():
        st.error("Admin access required.")
        st.stop()

# ──────────────────────────────────────────────────────────────────────────────
# UI — Auth: Login / Signup
# ──────────────────────────────────────────────────────────────────────────────
def show_login():
    st.subheader("Sign In")
    with st.form("login_form", clear_on_submit=False):
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        submitted = st.form_submit_button("Sign In")
        if submitted:
            user = verify_user(email, password)
            if user:
                # On every login, compute admin from ENV (source of truth)
                login_user(user)
                st.success("Welcome back! You are now signed in.")
                try:
                    st.switch_page("pages/1_Dashboard.py")
                except Exception:
                    st.rerun()
            else:
                st.error("Invalid credentials. Please check your email and password.")

def show_signup():
    st.subheader("Create Account")

    # For Option A, we NEVER allow users to self-promote in the UI.
    # We show a disabled hint instead (purely informational).
    with st.form("signup_form", clear_on_submit=False):
        full_name = st.text_input("Full name").strip()
        email = st.text_input("Email").strip()
        password = st.text_input("Password", type="password")

        # Informational (always disabled) — admin is controlled by the platform owner via ENV
        st.checkbox(
            "Register as admin (disabled — platform owner controls admin via email)",
            value=False,
            disabled=True,
            help="Admin access is tied to platform-owner email(s) only."
        )

        submitted = st.form_submit_button("Create my vault")
        if submitted:
            if not (full_name and email and password):
                st.warning("Please fill in all fields.")
                return

            # Server-side enforcement: admin is strictly from ENV
            is_admin_effective = is_admin_email(email)

            u = create_user(full_name, email, password, is_admin=is_admin_effective)
            if u is None:
                st.error("An account with that email already exists, or password missing.")
            else:
                # Make sure session admin flag is aligned to ENV
                login_user(u)
                st.success("Account created successfully.")
                st.rerun()

# ──────────────────────────────────────────────────────────────────────────────
# Landing / Home
# ──────────────────────────────────────────────────────────────────────────────
def show_landing():
    st.title("Chumcred Digital Vault 🔐")
    st.caption("Store and retrieve your most important documents — securely, from anywhere.")

    user = get_current_user()
    if not user:
        tab1, tab2 = st.tabs(["Sign In", "Sign Up"])
        with tab1:
            show_login()
        with tab2:
            show_signup()
        st.write("---")
        st.write("Powered by **Chumcred Limited**")
        return

    # Logged-in landing
    email = user.get("email", "")
    name = user.get("full_name", "")
    st.success(f"Signed in as: {name} · {email}")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        try:
            st.page_link("pages/1_Dashboard.py", label="📊 Dashboard", icon="📊")
        except Exception:
            st.write("📊 Open the Dashboard from the sidebar.")
    with c2:
        try:
            st.page_link("pages/2_Upload_New.py", label="📤 Upload New", icon="📤")
        except Exception:
            st.write("📤 Open Upload from the sidebar.")
    with c3:
        try:
            st.page_link("pages/3_Settings_&_Emergency.py", label="⚙️ Settings & Emergency", icon="⚙️")
        except Exception:
            st.write("⚙️ Open Settings from the sidebar.")
    with c4:
        # Show Admin Panel link ONLY if current user email is in ADMIN_EMAIL(S)
        if is_current_admin():
            try:
                st.page_link("pages/5_Admin_Panel.py", label="🛡️ Admin Panel", icon="🛡️")
            except Exception:
                st.write("🛡️ Open Admin from the sidebar.")

    st.write("---")
    if st.button("Log out"):
        logout_user()
        st.rerun()

    st.write("Powered by **Chumcred Limited**")

# ──────────────────────────────────────────────────────────────────────────────
# Run
# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    show_landing()
