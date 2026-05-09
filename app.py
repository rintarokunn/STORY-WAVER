# StoryWaver - AIと一緒に物語を創る

#ストリームリットのライブラリを使う
import streamlit as st 
#SQLiteを使うためのライブラリ
import sqlite3
#日付と時間を扱うためのライブラリ
import datetime
#openaiを使うためのライブラリ
from openai import OpenAI 


# OpenAIクライアント初期化
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])


#ここから先は物語を格納しておくためのデータベースの作成です。

#データベースとつなげるための関数を定義します。これで、データベースにアクセスするためのコードを簡単に再利用できるようになります。
def get_db_connection(): 
#SQLを使ってデータベースに接続します。ストーリウェーバーという名前のノートを指定。
#プログラムが一度にこなす仕事の並びを、スレッドという。スレッドは、同時に複数の仕事をこなすことができますが、SQLiteは同時に複数のスレッドからアクセスすることができません。check_same_thread=Falseを指定することで、複数のスレッドから同じデータベース接続を使用できるようになります。    
#Falseにすることで、同じスレッドかどうかのチェックをしない。専門職がチェックして、資格持ってないですと言うのではなく、一般の人が交代でノートに書き込めるイメージです。
    conn = sqlite3.connect('storywaver.db', check_same_thread=False) 
#上記でつながったパイプをそとに出すためのコードです。これで、他の関数からもこのデータベースにアクセスできるようになります。
    return conn 

#データベースの関数を定義します。これで、データベースに必要なテーブルを作成することができます。CREATE TABLE IF NOT EXISTSは、テーブルがすでに存在する場合は何もしないという意味です。これで、プログラムを何度も実行してもエラーにならないようになります。
#全体で言うとここは、棚を作る手順書です、実際に棚はinit_db() から作られていきます。
def init_db():  
    #先ほど定義した、データベースとつながったパイプを使います。
    conn = get_db_connection() 
    #カーソル。先ほど定義したデータベースというパイプがあります。このパイプの中のノートに書いたり、棚からデータを出したりする作業員。Cで呼ぶことができる
    c = conn.cursor() 
    #実際にCに命令（エグゼキュート）するところ。ノートに書いたり、棚から出したりする。
    c.execute(''' CREATE TABLE IF NOT EXISTS stories ( 
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            title TEXT NOT NULL, 
            content TEXT, 
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP 
            ) ''')
    #カーソルがやったことをノート（storywaver.db）に刻み込む
    conn.commit() 
    #ノート（storywaver.db）を閉じる
    conn.close()

#データベースの関数です。上記の手順書の通りに棚を作れとスイッチを押しています。
init_db() 

# ========================================== # Streamlit UI （ユーザーインターフェース）画面作ってます# ========================================== 
# ページの設定。タイトル、アイコン、レイアウトを指定しています。これで、ブラウザのタブにタイトルとアイコンが表示され、ページ全体が広く使えるようになります。
st.set_page_config(page_title="StoryWaver", page_icon="📖", layout="wide") 
#タイトル
st.title("StoryWaver - AIと一緒に物語を創る") 
#このwebアプリの説明
st.caption("AIと対話しながら物語を創作するためのツールです。") 
#区切り線
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