import os
import json
import streamlit as st
import sqlite3
from datetime import datetime
from openai import OpenAI

# OpenAIクライアント初期化
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# ==========================================
#1 データベース設定
# ==========================================
def get_db_connection():
    conn = sqlite3.connect('storywaver.db', check_same_thread=False)
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    # 1. 物語のメイン棚（将来の編集用に updated_at も完備！）
    c.execute('''
        CREATE TABLE IF NOT EXISTS stories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 2. 会話の記録棚（storiesテーブルと紐付け！）
    c.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            story_id INTEGER,
            role TEXT,
            content TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (story_id) REFERENCES stories(id)
        )
    ''')

    # 3. 利用統計の棚（将来の分析用に！）
    c.execute('''
    CREATE TABLE IF NOT EXISTS usage_stats (
        date TEXT PRIMARY KEY,
        count INTEGER
    )
''')

    conn.commit()
    conn.close()

init_db()

# ==========================================
#2 Streamlit UI
# ==========================================
st.set_page_config(page_title="StoryWaver", page_icon="📝", layout="wide")
st.title("StoryWaver - AIと一緒に物語を創る")
st.caption("AIと対話しながら物語を創作するためのツールです。")
st.divider()

# 会話保存関数（紐付け先を story_id に変更したよ！）
def save_message(story_id, role, content):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO conversations (story_id, role, content)
        VALUES (?, ?, ?)
    ''', (story_id, role, content))
    conn.commit()
    conn.close()

# チャット履歴初期化
if "messages" not in st.session_state:
    st.session_state.messages = []

# チャット表示
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# チャット入力 
if prompt := st.chat_input("物語のアイデアや設定を教えてください..."): 
    # ユーザー入力の表示
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    # AI応答
    with st.chat_message("assistant"):
        with st.spinner("物語を紡いでいます..."):
            try:
                response_data = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
                    temperature=0.8,
                )
                response = response_data.choices[0].message.content
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
# ここに保存処理を入れる（後で）
            except Exception as e: st.error(fエラーが発生しました: {str(e)})

# ==========================================
st.divider()
conn = get_db_connection()
# 全ての物語を取得するよ
stories = conn.execute('SELECT * FROM stories ORDER BY created_at DESC').fetchall()
conn.close()

if stories:
    for story in stories:
        with st.expander(f"📅 {story[3]} - 📖 {story[1]}"):
            st.write(story[2] if story[2] else "（中身はまだありません）")
            st.caption(f"ID: {story[0]}")
else:
    st.info("まだ保存された物語はありません。最初の物語を書き上げよう！")