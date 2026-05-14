#-------------------------------OpenAI API呼び出し------------------------------------------------
from openai import OpenAI
import streamlit as st
# coreから必要な道具をインポート
from storywaver_core import is_allowed_before_api, save_new_cost

# クライアントは一箇所で定義
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def ask_ai(user_id, messages):
    # 金額チェック
    if not is_allowed_before_api(user_id):
        return "⚠️ 本日の上限額に達したため、物語を紡ぐことができません。"

    try:
        response_data = client.chat.completions.create(
            model="gpt-3.5-turbo", # または "gpt-4o-mini"
            messages=messages,
            temperature=0.8,
        )
        # 料金を保存
        save_new_cost(user_id, response_data.usage)
        return response_data.choices[0].message.content
    except Exception as e:
        return f"エラーが発生しました: {str(e)}"