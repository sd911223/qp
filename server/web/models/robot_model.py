from models import table_name
from models import database
from utils import utils


def get_all_robots(conn):
    if not conn:
        return []
    sql = "SELECT * " \
          "FROM {0} ".format(table_name.robot)
    info = conn.query(sql)
    return info


def set_robot_remark(conn, remark, robot_wx_id):
    if not conn:
        return 0
    sql = "UPDATE {0} SET remark = '{1}'  " \
          "WHERE wx_id = '{2}' ".format(table_name.robot, remark, robot_wx_id)
    return conn.execute_rowcount(sql)


def get_all_robot_groups(conn):
    if not conn:
        return []
    sql = "select robot_group.id,robot_group.group_id,robot_group.wx_id as wx_id," \
          "robot_group.time as time,robot_group.remark as group_remark,robot_group.diamond_uid" \
          ",players.nick_name,robot_group.rule,robot.remark as robot_remark,robot.id as robot_id,robot_group.time " \
          "from {0} left join {1} on players.uid = robot_group.diamond_uid inner join {2} on " \
          "robot.wx_id = robot_group.robot_id".format(table_name.robot_group, table_name.players,
                                                      table_name.robot)
    info = conn.query(sql)
    return info


def get_one_robot_groups(conn, gid):
    if not conn:
        return []
    sql = "select robot_group.id,robot_group.group_id,robot_group.remark as group_remark,robot_group.diamond_uid" \
          ",players.nick_name,robot_group.rule,robot.remark as robot_remark,robot.id as robot_id,robot_group.time " \
          "from {0} left join {1} on players.uid = robot_group.diamond_uid inner join {2} on " \
          "robot.wx_id = robot_group.robot_id where robot_group.id = {3}".format(table_name.robot_group,
                                                                                 table_name.players,
                                                                                 table_name.robot, gid)
    info = conn.get(sql)
    return info


def add_robot_group(conn, group_id, remark, uid, rule, robot_id):
    if not conn:
        return []
    time = utils.timestamp()
    try:
        sql = "INSERT INTO `{0}` SET group_id='{1}',remark='{2}',diamond_uid={3},rule='{4}',robot_id='{5}',time={6}". \
            format(table_name.robot_group, group_id, remark, uid, database.escape(utils.json_encode(rule)), robot_id,
                   time)
        return conn.execute_rowcount(sql)
    except Exception as ex:
        print(ex)
        return 0


def modify_robot_group(conn, remark, uid, rule, robot_group_id):
    if not conn:
        return []
    time = utils.timestamp()
    try:
        sql = "UPDATE `{0}` SET remark='{1}',diamond_uid={2},rule='{3}'" \
              ",time={4} WHERE id={5}".format(table_name.robot_group, remark, uid,
                                              database.escape(utils.json_encode(rule)),
                                              time, robot_group_id)
        return conn.execute_rowcount(sql)
    except Exception as ex:
        print(ex)
        return 0
