import sqlite3
import psycopg2

# ★ External Database URL を直接貼る
DATABASE_URL = "postgresql://growth_db_9sye_user:bFuMBgCNkvulqT2ThVCOp4o8WPt6rb25@dpg-d6e7j494tr6s73da9020-a.oregon-postgres.render.com/growth_db_9sye"

# SQLite
sqlite_conn = sqlite3.connect("growth.db")
sqlite_cur = sqlite_conn.cursor()

# PostgreSQL
pg_conn = psycopg2.connect(DATABASE_URL)
pg_cur = pg_conn.cursor()

# id を除いて取得
sqlite_cur.execute("SELECT category, study_time, created_at FROM logs")
rows = sqlite_cur.fetchall()

for row in rows:
    pg_cur.execute("""
        INSERT INTO logs (category, study_time, created_at)
        VALUES (%s, %s, %s)
    """, row)

pg_conn.commit()

sqlite_conn.close()
pg_conn.close()

print("🎉 移行完了！")