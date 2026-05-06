import streamlit as st

import sqlite3

from datetime import datetime

from openai import OpenAI

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

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



st.subheader("AIと物語を創ろう")



# セッション状態の初期化

if "messages" not in st.session_state:

    st.session_state.messages = []



# これまでの会話履歴を表示

for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        st.markdown(message["content"])



# ユーザー入力

if prompt := st.chat_input("物語のアイデアや設定を教えてください..."):

    # ユーザーのメッセージを追加

    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):

        st.markdown(prompt)



    # AIの返事（★ここを本物のAIに差し替え！）

    with st.chat_message("assistant"):

        with st.spinner("アニちゃんが考え中..."):

            try:

                # 本物のOpenAIを呼び出す命令

                response = client.chat.completions.create(

                    model="gpt-3.5-turbo",

                    messages=[{"role": "user", "content": prompt}],

                    temperature=0.8,

                )

                response = response.choices[0].message.content

            except Exception as e:



                response = f"エラーだよ！: {str(e)}"


            st.markdown(response)

# ==================== 会話ログ保存機能 ====================
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

# ユーザー入力部分（既存の if prompt := st.chat_input の部分を置き換え）
if prompt := st.chat_input("物語のアイデアや設定を教えてください..."):
    # プロジェクトIDは一旦仮で1固定（後でプロジェクト機能作ったら変更）
    project_id = 1
    
    # ユーザーのメッセージを保存
    save_message(project_id, "user", prompt)
    with st.chat_message("user"):
        st.markdown(prompt)

    # AIの返事
    with st.chat_message("assistant"):
        with st.spinner("考え中..."):
            # ここは OpenAI 呼び出しの response を使うよ
            try:
                response_data = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.8,
                )
                response = response_data.choices[0].message.content
                st.markdown(response)
                
                # AIの返事も保存
                save_message(project_id, "assistant", response)
            except Exception as e:
                st.error(f"エラーだよ！: {str(e)}")