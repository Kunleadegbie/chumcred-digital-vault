# pages/4_Export_and_Safety.py
import sys, os
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import streamlit as st
from auth import get_current_user
from db import get_user_documents, log_activity
from storage import build_user_zip

def main():
    user = get_current_user()
    if not user:
        st.error("Please sign in.")
        st.stop()

    st.title("Export & Safety 🔐")
    st.caption("Download everything in your vault as a single backup .zip and review safety best practices.")

    st.subheader("Full Vault Export")
    st.write("You can download a full backup of all your stored documents as a .zip file. Keep this safe.")
    if st.button("Generate & Download ZIP"):
        try:
            zip_bytes = build_user_zip(user["id"])
            st.download_button(
                "Download My Full Vault Backup (.zip)",
                data=zip_bytes,
                file_name="chumcred_vault_backup.zip",
                mime="application/zip"
            )
            log_activity(user_id=user["id"], action="export_zip", details="Full ZIP export")
        except Exception as e:
            st.error(f"Could not build ZIP: {e}")

    st.divider()

    st.subheader("Personal Safety Tips")
    st.write("- Keep your password secret. Do not share your login with anyone.")
    st.write("- Your emergency contact should know this vault exists, but you should only share your password if you fully trust them.")
    st.write("- Download and store your ZIP backup in a secure external drive or encrypted USB if possible.")
    st.write("- Review expiry dates for passports, insurance, licenses, etc. Renew early.")

    st.write("Powered by Chumcred Limited")

if __name__ == '__main__':
    main()
