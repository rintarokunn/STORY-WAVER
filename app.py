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
    st.subheader("🔑 無制限に使用できるようになる合言葉")
    input_key = st.text_input("合言葉を入力してください", type="password")
    
    st.header("💰 OpenAI APIの使用限度額")
    current_cost = get_db_cost()
    limit = 0.5
    st.metric("本日の利用額", f"${current_cost:.4f}", delta=f"上限まで残り ${limit - current_cost:.4f}")
    st.progress(min(current_cost / limit, 1.0))

#------#このアプリの説明－－－－－－－

# 畳み込み（Expander）を使って、画面をすっきりさせつつ技術アピール！
with st.expander("📊 本アプリケーションの機能説明はここを見てください！"):
    st.markdown("""
    ### 🏗️ 主要な処理の解説
    本アプリは、単なるUIの表示にとどまらず、実務運用を想定したバックエンド処理をPythonおよびStreamlitで実装しています。

    #### 1. セキュリティとコスト管理（サイドバー領域）
    * **環境変数の秘匿化**: `st.secrets` を活用し、管理者パスワードなどの機密情報を安全に管理。
    * **APIコストの可視化**: 自作の `storywaver_core` モジュールを介してDBから当日のOpenAI API消費額をリアルタイムに取得。`st.metric` と `st.progress` を用いて、上限設定に対する使用率をユーザーに可視化しています。

    #### 2. チャット駆動型の状態管理と非同期風処理
    * **状態維持（Session State）**: ページがリロードされても対話履歴が消えないよう、`st.session_state.messages` を用いてメモリ上にチャットログを保持。
    * **UXの最適化**: AIの応答待ち時間中、ユーザーにストレスを与えないよう `st.spinner` によるローディングアニメーションを制御しています。

    #### 3. データベース（SQLite3）による永続化
    * **データ連携**: 物語が生成された瞬間、プロンプトの文字数制限処理を行った上で、`INSERT` 文によりローカルDBへ自動保存。
    * **動的コンポーネント抽出**: `st.expander` をループで回し、DBから取得した過去の全創作ログを最新順にアコーディオン形式で動かせるよう設計しています。

    #### 4. オブジェクト指向によるモジュール化
    * **分離**: キャラクター作成フォーム（`st.form`）から送信されたデータは、一度ディクショナリ（辞書型）に内包。その後、別ファイルで定義した `StoryWaverCore` クラスのインスタンスへカプセル化された状態で引き渡され、ビジネスロジックを処理する設計（疎結合）にしています。
    * **状況、未完成。今後作っていこうと考えている**: 
                """)


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


