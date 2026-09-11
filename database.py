import sqlite3

def init_db():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activity (
            user_id INTEGER PRIMARY KEY,
            messages INTEGER DEFAULT 0,
            voice_seconds REAL DEFAULT 0.0
        )
    ''')
    conn.commit()
    conn.close()

def get_user_data(user_id):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT messages, voice_seconds FROM activity WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {'messages': row[0], 'voice_seconds': row[1]}
    return {'messages': 0, 'voice_seconds': 0.0}

def update_user_data(user_id, messages_add=0, voice_add=0.0):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO activity (user_id, messages, voice_seconds) VALUES (?, 0, 0.0)', (user_id,))
    cursor.execute('''
        UPDATE activity 
        SET messages = messages + ?, voice_seconds = voice_seconds + ? 
        WHERE user_id = ?
    ''', (messages_add, voice_add, user_id))
    conn.commit()
    conn.close()

def reset_user_data(user_id):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE activity SET messages = 0, voice_seconds = 0.0 WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()
