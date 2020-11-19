def get_charge_by_uid_and_level(conn, uid, level):
    if level == 2:
        col_name = 'invite_uid_2'
    elif level == 3:
        col_name = 'invite_uid_1'

    sql = f"SELECT * FROM players where {col_name}={uid}"
    players = conn.query(sql)
    data = []
    for i in players:
        sql = f"SELECT uid,nick_name,amount,order_time FROM `payment` WHERE uid={i['uid']} and order_time >= " \
              f"{i['bind_time']}"
        charge_data = conn.query(sql)
        for c in charge_data:
            data.append(c)
    return data
