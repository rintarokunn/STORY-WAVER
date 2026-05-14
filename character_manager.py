#-------------------------------キャラクター設定管理------------------------------------------------
class CharacterManager:
    def __init__(
        self,
        id=None,
        name="",
        personality="",
        appearance="",
        voice="",
        speaking_style="",
        background="",
        relation="",
        memo=""
    ):
        self.id = id
        self.name = name
        self.personality = personality
        self.appearance = appearance
        self.voice = voice
        self.speaking_style = speaking_style
        self.background = background
        self.relation = relation
        self.memo = memo

def create(self, char_data):
        # ここに、実際にDBのテーブルに保存するSQLコードを書くんだよ
        # core.py から「封筒（char_data）」が届く想定だね！
        print(f"データベースに {char_data['name']} を保存する処理を開始します...")
        
        # 本来はここに conn = sqlite3.connect... みたいな保存処理が入る
        return True
