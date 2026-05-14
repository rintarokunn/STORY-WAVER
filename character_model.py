#-------------------------------キャラクター設定管理------------------------------------------------
from character_model import CharacterModel
from storywaver_core import get_db_connection

class CharacterModel:
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


