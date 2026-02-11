import sqlite3

DB_PATH = "observability.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS traces (
            trace_id TEXT,
            node TEXT,
            latency REAL,
            success INTEGER,
            error TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_event(event):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO traces VALUES (?, ?, ?, ?, ?)",
        (
            event["trace_id"],
            event["node"],
            event["latency"],
            int(event["success"]),
            event["error"]
        )
    )
    conn.commit()
    conn.close()
