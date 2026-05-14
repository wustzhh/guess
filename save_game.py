import sqlite3, json, sys, os

db = r"D:\pyProj\guess\game_stats.db"

if sys.argv[1] == "fix7":
    conn = sqlite3.connect(db)
    log = [{"q":"死于234年之前还是之后？","a":"234年之前死的"},{"q":"死于208年之前还是之后？","a":"208年之前死的"},{"q":"放弃","a":"\u2014"}]
    conn.execute("UPDATE games SET log = ? WHERE id = 7", (json.dumps(log, ensure_ascii=False, separators=(",", ":")),))
    conn.commit()
    print("Fixed ID=7")
    conn.close()
elif sys.argv[1] == "save":
    category = sys.argv[2]
    character = sys.argv[3]
    questions = int(sys.argv[4])
    rounds = int(sys.argv[5])
    result = sys.argv[6]
    log_json = sys.stdin.read()
    
    conn = sqlite3.connect(db)
    conn.execute(
        "INSERT INTO games (category, character_name, questions, total_rounds, result, log) VALUES (?, ?, ?, ?, ?, ?)",
        (category, character, questions, rounds, result, log_json),
    )
    conn.commit()
    conn.close()
    print(f"Game saved: {category} - {character} ({result})")
    
    import subprocess
    subprocess.run([sys.executable, str(__file__.replace("save_game.py", "game_db.py")), "export"])
