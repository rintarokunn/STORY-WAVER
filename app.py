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

# ==========================================
# 3. チャット画面と自動保存の実装
# ==========================================
if prompt := st.chat_input("物語のアイデアや設定を教えてください…"):

# --- 1. ここらへんに管理者ログインを置く（サイドバー） ---
admin_key = st.sidebar.text_input("管理者コード", type="password")
is_admin = (admin_key == st.secrets.get("ADMIN_PASSWORD", "test"))

# --- 2. カウントの初期化 ---
if "chat_count" not in st.session_state:
    st.session_state.chat_count = 0

# --- 3. ここが本番！チャット入力の場所 ---
if prompt := st.chat_input("物語のアイデアや設定を教えてください..."):
    
    # 【お財布ガード】管理者じゃなくて、回数制限を超えていたら止める！
    if not is_admin and st.session_state.chat_count >= 3:
        st.error("デモ版の回数制限（3回）に達しました。リロードして最初から試してね！")
    else:
        # ここから下が、今までの「AIに送る処理」や「メッセージ表示」のコード
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # AIの応答処理が続く...
        # 最後にカウントを増やすのを忘れずに！
        if not is_admin:
            st.session_state.chat_count += 1    

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("考え中…"):
            try:
                # ★ここでAIに応答を求める（アンタが言った大事な設定を全部入れたよ！）
                response_data = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    # これまでの会話履歴を全部渡す [cite: 107]
                    messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
                    # クリエイティブな回答にするための設定
                    temperature=0.8,
                )
                response = response_data.choices[0].message.content
                st.markdown(response)
                # AIの返答を表示用リストに追加 
                st.session_state.messages.append({"role": "assistant", "content": response})

                # 【重要！】ここで物語（storiesテーブル）に自動保存する [c: 36]
                conn = get_db_connection() 
                c = conn.cursor() 
                
                # タイトルはAIの返答の最初の10文字を仮で使う
                temp_title = response[:10] + "..."
                # 新しい stories テーブルに保存 
                c.execute('''
                    INSERT INTO stories (title, content, created_at)
                    VALUES (?, ?, ?)
                ''', (temp_title, response, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit() 
                conn.close()
                
                # 保存できたら画面を更新して「紡いだ物語」リストに反映させる 
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