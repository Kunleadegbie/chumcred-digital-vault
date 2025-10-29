# db.py
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

DB_PATH = "vault.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    # Users table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        hashed_password TEXT NOT NULL,
        full_name TEXT,
        is_premium BOOLEAN DEFAULT 0,
        premium_activated_at TEXT,
        premium_amount REAL,
        emergency_name TEXT,
        emergency_email TEXT,
        emergency_relation TEXT,
        is_admin BOOLEAN DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        last_login_at TEXT
    );
    """)

    # Documents table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        filename_original TEXT NOT NULL,
        stored_path TEXT NOT NULL,
        file_type TEXT NOT NULL,
        category TEXT,
        notes TEXT,
        expiry_date TEXT,
        size_kb INTEGER,
        uploaded_at TEXT DEFAULT CURRENT_TIMESTAMP,
        is_generated BOOLEAN DEFAULT 0,
        FOREIGN KEY(user_id) REFERENCES users(id)
    );
    """)

    # Activity log table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS activity_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        action TEXT NOT NULL,
        document_id INTEGER,
        timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
        details TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(document_id) REFERENCES documents(id)
    );
    """)

    # Payments table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        currency TEXT NOT NULL,
        provider TEXT,
        reference_code TEXT UNIQUE,
        paid_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    );
    """)

    conn.commit()
    conn.close()

################################
# USER MANAGEMENT
################################

def create_user(full_name, email, password_plain, is_admin=False):
    conn = get_conn()
    cur = conn.cursor()
    hashed_pw = generate_password_hash(password_plain)
    cur.execute(
        """
        INSERT INTO users (full_name, email, hashed_password, is_admin)
        VALUES (?, ?, ?, ?)
        """,
        (full_name, email, hashed_pw, 1 if is_admin else 0),
    )
    conn.commit()
    conn.close()

def verify_user(email, password_plain):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE email = ?", (email,))
    row = cur.fetchone()
    if row and check_password_hash(row["hashed_password"], password_plain):
        user = dict(row)
        # Update last_login_at
        cur.execute(
            "UPDATE users SET last_login_at = ? WHERE id = ?",
            (datetime.utcnow().isoformat(), row["id"]),
        )
        conn.commit()
        conn.close()
        return user
    conn.close()
    return None

def get_user_by_id(user_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None

def update_emergency_contact(user_id: int, name: str, email: str, relation: str):
    """
    Save or update the emergency contact fields for this user.
    """
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE users
        SET emergency_name = ?,
            emergency_email = ?,
            emergency_relation = ?
        WHERE id = ?
        """,
        (name, email, relation, user_id),
    )
    conn.commit()
    conn.close()

def update_user_premium(user_id: int, amount=20.00, currency="USD"):
    """
    Mark the user as Premium Lifetime (unlimited docs) and log a payment.
    """
    now = datetime.utcnow().isoformat()
    conn = get_conn()
    cur = conn.cursor()

    # 1. Update user premium status
    cur.execute(
        """
        UPDATE users
        SET is_premium = 1,
            premium_activated_at = ?,
            premium_amount = ?
        WHERE id = ?
        """,
        (now, amount, user_id),
    )

    # 2. Insert a payment record for audit purposes
    ref_code = f"MANUAL-{user_id}-{now}"
    cur.execute(
        """
        INSERT INTO payments
        (user_id, amount, currency, provider, reference_code, paid_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (user_id, amount, currency, "manual", ref_code, now),
    )

    conn.commit()
    conn.close()

################################
# DOCUMENT MANAGEMENT
################################

def count_user_documents(user_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT COUNT(*) as c
        FROM documents
        WHERE user_id = ?
        """,
        (user_id,),
    )
    row = cur.fetchone()
    conn.close()
    return row["c"] if row else 0

def get_user_documents(user_id: int, search_text: str = "", category_filter: str = ""):
    conn = get_conn()
    cur = conn.cursor()
    base_query = """
        SELECT * FROM documents
        WHERE user_id = ?
    """
    params = [user_id]

    if search_text:
        base_query += " AND (filename_original LIKE ? OR notes LIKE ?)"
        like_str = f"%{search_text}%"
        params.extend([like_str, like_str])

    if category_filter and category_filter != "All":
        base_query += " AND (category = ?)"
        params.append(category_filter)

    base_query += " ORDER BY uploaded_at DESC"

    cur.execute(base_query, tuple(params))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def insert_document_record(
    user_id: int,
    filename_original: str,
    stored_path: str,
    file_type: str,
    category: str,
    notes: str,
    expiry_date: str,
    size_kb: int,
    is_generated: bool = False,
):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO documents
        (user_id, filename_original, stored_path, file_type,
         category, notes, expiry_date, size_kb, is_generated)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            filename_original,
            stored_path,
            file_type,
            category,
            notes,
            expiry_date,
            size_kb,
            1 if is_generated else 0,
        ),
    )
    doc_id = cur.lastrowid
    conn.commit()
    conn.close()
    return doc_id

def delete_document(user_id: int, doc_id: int):
    """
    Delete both DB row and physical file, but only if it belongs to this user.
    """
    import os

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM documents WHERE id = ? AND user_id = ?",
        (doc_id, user_id),
    )
    row = cur.fetchone()
    if not row:
        conn.close()
        return False

    stored_path = row["stored_path"]

    # 1. remove file
    try:
        if os.path.exists(stored_path):
            os.remove(stored_path)
    except Exception:
        pass

    # 2. remove row
    cur.execute(
        "DELETE FROM documents WHERE id = ? AND user_id = ?",
        (doc_id, user_id),
    )

    conn.commit()
    conn.close()
    return True

################################
# ACTIVITY LOG
################################

def log_activity(user_id: int, action: str, document_id: int = None, details: str = ""):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO activity_log (user_id, action, document_id, details)
        VALUES (?, ?, ?, ?)
        """,
        (user_id, action, document_id, details),
    )
    conn.commit()
    conn.close()

def get_recent_activity(user_id: int, limit: int = 20):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT * FROM activity_log
        WHERE user_id = ?
        ORDER BY timestamp DESC
        LIMIT ?
        """,
        (user_id, limit),
    )
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

################################
# ADMIN
################################

def admin_list_users_with_usage():
    """
    Return a list of rows like:
    {
        id,
        full_name,
        email,
        is_premium,
        is_admin,
        last_login_at,
        doc_count
    }
    """
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            u.id,
            u.full_name,
            u.email,
            u.is_premium,
            u.is_admin,
            u.last_login_at,
            COUNT(d.id) as doc_count
        FROM users u
        LEFT JOIN documents d
        ON u.id = d.user_id
        GROUP BY u.id
        ORDER BY u.created_at DESC
        """
    )
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_user_and_data(user_id: int):
    import os
    conn = get_conn()
    cur = conn.cursor()

    # 1. Get all docs for this user
    cur.execute("SELECT stored_path FROM documents WHERE user_id = ?", (user_id,))
    rows = cur.fetchall()

    # 2. Delete physical files
    for r in rows:
        try:
            path = r["stored_path"]
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass

    # 3. Delete rows in documents
    cur.execute("DELETE FROM documents WHERE user_id = ?", (user_id,))

    # 4. Delete activity logs
    cur.execute("DELETE FROM activity_log WHERE user_id = ?", (user_id,))

    # 5. Delete payments record (optional keep for audit? for MVP let's delete)
    cur.execute("DELETE FROM payments WHERE user_id = ?", (user_id,))

    # 6. Finally delete the user
    cur.execute("DELETE FROM users WHERE id = ?", (user_id,))

    conn.commit()
    conn.close()

