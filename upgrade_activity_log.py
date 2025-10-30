import os, sqlite3
DB_PATH = os.path.join(os.path.dirname(__file__), 'vault.db')
print('Using DB:', DB_PATH)
con = sqlite3.connect(DB_PATH); cur = con.cursor()
cur.execute('PRAGMA table_info(activity_log);')
cols = [r[1] for r in cur.fetchall()]
if 'doc_id' not in cols:
    print('Adding column: doc_id')
    cur.execute('ALTER TABLE activity_log ADD COLUMN doc_id INTEGER;')
    con.commit()
else:
    print('Column doc_id already exists.')
con.close()
print('? Done.')
