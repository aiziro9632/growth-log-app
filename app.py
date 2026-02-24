from flask import Flask, render_template, request, redirect, session, url_for, flash
import os
from datetime import datetime, timedelta

# --------------------------
# Flask初期化 & セッションキー
# --------------------------
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "supersecretkey")

# --------------------------
# ユーザー管理用カテゴリ
# --------------------------
CATEGORIES = [
    "ITパスポート",
    "プログラミング",
    "HSK",
    "GCI",
    "数学",
    "その他"
]
app = Flask(__name__)
app.secret_key = "supersecretkey"

# --------------------------
# DB選択（自動切り替え）
# --------------------------
DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL:
    import psycopg2
    PLACEHOLDER = "%s"
    def get_conn():
        return psycopg2.connect(DATABASE_URL)
else:
    import sqlite3
    PLACEHOLDER = "?"
    def get_conn():
        return sqlite3.connect("growth.db")

# --------------------------
# DB初期化
# --------------------------
from werkzeug.security import generate_password_hash, check_password_hash

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    # ユーザーテーブル
    if DATABASE_URL:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE,
                password TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                category TEXT,
                study_time INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    else:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                category TEXT,
                study_time INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

    conn.commit()
    conn.close()


init_db()

# --------------------------
# ログイン必須デコレーター
# --------------------------
from functools import wraps
from flask import session, redirect, url_for

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    # ユーザーテーブル
    if DATABASE_URL:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE,
                password TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                category TEXT,
                study_time INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    else:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
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
def format_time(minutes):
    hours = minutes // 60
    mins = minutes % 60
    if hours > 0:
        return f"{hours}時間{mins}分"
    else:
        return f"{mins}分"

@app.route("/", methods=["GET", "POST"])
@login_required

@app.route("/", methods=["GET", "POST"])
@login_required
def home():
    conn = get_conn()
    cur = conn.cursor()
    user_id = session["user_id"]

    now = datetime.now()
    if now.hour < 6:
        today_date = (now - timedelta(days=1)).date()
    else:
        today_date = now.date()
    start_of_today = datetime.combine(today_date, datetime.min.time()) + timedelta(hours=6)
    end_of_today = start_of_today + timedelta(days=1)

    start_week_date = today_date - timedelta(days=today_date.weekday())
    start_of_week = datetime.combine(start_week_date, datetime.min.time()) + timedelta(hours=6)
    end_of_week = start_of_week + timedelta(days=7)

    # POSTでログ追加
    if request.method == "POST":
        category = request.form["category"]
        study_time = int(request.form["study_time"])
        cur.execute(
            f"INSERT INTO logs (category, study_time, user_id) VALUES ({PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER})",
            (category, study_time, user_id)
        )
        conn.commit()
        return redirect("/")

    # 今日の合計
    cur.execute(
        f"SELECT COALESCE(SUM(study_time), 0) FROM logs WHERE created_at >= {PLACEHOLDER} AND created_at < {PLACEHOLDER} AND user_id = {PLACEHOLDER}",
        (start_of_today, end_of_today, user_id)
    )
    today_total = cur.fetchone()[0]

    # 今週の合計
    cur.execute(
        f"SELECT COALESCE(SUM(study_time), 0) FROM logs WHERE created_at >= {PLACEHOLDER} AND created_at < {PLACEHOLDER} AND user_id = {PLACEHOLDER}",
        (start_of_week, end_of_week, user_id)
    )
    week_total = cur.fetchone()[0]

    # カテゴリ別合計
    cur.execute(
        f"SELECT category, COALESCE(SUM(study_time),0) FROM logs WHERE user_id = {PLACEHOLDER} GROUP BY category",
        (user_id,)
    )
    category_totals = cur.fetchall()
    labels = [row[0] for row in category_totals]
    values = [row[1] for row in category_totals]

    # 全ログ
    cur.execute(f"SELECT * FROM logs WHERE user_id = {PLACEHOLDER} ORDER BY created_at DESC", (user_id,))
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
# ログイン
# --------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(f"SELECT id, password_hash FROM users WHERE username = {PLACEHOLDER}", (username,))
        user = cur.fetchone()
        conn.close()
        if user and check_password_hash(user[1], password):
            session["user_id"] = user[0]
            return redirect("/")
        flash("ユーザー名かパスワードが違います")
    return render_template("login.html")

# --------------------------
# 新規登録
# --------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        password_hash = generate_password_hash(password)
        conn = get_conn()
        cur = conn.cursor()
        try:
            cur.execute(f"INSERT INTO users (username, password_hash) VALUES ({PLACEHOLDER}, {PLACEHOLDER})",
                        (username, password_hash))
            conn.commit()
            session["user_id"] = cur.lastrowid if not DATABASE_URL else cur.fetchone()[0]
            conn.close()
            return redirect("/")
        except Exception:
            flash("ユーザー名が既に使われています")
            conn.close()
    return render_template("register.html")

# --------------------------
# ログアウト
# --------------------------
@app.route("/logout")
@login_required
def logout():
    session.pop("user_id", None)
    return redirect("/login")

# --------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)