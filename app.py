import streamlit as st
import sqlite3
from datetime import datetime
from openai import OpenAI

# OpenAIクライアントの初期化
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# ==========================================
# 1. データベース関数（記憶を司る部分）
# ==========================================
def get_db_connection():
    return sqlite3.connect('storywaver.db', check_same_thread=False)

def save_message(project_id, role, content):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO conversations (project_id, role, content)
        VALUES (?, ?, ?)
    ''', (project_id, role, content))
    conn.commit()
    conn.close()

# ==========================================
# 2. UI設定
# ==========================================
st.set_page_config(page_title="StoryWaver", page_icon="✍️")
st.title("StoryWaver - 記憶を持つAI")

# セッション状態の初期化
if "messages" not in st.session_state:
    st.session_state.messages = []

# 会話履歴の表示
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ==========================================
# 3. チャット処理（保存機能付き）
# ==========================================
if prompt := st.chat_input("物語のアイデアや設定を教えてください..."):
    # 1. ユーザーの入力を表示＆保存
    project_id = 1 
    st.session_state.messages.append({"role": "user", "content": prompt})
    save_message(project_id, "user", prompt) # DBへ保存！
    
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. AIの返答生成
    with st.chat_message("assistant"):
        with st.spinner("記憶に書き込み中..."):
            try:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.8,
                )
                res_text = response.choices[0].message.content
                
                # 3. AIの返答を表示＆保存
                st.markdown(res_text)
                st.session_state.messages.append({"role": "assistant", "content": res_text})
                save_message(project_id, "assistant", res_text) # DBへ保存！
                
            except Exception as e:
                st.error(f"エラーだよ！: {str(e)}")