import sqlite3
import json
import os
import sys
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

# Add server dir to path for game_engine import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from game_engine import CharacterEngine, DeepSeekAI

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "server_data.db")

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", os.urandom(24))

engine = CharacterEngine(api_key=os.environ.get("DEEPSEEK_API_KEY", ""))


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now', 'localtime'))
        );
        CREATE TABLE IF NOT EXISTS games (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            character_name TEXT NOT NULL,
            questions INTEGER NOT NULL DEFAULT 0,
            total_rounds INTEGER NOT NULL DEFAULT 0,
            result TEXT DEFAULT 'playing',
            qa_log TEXT DEFAULT '[]',
            created_at TEXT DEFAULT (datetime('now', 'localtime')),
            ended_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
    """)
    conn.commit()

    admin = conn.execute("SELECT id FROM users WHERE username = ?", ("admin",)).fetchone()
    if not admin:
        conn.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            ("admin", generate_password_hash("admin123")),
        )
        conn.commit()
        print("Default admin account created: admin / admin123")
    conn.close()


init_db()


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


# ── Auth Routes ──

@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        conn.close()
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("dashboard"))
        flash("用户名或密码错误")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ── Dashboard ──

@app.route("/dashboard")
@login_required
def dashboard():
    conn = get_db()
    uid = session["user_id"]

    games = conn.execute(
        "SELECT * FROM games WHERE user_id = ? ORDER BY created_at DESC LIMIT 20",
        (uid,),
    ).fetchall()

    stat = conn.execute(
        """SELECT
            COUNT(*) as total,
            SUM(CASE WHEN result='guessed' THEN 1 ELSE 0 END) as wins,
            SUM(CASE WHEN result='gave_up' THEN 1 ELSE 0 END) as losses,
            AVG(CASE WHEN result='guessed' THEN total_rounds END) as avg_rounds,
            MIN(CASE WHEN result='guessed' THEN total_rounds END) as best,
            MAX(CASE WHEN result='guessed' THEN total_rounds END) as worst
        FROM games WHERE user_id = ?""",
        (uid,),
    ).fetchone()

    # Check for active game
    active = conn.execute(
        "SELECT * FROM games WHERE user_id = ? AND result = 'playing' ORDER BY created_at DESC LIMIT 1",
        (uid,),
    ).fetchone()
    conn.close()

    game_list = []
    for g in games:
        d = dict(g)
        try:
            d["qa_log_parsed"] = json.loads(d["qa_log"]) if d["qa_log"] else []
        except (json.JSONDecodeError, TypeError):
            d["qa_log_parsed"] = []
        d["rating"] = _rating(d)
        game_list.append(d)

    return render_template(
        "dashboard.html",
        username=session["username"],
        games=game_list,
        stat=stat,
        active=active,
    )


# ── Game Routes ──

@app.route("/game/start", methods=["POST"])
@login_required
def game_start():
    category = request.form.get("category", "三国")

    # End any active game first
    conn = get_db()
    conn.execute(
        "UPDATE games SET result='gave_up', ended_at=datetime('now','localtime') WHERE user_id=? AND result='playing'",
        (session["user_id"],),
    )

    character = engine.pick_random(category)
    conn.execute(
        "INSERT INTO games (user_id, category, character_name, qa_log) VALUES (?, ?, ?, '[]')",
        (session["user_id"], character["category"], character["name"]),
    )
    conn.commit()

    game_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    session["active_game_id"] = game_id
    session["active_character"] = character["name"]
    conn.close()

    return redirect(url_for("game_play"))


@app.route("/game")
@login_required
def game_play():
    gid = session.get("active_game_id")
    if not gid:
        return redirect(url_for("dashboard"))

    conn = get_db()
    game = conn.execute("SELECT * FROM games WHERE id = ? AND user_id = ?", (gid, session["user_id"])).fetchone()
    conn.close()

    if not game:
        session.pop("active_game_id", None)
        session.pop("active_character", None)
        return redirect(url_for("dashboard"))

    if game["result"] != "playing":
        return redirect(url_for("game_result"))

    character = None
    for c in engine.characters:
        if c["name"] == game["character_name"]:
            character = c
            break

    qa_log = json.loads(game["qa_log"]) if game["qa_log"] else []

    return render_template("game.html", game=game, qa_log=qa_log, character_bio=character["bio"] if character else "")


@app.route("/game/ask", methods=["POST"])
@login_required
def game_ask():
    gid = session.get("active_game_id")
    if not gid:
        return jsonify({"error": "no active game"}), 400

    question = request.form.get("question", "").strip()
    if not question:
        return jsonify({"error": "empty question"}), 400

    conn = get_db()
    game = conn.execute("SELECT * FROM games WHERE id = ? AND user_id = ? AND result = 'playing'", (gid, session["user_id"])).fetchone()
    if not game:
        conn.close()
        return jsonify({"error": "game not found"}), 400

    character = None
    for c in engine.characters:
        if c["name"] == game["character_name"]:
            character = c
            break

    if not character:
        conn.close()
        return jsonify({"error": "character not found"}), 500

    qa_log = json.loads(game["qa_log"]) if game["qa_log"] else []
    result = engine.answer(character, question, qa_log=qa_log)
    questions_count = game["questions"] + 1
    total_rounds = game["total_rounds"] + 1

    qa_log.append({"q": question, "a": result["text"]})

    game_over = False
    if result["type"] == "correct":
        conn.execute(
            "UPDATE games SET questions=?, total_rounds=?, result='guessed', qa_log=?, ended_at=datetime('now','localtime') WHERE id=?",
            (questions_count, total_rounds, json.dumps(qa_log, ensure_ascii=False), gid),
        )
        conn.commit()
        game_over = True
    elif result["type"] == "wrong_guess":
        conn.execute(
            "UPDATE games SET questions=?, total_rounds=?, qa_log=? WHERE id=?",
            (questions_count, total_rounds, json.dumps(qa_log, ensure_ascii=False), gid),
        )
        conn.commit()
    else:
        conn.execute(
            "UPDATE games SET questions=?, total_rounds=?, qa_log=? WHERE id=?",
            (questions_count, total_rounds, json.dumps(qa_log, ensure_ascii=False), gid),
        )
        conn.commit()

    conn.close()

    response = {
        "type": result["type"],
        "text": result["text"],
        "rounds": total_rounds,
        "game_over": game_over,
        "character_bio": character["bio"] if game_over else None,
    }
    if game_over:
        response["qa_log"] = qa_log
    return jsonify(response)


@app.route("/game/giveup", methods=["POST"])
@login_required
def game_giveup():
    gid = session.get("active_game_id")
    if not gid:
        return jsonify({"error": "no active game"}), 400

    conn = get_db()
    game = conn.execute("SELECT * FROM games WHERE id = ? AND user_id = ? AND result = 'playing'", (gid, session["user_id"])).fetchone()
    if not game:
        conn.close()
        return jsonify({"error": "game not found"}), 400

    conn.execute(
        "UPDATE games SET result='gave_up', ended_at=datetime('now','localtime') WHERE id=?",
        (gid,),
    )
    conn.commit()

    character = None
    for c in engine.characters:
        if c["name"] == game["character_name"]:
            character = c
            break

    session.pop("active_game_id", None)
    session.pop("active_character", None)

    qa_log = json.loads(game["qa_log"]) if game["qa_log"] else []
    conn.close()

    return jsonify({
        "type": "gave_up",
        "text": "你放弃了！",
        "character_name": game["character_name"],
        "character_bio": character["bio"] if character else "",
        "rounds": game["total_rounds"],
        "qa_log": qa_log,
    })


@app.route("/game/result")
@login_required
def game_result():
    gid = session.get("active_game_id")
    if not gid:
        return redirect(url_for("dashboard"))

    conn = get_db()
    game = conn.execute("SELECT * FROM games WHERE id = ? AND user_id = ?", (gid, session["user_id"])).fetchone()
    conn.close()

    if not game or game["result"] == "playing":
        return redirect(url_for("game_play"))

    character = None
    for c in engine.characters:
        if c["name"] == game["character_name"]:
            character = c
            break

    qa_log = json.loads(game["qa_log"]) if game["qa_log"] else []
    return render_template(
        "game.html",
        game=game,
        qa_log=qa_log,
        game_over=True,
        character_bio=character["bio"] if character else "",
        character_name=game["character_name"],
        is_win=(game["result"] == "guessed"),
    )


# ── Stats ──

@app.route("/stats")
@login_required
def stats():
    conn = get_db()
    uid = session["user_id"]

    games = conn.execute(
        "SELECT * FROM games WHERE user_id = ? AND result != 'playing' ORDER BY created_at DESC",
        (uid,),
    ).fetchall()

    stat = conn.execute(
        """SELECT
            COUNT(*) as total,
            SUM(CASE WHEN result='guessed' THEN 1 ELSE 0 END) as wins,
            SUM(CASE WHEN result='gave_up' THEN 1 ELSE 0 END) as losses,
            ROUND(CAST(SUM(CASE WHEN result='guessed' THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*) * 100, 1) as win_rate,
            ROUND(AVG(CASE WHEN result='guessed' THEN total_rounds END), 1) as avg_rounds,
            MIN(CASE WHEN result='guessed' THEN total_rounds END) as best
        FROM games WHERE user_id = ? AND result != 'playing'""",
        (uid,),
    ).fetchone()

    cat_stats = conn.execute(
        """SELECT category,
            COUNT(*) as total,
            SUM(CASE WHEN result='guessed' THEN 1 ELSE 0 END) as wins
        FROM games WHERE user_id = ? AND result != 'playing'
        GROUP BY category""",
        (uid,),
    ).fetchall()
    conn.close()

    game_list = []
    for g in games:
        d = dict(g)
        try:
            d["qa_log_parsed"] = json.loads(d["qa_log"]) if d["qa_log"] else []
        except (json.JSONDecodeError, TypeError):
            d["qa_log_parsed"] = []
        game_list.append(d)

    return render_template(
        "stats.html",
        username=session["username"],
        games=game_list,
        stat=stat,
        cat_stats=cat_stats,
    )


# ── Admin: Register User (manual, no UI; use command line) ──

def create_user(username, password):
    conn = get_db()
    exists = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
    if exists:
        conn.close()
        return False, "用户已存在"
    conn.execute(
        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
        (username, generate_password_hash(password)),
    )
    conn.commit()
    conn.close()
    return True, f"用户 {username} 创建成功"


def _rating(game):
    """Generate a rating comment based on round count and result."""
    if game.get("result") == "gave_up":
        return "虽败犹荣"
    rounds = game.get("total_rounds", 0)
    if rounds <= 4:
        return "神机妙算！"
    elif rounds <= 7:
        return "思路清晰！"
    elif rounds <= 10:
        return "稳扎稳打"
    elif rounds <= 15:
        return "锲而不舍"
    else:
        return "终得正果"


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="猜人物游戏服务器")
    parser.add_argument("--create-user", nargs=2, metavar=("USERNAME", "PASSWORD"), help="手动注册新用户")
    parser.add_argument("--api-key", help="DeepSeek API Key（也可用环境变量 DEEPSEEK_API_KEY）")
    parser.add_argument("--host", default="0.0.0.0", help="监听地址 (默认: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=5000, help="监听端口 (默认: 5000)")
    parser.add_argument("--debug", action="store_true", help="调试模式")

    args = parser.parse_args()

    if args.create_user:
        username, password = args.create_user
        success, msg = create_user(username, password)
        print(msg)
    else:
        if args.api_key:
            os.environ["DEEPSEEK_API_KEY"] = args.api_key
            engine.ai = DeepSeekAI(args.api_key)
        if engine.ai and engine.ai.available:
            print(f"[AI] DeepSeek API 已启用")
        else:
            print("[AI] 未配置 API Key，使用本地规则匹配")

        print(f"服务启动: http://{args.host}:{args.port}")
        if args.debug:
            print("默认管理员: admin / admin123")
        app.run(host=args.host, port=args.port, debug=args.debug)
