from models import table_name
from utils import utils


def transfer_dou(conn, club_id, uid, count):
    sql = f"UPDATE `club_user` SET score=score+{count},add_score=add_score+{count},add_time={utils.timestamp()} " \
          f"WHERE club_id={club_id} and uid={uid}"
    return conn.execute_rowcount(sql)


def write_transfer_dou_log(conn_logs, club_id, uid, before_count, count, reason, oper_uid=-1):
    if not conn_logs or not club_id or not uid or not count:
        return 0
    sql = f"INSERT INTO `club_send_log` SET club_id={club_id},uid={uid},before_count={before_count}" \
          f",count={count},time={utils.timestamp()},reason={reason},operation_uid={oper_uid}"
    return conn_logs.execute_rowcount(sql)


def reduce_player_dou(conn, club_id, uid, count):
    sql = f"UPDATE `club_user` SET score=score-{count},minus_score=minus_score+{count},minus_time={utils.timestamp()} " \
          f"WHERE club_id={club_id} and uid={uid}"
    return conn.execute_rowcount(sql)


def get_total_dou_by_uid_and_owner_id(conn, owner_id, uid):
    sql = "SELECT SUM(score) as score from `{0}` where club_owner = {1} and uid = {2}".format(table_name.club_user,
                                                                                              owner_id, uid)
    return conn.get(sql)


def get_dou_by_uid_and_club_id(conn, club_id, uid):
    sql = f"SELECT score,lock_score from `club_user` where club_id = {club_id} and uid = {uid}"
    return conn.get(sql)


def get_recharge_config(conn, Currencytype, Configid):
    sql = f"select Id,Configid,Centers,Title,Serialnumber,Numbers,Imgpath,Phonetype,Gifts,Prices" \
          f",Currencytype,LimitCount " \
          f"from configdetailed where Configid in (3,4,6) order by Prices asc"
    return conn.query(sql)


def get_item_by_id(conn, item_id):
    sql = f"select Id,Configid,Centers,Isservice,Title,Serialnumber,Numbers,Imgpath,Phonetype,Gifts,Prices" \
          f",Currencytype, LimitCount " \
          f"from configdetailed where id = {item_id}"
    return conn.get(sql)


def insert_score_item(conn, integral_num, product_id, uid, phone, numbers, real_name, receiving_address, status):
    sql = f"INSERT INTO `integralorder` SET integral_num='{integral_num}',product_id={product_id},uid={uid}" \
          f",phone='{phone}',states={status}," \
          f"numbers={numbers},creation_time=now(),real_name='{real_name}',receiving_address='{receiving_address}'"

    return conn.execute_rowcount(sql)


def get_exchanged_item_count(conn, uid, product_id):
    sql = f"SELECT count(*) as count FROM `integralorder` WHERE uid={uid} AND product_id={product_id}"

    data = conn.get(sql)
    if data:
        return data['count']
    return 0
