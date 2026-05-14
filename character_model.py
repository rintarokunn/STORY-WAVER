#-------------------------------キャラクター設定管理------------------------------------------------
from character_model import CharacterModel
from storywaver_core import get_db_connection


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
