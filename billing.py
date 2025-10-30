
# billing.py
import streamlit as st
from db import compute_subscription_status, count_user_documents

FREE_LIMIT = 5

def guard_access(user, *, page="dashboard"):
    """
    Blocks access for expired subscribers.
    - FREE plan: allowed everywhere; uploads capped at FREE_LIMIT (handled on the upload page).
    - SUBSCRIBED + expired: lock the account (no access) until admin re-activates.
    """
    if not user:
        st.error("Please sign in.")
        st.stop()

    plan = (user.get("plan") or "FREE").upper()
    status = compute_subscription_status(user)

    # Only lock users who once subscribed and are now expired.
    if plan != "FREE" and status == "expired":
        st.error("Your subscription has expired. Access is locked until payment is confirmed by Admin.")
        st.info("Go to **Settings → Upgrade / Renewal** to submit your payment reference.")
        st.stop()

def show_subscription_banner(user):
    """
    Optional banner you can call on pages:
    - shows current plan and usage summary for FREE users
    """
    plan = (user.get("plan") or "FREE").upper()
    if plan == "FREE":
        used = count_user_documents(user["id"])
        st.info(f"Plan: Free — {used}/{FREE_LIMIT} used. You can upload up to {FREE_LIMIT} documents for free.")
