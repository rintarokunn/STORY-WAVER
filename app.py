import streamlit as st
import sqlite3
from datetime import datetime

# 1. データベース接続の設定
def get_db_connection():
    # SQLiteを使用。StoryWaver用のDBファイルを作成
    conn = sqlite3.connect('storywaver.db', check_same_thread=False)
    return conn

# 2. テーブル作成関数
def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    
    # Projectsテーブル：作品ごとのタイトルや説明を管理
    c.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Conversationsテーブル：ユーザーとAIの対話ログを保存
    c.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY,
            project_id INTEGER,
            role TEXT,  -- 'user' または 'assistant'
            content TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id)
        )
    ''')
    
    conn.commit()
    conn.close()

# 3. アプリ起動時に初期化を実行
init_db()