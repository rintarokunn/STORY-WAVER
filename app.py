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

# --- 3. ここが本番！チャット入力の場所 ---

# ==========================================
# 3. チャット画面と利用制限の実装
# ==========================================

# --- 1. 管理者設定とログ準備 ---
ADMIN_KEY = st.secrets.get("ADMIN_PASSWORD", "my_secret_password")
LOG_FILE = "api_usage.json"

def check_and_update_limit(limit=3, input_key=None):
    # 管理者チェック
    if input_key == ADMIN_KEY:
        return True, "admin"

    today = datetime.now().strftime("%Y-%m-%d")
    
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            try:
                data = json.load(f)
            except:
                data = {"date": today, "count": 0}
    else:
        data = {"date": today, "count": 0}

    if data.get("date") != today:
        data = {"date": today, "count": 0}

    if data["count"] >= limit:
        return False, data["count"]

    # ※ここではカウントを増やさず、チェックだけ返すように修正
    return True, data["count"]

# --- 2. 判定の準備（ここが最初！） ---
user_key = st.sidebar.text_input("管理者コード", type="password", key="admin_key_input")
is_admin_now = (user_key == ADMIN_KEY)

# 呼び出し！ここで current_count が定義されるよ
allowed_now, current_count = check_and_update_limit(limit=3, input_key=user_key)

st.subheader("これまでに紡いだ物語")

# --- 3. 画面上の警告表示 ---
if is_admin_now:
    st.success("🛡️ 管理者モード：制限なしで利用可能です！")
elif current_count >= 3:
    st.error(f"利用回数の上限に達しました。今日の利用は {current_count} 回目です。管理者コードを入力すると制限なしで利用できます。")

# --- 4. AI処理 ---
if prompt := st.chat_input("物語のアイデアや設定を教えてください..."):
    
    if not is_admin_now and current_count >= 3:
        st.stop() 
    else:
        # ユーザー表示
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # AI応答
        with st.chat_message("assistant"):
            if is_admin_now:
                st.caption("🛡️ 管理者モードで実行中")
            else:
                st.caption(f"📊 一般ユーザー利用: 本日 {current_count + 1} 回目")

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

                    # SQLite保存
                    conn = get_db_connection()
                    c = conn.cursor()
                    temp_title = response[:10] + "..."
                    c.execute('INSERT INTO stories (title, content, created_at) VALUES (?, ?, ?)', 
                                (temp_title, response, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                    conn.commit()
                    conn.close()

                    # 【重要】成功した時だけ、実際にJSONのカウントを増やす！
                    if not is_admin_now:
                        # ログを読み込んでカウントを+1して保存する処理
                        with open(LOG_FILE, "r") as f:
                            data = json.load(f)
                        data["count"] += 1
                        with open(LOG_FILE, "w") as f:
                            json.dump(data, f)

                    st.rerun()
                except Exception as e:
                    st.error(f"エラーが発生しました: {str(e)}")

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