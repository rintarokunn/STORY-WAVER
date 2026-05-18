import streamlit as st
from datetime import datetime
# 自作ファイルから道具を呼び出す！
from storywaver_core import get_db_cost, get_db_connection
from api_client import ask_ai
from storywaver_core import StoryWaverCore

# ページ設定は一番最初に1回だけ！
st.set_page_config(page_title="StoryWaver", page_icon="📖", layout="wide")

# サイドバー：認証とコスト表示
with st.sidebar:
    st.subheader("🔑 管理者のみ無制限の合言葉")
    input_key = st.text_input("合言葉を入力してください", type="password")
    
    st.header("💰 OpenAI APIキーの使用限度額")
    current_cost = get_db_cost()
    limit = 0.5
    st.metric("本日の利用額", f"${current_cost:.4f}", delta=f"上限まで残り ${limit - current_cost:.4f}")
    st.progress(min(current_cost / limit, 1.0))

# ユーザー判定
is_admin = (input_key == st.secrets["ADMIN_PASSWORD"])
user_id = "my_name" if is_admin else "guest"

st.title("StoryWaver - AIと一緒に物語を創る")
st.caption("AIと対話しながら物語を創作するためのツールです。")
st.divider()

# チャット履歴の初期化
if "messages" not in st.session_state:
    st.session_state.messages = []

# 過去のチャット表示
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 保存された物語の読み込み
conn = get_db_connection()
c = conn.cursor()
c.execute("SELECT * FROM stories ORDER BY created_at DESC")
stories = c.fetchall()
conn.close()

# 保存済み物語の表示
st.subheader("📚 これまでに紡いだ物語")
if stories:
    for story in stories:
        with st.expander(f"{story[1]} - {story[3]}"):
            st.write(story[2] if story[2] else "（中身はまだありません）")
else:
    st.info("まだ保存された物語はありません。")

# チャット入力
if prompt := st.chat_input("物語のアイデアを教えてください..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("物語を紡いでいます..."):
            # api_clientの関数を呼び出す！
            response = ask_ai(user_id, st.session_state.messages)
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

            # DBに保存
            conn = get_db_connection()
            c = conn.cursor()
            temp_title = (prompt[:27] + "...") if len(prompt) > 30 else prompt
            c.execute("INSERT INTO stories (title, content, created_at) VALUES (?, ?, ?)",
                        (temp_title, response, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()
            conn.close()
            st.success("物語を保存しました！")

core = StoryWaverCore()

st.header("🎭 キャラクター作成")

# 入力フォーム
with st.form("create_character_form"):
    name = st.text_input("キャラ名")
    personality = st.text_area("性格")
    appearance = st.text_area("外見")
    voice = st.text_input("声の特徴")
    speaking_style = st.text_input("話し方")
    background = st.text_area("背景設定")
    relation = st.text_input("主人公との関係性")
    memo = st.text_area("メモ")

    submitted = st.form_submit_button("キャラを作成する")

# ボタンが押されたら Core に渡す
if submitted:
    # 入力されたデータを「一通の封筒（辞書）」にまとめる
    char_data = {
        "name": name,
        "personality": personality,
        "appearance": appearance,
        "voice": voice,
        "speaking_style": speaking_style,
        "background": background,
        "relation": relation,
        "memo": memo
    }
    # Coreには「この封筒、お願い！」と渡すだけ
    result = core.create_character(char_data)
    if result=="成功":
        st.success(f"キャラ「{name}」を作成しました")
    else:
        st.error("キャラの作成に失敗しました")