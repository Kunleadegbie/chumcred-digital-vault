# pages/3_Settings_&_Emergency.py

import sys
import os
import streamlit as st
from auth import get_current_user

# Fix import path so this page can import db.py when running as a subpage
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from db import (
    get_user_by_id,
    update_emergency_contact,
    update_user_premium,
)


def refresh_session_user():
    """
    After we update something in the DB (like emergency contact or premium),
    reload fresh user data from DB into st.session_state.user so UI is accurate.
    """
    if "user" in st.session_state and st.session_state.user:
        uid = st.session_state.user["id"]
        latest = get_user_by_id(uid)
        if latest:
            st.session_state.user = latest


def main():
    user = get_current_user()
    if not user:
        st.error("Please sign in.")
        st.stop()

    # sync session with DB on every render
    refresh_session_user()
    user = get_current_user()

    st.title("Settings & Emergency Contact ⚙️")
    st.caption("Manage account info, emergency contact, and premium upgrade status.")

    # -------------------------
    # ACCOUNT OVERVIEW
    # -------------------------
    st.subheader("Account Overview")
    st.write(f"Name: {user.get('full_name', '')}")
    st.write(f"Email: {user.get('email', '')}")

    if user.get("is_premium"):
        st.success("Plan: ✅ Premium Lifetime (Unlimited storage forever)")
    else:
        st.info("Plan: 🔓 Free (5 documents max until you upgrade)")

    if user.get("is_admin"):
        st.warning("You are an ADMIN user 🛡. You can access the Admin Panel page.")

    st.divider()

    # -------------------------
    # EMERGENCY CONTACT
    # -------------------------
    st.subheader("Emergency Contact")
    st.write(
        "This is someone you trust who should at least know this vault exists "
        "if anything happens to you."
    )

    emergency_name = st.text_input(
        "Full Name of Contact",
        value=user.get("emergency_name") or ""
    )
    emergency_email = st.text_input(
        "Contact Email",
        value=user.get("emergency_email") or ""
    )
    emergency_relation = st.text_input(
        "Relationship",
        value=user.get("emergency_relation") or ""
    )

    if st.button("Save Emergency Contact"):
        update_emergency_contact(
            user_id=user["id"],
            name=emergency_name,
            email=emergency_email,
            relation=emergency_relation,
        )
        refresh_session_user()
        st.success("Emergency contact saved.")

    st.caption(
        "Note: We do NOT automatically send them your documents. "
        "This is only stored so someone you trust knows where your important files are."
    )

    st.divider()

    # -------------------------
    # PAYMENT OPTIONS / UPGRADE
    # -------------------------
    st.subheader("Payment Options")
    st.write("Choose how you want to upgrade:")

    col_n, col_d = st.columns(2)

    with col_n:
        st.markdown("**Pay in Naira (₦50,000)**")
        st.write("Supported: Debit card, bank transfer, USSD.")
        st.write("Provider: Paystack / Flutterwave")
        st.link_button("Pay ₦50,000 now", "https://paystack.com/your-payment-link-here")

    with col_d:
        st.markdown("**Pay in USD ($35)**")
        st.write("Supported: Visa / Mastercard / USD cards.")
        st.write("Provider: Stripe")
        st.link_button("Pay $35 now", "https://checkout.stripe.com/your-checkout-link-here")

    st.caption(
        "These buttons will open secure payment soon. "
        "For now you can simulate activation below."
    )

    st.divider()

    # -------------------------
    # PREMIUM UPGRADE CONTROL
    # -------------------------
    st.subheader("Upgrade to Premium Lifetime (₦50,000 or $35 one-time)")
    st.write(
        "Once you upgrade, you can store UNLIMITED documents forever. "
        "No subscription. No renewal. Just a single lifetime activation."
    )

    if not user.get("is_premium"):
        st.info(
            "In production, you'll be able to pay online (card / bank transfer). "
            "For now, click the button below to simulate payment of ₦50,000 / $35."
        )

        if st.button("Mark me as Premium (simulate payment)"):
            # Record a simulated NGN 50,000 payment
            update_user_premium(
                user_id=user["id"],
                amount=50000.00,
                currency="NGN"
            )
            refresh_session_user()
            st.success(
                "You are now Premium for life 🎉. "
                "Reload the page or go to Dashboard to see unlimited status."
            )
    else:
        st.success("You are already Premium Lifetime ✅")

    st.divider()
    st.subheader("Danger Zone")
    st.write("This will permanently erase your vault and all stored documents. This cannot be undone.")

if st.button("Delete my account and all documents", type="primary"):
    from db import delete_user_and_data
    delete_user_and_data(user["id"])
    st.success("Your account and all documents have been deleted.")
    st.warning("Please log out now.")


    st.write("Powered by Chumcred Limited")


if __name__ == "__main__":
    main()
