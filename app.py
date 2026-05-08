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
admin_key = st.sidebar.text_input("管理者コード", type="password")
is_admin = (admin_key == st.secrets.get("ADMIN_PASSWORD", "test"))
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

# --- 3. ここが本番！チャット入力の場所 ---

# --- 1. 今日の利用回数をDBから取得する関数 ---
def get_today_usage():
    today = datetime.now().strftime("%Y-%m-%d")
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT count FROM usage_stats WHERE date = ?', (today,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else 0

# --- 2. 管理者チェック（ここはOK！） ---
admin_key = st.sidebar.text_input("管理者コード", type="password", key="admin_key_input")
is_admin = (admin_key == st.secrets.get("ADMIN_PASSWORD", "test"))

# --- 3. メインのチャット処理 ---
if prompt := st.chat_input("物語のアイデアや設定を教えてください..."):
    
    # 今日の累計回数をチェック
    today_count = get_today_usage()

    # 【重要！】優先順位：管理者は「常にOK」。一般人は「累計3回まで」
    if not is_admin and today_count >= 3:
        st.error("本日の全体利用上限（3回）に達しました。里長（管理者）のみ利用可能です！")
    else:
        # --- ここから通常のAI処理 ---
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("考え中…"):
                try:
                    # AI応答、表示、履歴追加（中略）...
                    
                    # --- 成功したらDBの回数を増やす！ ---
                    if not is_admin:
                        today = datetime.now().strftime("%Y-%m-%d")
                        conn = get_db_connection()
                        c = conn.cursor()
                        c.execute('''
                            INSERT INTO usage_stats (date, count) VALUES (?, 1)
                            ON CONFLICT(date) DO UPDATE SET count = count + 1
                        ''', (today,))
                        conn.commit()
                        conn.close()

                    # 最後にリロードして反映
                    st.rerun()
                except Exception as e:
                    st.error(f"エラーだよ！: {str(e)}")

# ==========================================
# 4. 保存された物語の読み込みと表示
# ==========================================
st.divider()
st.subheader("これまでに紡いだ物語")

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