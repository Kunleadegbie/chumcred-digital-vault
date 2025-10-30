
# db.py
import os
import sqlite3
import datetime as dt
from typing import Optional, Dict, Any, List, Tuple
from werkzeug.security import generate_password_hash, check_password_hash

# ===================== Config =====================
DB_PATH = os.getenv("VAULT_DB_PATH", os.path.join(os.path.dirname(__file__), "vault.db"))
GRACE_DAYS = int(os.getenv("GRACE_DAYS", "0"))  # lock immediately after expiry

# ===================== Connection =================
def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

# ============== Introspection helpers =============
def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (name,))
    return cur.fetchone() is not None

def _column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table});")
    cols = [r[1] for r in cur.fetchall()]
    return column in cols

def _users_columns() -> set:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(users);")
    cols = {row[1] for row in cur.fetchall()}
    conn.close()
    return cols

def _norm_email(email: str) -> str:
    return (email or "").strip().lower()

# ============== Schema init & upgrades =============
def init_db():
    """Create base tables if missing; add new columns safely for older DBs."""
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

                -- canonical column
                password_hash TEXT,

                -- legacy installs may also have 'hashed_password' (keep if present)
                is_admin INTEGER DEFAULT 0,

                -- Emergency contact
                emergency_name TEXT,
                emergency_email TEXT,
                emergency_relation TEXT,

                -- Subscription / billing
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

         # inside init_db(), after creating activity_log (or at the end of init_db)
         ensure_activity_log_columns()

   
 # Payments
    if not _table_exists(conn, "payments"):
        cur.execute(
            """
            CREATE TABLE payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                provider TEXT,         -- 'paystack' | 'flutterwave' | 'stripe' | 'bank transfer'
                currency TEXT,         -- NGN | USD
                amount REAL,
                paid_at TEXT DEFAULT (datetime('now')),
                reference TEXT,        -- user-submitted reference/narration
                raw_json TEXT,         -- optional payload
                FOREIGN KEY(user_id) REFERENCES users(id)
            );
            """
        )

    # Safe column upgrades (idempotent)
    upgrades: List[Tuple[str, str, str, str]] = [
        ("users", "password_hash", "TEXT", "NULL"),
        ("users", "is_admin", "INTEGER", "0"),
        ("users", "emergency_name", "TEXT", "NULL"),
        ("users", "emergency_email", "TEXT", "NULL"),
        ("users", "emergency_relation", "TEXT", "NULL"),
        ("users", "plan", "TEXT", "'FREE'"),
        ("users", "subscription_start", "TEXT", "NULL"),
        ("users", "subscription_end", "TEXT", "NULL"),
        ("users", "is_premium", "INTEGER", "0"),
        ("users", "last_payment_amount", "REAL", "NULL"),
        ("users", "last_payment_currency", "TEXT", "NULL"),
        ("users", "last_payment_provider", "TEXT", "NULL"),
        ("users", "payment_status", "TEXT", "NULL"),
    ]
    for table, column, coltype, default_val in upgrades:
        if not _column_exists(conn, table, column):
            cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {coltype} DEFAULT {default_val};")

    # Ensure payments has 'reference' and 'raw_json'
    if not _column_exists(conn, "payments", "reference"):
        cur.execute("ALTER TABLE payments ADD COLUMN reference TEXT;")
    if not _column_exists(conn, "payments", "raw_json"):
        cur.execute("ALTER TABLE payments ADD COLUMN raw_json TEXT;")

    conn.commit()
    conn.close()

# ================= Users (get/set) =================
def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id=?;", (user_id,))
    row = cur.fetchone(); conn.close()
    return dict(row) if row else None

def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    email = _norm_email(email)
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE lower(email)=?;", (email,))
    row = cur.fetchone(); conn.close()
    return dict(row) if row else None

def set_admin_flag(user_id: int, is_admin: bool) -> None:
    conn = get_conn(); cur = conn.cursor()
    cur.execute("UPDATE users SET is_admin=? WHERE id=?;", (1 if is_admin else 0, user_id))
    conn.commit(); conn.close()

def has_admin() -> bool:
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT 1 FROM users WHERE is_admin=1 LIMIT 1;")
    row = cur.fetchone(); conn.close()
    return bool(row)

def update_emergency_contact(user_id: int, name: str, email: str, relation: str) -> None:
    conn = get_conn(); cur = conn.cursor()
    cur.execute(
        "UPDATE users SET emergency_name=?, emergency_email=?, emergency_relation=? WHERE id=?;",
        (name, email, relation, user_id),
    )
    conn.commit(); conn.close()

# ================= Authentication =================
def ensure_user_columns():
    conn = get_conn(); cur = conn.cursor()
    cur.execute("PRAGMA table_info(users);")
    cols = [r[1] for r in cur.fetchall()]
    if "password_hash" not in cols:
        cur.execute("ALTER TABLE users ADD COLUMN password_hash TEXT;")
    if "is_admin" not in cols:
        cur.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0;")
    conn.commit(); conn.close()


# db.py — replace your current create_user with this version
def create_user(full_name: str, email: str, password: str, is_admin: bool = False) -> Optional[Dict[str, Any]]:
    ensure_user_columns()
    email = _norm_email(email)
    if not (full_name and email and password):
        return None
    if get_user_by_email(email):
        return None

    # 🚫 If any admin already exists, force new signups to non-admin
    try:
        admin_exists = has_admin()
    except Exception:
        admin_exists = True  # safest default: don't allow accidental admin creation

    effective_is_admin = (is_admin and not admin_exists)

    pw_hash = generate_password_hash(password)
    cols = _users_columns()

    insert_cols = ["full_name", "email", "is_admin"]
    params = [full_name.strip(), email, 1 if effective_is_admin else 0]

    if "password_hash" in cols:
        insert_cols.append("password_hash")
        params.append(pw_hash)
    if "hashed_password" in cols:
        insert_cols.append("hashed_password")
        params.append(pw_hash)

    placeholders = ", ".join("?" for _ in insert_cols)
    sql = f"INSERT INTO users ({', '.join(insert_cols)}) VALUES ({placeholders});"

    conn = get_conn(); cur = conn.cursor()
    cur.execute(sql, params)
    conn.commit(); conn.close()
    return get_user_by_email(email)

def verify_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    ensure_user_columns()
    email = _norm_email(email)
    u = get_user_by_email(email)
    if not u:
        return None
    pw_hash = u.get("password_hash") or u.get("hashed_password") or ""
    try:
        ok = check_password_hash(pw_hash, password or "")
    except Exception:
        ok = False
    return u if ok else None

def update_password(user_id: int, new_password: str) -> None:
    ensure_user_columns()
    pw_hash = generate_password_hash(new_password)
    cols = _users_columns()

    sets = []
    params: List[Any] = []
    if "password_hash" in cols:
        sets.append("password_hash=?")
        params.append(pw_hash)
    if "hashed_password" in cols:
        sets.append("hashed_password=?")
        params.append(pw_hash)
    sets_sql = ", ".join(sets) if sets else "password_hash=?"
    if not sets:
        params.append(pw_hash)

    params.append(user_id)
    conn = get_conn(); cur = conn.cursor()
    cur.execute(f"UPDATE users SET {sets_sql} WHERE id=?;", params)
    conn.commit(); conn.close()

# ========= Subscription & Billing =========
def compute_subscription_status(u: Dict[str, Any]) -> str:
    """
    'active'  : today <= subscription_end
    'grace'   : subscription_end < today <= subscription_end + GRACE_DAYS
    'expired' : today > subscription_end + GRACE_DAYS OR missing/invalid
    """
    if not u:
        return "expired"
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
    if not u or not u.get("subscription_end"):
        return 0
    try:
        end = dt.date.fromisoformat(u["subscription_end"])
    except Exception:
        return 0
    return (end - dt.date.today()).days

def is_subscription_active(u: Dict[str, Any]) -> bool:
    return compute_subscription_status(u) == "active"

def is_subscription_locked(u: Dict[str, Any]) -> bool:
    return compute_subscription_status(u) == "expired"

def set_subscription(user_id: int, start: dt.date, end: dt.date, amount: float, currency: str, provider: str) -> None:
    conn = get_conn(); cur = conn.cursor()
    cur.execute(
        """
        UPDATE users SET
            plan='ANNUAL',
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
    conn.commit(); conn.close()

def update_payment_status(user_id: int, status: str) -> None:
    conn = get_conn(); cur = conn.cursor()
    cur.execute("UPDATE users SET payment_status=? WHERE id=?;", (status, user_id))
    conn.commit(); conn.close()

def record_payment_submission(user_id: int, provider: str, currency: str, amount: float, reference: str):
    conn = get_conn(); cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO payments (user_id, provider, currency, amount, reference, raw_json)
        VALUES (?, ?, ?, ?, ?, ?);
        """,
        (user_id, provider.lower(), currency.upper(), amount, reference.strip(), "submitted_by_user"),
    )
    conn.commit(); conn.close()

def list_pending_payment_refs() -> List[Dict[str, Any]]:
    conn = get_conn(); cur = conn.cursor()
    cur.execute(
        """
        SELECT p.id AS pid, p.user_id, u.full_name, u.email,
               p.provider, p.currency, p.amount, p.reference, p.paid_at, u.payment_status
        FROM payments p
        LEFT JOIN users u ON u.id = p.user_id
        WHERE COALESCE(u.payment_status,'')='pending'
        ORDER BY p.id DESC;
        """
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


# --- add these helpers anywhere below your subscription functions ---

def has_active_or_free_quota(u: Dict[str, Any], used_count: int, free_limit: int = 5) -> bool:
    """
    Returns True if:
      - user is FREE and used_count < free_limit, OR
      - user has an ACTIVE subscription.
    """
    plan = (u.get("plan") or "FREE").upper()
    status = compute_subscription_status(u)
    if plan == "FREE":
        return used_count < free_limit
    return status == "active"

def is_account_locked(u: Dict[str, Any]) -> bool:
    """
    Lock the account (no access) ONLY if the user once subscribed (plan != FREE)
    and the subscription is fully expired (GRACE_DAYS=0).
    FREE users (never paid) are NOT locked—they can use their 5 free uploads.
    """
    plan = (u.get("plan") or "FREE").upper()
    if plan == "FREE":
        return False
    return compute_subscription_status(u) == "expired"

def needs_renewal_reminder(u: Dict[str, Any]) -> bool:
    """
    True when user has an active subscription that will end within 7 days.
    """
    plan = (u.get("plan") or "FREE").upper()
    if plan == "FREE":
        return False
    days = subscription_days_left(u)
    return 0 < days <= 7


# ================== Documents ===================
def insert_document(
    user_id: int,
    filename_original: str,
    stored_path: str,
    file_type: str,
    size_kb: int,
    category: Optional[str] = None,
    notes: Optional[str] = None,
    expiry_date: Optional[str] = None,
) -> int:
    conn = get_conn(); cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO documents
            (user_id, filename_original, stored_path, file_type, size_kb, category, notes, expiry_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """,
        (user_id, filename_original, stored_path, file_type, size_kb, category, notes, expiry_date),
    )
    doc_id = cur.lastrowid
    conn.commit(); conn.close()
    return doc_id

def get_user_documents(user_id: int, search_text: str = "", category_filter: str = "All") -> List[Dict[str, Any]]:
    conn = get_conn(); cur = conn.cursor()
    where = ["user_id = ?"]
    params: List[Any] = [user_id]
    if search_text:
        where.append("(lower(filename_original) LIKE ? OR lower(notes) LIKE ?)")
        like = f"%{search_text.lower()}%"
        params.extend([like, like])
    if category_filter and category_filter != "All":
        where.append("category = ?")
        params.append(category_filter)
    sql = f"SELECT * FROM documents WHERE {' AND '.join(where)} ORDER BY uploaded_at DESC;"
    cur.execute(sql, tuple(params))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def count_user_documents(user_id: int) -> int:
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS c FROM documents WHERE user_id=?;", (user_id,))
    row = cur.fetchone(); conn.close()
    return int(row["c"] if row else 0)

def delete_document(user_id: int, doc_id: int) -> bool:
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT id FROM documents WHERE id=? AND user_id=?;", (doc_id, user_id))
    row = cur.fetchone()
    if not row:
        conn.close()
        return False
    cur.execute("DELETE FROM documents WHERE id=?;", (doc_id,))
    conn.commit(); conn.close()
    return True

# ================== Activity ====================

# --- in db.py ---

def ensure_activity_log_columns():
    con = get_conn(); cur = con.cursor()
    cur.execute("PRAGMA table_info(activity_log);")
    cols = [r[1] for r in cur.fetchall()]
    if "doc_id" not in cols:
        cur.execute("ALTER TABLE activity_log ADD COLUMN doc_id INTEGER;")
    con.commit(); con.close()

def log_activity(user_id: int, action: str, doc_id: int | None = None, details: str | None = None) -> None:
    # auto-heal before inserting
    ensure_activity_log_columns()
    con = get_conn(); cur = con.cursor()
    cur.execute(
        "INSERT INTO activity_log (user_id, action, doc_id, details) VALUES (?, ?, ?, ?);",
        (user_id, action, doc_id, details),
    )
    con.commit(); con.close()

def get_recent_activity(user_id: int, limit: int = 20) -> List[Dict[str, Any]]:
    conn = get_conn(); cur = conn.cursor()
    cur.execute(
        "SELECT * FROM activity_log WHERE user_id=? ORDER BY timestamp DESC LIMIT ?;",
        (user_id, limit),
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

# ================= Admin listings ===============
def list_users(search: str = "") -> List[Dict[str, Any]]:
    conn = get_conn(); cur = conn.cursor()
    if search:
        like = f"%{search.lower()}%"
        cur.execute(
            """
            SELECT * FROM users
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
