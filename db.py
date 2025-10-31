# db.py
# -*- coding: utf-8 -*-
"""
Chumcred Vault Database Module
Handles user authentication, documents, activity log, payments, and subscriptions.
"""

import os
import sqlite3
import datetime as dt
from typing import Optional, Dict, Any, List
from werkzeug.security import generate_password_hash, check_password_hash

# ---------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------
# Tip: For Streamlit Cloud, set env VAULT_DB_PATH=/tmp/vault.db
DEFAULT_DB = os.path.join(os.path.dirname(__file__), "vault.db")
DB_PATH = os.getenv("VAULT_DB_PATH", DEFAULT_DB)
GRACE_DAYS = int(os.getenv("GRACE_DAYS", "7"))  # grace period after expiry

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


# ---------------------------------------------------------------------
# INTERNAL HELPERS
# ---------------------------------------------------------------------
def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (name,))
    return cur.fetchone() is not None


def _column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table});")
    cols = [r[1] for r in cur.fetchall()]
    return column in cols


def _users_has_column(col: str) -> bool:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(users);")
    cols = [r[1] for r in cur.fetchall()]
    conn.close()
    return col in cols


def ensure_activity_log_columns() -> None:
    """Ensure activity_log has doc_id column for older DBs."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(activity_log);")
    cols = [r[1] for r in cur.fetchall()]
    if "doc_id" not in cols:
        cur.execute("ALTER TABLE activity_log ADD COLUMN doc_id INTEGER;")
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------
# INITIALIZATION / MIGRATIONS
# ---------------------------------------------------------------------
def init_db() -> None:
    """Create base tables if missing; safely add new columns for older DBs."""
    conn = get_conn()
    cur = conn.cursor()

    # Users
    if not _table_exists(conn, "users"):
        cur.execute(
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT,
                email TEXT UNIQUE,
                password_hash TEXT,
                -- legacy projects may have 'hashed_password' NOT NULL; we'll migrate below
                is_admin INTEGER DEFAULT 0,
                emergency_name TEXT,
                emergency_email TEXT,
                emergency_relation TEXT,
                plan TEXT DEFAULT 'FREE',
                subscription_start TEXT,
                subscription_end TEXT,
                is_premium INTEGER DEFAULT 0,
                last_payment_amount REAL,
                last_payment_currency TEXT,
                last_payment_provider TEXT,
                payment_status TEXT
            );
            """
        )

    # Documents
    if not _table_exists(conn, "documents"):
        cur.execute(
            """
            CREATE TABLE documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                filename_original TEXT,
                stored_path TEXT,
                file_type TEXT,
                size_kb INTEGER,
                category TEXT,
                notes TEXT,
                uploaded_at TEXT DEFAULT (datetime('now')),
                expiry_date TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id)
            );
            """
        )

    # Activity log
    if not _table_exists(conn, "activity_log"):
        cur.execute(
            """
            CREATE TABLE activity_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT,
                doc_id INTEGER,
                details TEXT,
                timestamp TEXT DEFAULT (datetime('now')),
                FOREIGN KEY(user_id) REFERENCES users(id)
            );
            """
        )

    # Payments
    if not _table_exists(conn, "payments"):
        cur.execute(
            """
            CREATE TABLE payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                provider TEXT,
                currency TEXT,
                amount REAL,
                paid_at TEXT DEFAULT (datetime('now')),
                reference TEXT,
                raw_json TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id)
            );
            """
        )

    # Safe column upgrades (idempotent)
    def _addcol(table: str, column: str, decl: str):
        if not _column_exists(conn, table, column):
            cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {decl};")

    _addcol("users", "password_hash", "TEXT")
    _addcol("users", "is_admin", "INTEGER DEFAULT 0")
    _addcol("users", "plan", "TEXT DEFAULT 'FREE'")
    _addcol("users", "subscription_start", "TEXT")
    _addcol("users", "subscription_end", "TEXT")
    _addcol("users", "last_payment_amount", "REAL")
    _addcol("users", "last_payment_currency", "TEXT")
    _addcol("users", "last_payment_provider", "TEXT")
    _addcol("users", "payment_status", "TEXT")
    _addcol("payments", "reference", "TEXT")
    _addcol("payments", "raw_json", "TEXT")

    # ---- Legacy compatibility migration ('hashed_password' -> 'password_hash') ----
    # If the table still has a legacy 'hashed_password' column, ensure password_hash exists and copy values.
    if _column_exists(conn, "users", "hashed_password"):
        if not _column_exists(conn, "users", "password_hash"):
            cur.execute("ALTER TABLE users ADD COLUMN password_hash TEXT;")
        cur.execute(
            """
            UPDATE users
               SET password_hash = COALESCE(password_hash, hashed_password)
             WHERE hashed_password IS NOT NULL
               AND (password_hash IS NULL OR password_hash = '');
            """
        )

    conn.commit()
    ensure_activity_log_columns()
    conn.close()


# ---------------------------------------------------------------------
# USERS / AUTH
# ---------------------------------------------------------------------
def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id=?;", (user_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE email=?;", (email,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def has_admin() -> bool:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users WHERE is_admin=1;")
    result = cur.fetchone()[0]
    conn.close()
    return result > 0


def create_user(full_name: str, email: str, password: str, is_admin: bool = False) -> Optional[Dict[str, Any]]:
    """Create new user. Returns user dict or None if email exists.
       Dual-writes to legacy 'hashed_password' when present (avoids NOT NULL failures)."""
    if get_user_by_email(email):
        return None
    pw_hash = generate_password_hash(password)

    conn = get_conn()
    cur = conn.cursor()

    if _users_has_column("hashed_password"):
        cur.execute(
            """
            INSERT INTO users (full_name, email, password_hash, hashed_password, is_admin)
            VALUES (?, ?, ?, ?, ?);
            """,
            (full_name, email, pw_hash, pw_hash, 1 if is_admin else 0),
        )
    else:
        cur.execute(
            """
            INSERT INTO users (full_name, email, password_hash, is_admin)
            VALUES (?, ?, ?, ?);
            """,
            (full_name, email, pw_hash, 1 if is_admin else 0),
        )

    conn.commit()
    conn.close()
    return get_user_by_email(email)


def verify_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    """Check password; return user if valid. Falls back to legacy 'hashed_password' if needed."""
    u = get_user_by_email(email)
    if not u:
        return None

    pw_hash = (u.get("password_hash") or "").strip()

    # fallback to legacy if needed
    if not pw_hash and "hashed_password" in u:
        pw_hash = (u.get("hashed_password") or "").strip()

    if not pw_hash:
        return None

    try:
        ok = check_password_hash(pw_hash, password)
    except Exception:
        ok = False
    return u if ok else None


def update_password(user_id: int, new_password: str) -> None:
    pw_hash = generate_password_hash(new_password)
    conn = get_conn()
    cur = conn.cursor()

    if _users_has_column("hashed_password"):
        cur.execute(
            "UPDATE users SET password_hash=?, hashed_password=? WHERE id=?;",
            (pw_hash, pw_hash, user_id),
        )
    else:
        cur.execute("UPDATE users SET password_hash=? WHERE id=?;", (pw_hash, user_id))

    conn.commit()
    conn.close()


def update_emergency_contact(user_id: int, name: str, email: str, relation: str) -> None:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET emergency_name=?, emergency_email=?, emergency_relation=? WHERE id=?;",
        (name, email, relation, user_id),
    )
    conn.commit()
    conn.close()


def set_admin_flag(user_id: int, is_admin: bool) -> None:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE users SET is_admin=? WHERE id=?;", (1 if is_admin else 0, user_id))
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------
# DOCUMENTS
# ---------------------------------------------------------------------
def insert_document_record(
    user_id: int,
    filename_original: str,
    stored_path: str,
    file_type: str,
    category: Optional[str],
    notes: Optional[str],
    expiry_date: Optional[str],
    size_kb: Optional[int],
    is_generated: bool = False,
) -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO documents
        (user_id, filename_original, stored_path, file_type, size_kb, category, notes, expiry_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """,
        (user_id, filename_original, stored_path, file_type, size_kb, category, notes, expiry_date),
    )
    conn.commit()
    doc_id = cur.lastrowid
    conn.close()
    return doc_id


# Backward-compat alias if older pages import insert_document
insert_document = insert_document_record


def get_user_documents(user_id: int, search_text: str = "", category_filter: str = "All") -> List[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.cursor()
    q = """
        SELECT * FROM documents
        WHERE user_id=?
    """
    params = [user_id]
    if search_text:
        q += " AND (filename_original LIKE ? OR notes LIKE ?)"
        like = f"%{search_text}%"
        params.extend([like, like])
    if category_filter and category_filter != "All":
        q += " AND category=?"
        params.append(category_filter)
    q += " ORDER BY uploaded_at DESC;"
    cur.execute(q, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def count_user_documents(user_id: int) -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM documents WHERE user_id=?;", (user_id,))
    count = cur.fetchone()[0]
    conn.close()
    return count


def delete_document(user_id: int, doc_id: int) -> bool:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM documents WHERE id=? AND user_id=?;", (doc_id, user_id))
    conn.commit()
    ok = cur.rowcount > 0
    conn.close()
    return ok


# ---------------------------------------------------------------------
# ACTIVITY LOG
# ---------------------------------------------------------------------
def log_activity(user_id: int, action: str, doc_id: Optional[int] = None, details: Optional[str] = None) -> None:
    ensure_activity_log_columns()
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO activity_log (user_id, action, doc_id, details) VALUES (?, ?, ?, ?);",
        (user_id, action, doc_id, details),
    )
    conn.commit()
    conn.close()


def get_recent_activity(user_id: int) -> List[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM activity_log WHERE user_id=? ORDER BY id DESC LIMIT 20;",
        (user_id,),
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


# ---------------------------------------------------------------------
# PAYMENTS (USER SUBMISSION + ADMIN REVIEW)
# ---------------------------------------------------------------------
def record_payment_submission(
    user_id: int,
    provider: str,
    currency: str,
    amount: float,
    reference: str,
    raw_json: Optional[str] = None,
) -> None:
    """
    Store a user's payment submission so the admin can review & approve later.
    """
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO payments (user_id, provider, currency, amount, reference, raw_json)
        VALUES (?, ?, ?, ?, ?, ?);
        """,
        (user_id, provider, currency, amount, reference, raw_json),
    )
    # Mark user as pending
    cur.execute("UPDATE users SET payment_status=? WHERE id=?;", ("pending", user_id))
    conn.commit()
    conn.close()


def update_payment_status(user_id: int, status: str) -> None:
    """
    Update user's payment_status (e.g., 'pending', 'active', 'expired', 'rejected').
    """
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE users SET payment_status=? WHERE id=?;", (status, user_id))
    conn.commit()
    conn.close()

def list_pending_payments() -> List[Dict[str, Any]]:
    """Admin helper: list latest pending payments with user info + status."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            p.id AS pid,                -- alias for UI keys/buttons
            p.user_id,
            p.provider,
            p.currency,
            p.amount,
            p.paid_at,
            p.reference,
            p.raw_json,
            u.full_name,
            u.email,
            u.payment_status AS payment_status,
            u.plan AS user_plan,
            u.subscription_end AS user_subscription_end
        FROM payments p
        JOIN users u ON u.id = p.user_id
        WHERE u.payment_status = 'pending'
        ORDER BY p.id DESC;
        """
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

# Back-compat alias (keep if your Admin Panel imports this name)
def list_pending_payment_refs() -> List[Dict[str, Any]]:
    return list_pending_payments()


# ---------------------------------------------------------------------
# SUBSCRIPTIONS
# ---------------------------------------------------------------------
def compute_subscription_status(u: Dict[str, Any]) -> str:
    """
    Return 'active', 'grace', or 'expired'.
    - active: today <= subscription_end
    - grace:  subscription_end < today <= subscription_end + GRACE_DAYS
    - expired: missing end OR today > end + grace
    """
    end_str = u.get("subscription_end")
    if not end_str:
        return "expired"
    try:
        end = dt.date.fromisoformat(end_str)
    except Exception:
        return "expired"
    today = dt.date.today()
    if today <= end:
        return "active"
    if today <= end + dt.timedelta(days=GRACE_DAYS):
        return "grace"
    return "expired"


def subscription_days_left(u: Dict[str, Any]) -> int:
    """Days until end date (0 if unknown/invalid; negative inside grace)."""
    if not u.get("subscription_end"):
        return 0
    try:
        end = dt.date.fromisoformat(u["subscription_end"])
    except Exception:
        return 0
    return (end - dt.date.today()).days


def set_subscription(user_id: int, start: dt.date, end: dt.date, amount: float, currency: str, provider: str) -> None:
    """
    Admin uses this to activate/renew a user's annual plan.
    """
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE users
        SET plan='ANNUAL',
            subscription_start=?,
            subscription_end=?,
            is_premium=1,
            last_payment_amount=?,
            last_payment_currency=?,
            last_payment_provider=?,
            payment_status='active'
        WHERE id=?;
        """,
        (start.isoformat(), end.isoformat(), amount, currency, provider, user_id),
    )
    conn.commit()
    conn.close()


# Legacy convenience for older pages:
def is_account_locked(u: Dict[str, Any]) -> bool:
    """Locked if subscription fully expired (after grace)."""
    return compute_subscription_status(u) == "expired"


# ---------------------------------------------------------------------
# SUBSCRIPTION REMINDER
# ---------------------------------------------------------------------
def needs_renewal_reminder(u: Dict[str, Any]) -> bool:
    """
    Return True if user's subscription is within 7 days of expiry
    (or in grace period) and still not renewed.
    """
    end_str = u.get("subscription_end")
    if not end_str:
        return False
    try:
        end = dt.date.fromisoformat(end_str)
    except Exception:
        return False

    today = dt.date.today()
    days_left = (end - today).days

    # Show reminder when 0 <= days_left <= 7 or already in grace
    if 0 <= days_left <= 7:
        return True
    if today > end and today <= end + dt.timedelta(days=GRACE_DAYS):
        return True

    return False


# ---------------------------------------------------------------------
# ADMIN USER MANAGEMENT
# ---------------------------------------------------------------------
def list_users(search: str = "") -> List[Dict[str, Any]]:
    """
    Return all users, optionally filtered by name or email.
    Used in Admin Panel to display users and manage privileges.
    """
    conn = get_conn()
    cur = conn.cursor()
    if search:
        like = f"%{search.lower()}%"
        cur.execute(
            """
            SELECT *
            FROM users
            WHERE lower(full_name) LIKE ? OR lower(email) LIKE ?
            ORDER BY id DESC;
            """,
            (like, like),
        )
    else:
        cur.execute("SELECT * FROM users ORDER BY id DESC;")

    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


# ---------------------------------------------------------------------
# AUTO-INIT ON IMPORT
# ---------------------------------------------------------------------
init_db()
