
# pages/3_Settings_&_Emergency.py
import sys, os
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import streamlit as st
from auth import get_current_user
from db import (
    get_user_by_id,
    update_emergency_contact,
    record_payment_submission,
    update_payment_status,
)

ANNUAL_NGN = int(os.getenv("ANNUAL_PRICE_NGN", "35000"))
ANNUAL_USD = float(os.getenv("ANNUAL_PRICE_USD", "20"))

def refresh_session_user():
    if "user" in st.session_state and st.session_state.user:
        uid = st.session_state.user["id"]
        latest = get_user_by_id(uid)
        if latest:
            st.session_state.user = latest

# ... all the code above remains the same ...

def main():
    user = get_current_user()
    if not user:
        st.error("Please sign in.")
        st.stop()

    refresh_session_user()
    user = get_current_user()

    st.title("Settings & Emergency Contact ⚙️")
    st.caption("Manage account info, emergency contact, and premium upgrade status.")

    # --- Account Overview ---
    st.subheader("Account Overview")
    st.write(f"Name: {user.get('full_name', '')}")
    st.write(f"Email: {user.get('email', '')}")

    if user.get("is_premium") or (user.get("plan") and user["plan"].upper() != "FREE"):
        st.success("Plan: ✅ Annual / Active (Unlimited storage)")
    else:
        st.info("Plan: 🔓 Free (5 documents max until you upgrade)")

    if user.get("is_admin"):
        st.warning("You are an ADMIN user 🛡. You can access the Admin Panel page.")

    st.divider()

    # --- Emergency Contact ---
    st.subheader("Emergency Contact")
    st.write("This is someone you trust who should at least know this vault exists if anything happens to you.")
    emergency_name = st.text_input("Full Name of Contact", value=user.get("emergency_name") or "")
    emergency_email = st.text_input("Contact Email", value=user.get("emergency_email") or "")
    emergency_relation = st.text_input("Relationship", value=user.get("emergency_relation") or "")
    if st.button("Save Emergency Contact"):
        update_emergency_contact(user["id"], emergency_name, emergency_email, emergency_relation)
        refresh_session_user()
        st.success("Emergency contact saved.")

    st.divider()

    # --- Upgrade / Renewal Section ---
    st.subheader("Upgrade / Renewal (Admin Approval Required)")
    st.info(
        "Pay via **Paystack / Flutterwave / Stripe / Bank Transfer**, then submit your reference below. "
        "**An admin will review and activate your account.**"
    )

    with st.expander("🏦 Pay by Bank Transfer (NGN)"):
        st.markdown(
            """
            **Account Name:** Chumcred Limited  
            **Bank:** Sterling Bank Plc  
            **Account Number:** 0087611334                  
            **Amount:** ₦35,000 (initial) / ₦25,000 (renewal)  
            **Narration/Reference:** *your email + 'Chumcred Vault'*
            """
        )

    with st.form("submit_reference", clear_on_submit=True):
        provider = st.selectbox("Provider", ["Paystack", "Flutterwave", "Stripe", "Bank Transfer"])
        currency = st.selectbox("Currency", ["NGN", "USD"])
        amount = st.number_input("Amount paid", min_value=0.0, step=1.0, value=0.0)
        reference = st.text_input("Payment reference / narration")
        submitted = st.form_submit_button("Submit reference for admin review")
        if submitted:
            if not reference or amount <= 0:
                st.warning("Please enter a valid amount and reference.")
            else:
                from db import record_payment_submission, update_payment_status
                record_payment_submission(user["id"], provider, currency, amount, reference)
                update_payment_status(user["id"], "pending")
                refresh_session_user()
                st.success("Reference submitted. Admin will review and activate your account.")

    # --- Renewal Reminder ---
    from db import needs_renewal_reminder, subscription_days_left
    if needs_renewal_reminder(user):
        st.warning(
            f"Your subscription will expire in {max(subscription_days_left(user),0)} day(s). "
            "Please renew to avoid lockout."
        )

    st.write("---")
    st.caption("Powered by Chumcred Limited")


if __name__ == "__main__":
    main()
