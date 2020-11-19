from models import table_name
from models.database import share_db


def get_room_config(game_id):
    if not game_id:
        return 0
    sql = "SELECT * FROM `{0}` WHERE id={1} LIMIT 1 ".format(table_name.room_config, game_id)
    return share_db().get(sql)
