import streamlit as st
import sqlite3
from datetime import datetime

# ==========================================
# 1. データベースの設定と初期化
# ==========================================
def get_db_connection():
    # SQLiteを使用。StoryWaver用のDBファイルを作成
    conn = sqlite3.connect('storywaver.db', check_same_thread=False)
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    
    # Projectsテーブル
    c.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Conversationsテーブル
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

# アプリ起動時にデータベースを準備
init_db()

# ==========================================
# 2. Streamlit UI（ヘッダー部分）
# ==========================================
st.set_page_config(page_title="StoryWaver", page_icon="✍️")
st.title("StoryWaver - AIと一緒に物語を創る")
st.write("StoryWaverは、AIと対話しながら物語を創作するためのツールです。")

st.divider() # 線を引いて区切りを作るよ

# ==========================================
# 3. チャット画面の実装
# ==========================================

# セッション状態（ブラウザをリロードしても会話が消えない仕組み）の初期化
if 'messages' not in st.session_state:
    st.session_state.messages = []

st.subheader("🖋 AIと物語を創ろう")

# これまでの会話履歴を表示
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ユーザーからの入力を受け取る
if prompt := st.chat_input("物語のアイデアや設定を教えてください..."):
    # ユーザーのメッセージを保存＆表示
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # AIの返事（現在は仮の返事）
    with st.chat_message("assistant"):
        with st.spinner("考え中..."):
            # ここは後で OpenAI の API と繋ぐ場所だよ！
            response = "なるほど！面白い設定だね。それについてもっと詳しく聞かせてくれる？"
            st.markdown(response)
    
    # AIの返事も保存
    st.session_state.messages.append({"role": "assistant", "content": response})
