
# pages/6_Privacy_and_Terms.py
import streamlit as st
import os

ANNUAL_PRICE_NGN = int(os.getenv("ANNUAL_PRICE_NGN", "35000"))
ANNUAL_PRICE_USD = float(os.getenv("ANNUAL_PRICE_USD", "20"))
RENEW_PRICE_NGN = int(os.getenv("ANNUAL_RENEW_NGN", "25000"))
RENEW_PRICE_USD = float(os.getenv("ANNUAL_RENEW_USD", "15"))

def main():
    st.title("Privacy Policy & Terms of Use")
    st.caption("Effective date: October 2025")
    st.write("Powered by **Chumcred Limited**")

    st.header("1. What is Chumcred Digital Vault?")
    st.write(
        "Chumcred Digital Vault is a secure digital storage service for important personal and business documents "
        "(e.g., IDs, certificates, property titles, banking records). You can upload, organize, and retrieve documents "
        "anytime, and export or delete your data whenever you choose."
    )

    st.header("2. Ownership of Content")
    st.write(
        "You own the documents you upload. Chumcred Limited does not claim ownership of your content."
    )

    st.subheader("2.1 Right to Download")
    st.write("You can download your documents and export your vault at any time.")

    st.subheader("2.2 Right to Delete")
    st.write(
        "You can delete individual documents or request full account deletion, which permanently removes your account, "
        "all documents, and related records from our system."
    )

    st.header("3. Information We Store")
    st.write(
        "- Account details (name, email, hashed password).\n"
        "- Uploaded documents and associated metadata (e.g., category, notes).\n"
        "- Optional emergency contact information.\n"
        "- Activity logs (e.g., upload, delete, export) for your own tracking.\n"
        "- Subscription/payment status (Free or Annual)."
    )

    st.header("4. How We Protect Data")
    st.write(
        "We use secure connections (HTTPS) to protect data in transit and store data in a restricted environment. "
        "Passwords are stored using one-way hashing. We continuously work to improve file-level protections and "
        "internal controls. We do not share or publish your documents."
    )

    st.subheader("4.1 Your Responsibility")
    st.write(
        "Choose a strong password and keep it confidential. Do not share your login with anyone you do not trust."
    )

    st.header("5. Plans, Pricing, and Renewals")
    st.write(
        f"Chumcred Vault offers a Free plan (limited uploads) and an **Annual plan**. "
        f"Current pricing: **₦{ANNUAL_PRICE_NGN}** or **${ANNUAL_PRICE_USD}** for the first year, "
        f"then **₦{RENEW_PRICE_NGN}** or **${RENEW_PRICE_USD}** on each anniversary. "
        "The Annual plan enables unlimited uploads during the active subscription term."
    )

    st.subheader("5.1 Grace Period and Account Lock")
    st.write(
        "If your annual plan expires, a 7-day grace period applies. During grace, you will be prompted to renew. "
        "After grace, your account will be locked until renewal is completed."
    )

    st.subheader("5.2 Refunds")
    st.write(
        "Annual payments generally are non-refundable once access is granted. If you believe you were charged in error, "
        "please contact support for review."
    )

    st.header("6. Emergency Contact")
    st.write(
        "You can optionally store a trusted person’s name, relationship, and email as an emergency contact. "
        "We do not automatically share your documents with them."
    )

    st.header("7. Prohibited Use")
    st.write(
        "You agree not to upload or store illegal content or use Chumcred Vault in violation of applicable laws."
    )

    st.header("8. Account Deletion")
    st.write(
        "Upon full account deletion, your user record, documents, and associated logs are permanently removed. "
        "This action cannot be undone."
    )

    st.header("9. Service Availability")
    st.write(
        "We strive for high availability, but service uptime is not guaranteed. There may be maintenance windows, "
        "infrastructure incidents, or legal directives that affect access."
    )

    st.header("10. Disclaimer")
    st.write(
        "Chumcred Vault is a digital convenience/backup solution and does not replace legal originals or certified copies. "
        "Always retain original physical documents where required by law."
    )

    st.header("11. Contact")
    st.write(
        "Chumcred Limited  \n"
        "Support: support@chumcred.com"
    )

    st.write("---")
    st.caption(
        "By using Chumcred Vault, you confirm that you have read and agree to this Privacy Policy & Terms of Use."
    )


if __name__ == "__main__":
    main()
