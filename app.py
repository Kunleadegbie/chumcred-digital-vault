
# app.py
import streamlit as st
from auth import login_user, get_current_user, logout_user
from db import init_db, create_user

st.set_page_config(
    page_title="Chumcred Digital Vault",
    page_icon="🔐",
    layout="wide"
)

# make sure DB tables exist
init_db()

# session bootstrap
if "user" not in st.session_state:
    st.session_state.user = None

# if not logged in: show landing / login / signup
if st.session_state.user is None:
    st.title("Chumcred Digital Vault 🔐")
    st.write("Your important documents. Safe, forever. Powered by Chumcred Limited.")

    tab_login, tab_signup = st.tabs(["Login", "Sign up"])

    # =====================
    # LOGIN TAB
    # =====================
    with tab_login:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_pw")

        if st.button("Sign in"):
            user = login_user(email, password)
            if user:
                st.session_state.user = user
                st.rerun()
            else:
                st.error("Invalid credentials")

    # =====================
    # SIGNUP TAB
    # =====================
    with tab_signup:
        full_name = st.text_input("Full Name", key="signup_name")
        email_new = st.text_input("Email for signup", key="signup_email")
        password_new = st.text_input("Choose Password", type="password", key="signup_pw")

        # 👇 THIS is the admin checkbox you were expecting
        admin_flag = st.checkbox(
            "Register as admin (only for platform owner)",
            value=False,
            help="Tick this ONLY if you are the owner of the platform. Admins can view system-wide usage."
        )

        if st.button("Create my vault"):
            if full_name and email_new and password_new:
                try:
                    # create_user now accepts is_admin
                    create_user(full_name, email_new, password_new, is_admin=admin_flag)
                    st.success("Account created. Please log in on the Login tab.")
                except Exception as e:
                    st.error(f"Signup failed. Email may already exist. Details: {e}")
            else:
                st.warning("Please fill all fields before creating your vault.")

# if logged in: show nav help
else:
    st.sidebar.success(f"Logged in as {st.session_state.user['full_name']}")
    if st.session_state.user.get("is_admin"):
        st.sidebar.info("Admin Mode Enabled 🛡")

    if st.sidebar.button("Log out"):
        logout_user()
        st.rerun()

    st.write("Welcome back 👋")
    st.write("Use the sidebar pages to access your vault:")
    st.write("• Dashboard – view, download, delete, activity log")
    st.write("• Upload New Document – add new secure files")
    st.write("• Settings & Emergency Contact – emergency contact + premium upgrade")
    st.write("• Export & Safety – download full ZIP backup, safety guidance")
    if st.session_state.user.get("is_admin"):
        st.write("• Admin Panel – monitor users and capacity")

    st.caption("Powered by Chumcred Limited")




