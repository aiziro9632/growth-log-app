from flask import Flask, render_template, request, redirect
import os
from datetime import datetime, timedelta
CATEGORIES = [
    "ITパスポート",
    "プログラミング",
    "HSK",
    "GCI",
    "数学",
    "その他"
]

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

    now = datetime.now()

    # ===== 今日（6時基準）=====
    if now.hour < 6:
        today_date = (now - timedelta(days=1)).date()
    else:
        today_date = now.date()

    start_of_today = datetime.combine(today_date, datetime.min.time()) + timedelta(hours=6)
    end_of_today = start_of_today + timedelta(days=1)

    # 今日の合計
    cur.execute("""
        SELECT COALESCE(SUM(study_time), 0)
        FROM logs
        WHERE created_at >= %s AND created_at < %s
    """, (start_of_today, end_of_today))
    today_total = cur.fetchone()[0]

    # ===== 今週（6時基準）=====
    start_week_date = today_date - timedelta(days=today_date.weekday())
    start_of_week = datetime.combine(start_week_date, datetime.min.time()) + timedelta(hours=6)
    end_of_week = start_of_week + timedelta(days=7)

    # 今週の合計
    cur.execute("""
        SELECT COALESCE(SUM(study_time), 0)
        FROM logs
        WHERE created_at >= %s AND created_at < %s
    """, (start_of_week, end_of_week))
    week_total = cur.fetchone()[0]

    if request.method == "POST":
        category = request.form["category"]
        study_time = int(request.form["study_time"])

        cur.execute(
            "INSERT INTO logs (category, study_time) VALUES (%s, %s)",
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
    categories=CATEGORIES,
    labels=labels,
    values=values,
    today_total_str=format_time(today_total),
    week_total_str=format_time(week_total)
)


# --------------------------
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)