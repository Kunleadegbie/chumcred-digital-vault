
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
    list_pending_payment_refs,
    set_subscription,
    update_payment_status,
)

def guard_admin():
    u = get_current_user()
    if not u or not u.get("is_admin"):
        st.error("Access denied. Admins only.")
        st.stop()
    return u

# pages/5_Admin_Panel.py — in the Users section
def section_users():
    st.subheader("Users")
    q = st.text_input("Search by name or email", value="")
    rows = list_users(q)
    if not rows:
        st.caption("No users found.")
        return

    for r in rows:
        with st.expander(f"{r['full_name']} • {r['email']}"):
            st.write(f"Plan: {r.get('plan') or 'FREE'}")
            st.write(f"Subscription end: {r.get('subscription_end') or '—'}")
            st.write(f"Payment status: {r.get('payment_status') or '—'}")
            st.write(f"Admin: {'✅' if r.get('is_admin') else '❌'}")

            c1, c2 = st.columns(2)
            with c1:
                if not r.get("is_admin"):
                    if st.button("Make Admin", key=f"mkadm_{r['id']}"):
                        set_admin_flag(r["id"], True)
                        st.success(f"{r['email']} is now an admin.")
                        st.experimental_rerun()
            with c2:
                if r.get("is_admin"):
                    if st.button("Remove Admin", key=f"rmadm_{r['id']}"):
                        set_admin_flag(r["id"], False)
                        st.success(f"Admin rights removed for {r['email']}.")
                        st.experimental_rerun()



def section_users():
    st.subheader("Users")
    q = st.text_input("Search by name or email", value="")
    rows = list_users(q)
    if not rows:
        st.caption("No users found.")
        return
    for r in rows:
        with st.expander(f"{r['full_name']} • {r['email']}"):
            st.write(f"Plan: {r.get('plan') or 'FREE'}")
            st.write(f"Subscription end: {r.get('subscription_end') or '—'}")
            st.write(f"Payment status: {r.get('payment_status') or '—'}")
            c1, c2 = st.columns(2)
            with c1:
                st.write(f"Admin: {'✅' if r.get('is_admin') else '❌'}")
                if st.button("Make Admin", key=f"mkadm_{r['id']}"):
                    set_admin_flag(r["id"], True)
                    st.success("User promoted to admin.")
                    st.experimental_rerun()
            with c2:
                if r.get("is_admin"):
                    if st.button("Remove Admin", key=f"rmadm_{r['id']}"):
                        set_admin_flag(r["id"], False)
                        st.success("Admin rights removed.")
                        st.experimental_rerun()

def section_pending_approvals():
    st.subheader("🧾 Pending payment approvals")
    rows = list_pending_payment_refs()
    if not rows:
        st.caption("No pending submissions.")
        return
    for r in rows:
        with st.expander(f"{r['full_name']} • {r['email']} • {r['currency']} {r['amount']} • Ref: {r['reference']}"):
            st.write(f"Provider: {r['provider']}")
            st.write(f"Submitted at: {r['paid_at']}")
            st.write(f"Current user payment_status: {r['payment_status']}")
            c1, c2, c3 = st.columns(3)
            with c1:
                start = st.date_input("Start date", value=dt.date.today(), key=f"start_{r['pid']}")
            with c2:
                end = st.date_input("End date (12 months)", value=dt.date.today() + dt.timedelta(days=365), key=f"end_{r['pid']}")
            with c3:
                if st.button("✅ Approve & Activate", key=f"approve_{r['pid']}"):
                    set_subscription(
                        user_id=r["user_id"],
                        start=start,
                        end=end,
                        amount=float(r["amount"] or 0.0),
                        currency=(r["currency"] or "NGN"),
                        provider=(r["provider"] or "manual"),
                    )
                    update_payment_status(r["user_id"], "active")
                    st.success("Activated. User is now on Annual plan.")
                    st.experimental_rerun()

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
