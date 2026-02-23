import sqlite3

conn = sqlite3.connect("growth.db")
cur = conn.cursor()

cur.execute("PRAGMA table_info(logs);")
columns = cur.fetchall()

print("logsテーブルの構造:")
for col in columns:
    print(col)

conn.close()