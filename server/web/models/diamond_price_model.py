from models import table_name


def get_all_diamonds_price(conn):
    if not conn:
        return []
    sql = "SELECT * FROM `{0}`".format(table_name.price_config)
    return conn.query(sql)
