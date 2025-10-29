# pages/5_Admin_Panel.py
import streamlit as st
from auth import get_current_user
from db import admin_list_users_with_usage, count_user_documents

def main():
    user = get_current_user()
    if not user:
        st.error("Please sign in.")
        st.stop()

    if not user.get("is_admin"):
        st.error("Access denied. Admins only.")
        st.stop()

    st.title("Admin Panel 🛡")
    st.caption("Platform owner view. Monitor usage, premium status, and capacity.")

    rows = admin_list_users_with_usage()
    st.subheader("Users Overview")
    st.write("Below is every registered account, doc usage, and status.")
    for r in rows:
        with st.expander(f"{r['full_name']} <{r['email']}>"):
            st.write(f"User ID: {r['id']}")
            st.write(f"Docs Stored: {r['doc_count']}")
            st.write("Plan: " + ("Premium Lifetime ✅" if r['is_premium'] else "Free 🔓"))
            st.write("Admin? " + ("Yes 🛡" if r['is_admin'] else "No"))
            st.write(f"Last Login: {r['last_login_at']}")

    st.info("Future enhancements here: storage cost monitoring, abuse flags, and account deactivation.")

    st.write("Powered by Chumcred Limited")

if __name__ == '__main__':
    main()
