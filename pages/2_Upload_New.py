
# pages/2_Upload_New.py
import streamlit as st
from auth import get_current_user
from db import (
    insert_document, log_activity, count_user_documents,
    is_subscription_active, is_account_locked
)
from storage import save_uploaded_file, ALLOWED_EXTENSIONS

FREE_LIMIT = 5
CATEGORY_OPTIONS = [
    "Identity", "Banking & Finance", "Property & Assets", "Medical / Health",
    "School / Certificates", "Legal", "Other"
]

def main():
    user = get_current_user()
    if not user:
        st.error("Please sign in to continue.")
        st.stop()

    # If the user once subscribed and is now expired → fully lock uploads
    if is_account_locked(user):
        st.error("Your subscription has expired. Uploads are disabled until admin approves renewal.")
        st.info("Go to **Settings → Upgrade / Renewal** to submit your payment reference.")
        st.stop()

    st.title("📤 Upload a New Document")
    st.caption("Store your important files securely in your Chumcred Vault.")

    used = count_user_documents(user["id"])
    active = is_subscription_active(user)
    plan = (user.get("plan") or "FREE").upper()

    if plan == "FREE":
        st.info(f"Plan: Free — {used}/{FREE_LIMIT} used. You can upload up to {FREE_LIMIT} documents for free.")
        if used >= FREE_LIMIT:
            st.error("Free limit reached. Please subscribe to continue uploading.")
            st.stop()
    else:
        if active:
            st.success("Plan: Annual — Unlimited uploads enabled.")
        else:
            # (Shouldn’t reach here because is_account_locked() would have stopped; safe message anyway)
            st.error("Your subscription is not active. Uploads are disabled.")
            st.stop()

    with st.form("upload_form", clear_on_submit=True):
        uploaded_file = st.file_uploader(
            "Choose a file to upload",
            type=[ext.replace(".", "") for ext in ALLOWED_EXTENSIONS],
            help="Supported: PDF, Word, Excel, PowerPoint, images, CSV, TXT",
        )
        category = st.selectbox("Category", CATEGORY_OPTIONS, index=0)
        notes = st.text_area("Notes / Description (optional)")
        expiry_date = st.date_input("Expiry / Renewal Date (optional)", value=None)

        submitted = st.form_submit_button("Save to Vault")
        if submitted:
            if uploaded_file is None:
                st.warning("Please choose a file.")
                st.stop()

            stored_path, size_kb, ext = save_uploaded_file(
                user_id=user["id"],
                uploaded_file=uploaded_file,
            )

            expiry_str = expiry_date.isoformat() if expiry_date else None
            doc_id = insert_document(
                user_id=user["id"],
                filename_original=uploaded_file.name,
                stored_path=stored_path,
                file_type=ext,
                size_kb=size_kb,
                category=category,
                notes=notes,
                expiry_date=expiry_str,
            )

            log_activity(user_id=user["id"], action="upload", doc_id=doc_id,
                         details=f"Uploaded {uploaded_file.name}")
            st.success("✅ Document saved to your vault!")

    st.divider()
    st.caption("Powered by Chumcred Limited")

if __name__ == "__main__":
    main()
