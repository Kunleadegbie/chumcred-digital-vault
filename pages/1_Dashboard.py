# pages/1_Dashboard.py
# -*- coding: utf-8 -*-
"""
Chumcred Vault — Dashboard
Shows plan status, documents list (download/delete), and recent activity.
Admin is recognized via ENV (ADMIN_EMAIL or ADMIN_EMAILS) — no self-elevation.
"""

import os
import streamlit as st

from auth import get_current_user
from db import (
    get_user_documents,
    count_user_documents,
    delete_document,
    log_activity,
    get_recent_activity,
    compute_subscription_status,
    subscription_days_left,
)

FREE_LIMIT = 5

# ──────────────────────────────────────────────────────────────────────────────
# Admin via ENV — single source of truth (Option A)
#   Set in Railway → Variables:
#     ADMIN_EMAIL=chumcred@gmail.com
#     or
#     ADMIN_EMAILS=kuedimfi@gmail.com,adekadegbie@gmail.com
# ──────────────────────────────────────────────────────────────────────────────
def _load_admin_emails_from_env() -> set:
    many = os.getenv("ADMIN_EMAILS", "")
    single = os.getenv("ADMIN_EMAIL", "")
    raw = many if many.strip() else single
    emails = [e.strip().lower() for e in raw.split(",") if e.strip()]
    return set(emails)

ADMIN_EMAILS = _load_admin_emails_from_env()

def is_admin_email(email: str | None) -> bool:
    return bool(email and email.strip().lower() in ADMIN_EMAILS)

def is_current_admin() -> bool:
    """
    Prefer the session flag set at login (from app.py). Fallback to ENV check.
    """
    if st.session_state.get("is_admin") is True:
        return True
    u = get_current_user()
    return is_admin_email((u or {}).get("email"))

# ──────────────────────────────────────────────────────────────────────────────
# UI helpers
# ──────────────────────────────────────────────────────────────────────────────
def show_plan_status(user: dict, used_count: int) -> None:
    """
    Render plan/usage status and guard expired accounts.
    - FREE: shows 5-document limit usage banner
    - ANNUAL (active): success banner
    - ANNUAL (grace): warning banner
    - ANNUAL (expired): hard lock (stop)
    """
    plan = (user.get("plan") or "FREE").upper()
    status = compute_subscription_status(user)

    col1, col2 = st.columns([3, 1])
    with col1:
        if plan == "FREE":
            st.info(
                f"🔓 Free Plan — {used_count}/{FREE_LIMIT} documents used. "
                f"Upload up to {FREE_LIMIT} docs for free. "
                "Upgrade to continue after the limit."
            )
        else:
            if status == "active":
                days = max(subscription_days_left(user), 0)
                st.success(
                    f"✅ Annual Plan — Active. Unlimited uploads enabled. "
                    f"{days} day(s) left in this cycle."
                )
            elif status == "grace":
                days = max(subscription_days_left(user), 0)
                st.warning("⚠️ Annual Plan — Grace period. Please renew soon to avoid lockout.")
            else:
                st.error(
                    "⛔ Your subscription has expired. Access is locked until an admin confirms renewal payment. "
                    "Go to **Settings → Upgrade / Renewal** to submit a payment reference."
                )
                st.stop()  # hard lock for subscribed-but-expired users
    with col2:
        st.metric("Total Docs", used_count)

def show_document_table(user_id: int, docs: list) -> None:
    st.subheader("Your Documents")
    if not docs:
        st.caption("No documents yet.")
        return

    for doc in docs:
        title = f"📄 {doc.get('filename_original') or 'Untitled'}"
        with st.expander(title, expanded=False):
            c1, c2, c3 = st.columns([2, 2, 1])

            with c1:
                st.write(f"**Category:** {doc.get('category') or '—'}")
                st.write(f"**Uploaded:** {doc.get('uploaded_at') or '—'}")
                st.write(f"**Type:** {doc.get('file_type') or '—'}")
                size_kb = doc.get("size_kb")
                st.write(f"**Size:** {size_kb} KB" if size_kb is not None else "**Size:** —")

            with c2:
                st.write("**Notes:**")
                st.write(doc.get("notes") or "—")
                expiry_date = doc.get("expiry_date")
                if expiry_date:
                    st.warning(f"**Expiry Date:** {expiry_date}")
                else:
                    st.caption("No expiry set")

            with c3:
                stored_path = doc.get("stored_path")

                # Download (only if file is present on disk)
                if stored_path and os.path.exists(stored_path):
                    try:
                        with open(stored_path, "rb") as f:
                            st.download_button(
                                "Download",
                                data=f.read(),
                                file_name=doc.get("filename_original") or "document",
                                key=f"dl_{doc['id']}",
                            )
                    except Exception:
                        st.caption("File not readable on server.")
                else:
                    st.caption("File not present on this server.")

                # Delete (user can delete their own doc; admin also allowed if needed)
                if st.button("Delete", key=f"del_{doc['id']}"):
                    ok = delete_document(user_id, doc["id"])
                    if ok:
                        log_activity(
                            user_id=user_id,
                            action="delete",
                            doc_id=doc["id"],
                            details=f"Deleted {doc.get('filename_original')}",
                        )
                        st.success("Deleted. Refresh this page to update the list.")
                    else:
                        st.error("Delete failed (not allowed or missing).")

def show_activity(user_id: int) -> None:
    st.subheader("Recent Activity")
    events = get_recent_activity(user_id)
    if not events:
        st.caption("No recent activity yet.")
        return
    for e in events:
        when = e.get("timestamp") or "—"
        action = e.get("action") or "—"
        details = e.get("details") or ""
        st.write(f"- {when}: **{action}** {details}")

# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────
def main() -> None:
    user = get_current_user()
    if not user:
        st.error("Please sign in.")
        st.stop()

    st.title("Your Secure Vault 🔐")

    used = count_user_documents(user["id"])
    show_plan_status(user, used)

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
        search_text=(search_text or "").strip(),
        category_filter=category_filter,
    )
    show_document_table(user["id"], docs)

    st.divider()
    show_activity(user["id"])

    # Optional: show a tiny admin badge if the current user is an admin (based on ENV)
    if is_current_admin():
        st.caption("🛡️ Admin recognized (env).")

    st.write("---")
    st.caption("Powered by Chumcred Limited")

if __name__ == "__main__":
    main()
