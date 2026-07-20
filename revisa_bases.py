import sqlite3

con = sqlite3.connect("erp_cafe.db")
cur = con.cursor()

cur.execute("""
SELECT name
FROM sqlite_master
WHERE type='table'
""")

for t in cur.fetchall():
    print(t)

con.close()