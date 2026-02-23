import psycopg2

# Renderで設定したDATABASE_URLを使う
DATABASE_URL = "postgresql://growth_db_9sye_user:bFuMBgCNkvulqT2ThVCOp4o8WPt6rb25@dpg-d6e7j494tr6s73da9020-a.oregon-postgres.render.com/growth_db_9sye"

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# 一度削除してから作成
cur.execute("DROP TABLE IF EXISTS logs;")

cur.execute("""
CREATE TABLE logs (
    id INTEGER PRIMARY KEY,
    category TEXT,
    study_time INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")

conn.commit()
cur.close()
conn.close()

print("テーブル作成完了！")