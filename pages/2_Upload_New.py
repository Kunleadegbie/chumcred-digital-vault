
# pages/2_Upload_New.py
# -*- coding: utf-8 -*-
"""
Chumcred Vault — Upload New Document
Free plan: up to 5 uploads.
Annual plan: unlimited while active (grace shows warning), locked when expired.
"""

import streamlit as st
from datetime import date

from auth import get_current_user
from db import (
    insert_document_record,
    log_activity,
    count_user_documents,
    compute_subscription_status,
)
from storage import save_uploaded_file, ALLOWED_EXTENSIONS

FREE_LIMIT = 5

CATEGORY_OPTIONS = [
    "Identity",
    "Banking & Finance",
    "Property & Assets",
    "Medical / Health",
    "School / Certificates",
    "Legal",
    "Other",
]


def main() -> None:
    user = get_current_user()
    if not user:
        st.error("Please sign in.")
        st.stop()

    st.title("Upload New Document 📤")
    st.caption("Add passports, CAC docs, insurance policies, employment letters, receipts, etc.")

    # Plan/status
    plan = (user.get("plan") or "FREE").upper()
    used = count_user_documents(user["id"])

    if plan == "FREE":
        # Free-plan users can upload up to FREE_LIMIT, regardless of subscription fields.
        if used >= FREE_LIMIT:
            st.error(
                f"You've reached the free limit of {FREE_LIMIT} documents. "
                "Please upgrade/subscribe to continue uploading."
            )
            st.stop()
        else:
            st.info(
                f"🔓 Free Plan — {used}/{FREE_LIMIT} used. "
                f"You can upload {FREE_LIMIT - used} more document(s) for free."
            )
    else:
        # Subscribed users must pass subscription checks.
        status = compute_subscription_status(user)
        if status == "expired":
            st.error(
                "⛔ Your subscription has expired. Uploads are disabled until an admin confirms renewal. "
                "Go to **Settings → Upgrade / Renewal** to submit your payment reference."
            )
            st.stop()
        elif status == "grace":
            st.warning("⚠️ Your plan is in grace period — please renew soon to avoid lockout.")

    # Upload form
    with st.form("upload_form", clear_on_submit=True):
        uploaded_file = st.file_uploader(
            "Choose a file to upload",
            type=[ext.replace(".", "") for ext in ALLOWED_EXTENSIONS],
            help="Supported: PDF, Word, Excel, PowerPoint, images, CSV, TXT",
        )
        category = st.selectbox("Category", CATEGORY_OPTIONS, index=0)
        notes = st.text_area("Notes / Description (optional)")
        expiry_date = st.date_input(
            "Expiry / Renewal Date (optional)",
            value=None,
            help="Example: Passport expiry date, insurance renewal date",
        )

        submitted = st.form_submit_button("Save to Vault")

    if submitted:
        if uploaded_file is None:
            st.warning("Please choose a file.")
            st.stop()

        # Final guard for FREE users just in case of rapid multiple submits
        if plan == "FREE":
            used_now = count_user_documents(user["id"])
            if used_now >= FREE_LIMIT:
                st.error(
                    f"You've reached the free limit of {FREE_LIMIT} documents. "
                    "Please upgrade/subscribe to continue uploading."
                )
                st.stop()

        # Save file to disk
        stored_path, size_kb, ext = save_uploaded_file(
            user_id=user["id"],
            uploaded_file=uploaded_file,
        )

        # Store metadata in DB
        expiry_str = expiry_date.isoformat() if isinstance(expiry_date, date) else None
        doc_id = insert_document_record(
            user_id=user["id"],
            filename_original=uploaded_file.name,
            stored_path=stored_path,
            file_type=ext,
            category=category,
            notes=notes,
            expiry_date=expiry_str,
            size_kb=size_kb,
            is_generated=False,
        )

        # Log activity
        log_activity(
            user_id=user["id"],
            action="upload",
            doc_id=doc_id,
            details=f"Uploaded {uploaded_file.name}",
        )

        st.success("Document saved to your vault ✅")

    st.divider()
    st.write("Security tips:")
    st.write("- Only upload documents you personally own or are authorized to store.")
    st.write("- Keep your login private.")
    st.write("- Set expiry dates so you get visual reminders before critical documents expire.")

    st.write("Powered by Chumcred Limited")


if __name__ == "__main__":
    main()
