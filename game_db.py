import sqlite3
import json
import sys
import os
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "game_stats.db"
HTML_PATH = Path(__file__).parent / "stats.html"


def get_conn():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS games (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            played_at TEXT DEFAULT (datetime('now', 'localtime')),
            category TEXT NOT NULL,
            character_name TEXT NOT NULL,
            questions INTEGER NOT NULL,
            total_rounds INTEGER NOT NULL,
            result TEXT NOT NULL CHECK (result IN ('guessed', 'gave_up')),
            log TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS current_game (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            category TEXT NOT NULL,
            character_name TEXT NOT NULL,
            started_at TEXT DEFAULT (datetime('now', 'localtime'))
        )
    """)
    conn.commit()
    conn.close()
    print(f"Database initialized: {DB_PATH}")


def save_game(category, character_name, questions, total_rounds, result, log_json="[]"):
    init_db()
    conn = get_conn()
    conn.execute(
        "INSERT INTO games (category, character_name, questions, total_rounds, result, log) VALUES (?, ?, ?, ?, ?, ?)",
        (category, character_name, int(questions), int(total_rounds), result, log_json),
    )
    conn.commit()
    conn.close()
    print(f"Game saved: {category} - {character_name} ({result})")
    generate_data_js()


def get_all_games():
    init_db()
    conn = get_conn()
    rows = conn.execute("SELECT * FROM games ORDER BY played_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def generate_data_js():
    games = get_all_games()
    data_json = json.dumps(games, ensure_ascii=False)
    js_content = "window.GAME_DATA = " + data_json + ";"
    DATA_JS_PATH = Path(__file__).parent / "stats.js"
    DATA_JS_PATH.write_text(js_content, encoding="utf-8")
    print(f"Data updated: {DATA_JS_PATH}")


def set_current_character(category, character_name):
    init_db()
    conn = get_conn()
    conn.execute("DELETE FROM current_game")
    conn.execute("INSERT INTO current_game (id, category, character_name) VALUES (1, ?, ?)", (category, character_name))
    conn.commit()
    conn.close()
    print(f"Current character set: {category} - {character_name}")


def get_current_character():
    init_db()
    conn = get_conn()
    row = conn.execute("SELECT category, character_name FROM current_game WHERE id = 1").fetchone()
    conn.close()
    if row:
        return {"category": row["category"], "character_name": row["character_name"]}
    return None


def clear_current_game():
    init_db()
    conn = get_conn()
    conn.execute("DELETE FROM current_game")
    conn.commit()
    conn.close()
    print("Current game cleared.")


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python game_db.py init")
        print("  python game_db.py save <category> <character> <questions> <rounds> <result> [log_json]")
        print("  python game_db.py export")
        print("  python game_db.py stats")
        print("  python game_db.py new-game <category> <character>")
        print("  python game_db.py current")
        print("  python game_db.py end-game")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "init":
        init_db()
    elif cmd == "save":
        if len(sys.argv) < 7:
            print("Error: save requires at least 5 arguments: category, character, questions, rounds, result")
            sys.exit(1)
        category = sys.argv[2]
        character = sys.argv[3]
        questions = sys.argv[4]
        rounds = sys.argv[5]
        result = sys.argv[6]
        log_json = "[]"
        if len(sys.argv) > 7 and sys.argv[7] == "--log-file" and len(sys.argv) > 8:
            with open(sys.argv[8], "r", encoding="utf-8") as f:
                log_json = f.read().strip()
        elif not sys.stdin.isatty():
            log_json = sys.stdin.read().strip()
        elif len(sys.argv) > 7:
            log_json = sys.argv[7]
        save_game(category, character, questions, rounds, result, log_json)
        clear_current_game()
    elif cmd == "export":
        generate_data_js()
    elif cmd == "stats":
        games = get_all_games()
        total = len(games)
        wins = sum(1 for g in games if g["result"] == "guessed")
        print(f"Total: {total} | Wins: {wins} | Win Rate: {round(wins/total*100,1) if total else 0}%")
        for g in games:
            emoji = "O" if g["result"] == "guessed" else "X"
            print(f"  [{emoji}] {g['played_at'][:16]} | {g['category']} | {g['character_name']} | {g['total_rounds']} rounds")
    elif cmd == "new-game":
        if len(sys.argv) < 4:
            print("Error: new-game requires category and character")
            sys.exit(1)
        set_current_character(sys.argv[2], sys.argv[3])
    elif cmd == "current":
        g = get_current_character()
        if g:
            print(f"Current: {g['category']} - {g['character_name']}")
        else:
            print("No current game.")
    elif cmd == "end-game":
        clear_current_game()
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
