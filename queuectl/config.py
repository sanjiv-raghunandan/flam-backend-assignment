from . import db

def set_config(key, value):
    """Sets a configuration value."""
    conn = db.get_db()
    conn.execute('REPLACE INTO config (key, value) VALUES (?, ?)', (key, value))
    conn.commit()
    conn.close()

def get_config(key, default=None):
    """Gets a configuration value."""
    conn = db.get_db()
    row = conn.execute('SELECT value FROM config WHERE key = ?', (key,)).fetchone()
    conn.close()
    return row['value'] if row else default
