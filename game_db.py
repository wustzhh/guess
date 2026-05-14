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
    generate_html()


def get_all_games():
    init_db()
    conn = get_conn()
    rows = conn.execute("SELECT * FROM games ORDER BY played_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def generate_html():
    games = get_all_games()
    total = len(games)
    wins = sum(1 for g in games if g["result"] == "guessed")
    losses = total - wins
    win_rate = round(wins / total * 100, 1) if total > 0 else 0
    avg_rounds = round(sum(g["total_rounds"] for g in games) / total, 1) if total > 0 else 0
    best = min((g["total_rounds"] for g in games if g["result"] == "guessed"), default=0)
    categories = {}
    for g in games:
        cat = g["category"]
        if cat not in categories:
            categories[cat] = {"total": 0, "wins": 0}
        categories[cat]["total"] += 1
        if g["result"] == "guessed":
            categories[cat]["wins"] += 1

    games_json = json.dumps(games, ensure_ascii=False, indent=2)
    categories_json = json.dumps(categories, ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>猜人物游戏 - 战绩总览</title>
<style>
  :root {{
    --bg: #0f0f1a;
    --card: #1a1a2e;
    --card-hover: #222240;
    --accent: #e94560;
    --accent2: #0f3460;
    --gold: #f5c518;
    --green: #4ecca3;
    --red: #e94560;
    --text: #eaeaea;
    --text-dim: #8888aa;
    --border: #2a2a4a;
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: "Segoe UI", "Microsoft YaHei", sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
    padding: 2rem;
  }}
  .header {{
    text-align: center;
    margin-bottom: 2.5rem;
  }}
  .header h1 {{
    font-size: 2.2rem;
    background: linear-gradient(135deg, var(--gold), var(--accent));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.3rem;
  }}
  .header p {{ color: var(--text-dim); font-size: 0.95rem; }}

  .stats-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 1.2rem;
    margin-bottom: 2.5rem;
    max-width: 900px;
    margin-left: auto;
    margin-right: auto;
  }}
  .stat-card {{
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.5rem;
    text-align: center;
    transition: transform 0.2s, box-shadow 0.2s;
  }}
  .stat-card:hover {{
    transform: translateY(-4px);
    box-shadow: 0 8px 25px rgba(233, 69, 96, 0.15);
  }}
  .stat-card .number {{
    font-size: 2.5rem;
    font-weight: 700;
    line-height: 1;
    margin-bottom: 0.3rem;
  }}
  .stat-card .label {{
    color: var(--text-dim);
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 1px;
  }}
  .stat-card.win .number {{ color: var(--green); }}
  .stat-card.loss .number {{ color: var(--red); }}
  .stat-card.gold .number {{ color: var(--gold); }}
  .stat-card.accent .number {{ color: var(--accent); }}

  .section-title {{
    font-size: 1.3rem;
    margin-bottom: 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 2px solid var(--accent);
    display: inline-block;
  }}

  .category-tags {{
    display: flex;
    flex-wrap: wrap;
    gap: 0.8rem;
    margin-bottom: 2.5rem;
    max-width: 900px;
    margin-left: auto;
    margin-right: auto;
  }}
  .cat-tag {{
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 0.5rem 1.2rem;
    font-size: 0.9rem;
  }}
  .cat-tag span {{ color: var(--gold); font-weight: 600; }}

  .table-wrap {{
    max-width: 1100px;
    margin: 0 auto 2rem;
    overflow-x: auto;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    background: var(--card);
    border-radius: 12px;
    overflow: hidden;
  }}
  thead th {{
    background: var(--accent2);
    padding: 0.9rem 1rem;
    text-align: left;
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: var(--text-dim);
  }}
  tbody td {{
    padding: 0.8rem 1rem;
    border-bottom: 1px solid var(--border);
    font-size: 0.95rem;
  }}
  tbody tr:hover {{ background: var(--card-hover); }}
  tbody tr:last-child td {{ border-bottom: none; }}
  .badge {{
    display: inline-block;
    padding: 0.2rem 0.7rem;
    border-radius: 12px;
    font-size: 0.8rem;
    font-weight: 600;
  }}
  .badge.win {{ background: rgba(78, 204, 163, 0.15); color: var(--green); }}
  .badge.lose {{ background: rgba(233, 69, 96, 0.15); color: var(--red); }}

  .log-toggle {{
    cursor: pointer;
    color: var(--gold);
    font-size: 0.85rem;
    user-select: none;
    text-decoration: underline;
  }}
  .log-toggle:hover {{ color: var(--accent); }}
  .log-detail {{
    display: none;
    margin-top: 0.5rem;
    background: var(--bg);
    border-radius: 8px;
    padding: 0.8rem;
    font-size: 0.85rem;
    line-height: 1.6;
  }}
  .log-detail.show {{ display: block; }}
  .log-detail .q {{ color: var(--gold); }}
  .log-detail .a {{ color: var(--green); }}

  .empty {{
    text-align: center;
    padding: 4rem 2rem;
    color: var(--text-dim);
    font-size: 1.1rem;
  }}

  .footer {{
    text-align: center;
    color: var(--text-dim);
    font-size: 0.8rem;
    margin-top: 3rem;
    padding-top: 1rem;
    border-top: 1px solid var(--border);
  }}
</style>
</head>
<body>

<div class="header">
  <h1>猜人物游戏 · 战绩总览</h1>
  <p>看看你的推理实力如何</p>
</div>

<div class="stats-grid">
  <div class="stat-card gold">
    <div class="number">{total}</div>
    <div class="label">总场次</div>
  </div>
  <div class="stat-card win">
    <div class="number">{wins}</div>
    <div class="label">猜中</div>
  </div>
  <div class="stat-card loss">
    <div class="number">{losses}</div>
    <div class="label">放弃</div>
  </div>
  <div class="stat-card accent">
    <div class="number">{win_rate}%</div>
    <div class="label">猜中率</div>
  </div>
  <div class="stat-card gold">
    <div class="number">{avg_rounds}</div>
    <div class="label">平均轮次</div>
  </div>
  <div class="stat-card win">
    <div class="number">{best if best > 0 else '-'}</div>
    <div class="label">最佳纪录</div>
  </div>
</div>

<div class="category-tags">
  {"".join(f'<div class="cat-tag">{cat} <span>{info["wins"]}/{info["total"]}</span></div>' for cat, info in categories.items()) if categories else '<div class="cat-tag" style="color:var(--text-dim)">暂无分类数据</div>'}
</div>

<div class="table-wrap">
  <h2 class="section-title">对局记录</h2>
  {"" if total > 0 else '<div class="empty">还没有对局记录，快去玩一局吧！</div>'}
  {"<table><thead><tr><th>#</th><th>时间</th><th>分类</th><th>答案</th><th>提问数</th><th>总轮次</th><th>结果</th><th>详情</th></tr></thead><tbody>" if total > 0 else ""}
  {"".join(_render_row(i, g) for i, g in enumerate(games)) if total > 0 else ""}
  {"</tbody></table>" if total > 0 else ""}
</div>

<div class="footer">
  猜人物游戏 · 战绩系统 · 数据存储于 game_stats.db
</div>

<script>
function toggleLog(id) {{
  var el = document.getElementById('log-' + id);
  el.classList.toggle('show');
}}
</script>
</body>
</html>"""

    HTML_PATH.write_text(html, encoding="utf-8")
    print(f"HTML report generated: {HTML_PATH}")


def _render_row(index, game):
    gid = game["id"]
    time_str = game["played_at"][:16] if game["played_at"] else ""
    result_badge = f'<span class="badge win">猜中</span>' if game["result"] == "guessed" else f'<span class="badge lose">放弃</span>'

    log_html = ""
    try:
        log_data = json.loads(game["log"]) if game["log"] else []
        if log_data:
            lines = "".join(
                f'<div><span class="q">Q{i+1}: {item["q"]}</span><br><span class="a">A: {item["a"]}</span></div>'
                for i, item in enumerate(log_data)
            )
            log_html = f'<span class="log-toggle" onclick="toggleLog({gid})">展开</span><div class="log-detail" id="log-{gid}">{lines}</div>'
        else:
            log_html = '<span style="color:var(--text-dim)">-</span>'
    except (json.JSONDecodeError, TypeError):
        log_html = '<span style="color:var(--text-dim)">-</span>'

    return f"""<tr>
    <td>{gid}</td>
    <td>{time_str}</td>
    <td>{game["category"]}</td>
    <td><strong>{game["character_name"]}</strong></td>
    <td>{game["questions"]}</td>
    <td>{game["total_rounds"]}</td>
    <td>{result_badge}</td>
    <td>{log_html}</td>
  </tr>"""


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python game_db.py init")
        print("  python game_db.py save <category> <character> <questions> <rounds> <result> [log_json]")
        print("  python game_db.py export")
        print("  python game_db.py stats")
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
        log_json = sys.argv[7] if len(sys.argv) > 7 else "[]"
        save_game(category, character, questions, rounds, result, log_json)
    elif cmd == "export":
        generate_html()
    elif cmd == "stats":
        games = get_all_games()
        total = len(games)
        wins = sum(1 for g in games if g["result"] == "guessed")
        print(f"Total: {total} | Wins: {wins} | Win Rate: {round(wins/total*100,1) if total else 0}%")
        for g in games:
            emoji = "O" if g["result"] == "guessed" else "X"
            print(f"  [{emoji}] {g['played_at'][:16]} | {g['category']} | {g['character_name']} | {g['total_rounds']} rounds")
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
