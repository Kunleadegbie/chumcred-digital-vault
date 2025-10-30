# pages/1_Dashboard.py  (only the top imports + pre-title guard lines are new)

from billing import guard_access, show_subscription_banner

import streamlit as st
from billing import guard_access, show_subscription_banner
from auth import get_current_user
from db import (
    get_user_documents, count_user_documents, delete_document, log_activity, get_recent_activity,
    is_account_locked, needs_renewal_reminder, subscription_days_left
)
import os

FREE_LIMIT = 5

def main():
    user = get_current_user()
    if not user:
        st.error("Please sign in.")
        st.stop()

    guard_access(user)             # ✅ prevents expired subscribers from accessing
    show_subscription_banner(user) # (optional) shows Free 5/5 usage banner


    # Hard lock ONLY for subscribed-but-expired users
    if is_account_locked(user):
        st.error("Your subscription has expired. Access is locked until payment is confirmed by Admin.")
        st.info("Go to **Settings → Upgrade / Renewal** to submit your payment reference.")
        st.stop()

    st.title("Your Secure Vault 🔐")

    # Renewal reminder banner (7 days)
    if needs_renewal_reminder(user):
        st.warning(f"Your subscription will expire in {max(subscription_days_left(user),0)} day(s). "
                   "Please renew to avoid lockout.")

    used = count_user_documents(user["id"])

    # ... keep your existing dashboard UI (plan status, docs table, etc.)
    # (No change to your existing functions render)


def show_plan_status(user, used_count: int):
    col1, col2 = st.columns([2, 1])
    with col1:
        if user.get("is_premium"):
            st.markdown("✅ **Premium Annual Plan** (Unlimited Storage Active)")
            st.caption("Your annual plan is active. Enjoy unlimited uploads.")
        else:
            st.markdown(f"🔓 **Free Plan** · {used_count}/{FREE_LIMIT} documents used")
            st.info(
                "After 5 uploads, please upgrade. Annual plan costs ₦35,000 or $20 — "
                "renewable yearly (₦25,000 / $15 on anniversary)."
            )
    with col2:
        st.metric("Total Docs", used_count)


def show_document_table(user_id: int, docs: list):
    st.subheader("Your Documents")
    if not docs:
        st.write("No documents yet.")
        return

    for doc in docs:
        with st.expander(f"📄 {doc['filename_original']}"):
            c1, c2, c3 = st.columns([2, 2, 1])
            with c1:
                st.write(f"Category: {doc.get('category') or '-'}")
                st.write(f"Uploaded: {doc.get('uploaded_at')}")
                st.write(f"Type: {doc.get('file_type')}")
                st.write(f"Size: {doc.get('size_kb')} KB")

            with c2:
                st.write("Notes:")
                st.write(doc.get("notes") or "—")
                expiry_date = doc.get("expiry_date")
                if expiry_date:
                    st.warning(f"Expiry Date: {expiry_date}")
                else:
                    st.caption("No expiry set")

            with c3:
                stored_path = doc.get("stored_path")
                if os.path.exists(stored_path):
                    with open(stored_path, "rb") as f:
                        st.download_button(
                            "Download",
                            data=f.read(),
                            file_name=doc["filename_original"],
                            key=f"dl_{doc['id']}",
                        )

                if st.button("Delete", key=f"del_{doc['id']}"):
                    ok = delete_document(user_id, doc["id"])
                    if ok:
                        log_activity(
                            user_id,
                            "delete",
                            doc["id"],
                            details=f"Deleted {doc['filename_original']}",
                        )
                        st.success("Deleted. Please refresh this page.")
                    else:
                        st.error("Delete failed or not allowed.")


def show_activity(user_id: int):
    st.subheader("Recent Activity")
    events = get_recent_activity(user_id)
    if not events:
        st.caption("No recent activity yet.")
    else:
        for e in events:
            st.write(f"- {e['timestamp']}: {e['action']} {e['details'] or ''}")


def main():
    # 1️⃣ Load the user first
    user = get_current_user()
    if not user:
        st.error("Please sign in.")
        st.stop()

    # 2️⃣ Subscription checks
    guard_access(user)
    show_subscription_banner(user)

    # 3️⃣ Dashboard content
    st.title("Your Secure Vault 🔐")
    used = count_user_documents(user["id"])
    show_plan_status(user, used)

    # 4️⃣ Search/filter
    st.divider()
    st.caption("Filter your vault")
    col_search, col_cat = st.columns([2, 1])
    with col_search:
        search_text = st.text_input("Search by filename or notes", value="")
    with col_cat:
        category_filter = st.selectbox(
            "Category filter",
            [
                "All",
                "Identity",
                "Banking & Finance",
                "Property & Assets",
                "Medical / Health",
                "School / Certificates",
                "Legal",
                "Other",
            ],
            index=0,
        )

    docs = get_user_documents(
        user_id=user["id"],
        search_text=search_text.strip(),
        category_filter=category_filter,
    )

    show_document_table(user["id"], docs)

    st.divider()
    show_activity(user["id"])

    st.caption("Powered by Chumcred Limited")


if __name__ == "__main__":
    main()
