import streamlit as st 
import sqlite3
import datetime
from openai import OpenAI 

# OpenAIクライアント初期化
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# ========================================== # データベース設定 # ==========================================
def get_db_connection(): 
    conn = sqlite3.connect('storywaver.db', check_same_thread=False) 
    return conn 

def init_db(): 
    conn = get_db_connection() 
    c = conn.cursor() 
    c.execute(''' CREATE TABLE IF NOT EXISTS stories ( id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, content TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP ) ''')
    conn.commit() 
    conn.close()

init_db() 
# ========================================== # Streamlit UI # ========================================== 
st.set_page_config(page_title="StoryWaver", page_icon="📖", layout="wide") 
st.title("StoryWaver - AIと一緒に物語を創る") 
st.caption("AIと対話しながら物語を創作するためのツールです。") 
st.divider()
# 管理者設定 
ADMIN_KEY = st.secrets.get("ADMIN_PASSWORD", "admin123")
with st.sidebar: 
    st.subheader("管理者設定") 
user_key = st.text_input("管理者コード", type="password", key="admin_key") 
is_admin = (user_key == ADMIN_KEY)
if is_admin: st.success("管理者モード有効")
else: st.info("一般ユーザーとして利用中") 
# チャット履歴初期化
if "messages" not in st.session_state: 
    st.session_state.messages = []
# 過去のチャット表示
for msg in st.session_state.messages: 
    with st.chat_message(msg["role"]): 
        st.markdown(msg["content"])
# ========================================== # チャット入力 # ========================================== 
if prompt := st.chat_input("物語のアイデアや設定を教えてください..."): 
# ユーザー入力表示
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
            # 物語をデータベースに保存 
            conn = get_db_connection() 
            c = conn.cursor() 
            temp_title = (prompt+ "...") if len(prompt) > 30 else prompt 
            c.execute(''' INSERT INTO stories (title, content, created_at) VALUES (?, ?, ?) ''', 
                (temp_title, response, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))) 
            conn.commit() 
            conn.close() 
            st.success("物語を保存しました！") 
            st.rerun() 
        except Exception as e: 
            st.error(f"エラーが発生しました: {str(e)}") 
# ========================================== # 保存済み物語の表示 # ========================================== 
st.divider()
st.subheader("これまでに紡いだ物語") 
conn = get_db_connection() 
stories = conn.execute('SELECT * FROM stories ORDER BY created_at DESC').fetchall()
conn.close()
if stories: 
    for story in stories: 
        with st.expander(f"{story[1]} - {story[3]}"):
            st.write(story[2] if story[2] else "（中身はまだありません）") 
        st.caption(f"ID: {story[0]}") 
else: st.info("まだ保存された物語はありません。最初の物語を書き上げよう！") 