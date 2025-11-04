# app.py
import os
import inspect
import streamlit as st


# ✅ This must be first Streamlit command
st.set_page_config(
    page_title="Chumcred Digital Vault",
    page_icon="logo.png",   # or "🔐"
    layout="wide",
    initial_sidebar_state="expanded"
)

# Now safe to use other Streamlit functions
st.image("logo.png", width=240)


from db import (
    init_db,
    verify_user,
    create_user,
    get_user_by_email,
    DB_PATH,
    has_admin,
)


# ---------- Init DB once ----------
@st.cache_resource(show_spinner=False)
def _boot():
    init_db()
    return True

_boot()

# ---------- Session helpers ----------
def login_user(user: dict):
    st.session_state.user = user

def logout_user():
    st.session_state.user = None

def get_current_user():
    return st.session_state.get("user")

# ---------- Sidebar debug (optional while stabilizing) ----------
# with st.sidebar.expander("Debug (hide in production)"):
    # st.code(f"DB_PATH: {DB_PATH}")
    # st.code(f"app.py: {__file__}")

# ---------- UI ----------
def show_login():
    st.subheader("Sign In")
    with st.form("login_form", clear_on_submit=False):
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        submitted = st.form_submit_button("Sign In")
        if submitted:
            user = verify_user(email, password)
            if user:
                login_user(user)
                st.success("Welcome back! You are now signed in.")
                # Smooth redirect to Dashboard if available
                try:
                    st.switch_page("pages/1_Dashboard.py")
                except Exception:
                    st.rerun()
            else:
                st.error("Invalid credentials. Please check your email and password.")

# app.py — inside your show_signup(), use this version of the form block

def show_signup():
    st.subheader("Create Account")
    admin_exists = has_admin()  # import from db

    with st.form("signup_form", clear_on_submit=False):
        full_name = st.text_input("Full name").strip()
        email = st.text_input("Email").strip()
        password = st.text_input("Password", type="password")

        # UI: checkbox only enabled if NO admin exists yet
        if not admin_exists:
            is_admin_checkbox = st.checkbox("Register as admin (only for platform owner)")
        else:
            # greyed out / informative
            st.checkbox(
                "Register as admin (disabled — an admin already exists)",
                value=False,
                disabled=True,
                help="The first admin has already been set up. Ask an admin to promote you in the Admin Panel."
            )
            is_admin_checkbox = False  # UI fallback

        submitted = st.form_submit_button("Create my vault")
        if submitted:
            if not (full_name and email and password):
                st.warning("Please fill in all fields.")
                return

            # Server-side enforcement (double safety)
            is_admin_effective = is_admin_checkbox and (not admin_exists)

            u = create_user(full_name, email, password, is_admin=is_admin_effective)
            if u is None:
                st.error("An account with that email already exists, or password missing.")
            else:
                st.success("Account created successfully.")
                st.session_state.user = u
                st.rerun()



def show_landing():
    st.title("Chumcred Digital Vault 🔐")
    st.caption("Store and retrieve your most important documents — securely, from anywhere.")

    # If not logged in: show tabs to login/signup
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
    st.success(f"Signed in as: {user.get('full_name', '')} · {user.get('email', '')}")
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
        if user.get("is_admin"):
            try:
                st.page_link("pages/5_Admin_Panel.py", label="🛡️ Admin Panel", icon="🛡️")
            except Exception:
                st.write("🛡️ Open Admin from the sidebar.")

    st.write("---")
    if st.button("Log out"):
        logout_user()
        st.rerun()

    st.write("Powered by **Chumcred Limited**")

# ---------- Run ----------
if __name__ == "__main__":
    show_landing()
