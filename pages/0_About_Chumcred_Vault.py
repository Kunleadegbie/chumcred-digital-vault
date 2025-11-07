# pages/0_About_Chumcred_Vault.py
# -*- coding: utf-8 -*-
"""
Chumcred Digital Vault — Product Overview Page
Explains what the vault is, who it's for, features, benefits, pricing, security, and FAQs.
Shown above Dashboard to help new visitors decide.
"""

import streamlit as st
import datetime as dt

# Basic brand accents (you can move these to a central theme if you like)
PRIMARY = "#0033A0"   # Royal Blue
ACCENT  = "#FFD700"   # Gold

st.set_page_config(page_title="About Chumcred Digital Vault", page_icon="🔐")

# ---- Header / Hero ----
st.markdown(
    f"""
    <div style="padding:18px 18px 4px 18px; border-radius:12px; background: linear-gradient(135deg, {PRIMARY} 0%, #0a4ed1 50%, {ACCENT} 100%); color:white;">
      <h1 style="margin:0; font-size:2.0rem;">Chumcred Digital Vault</h1>
      <p style="margin:.25rem 0 0 0; font-size:1.06rem;">
        Protect what matters most — store, access, and share vital documents securely, anywhere.
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.caption("Powered by Chumcred Limited")

# CTA row
colA, colB = st.columns([1, 1])
with colA:
    st.page_link("app.py", label="🔑 Sign in / Create your vault", icon=None)
with colB:
    st.page_link("pages/1_Dashboard.py", label="📂 Go to Dashboard (if signed in)", icon=None)

st.divider()

# ---- What it is / Who it's for ----
st.subheader("What is the Chumcred Digital Vault?")
st.markdown(
    """
**Chumcred Digital Vault** is a secure, cloud-based repository for your important personal and business documents.  
Upload once, and you’ll always know where they are — neatly organized, searchable, and retrievable in seconds.

**Perfect for:**
- Professionals and families who never want to lose **certificates, IDs, receipts, medical records, or property papers**
- Entrepreneurs who must keep **CAC documents, tax records, contracts, invoices, bank letters** safe and handy
- Students and jobseekers managing **transcripts, resumes, references, and credentials**
"""
)

# ---- Core benefits cards ----
st.subheader("Why people choose the Vault")
cb1, cb2, cb3 = st.columns(3)
with cb1:
    st.markdown("### 🔐 Security\n- Account-based access control\n- HTTPS transport encryption\n- Server-side secure storage\n- Admin review for plan activations")
with cb2:
    st.markdown("### 💾 Convenience\n- Upload PDFs, Word, Excel, PowerPoint, images\n- Search and categorize\n- Download anytime, anywhere")
with cb3:
    st.markdown("### 🆘 Preparedness\n- **Emergency Contact** entry so your trusted person knows about your vault\n- Optional expiry/renewal notes to remind you of critical dates")

st.divider()

# ---- How it works (simple steps) ----
st.subheader("How it works (in 3 minutes)")
st.markdown(
    """
1. **Create your vault** (free) → You get **5 free uploads** to test drive the experience.  
2. **Upload any file** → PDF, Word, Excel, PowerPoint, images. Add notes, category, and optional expiry date.  
3. **Retrieve & share** when needed → Download your original file on any device, anytime.

**After your free 5 uploads:**  
Upgrade to the **Annual Plan** (admin-approved) to continue using the vault with full access all year. If the plan expires, there’s a **7-day grace period**; after that, the account is locked until renewal is approved.
"""
)

# ---- Features list ----
st.subheader("Key features at a glance")
st.markdown(
    """
- ✅ **Multi-format upload:** PDF, DOCX, XLSX, PPTX, JPG/PNG, CSV, TXT  
- ✅ **Categories & notes:** keep context with each file  
- ✅ **Search & filter:** quickly find the right document  
- ✅ **Download originals:** no quality loss  
- ✅ **Activity log:** recent actions in your vault  
- ✅ **Emergency contact:** store a trusted person’s details  
- ✅ **Expiry/renewal note:** add an expiry date to see reminders inside the app  
- ✅ **Admin-approved billing:** prevents abuse and keeps service quality high
"""
)

# ---- Security & Privacy (accurate to current build) ----
st.subheader("Security & privacy")
st.markdown(
    """
Your vault is designed for **practical security** and controlled access.

- **Transport security:** the app runs over HTTPS when hosted with TLS (recommended for production).
- **Access control:** only authenticated users can access their vault.
- **Server-side storage:** documents are stored on the server with access checks tied to your account.
- **Admin approval for plan activation:** a human validation layer to reduce fraud/abuse.

> **Roadmap — upcoming security upgrades**
> - Bring-your-own-key (BYOK) option for at-rest encryption
> - Optional client-side encryption for highly sensitive files
> - 2-Factor Authentication (2FA)
> - Automated email reminders for expiring documents
"""
)

# ---- Pricing & Plans ----
st.subheader("Plans & pricing")
p1, p2 = st.columns([1, 1])
with p1:
    st.markdown(
        f"""
        <div style="border:1px solid #e7e7e7; border-radius:10px; padding:16px;">
          <h3 style="margin-top:0;">Free</h3>
          <ul>
            <li><b>5 uploads</b> to test drive</li>
            <li>All file types supported</li>
            <li>Search, categories, notes</li>
            <li>Emergency contact</li>
          </ul>
          <b>₦0 / $0</b>
        </div>
        """,
        unsafe_allow_html=True,
    )
with p2:
    st.markdown(
        f"""
        <div style="border:2px solid {PRIMARY}; border-radius:10px; padding:16px; background:#f7fbff;">
          <h3 style="margin-top:0;">Annual Plan</h3>
          <ul>
            <li>Continued access after free tier</li>
            <li>Admin-approved activation</li>
            <li>7-day grace period on expiry</li>
            <li>Priority support & roadmap features</li>
          </ul>
          <b>₦50,000 or $35 / year</b>
          <div style="margin-top:6px; font-size:.92rem; color:#555;">
            Renewal is required annually; if not renewed after grace, your account is locked until payment is approved.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.info(
    "Prefer bank transfer? You can submit a payment reference on the **Settings & Emergency** page. "
    "Admin will review and activate your plan."
)

# CTA again
cta1, cta2 = st.columns([1, 1])
with cta1:
    st.page_link("app.py", label="✨ Create your vault (free)", icon=None)
with cta2:
    st.page_link("pages/3_Settings_&_Emergency.py", label="💳 Payment & Emergency contact", icon=None)

st.divider()

# ---- What to store examples ----
st.subheader("What can I store?")
st.markdown(
    """
- **Identity:** International passport, NIN, driver’s license, birth certificate  
- **Education & career:** Certificates, transcripts, resumes, references  
- **Property & business:** CAC docs, property titles, lease agreements, contracts, invoices  
- **Banking & finance:** Statements, letters of reference, tax documents, receipts  
- **Medical & insurance:** Test results, NHIS, insurance policies, emergency info  
"""
)

# ---- Quick start guide ----
st.subheader("Quick start guide")
st.code(
    """1) Sign in or create your vault (free)
2) Upload your first 5 documents (any format)
3) Add category and notes for context
4) Mark renewal/expiry dates (optional)
5) When you need the file, open your vault → Download
6) After 5 uploads, activate Annual Plan to continue using the vault""",
    language="text",
)

# ---- Trust & support ----
st.subheader("Trust, support, and data handling")
st.markdown(
    """
- **We never sell your data.** Your documents are tied to your account and served back to you when you request them.  
- **Backups** and **operational controls** are maintained to keep the service reliable.  
- If you need help, reach out via **chumcred@gmail.com**.  
- For details, see **Privacy & Terms** in the sidebar.
"""
)

# ---- FAQs ----
st.subheader("Frequently Asked Questions (FAQs)")
with st.expander("Is this like Google Drive or Dropbox?"):
    st.markdown(
        "Similar in that you can store and retrieve files, but the **Vault focuses on vital documents**, "
        "with categories, expiry notes, an emergency contact field, and admin-approved billing designed for our market."
    )
with st.expander("What happens if I don’t renew after one year?"):
    st.markdown(
        "There is a **7-day grace period**. After that, your account is **locked** until renewal is reviewed and approved by admin."
    )
with st.expander("Can I try for free?"):
    st.markdown(
        "Yes. You get **5 free uploads** to experience the Vault before deciding."
    )
with st.expander("How safe is my data?"):
    st.markdown(
        "Sessions run over **HTTPS** in production; files are stored server-side with access controls bound to your account. "
        "We’re rolling out additional encryption layers and 2FA as part of our security roadmap."
    )
with st.expander("How do I pay?"):
    st.markdown(
        "Use the **Settings & Emergency** page to pay online (NGN/USD) or submit a bank-transfer reference for admin approval."
    )

st.divider()

# Footer / contact
st.markdown(
    f"""
    <div style="padding:16px; border-radius:10px; background:#f7f9ff; border:1px solid #e7e7e7;">
      <b>Questions?</b> Email <a href="mailto:chumcred@gmail.com">chumcred@gmail.com.com</a><br/>
      <span style="color:#666;">© {dt.date.today().year} Chumcred Limited</span>
    </div>
    """,
    unsafe_allow_html=True,
)
