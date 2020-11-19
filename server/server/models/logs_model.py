from models import database
from models import table_name
from models.database import share_redis_game as share_connect
from utils import utils

EMOTION_TO_SELF = 1
EMOTION_TO_OTHER = 5

MAX_DATABASE_PLAYER = 10


def get_player_attr_by_seat_index(seats, idx,is_fangpao=False,ppseatid=0):
    seat = None
    if len(seats) >= idx + 1:
        seat = seats[idx]
    if not seat:
        return 0, "", 0, ""
    from games.anhua_paohuzi import player
    if isinstance(seat,player.Player):
        return seat.uid, seat.nick_name, seat.rod_data[seat.round_index]['score'], seat.avatar
    from games.fang_pao_fa import player
    if isinstance(seat,player.Player):
        if is_fangpao and seat.seat_id == ppseatid:
            return seat.uid, seat.nick_name, -seat.other_all_huxi_list[seat.round_index-1], seat.avatar
        else:
            return seat.uid, seat.nick_name, seat.other_all_huxi_list[seat.round_index-1], seat.avatar
    return seat.uid, seat.nick_name, seat.score, seat.avatar
def get_player_attr_by_seat_index1(seats, idx):
    seat = None
    if len(seats) >= idx + 1:
        seat = seats[idx]
    if not seat:
        return 0, "", 0, ""
    from games.anhua_paohuzi import player
    # if isinstance(seat,player.Player):
    #     return seat.uid, seat.nick_name, seat.rod_data[seat.round_index]['score'], seat.avatar
    return seat.uid, seat.nick_name, seat.score, seat.avatar

def insert_round_log(record_id: str, seq, game_type, seats, round_details=list([]),hz=False,is_fangpao=False,ppseatid=0):
    sql = "INSERT INTO `{0}` SET record_id='{1}', seq='{2}', game_type='{3}', " \
          "score1='{4}', score2='{5}', score3='{6}', " \
          "score4='{7}', score5='{8}', score6='{9}', " \
          "score7='{10}', score8='{11}', score9='{12}', score10='{13}'," \
          "finish_time='{14}',round_detail='{15}'"
    record_id = database.escape(record_id)
    scores = []
    for i in range(MAX_DATABASE_PLAYER):
        _, _, score, _ = get_player_attr_by_seat_index(seats, i + 1,is_fangpao,ppseatid)
        scores.append(score)
    from games.anhua_paohuzi import player
    maxscore = max(scores)
    player1 = None
    for p in seats:
        if not p:
            continue
        player1 = p
        break
    if isinstance(player1,player.Player):
        for i,j in enumerate(scores):
            if maxscore > j:
                scores[i] = -maxscore
                break
    from games.fang_pao_fa import player
    if isinstance(player1,player.Player):
        for i,j in enumerate(scores):
            if i > len(seats)-1:
                break
            if maxscore == j and hz:
                scores[i] = -maxscore
                break
    sql = sql.format(table_name.round_logs, record_id, seq, game_type,
                     scores[0],
                     scores[1],
                     scores[2],
                     scores[3],
                     scores[4],
                     scores[5],
                     scores[6],
                     scores[7],
                     scores[8],
                     scores[9],
                     utils.timestamp(),
                     utils.json_encode(round_details)
                     )
    return database.share_db_logs().execute_lastrowid(sql)


def insert_room_log(record_id: str, room_id, game_type, seats, owner: int, round_count: int,
                    rule_details, club_id=-1, game_finish_data="", group_id='-1', diamond=0, match_type=0, floor=-1,
                    sub_floor=-1, match_config='',union_id=-1):
    if not seats or len(seats) <= 1:
        return 0
    sql = "INSERT INTO `{0}` SET record_id='{1}', room_id='{2}', game_type='{3}', " \
          "{4}" \
          "finish_time='{5}', owner='{6}', round_count='{7}', " \
          "club_id='{8}', rule_details = '{9}',game_finish_data='{10}'," \
          "group_id='{11}',diamond={12},match_type={13},floor={14},sub_floor={15},match_config='{16}',union_id='{17}'"
    record_id = database.escape(record_id)

    user_info_template = "uid{0}='{1}', name{0}='{2}', score{0}='{3}', avatar{0}='{4}',"
    user_info_str = ""
    for i in range(MAX_DATABASE_PLAYER):
        seat_index = i + 1
        uid, name, score, avatar = get_player_attr_by_seat_index1(seats, seat_index)
        user_info_str += user_info_template.format(seat_index, uid, database.escape(name), score, avatar)

    sql = sql.format(table_name.room_logs, record_id, room_id, game_type,
                     user_info_str,
                     utils.timestamp(),
                     int(owner), int(round_count), club_id, utils.json_encode(rule_details),
                     utils.json_encode(game_finish_data),
                     group_id, diamond, match_type, floor, sub_floor, utils.json_encode(match_config), union_id)
    return database.share_db_logs().execute_lastrowid(sql)


def add_round_review_log(data, max_nums=10000):
    if not share_connect():
        return 0
    key = "round_review_logs"
    share_connect().lpush(key, utils.json_encode(data))
    share_connect().ltrim(key, 0, max_nums)


def add_emotion_log(from_uid, to_uid, emotion_id, emotion_type):
    sql = "INSERT INTO `{0}` SET uid={1}, refer_id={2}, display_diamond={3}, actual_diamond={4}, emotion_id={5}," \
          "time = {6}, type={7}"
    sql = sql.format(table_name.emotion_logs, from_uid, to_uid, 1, 0, int(emotion_id), utils.timestamp(),
                     int(emotion_type))
    return database.share_db_logs().execute_lastrowid(sql)


def add_diamonds_log(uid, diamonds, reason_id, step, left_diamonds, refer_uid=0, refer_nick_name='', memo='',
                     record_id=''):
    """插入钻石日志"""
    if not uid or not diamonds or not reason_id:
        return 0

    time = utils.timestamp()
    inserts = {
        'uid': int(uid),
        'refer_uid': int(refer_uid),
        'refer_nick_name': database.escape(refer_nick_name),
        'diamonds': int(diamonds),
        'reason_id': int(reason_id),
        'left_diamonds': int(left_diamonds),
        'time': time,
        'memo': database.escape(memo),
        'step': int(step),
        'record_id': record_id,
    }
    sql = database.make_insert(table_name.diamond_logs, inserts)
    return database.share_db_logs().execute(sql)


def add_la_jiao_dou_log(uid, la_jiao_dou, reason_id, step, left_la_jiao_dou, refer_uid=0, refer_nick_name='', memo='',
                        record_id=''):
    """插入辣椒豆日志"""
    if not uid or not la_jiao_dou or not reason_id:
        return 0

    time = utils.timestamp()
    inserts = {
        'uid': int(uid),
        'refer_uid': int(refer_uid),
        'refer_nick_name': database.escape(refer_nick_name),
        'la_jiao_dou': int(la_jiao_dou),
        'reason_id': int(reason_id),
        'left_la_jiao_dou': int(left_la_jiao_dou),
        'time': time,
        'memo': database.escape(memo),
        'step': int(step),
        'record_id': record_id,
    }
    sql = database.make_insert(table_name.la_jiao_dou_logs, inserts)
    return database.share_db_logs().execute(sql)


def add_club_winner_log(record_id, club_id, datas, score, time, game_type, rule_details, room_id, is_read=0):
    sql = "INSERT INTO `{0}` SET record_id='{1}', club_id={2}, players={3}, score={4}, time={5}," \
          "game_type={6}, rule_details='{7}',room_id={8},is_read={9}"
    sql = sql.format(table_name.club_winner, record_id, club_id, datas, score, time, game_type, rule_details, room_id,
                     is_read)
    return database.share_db_logs().execute_lastrowid(sql)


def add_debug_log(record_id, seq, table_id, nickname=""):
    time = utils.timestamp()
    sql = f"INSERT INTO `debug_log` SET record_id='{record_id}',table_id={table_id},seq={seq}, " \
        f"nickname='{nickname}',time={time}"
    return database.share_db_logs().execute_lastrowid(sql)


def modify_redis_data(table_id, data):
    if not share_connect():
        return 0
    share_connect().set(f"table_{table_id}", utils.json_encode(data))


def delete_redis_data(table_id):
    if not share_connect():
        return 0
    share_connect().delete(f"table_{table_id}")


def add_club_diamonds_log(uid, diamond, club_id, record_id, la_jiao_dou=0):
    """插入俱乐部钻石日志"""
    time = utils.timestamp()
    inserts = {
        'uid': int(uid),
        'diamonds': int(diamond),
        'club_id': club_id,
        'time': time,
        'la_jiao_dou': int(la_jiao_dou),
        'record_id': record_id,
    }
    sql = database.make_insert(table_name.club_diamond_logs, inserts)
    return database.share_db_logs().execute(sql)


# 添加俱乐部钻石消耗记录
def add_union_diamonds_log(uid, diamond, union_id, record_id):
    time = utils.timestamp()
    inserts = {
        'uid': int(uid),
        'diamonds': int(diamond),
        'union_id': union_id,
        'time': time,
        'record_id': record_id,
    }
    sql = database.make_insert("union_diamond_logs", inserts)
    return database.share_db_logs().execute(sql)


def add_player_game_info(record_id, uid, score, game_type):
    sql = f"INSERT INTO `room_user` SET record_id='{record_id}',uid='{uid}',score='{score}', game_type='{game_type}'"
    return database.share_db_logs().execute(sql)


# 推送房间税收信息
def push_union_romm_tax(data):
    if not share_connect():
        return 0
    key = "union_room_profit"
    share_connect().lpush(key, utils.json_encode(data))

