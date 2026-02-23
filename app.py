from flask import Flask, render_template, request, redirect
import os
from datetime import datetime, timedelta

app = Flask(__name__)

# --------------------------
# DB選択（自動切り替え）
# --------------------------
DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    import psycopg2
    def get_conn():
        return psycopg2.connect(DATABASE_URL)
    PLACEHOLDER = "%s"
else:
    import sqlite3
    def get_conn():
        return sqlite3.connect("growth.db")
    PLACEHOLDER = "?"

# --------------------------
# DB初期化
# --------------------------
def init_db():
    conn = get_conn()
    cur = conn.cursor()

    if DATABASE_URL:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id SERIAL PRIMARY KEY,
                category TEXT,
                study_time INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    else:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT,
                study_time INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

    conn.commit()
    conn.close()

init_db()

# --------------------------
# ホーム
# --------------------------
@app.route("/", methods=["GET", "POST"])
def home():
    conn = get_conn()
    cur = conn.cursor()

    if request.method == "POST":
        category = request.form["category"]
        study_time = int(request.form["study_time"])

        cur.execute(
            f"INSERT INTO logs (category, study_time, created_at) VALUES ({PLACEHOLDER}, {PLACEHOLDER}, CURRENT_TIMESTAMP)",
            (category, study_time)
        )
        conn.commit()
        return redirect("/")
    
    # カテゴリ別合計（グラフ用）
    cur.execute("""
        SELECT category, SUM(study_time)
        FROM logs
        GROUP BY category
    """)
    category_totals = cur.fetchall()

    labels = [row[0] for row in category_totals]
    values = [row[1] or 0 for row in category_totals]

    cur.execute("SELECT * FROM logs ORDER BY created_at DESC")
    logs = cur.fetchall()

    conn.close()

    return render_template(
    "index.html",
    logs=logs,
    labels=labels,
    values=values
)

# --------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)