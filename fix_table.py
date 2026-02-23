import psycopg2

DATABASE_URL = "postgresql://growth_db_9sye_user:bFuMBgCNkvulqT2ThVCOp4o8WPt6rb25@dpg-d6e7j494tr6s73da9020-a.oregon-postgres.render.com/growth_db_9sye"

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

cur.execute("DROP TABLE IF EXISTS logs;")

cur.execute("""
CREATE TABLE logs (
    id SERIAL PRIMARY KEY,
    category TEXT,
    study_time INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")

conn.commit()
cur.close()
conn.close()

print("テーブル作り直し完了！")