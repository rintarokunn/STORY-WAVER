import streamlit as st
import sqlite3
from datetime import datetime
from openai import OpenAI

# OpenAIクライアント初期化
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# ==========================================
# データベース設定
# ==========================================
def get_db_connection():
    conn = sqlite3.connect('storywaver.db', check_same_thread=False)
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS stories (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY,
            project_id INTEGER,
            role TEXT,
            content TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id)
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# ==========================================
# Streamlit UI
# ==========================================
st.set_page_config(page_title="StoryWaver", page_icon="📝", layout="wide")
st.title("StoryWaver - AIと一緒に物語を創る")
st.caption("AIと対話しながら物語を創作するためのツールです。")
st.divider()

# 会話保存関数
def save_message(project_id, role, content):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO conversations (project_id, role, content)
        VALUES (?, ?, ?)
    ''', (project_id, role, content))
    conn.commit()
    conn.close()

# チャット履歴初期化
if "messages" not in st.session_state:
    st.session_state.messages = []

# チャット表示
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ユーザー入力
if prompt := st.chat_input("物語のアイデアや設定を教えてください…"):
    project_id = 1
    save_message(project_id, "user", prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("考え中…"):
            try:
                response_data = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
                    temperature=0.8,
                )
                response = response_data.choices[0].message.content
                st.markdown(response)
                save_message(project_id, "assistant", response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                st.error(f"エラーが発生しました: {str(e)}")
                
# ==========================================
# 4. 保存された物語の読み込みと表示
# ==========================================

st.divider()
st.subheader("これまでに紡いだ物語")

# データベースから物語を取得（新しい順）
conn = get_db_connection()
# fetchall()で全てのデータを取り出すよ
stories = conn.execute('SELECT * FROM stories ORDER BY created_at DESC').fetchall()
conn.close()

if stories:
    for story in stories:
        # story[0]:id, story[1]:title, story[2]:content, story[3]:datetime
        # エクスパンダーを使って、タイトルをクリックした時だけ中身が見えるようにするよ
        with st.expander(f"📅 {story[3]} - 📖 {story[1]}"):
            st.write(story[2])
            # 隙間を作るためのスペース
            st.caption(f"ID: {story[0]}")
else:
    st.info("まだ保存された物語はありません。最初の物語を書き上げよう！")