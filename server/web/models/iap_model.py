from models import database
from models import table_name
from utils import utils


def get_by_oid(conn, oid):
    if not conn or not oid:
        return {}
    sql = "SELECT * FROM `{0}` WHERE oid='{1}' LIMIT 1".format(table_name.iap, database.escape(oid))
    return conn.get(sql)


def create_order(conn, uid, oid, raw_data, item_id, channel_id, sandbox, status):
    if not conn or not oid:
        return {}
    sql = "INSERT INTO `{0}` SET uid={1},oid='{2}',raw_data='{3}',item_id='{4}',channel_id={5}," \
          "sandbox={6},status={7},time={8}". \
        format(table_name.iap, uid, oid, raw_data, item_id, channel_id, sandbox, status,
               utils.timestamp())
    return conn.execute_rowcount(sql)


def modify_data_and_status_by_oid(conn, ret_raw_data, status, oid):
    if not conn or not oid:
        return {}
    sql = "UPDATE `{0}` SET ret_raw_data='{1}',status={2} WHERE oid='{3}' LIMIT 1".format(table_name.iap,
                                                                                          database.escape(
                                                                                              str(ret_raw_data)),
                                                                                          status, oid)
    return conn.execute_rowcount(sql)
