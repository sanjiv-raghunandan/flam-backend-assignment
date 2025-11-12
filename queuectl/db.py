import sqlite3
import json
from pathlib import Path

DB_FILE = Path.home() / ".queuectl.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            command TEXT NOT NULL,
            state TEXT NOT NULL,
            attempts INTEGER NOT NULL,
            max_retries INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            is_dlq BOOLEAN DEFAULT FALSE
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS config (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn
