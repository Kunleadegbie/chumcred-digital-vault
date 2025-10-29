# pages/1_Dashboard.py
import streamlit as st
import os
from auth import get_current_user
from db import (
    get_user_documents,
    count_user_documents,
    delete_document,
    log_activity,
    get_recent_activity,
)

FREE_LIMIT = 5


def show_plan_status(user, used_count: int):
    col1, col2 = st.columns([2, 1])

    with col1:
        if user["is_premium"]:
            st.markdown("✅ **Premium Lifetime** (Unlimited Storage Active)")
            st.caption("You paid once. You’re covered for life.")
        else:
            st.markdown(f"🔓 **Free Plan** · {used_count}/{FREE_LIMIT} documents used")
            st.info(
                "After 5 uploads, you’ll need to upgrade. One-time payment: ₦50,000 or $35 "
                "for unlimited lifetime storage."
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

                # Download
                if os.path.exists(stored_path):
                    with open(stored_path, "rb") as f:
                        st.download_button(
                            "Download",
                            data=f.read(),
                            file_name=doc["filename_original"],
                            key=f"dl_{doc['id']}",
                        )

                # Delete
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
    user = get_current_user()
    if not user:
        st.error("Please go back and sign in.")
        st.stop()

    st.title("Your Secure Vault 🔐")

    used = count_user_documents(user["id"])
    show_plan_status(user, used)

    # Filters / search
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

    st.write("Powered by Chumcred Limited")


if __name__ == "__main__":
    main()
