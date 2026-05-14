#-------------------------------キャラクター設定管理------------------------------------------------

from character_model import CharacterModel
from storywaver_core import get_db_connection

class character_model:
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

# character_manager.py

class CharacterManager:

    def create(self, model: CharacterModel):
        conn = get_db_connection()
        c = conn.cursor()

        c.execute('''
            INSERT INTO characters 
            (name, personality, appearance, voice, speaking_style, background, relation, memo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            model.name,
            model.personality,
            model.appearance,
            model.voice,
            model.speaking_style,
            model.background,
            model.relation,
            model.memo
        ))

        conn.commit()
        conn.close()

    def get_all(self):
        conn = get_db_connection()
        c = conn.cursor()

        c.execute("SELECT * FROM characters ORDER BY created_at DESC")
        rows = c.fetchall()
        conn.close()

        return [CharacterModel(*row) for row in rows]

    def get(self, char_id):
        conn = get_db_connection()
        c = conn.cursor()

        c.execute("SELECT * FROM characters WHERE id = ?", (char_id,))
        row = c.fetchone()
        conn.close()

        return CharacterModel(*row) if row else None

    def update(self, char_id, field, value):
        conn = get_db_connection()
        c = conn.cursor()

        c.execute(f"UPDATE characters SET {field} = ? WHERE id = ?", (value, char_id))
        conn.commit()
        conn.close()

    def delete(self, char_id):
        conn = get_db_connection()
        c = conn.cursor()

        c.execute("DELETE FROM characters WHERE id = ?", (char_id,))
        conn.commit()
        conn.close()

