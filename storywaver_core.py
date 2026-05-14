#-------------------------------中枢（DB・API・料金管理・保存処理）---------------------------------------------

import sqlite3
from datetime import datetime

from character_manager import CharacterManager


class StoryWaverCore:
    def __init__(self):
        self.character_manager = CharacterManager()

# storywaver_core.py 内

def create_character(self, char_data):
    """
    app.py から char_data という辞書を受け取って処理する
    """
    try:
        # すでに app.py で辞書にまとめているから、
        # そのままマネージャーの create メソッドに投げちゃえばOK！
        self.character_manager.create(char_data)
        
        return "成功"
    except Exception as e:
        return f"エラー: {str(e)}"
#
#  料金設定
PRICE_PER_TOKEN_INPUT = 0.150 / 1_000_000
PRICE_PER_TOKEN_OUTPUT = 0.600 / 1_000_000

def get_db_connection():
    return sqlite3.connect('storywaver.db', check_same_thread=False)

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    # 物語の棚
    c.execute('''CREATE TABLE IF NOT EXISTS stories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP)''')
    
    # キャラクターの棚 （新規追加）
    c.execute('''
    CREATE TABLE IF NOT EXISTS characters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        personality TEXT,
        appearance TEXT,
        voice TEXT,
        speaking_style TEXT,
        background TEXT,
        relation TEXT,
        memo TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
''')
    
    # 料金の棚
    c.execute('''CREATE TABLE IF NOT EXISTS api_usage (
                date TEXT PRIMARY KEY,
                total_cost REAL DEFAULT 0.0)''')
    conn.commit()
    conn.close()

def get_db_cost():
    today = datetime.now().strftime("%Y-%m-%d")
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT total_cost FROM api_usage WHERE date = ?", (today,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else 0.0

def is_allowed_before_api(user_id, total_cost_limit=0.5):
    if user_id == "my_name": return True
    return get_db_cost() < total_cost_limit

def save_new_cost(user_id, usage):
    if user_id == "my_name": return
    today = datetime.now().strftime("%Y-%m-%d")
    current_cost = get_db_cost()
    call_cost = (usage.prompt_tokens * PRICE_PER_TOKEN_INPUT) + \
                (usage.completion_tokens * PRICE_PER_TOKEN_OUTPUT)
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO api_usage (date, total_cost) VALUES (?, ?)", 
                (today, current_cost + call_cost))
    conn.commit()
    conn.close()

# 起動時に棚を作る
init_db()