import os, sqlite3
DB_PATH = os.path.join(os.path.dirname(__file__), "vault.db")
print("Using DB:", DB_PATH)
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
cur.execute("PRAGMA table_info(payments);")
cols = [r[1] for r in cur.fetchall()]
added = False
if "reference" not in cols:
    print("Adding column: reference")
    cur.execute("ALTER TABLE payments ADD COLUMN reference TEXT;")
    added = True
if "raw_json" not in cols:
    print("Adding column: raw_json")
    cur.execute("ALTER TABLE payments ADD COLUMN raw_json TEXT;")
    added = True
conn.commit()
conn.close()
print("Done. Columns now present:", ["reference" in cols or added, "raw_json" in cols or added])
