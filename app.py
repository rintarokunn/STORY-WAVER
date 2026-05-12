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

# ========================================== # チャット表示 # ==========================================
#もしセッションステートにメッセージがない状態であれば
if "messages" not in st.session_state: 
#メッセージをいれておくリストを作る。
    st.session_state.messages = []
# ↓これが画面に出れば、初期化は通ってる！
    st.write("デバッグ：今、空のリストを作ったよ！")

# 過去のチャット表示
#僕らが入れていくメッセージをst.session_state.messagesリストに格納していく。
for msg in st.session_state.messages: 
#取り出したメッセージの役割を見て、ユーザーかAIかの吹き出しを準備する
    with st.chat_message(msg["role"]): 
#メッセージの内容を表示する
        st.markdown(msg["content"])

# ========================================== # チャット入力 # ========================================== 

if prompt := st.chat_input("物語のアイデアや設定を教えてください..."): 
# ユーザー入力表示
    st.session_state.messages.append({"role": "user", "content": prompt}) 
#チャットメッセージにはユーザーの吹き出しを作る
with st.chat_message("user"): 
    st.markdown(prompt) 
# AIが作られた吹き出しの中でAIの回答を表示する
with st.chat_message("assistant"): 
#AIが物語を紡いでいる間、スピナーを表示する。ユーザーに待ってもらうためのアニメーション
    with st.spinner("物語を紡いでいます..."): 
#try exceptは、エラーが発生した時の処理を定義してってこと。tryはこの作業をとりあえずやってみて、exceptは止まらずにこっちの予備プランを実行してねって意味。
        try:
# プログラムの最初の方（def main(): の中など）に書く
#client.chat.completionsを使い、AIに物語を作ってもらう！
# AIを呼ぶ直前にこれを書いて、中身があるかチェックする
            if len(st.session_state.messages) > 0:
# ここに response_data = client.chat.completions.create(...) を入れる
                response_data = client.chat.completions.create( 
                model="gpt-3.5-turbo", 
                messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages], 
#AIが創造性があるかつ、真面目な側面も持つようになる
                temperature=0.8, 
                ) 
#AIが一番自信がある（確率が高い）と判断した、１番目の回答を取得する。
                response = response_data.choices[0].message.content 
#吹き出しを作る            
                st.markdown(response) 
#AIがセッションステートメントから回答を取り出し、AIの吹き出しを作る
                st.session_state.messages.append({"role": "assistant", "content": response}) 
            
#---------物語を一生消えないノート（データベース）に保存---------------------------------

#get_db_connection()にコネクトして、データベースにアクセスする
            conn = get_db_connection() 
#カーソル君を作る
            c = conn.cursor() 
#物語のタイトルを決める。ユーザーのプロンプトをタイトルにするけど、長すぎると見づらいから、30文字以上なら「...」をつけて短くする。
            temp_title = (prompt+ "...") if len(prompt) > 30 else prompt 
#日付や時間も一緒に、タイトルとかと入力する。
            c.execute(''' INSERT INTO stories (title, content, created_at) VALUES (?, ?, ?) ''',
                    (temp_title, response, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))) 
#カーソルがやったことをノートに刻み込む
            conn.commit()
#ノートを閉じる
            conn.close() 
#ユーザーに物語が保存されたことを知らせる
            st.success("物語を保存しました！") 
#メッセージをリセットし、前の物語と混ざらないようにする。
            st.rerun()   

#exceptは「もし失敗したら、ここを実行して！」という合図。
#Exceptionは、すべてのエラーをキャッチするための一般的なエラークラスです。つまり、何か問題が起きたときに、その問題を捕まえて、ユーザーにエラーメッセージを表示するためのコードです。
#as eとすることによって、起きたエラーをeという変数の箱に保存してくれる。これでエラーの具体的な理由が表示されるようになる
        except Exception as e: 

            st.error(f"エラーが発生しました: {str(e)}") 

# ========================================== # 保存済み物語の表示 # ========================================== 

#区切り線
st.divider()
st.subheader("紡いだ物語") 
conn = get_db_connection() 
#すでに保存されている物語データベースを取り出す。
stories = conn.execute('SELECT * FROM stories ORDER BY created_at DESC').fetchall()
#conn.comittoは、データベースに対する変更内容を保存するために使っていたのであり、今は物語をデータベースから取り出すだけの処理なのでいらない。
conn.close()
#python基本文法の辞書の仕組みを使って、物語の要素ごとにそれに該当する番号を指定して取り出して表示するところ。例えば、story[1]はタイトル、story[2]は内容、story[3]は作成日時を表す。
#それ以外なら、まだ保存されていませんと表示する
#withは、
if stories: 
    for story in stories: 
#withは、画面に表示したい場所をまとめてくくってくれる！
        with st.expander(f"{story[1]} - {story[3]}"):
            st.write(story[2] if story[2] else "（中身はまだありません）") 
        st.caption(f"ID: {story[0]}") 
else: st.info("まだ保存された物語はありません。最初の物語を書き上げよう！") 