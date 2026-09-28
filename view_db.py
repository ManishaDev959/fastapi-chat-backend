import sqlite3

conn = sqlite3.connect("chat.db")
conn.row_factory = sqlite3.Row
cur = conn.cursor()

tables = [r[0] for r in cur.execute(
    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
)]

for t in tables:
    print(f"\n=== {t} ===")
    rows = cur.execute(f"SELECT * FROM {t}").fetchall()
    if not rows:
        print("(empty)")
        continue
    cols = rows[0].keys()
    print(" | ".join(cols))
    print("-" * 60)
    for r in rows:
        print(" | ".join(str(r[c])[:40] for c in cols))

conn.close()