from . import database
from . import table_name


def _make_admin_data(row):
    if not row:
        return None
    row['powers'] = database.split_to_list(row.powers)
    return row


def get_by_union_id(conn, union_id):
    if not conn:
        return {}
    sql = "SELECT * FROM `{0}` WHERE union_id='{1}' LIMIT 1".format(table_name.admins, union_id)
    return _make_admin_data(conn.get(sql))


def create_agent_admin(conn, uid, union_id):
    sql = f"INSERT INTO `admins` SET name='ID-{uid}',password='poweroverwhelming',powers='1,601,602,603',is_root=0," \
          f"status=1,refer_uid={uid},is_partner=0,union_id='{union_id}'"
    return conn.execute_rowcount(sql)


def get_player_by_union_id(conn, union_id):
    sql = f"SELECT * FROM `players` WHERE unionid='{union_id}' LIMIT 1"
    return conn.get(sql)
