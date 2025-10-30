# jobs/send_renewal_reminders.py
import os, smtplib, ssl, datetime as dt
from email.message import EmailMessage
from db import get_conn

RENEW_LINK_NGN = "https://paystack.com/your-renewal-link"
RENEW_LINK_USD = "https://checkout.stripe.com/your-renewal-link"

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
MAIL_FROM = os.getenv("MAIL_FROM", "support@chumcred.com")

def send_email(to, subject, body):
    msg = EmailMessage()
    msg["From"] = MAIL_FROM
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)
    ctx = ssl.create_default_context()
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
        s.starttls(context=ctx)
        s.login(SMTP_USER, SMTP_PASS)
        s.send_message(msg)

def users_needing_reminders():
    conn = get_conn(); conn.row_factory=None
    cur = conn.cursor()
    today = dt.date.today()
    targets = []
    for delta in [7, 3, 1, 0, -3, -7]:  # before, on, and during grace
        d = (today + dt.timedelta(days=delta)).isoformat()
        cur.execute("""
            SELECT id, email, full_name, subscription_end FROM users
            WHERE subscription_end = ?
        """, (d,))
        targets += cur.fetchall()
    conn.close()
    return targets

def main():
    for (uid, email, name, end) in users_needing_reminders():
        body = f"""Hello {name},

Your Chumcred Vault annual plan is due/near expiry.

Renew now to maintain uninterrupted access:
- Paystack (NGN): {RENEW_LINK_NGN}
- Stripe (USD):   {RENEW_LINK_USD}

If your plan passes the 7-day grace period after expiry, your account will be locked until renewal.

— Chumcred Limited
"""
        try:
            send_email(email, "Chumcred Vault — Renewal Reminder", body)
        except Exception:
            pass

if __name__ == "__main__":
    main()
