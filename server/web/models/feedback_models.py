def insert_feedback(conn, uid, phone, content, now):
    if not conn:
        return 0
    sql = f"INSERT INTO `user_feedback` SET uid={uid},phone='{phone}',content='{content}',time={now}"
    return conn.execute_rowcount(sql)
