from models import table_name


def get_lottery_list(conn):
    """获取所有的红包配置列表"""
    sql = "SELECT * FROM `{0}` LIMIT 20"
    sql = sql.format(table_name.lottery)
    return conn.query(sql)
