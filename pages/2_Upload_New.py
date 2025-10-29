# pages/2_Upload_New.py
import streamlit as st
from auth import get_current_user
from db import (
    count_user_documents,
    insert_document_record,
    log_activity,
    get_user_by_id
)
from storage import save_uploaded_file, ALLOWED_EXTENSIONS
from datetime import datetime

FREE_LIMIT = 5

CATEGORY_OPTIONS = [
    "Identity",
    "Banking & Finance",
    "Property & Assets",
    "Medical / Health",
    "School / Certificates",
    "Legal",
    "Other"
]

def can_upload_more_docs(user, current_count):
    """
    Return (allowed: bool, message: str)
    """
    if user["is_premium"]:
        return True, "Premium: unlimited."
    else:
        if current_count >= FREE_LIMIT:
            return False, (
		"You have reached your free limit of 5 documents. "
                "Upgrade once for ₦50,000 or $35 to unlock unlimited lifetime storage."
            )
        else:
            return True, f"You are on Free Plan. {current_count}/{FREE_LIMIT} used."
def main():
    user = get_current_user()
    if not user:
        st.error("Please go back and sign in.")
        st.stop()

    st.title("Upload New Document 📤")
    st.caption("Add passports, CAC docs, insurance policies, employment letters, receipts, etc.")

    # Check limits
    current_count = count_user_documents(user["id"])
    allowed, msg = can_upload_more_docs(user, current_count)
    if user["is_premium"]:
        st.success(msg)
    else:
        if allowed:
            st.info(msg)
        else:
            st.error(msg)

    # Upload form
    with st.form("upload_form", clear_on_submit=True):
        uploaded_file = st.file_uploader(
            "Choose a file to upload",
            type=[ext.replace(".", "") for ext in ALLOWED_EXTENSIONS],
            help="Supported: PDF, Word, Excel, PowerPoint, images, CSV, TXT"
        )
        category = st.selectbox("Category", CATEGORY_OPTIONS, index=0)
        notes = st.text_area("Notes / Description (optional)")
        expiry_date = st.date_input(
            "Expiry / Renewal Date (optional)",
            value=None,
            help="Example: Passport expiry date, insurance renewal date"
        )

        submitted = st.form_submit_button("Save to Vault")

        if submitted:
            if not allowed:
                st.error("Upload blocked until you upgrade.")
                st.stop()

            if uploaded_file is None:
                st.warning("Please choose a file.")
                st.stop()

            # Save file to disk
            stored_path, size_kb, ext = save_uploaded_file(
                user_id=user["id"],
                uploaded_file=uploaded_file
            )

            # Store metadata in DB
            expiry_str = expiry_date.isoformat() if expiry_date else None

            doc_id = insert_document_record(
                user_id=user["id"],
                filename_original=uploaded_file.name,
                stored_path=stored_path,
                file_type=ext,
                category=category,
                notes=notes,
                expiry_date=expiry_str,
                size_kb=size_kb,
                is_generated=False
            )

            # Log activity
            log_activity(
                user_id=user["id"],
                action="upload",
                document_id=doc_id,
                details=f"Uploaded {uploaded_file.name}"
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
