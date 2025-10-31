
# pages/5_Admin_Panel.py
import sys, os, datetime as dt

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import streamlit as st
from auth import get_current_user
from db import (
    list_users,
    set_admin_flag,
    list_pending_payment_refs,  # alias points to list_pending_payments()
    set_subscription,
    update_payment_status,
)

# ----------------------------- Guards -----------------------------
def guard_admin():
    u = get_current_user()
    if not u or not u.get("is_admin"):
        st.error("Access denied. Admins only.")
        st.stop()
    return u

# ------------------------- Users management ------------------------
def section_users():
    st.subheader("Users")
    q = st.text_input("Search by name or email", value="")
    rows = list_users(q)
    if not rows:
        st.caption("No users found.")
        return

    for r in rows:
        full_name = r.get("full_name", "—")
        email = r.get("email", "—")
        with st.expander(f"{full_name} • {email}"):
            st.write(f"Plan: {r.get('plan') or 'FREE'}")
            st.write(f"Subscription end: {r.get('subscription_end') or '—'}")
            st.write(f"Payment status: {r.get('payment_status') or '—'}")

            c1, c2 = st.columns(2)
            with c1:
                st.write(f"Admin: {'✅' if r.get('is_admin') else '❌'}")
                if not r.get("is_admin"):
                    if st.button("Make Admin", key=f"mkadm_{r.get('id')}"):
                        set_admin_flag(r["id"], True)
                        st.success(f"{email} is now an admin.")
                        st.rerun()
            with c2:
                if r.get("is_admin"):
                    if st.button("Remove Admin", key=f"rmadm_{r.get('id')}"):
                        set_admin_flag(r["id"], False)
                        st.success(f"Admin rights removed for {email}.")
                        st.rerun()

# ---------------------- Pending payment approvals -------------------
def section_pending_approvals():
    st.subheader("🧾 Pending payment approvals")
    rows = list_pending_payment_refs()  # returns latest pending payments w/ user info

    if not rows:
        st.caption("No pending submissions.")
        return

    for r in rows:
        # Tolerate either alias; DB helper may expose p.id AS pid or p.id as id
        pid = r.get("pid", r.get("id"))
        user_id = r.get("user_id")
        full_name = r.get("full_name", "—")
        email = r.get("email", "—")
        currency = r.get("currency", "NGN")
        amount = r.get("amount", 0)
        reference = r.get("reference", "—")
        provider = r.get("provider", "manual")
        paid_at = r.get("paid_at", "—")
        payment_status = r.get("payment_status", "—")
        user_plan = r.get("user_plan", r.get("plan", "FREE"))
        user_subscription_end = r.get("user_subscription_end", r.get("subscription_end", "—"))

        header = f"{full_name} • {email} • {currency} {amount} • Ref: {reference}"
        with st.expander(header):
            st.write(f"Provider: {provider}")
            st.write(f"Submitted at: {paid_at}")
            st.write(f"Current user payment_status: {payment_status}")
            st.write(f"User plan: {user_plan}")
            st.write(f"Current subscription end: {user_subscription_end}")

            c1, c2, c3 = st.columns(3)
            today = dt.date.today()
            default_end = today + dt.timedelta(days=365)

            with c1:
                start = st.date_input("Start date", value=today, key=f"start_{pid}")
            with c2:
                end = st.date_input("End date (12 months)", value=default_end, key=f"end_{pid}")
            with c3:
                approve_key = f"approve_{pid}"
                reject_key = f"reject_{pid}"
                a = st.button("✅ Approve & Activate", key=approve_key)
                rj = st.button("❌ Reject", key=reject_key)

                if a:
                    if not user_id:
                        st.error("Missing user_id on this payment record; cannot approve.")
                    else:
                        set_subscription(
                            user_id=user_id,
                            start=start,
                            end=end,
                            amount=float(amount or 0.0),
                            currency=(currency or "NGN"),
                            provider=(provider or "manual"),
                        )
                        update_payment_status(user_id, "active")
                        st.success("Activated. User is now on Annual plan.")
                        st.rerun()

                if rj:
                    if not user_id:
                        st.error("Missing user_id on this payment record; cannot reject.")
                    else:
                        update_payment_status(user_id, "rejected")
                        st.warning("Payment marked as rejected.")
                        st.rerun()

# ------------------------------ Main -------------------------------
def main():
    guard_admin()
    st.title("Admin Panel 🛡️")

    tab1, tab2 = st.tabs(["Pending Approvals", "Users"])
    with tab1:
        section_pending_approvals()
    with tab2:
        section_users()

    st.caption("Powered by Chumcred Limited")

if __name__ == "__main__":
    main()
