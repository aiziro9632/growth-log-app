from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)

# --------------------------
# 時間表示用関数
# --------------------------
def format_time(minutes):
    hours = minutes // 60
    mins = minutes % 60
    if hours > 0:
        return f"{hours}時間{mins}分"
    else:
        return f"{mins}分"

# --------------------------
# DB初期化
# --------------------------
def init_db():
    conn = sqlite3.connect("growth.db")
    cur = conn.cursor()
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

CATEGORIES = ["ITパスポート", "プログラミング", "HSK", "GCI","数学", "その他"]

# --------------------------
# ホームページ
# --------------------------
@app.route("/", methods=["GET", "POST"])
def home():
    conn = sqlite3.connect("growth.db")
    cur = conn.cursor()

    now = datetime.now()

    # 今日の6時を起点
    if now.hour < 6:
        today_date = (now - timedelta(days=1)).date()
    else:
        today_date = now.date()
    start_of_today = datetime.combine(today_date, datetime.min.time()) + timedelta(hours=6)
    end_of_today = start_of_today + timedelta(days=1)

    # 今週（月曜日6時）を起点
    start_week_date = today_date - timedelta(days=today_date.weekday())
    start_of_week = datetime.combine(start_week_date, datetime.min.time()) + timedelta(hours=6)
    end_of_week = start_of_week + timedelta(days=7)

    # --------------------------
    # POSTで学習記録追加
    # --------------------------
    if request.method == "POST":
        category = request.form["category"]
        study_time = int(request.form["study_time"])
        cur.execute(
            "INSERT INTO logs (category, study_time, created_at) VALUES (?, ?, ?)",
            (category, study_time, start_of_today.strftime("%Y-%m-%d %H:%M:%S"))
        )
        conn.commit()
        return redirect("/")

    # --------------------------
    # 全データ取得
    # --------------------------
    cur.execute("SELECT * FROM logs ORDER BY created_at DESC")
    logs = cur.fetchall()

    # 今日の合計
    cur.execute(
        "SELECT SUM(study_time) FROM logs WHERE created_at >= ? AND created_at < ?",
        (start_of_today, end_of_today)
    )
    today_total = cur.fetchone()[0] or 0
    today_total_str = format_time(today_total)

    # 今週の合計
    cur.execute(
        "SELECT SUM(study_time) FROM logs WHERE created_at >= ? AND created_at < ?",
        (start_of_week, end_of_week)
    )
    week_total = cur.fetchone()[0] or 0
    week_total_str = format_time(week_total)

    # カテゴリ別合計
    cur.execute("""
        SELECT category, SUM(study_time)
        FROM logs
        GROUP BY category
    """)
    category_totals = cur.fetchall()
    labels = [row[0] for row in category_totals]
    values = [row[1] for row in category_totals]

    conn.close()

    # --------------------------
    # レンダリング
    # --------------------------
    return render_template(
        "index.html",
        logs=logs,
        categories=CATEGORIES,
        category_totals=category_totals,
        today_total_str=today_total_str,
        week_total_str=week_total_str,
        labels=labels,
        values=values
    )

# --------------------------
# 削除
# --------------------------
@app.route("/delete/<int:log_id>")
def delete_log(log_id):
    conn = sqlite3.connect("growth.db")
    cur = conn.cursor()
    cur.execute("DELETE FROM logs WHERE id = ?", (log_id,))
    conn.commit()
    conn.close()
    return redirect("/")

# --------------------------
# 実行
# --------------------------
if __name__ == "__main__":
    app.run()
