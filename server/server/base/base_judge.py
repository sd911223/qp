# coding:utf-8
import math
from copy import deepcopy

import pydash as _

from base import error, const, commands_system
from base.base_game import BaseGame
from models import tables_model, floor_model, club_model, players_model, database, logs_model, club_user_game_model, union_model
from protocol import channel_protocol, protocol_utils
from utils import earth_position
from utils import utils


class BaseJudge(object):
    def __init__(self, ret, service: BaseGame):
        assert service
        self.__first_join = False
        self.__change_config = False
        self.__start_time = utils.timestamp()
        self.__game_type = int(ret['game_type'])
        self.__rule_type = int(ret['rule_type'])
        self.__tid = int(ret['tid'])
        self.__tip = 0
        self.__tip_limit = 0
        # 0 大赢家支付 1 赢家AA支付 2 玩家AA支付
        self.__tip_payment_method = 0
        self.__owner = int(ret['owner'])
        self.__diamonds = int(ret['diamonds'])
        self.__consume_type = int(ret['consume_type'])
        self.__round_index = 1
        self.__total_round = int(ret['round_count'])
        rules = ret['rules']
        rules = rules.replace('\\"','\"',len(rules))
        self.__rule_details = utils.json_decode(rules)
        match_config = ret['match_config']
        match_config = match_config.replace('\\"','\"',len(match_config))
        self.__match_config = utils.json_decode(match_config)
        self.__match_type = ret['match_type']
        self.__match_score = 0  # 入场分数
        self.__match_enter_score = 1  # 游戏底分
        self.__match_limit_type = 1  # 1,2,3 抽水玩家(大赢家，前2名，前3名)
        self.__match_limit_score = 0  # 0,50,100,200,300 抽水分
        self.__match_limit_rate = 1  # 1,2,3,4,5 抽水比例
        self.__init_match_config()
        self.__is_agent = int(ret['is_agent'])
        self.__status = 0
        self.__floor = ret['floor']
        self.__flow_status = 0
        self.__dec_diamond = 0
        self.__already_started = False
        self.__sub_floor_id = ret['sub_floor']

        self.__group_id = ret['group_id']
        self.__robot_id = ret['robot_id']
        self.__club_id = ret['club_id']
        # tim  add
        self.__union_id = ret['union_id']

        self.__record_id = ""
        self.__dai_kai = int(ret['is_agent'])

        self.__service = service

        self.__round_review_data = []
        self.__seats = []

        self.__owner_player = None

        self.__init_record_id()
        self.__init_tip()
        self.__table_info = {
            "player_list": [],
            "players": [],
            "max_player": 0,
            "game_type": self.game_type,
            "rule_type": self.rule_type,
            "round_index": self.round_index,
            "table_status": 0
        }

    def __init_tip(self):
        if 'tip' in self.__rule_details:
            self.__tip = int(self.__rule_details['tip'])
            if self.__tip < 0 or self.__tip > 100:
                self.__tip = 0
        if 'tipLimit' in self.__rule_details:
            self.__tip_limit = int(self.__rule_details['tipLimit'])
        if 'tipPaymentMethod' in self.__rule_details:
            self.__tip_payment_method = int(self.__rule_details['tipPaymentMethod'])

    @property
    def tip(self):
        return self.__tip

    @property
    def first_join(self):
        return self.__first_join

    @property
    def change_config(self):
        return self.__change_config

    @change_config.setter
    def change_config(self, is_change):
        self.__change_config = is_change

    def __init_match_config(self):
        if not self.__match_type:
            return
        self.__match_score = self.__match_config['score']
        self.__match_enter_score = self.__match_config['enterScore']
        self.__match_limit_type = self.__match_config['limitType']
        self.__match_limit_score = self.__match_config['limitScore']
        self.__match_limit_rate = self.__match_config['limitRate']

    @property
    def already_started(self):
        return self.__already_started

    @already_started.setter
    def already_started(self, is_start):
        self.__already_started = is_start

    @property
    def match_config(self):
        return self.__match_config

    @property
    def match_type(self):
        return self.__match_type

    @property
    def match_score(self):
        return self.__match_score

    @property
    def match_enter_score(self):
        return self.__match_enter_score

    @property
    def match_limit_type(self):
        return self.__match_limit_type

    @property
    def match_limit_score(self):
        return self.__match_limit_score

    @property
    def match_limit_rate(self):
        return self.__match_limit_rate

    @property
    def sub_floor_id(self):
        return self.__sub_floor_id

    @property
    def floor(self):
        return self.__floor

    @property
    def dec_diamond(self):
        return self.__dec_diamond

    @dec_diamond.setter
    def dec_diamond(self, num):
        self.__dec_diamond = num

    @property
    def dai_kai(self):
        return self.__dai_kai

    @property
    def table_info(self):
        return self.__table_info

    @property
    def club_players_info(self):
        players = []
        for p in self.__seats:
            if not p:
                continue
            players.append(p.club_info)
        return deepcopy(players)

    @property
    def club_id(self):
        return self.__club_id

    @property
    def union_id(self):
        return self.__union_id

    @property
    def group_id(self):
        return self.__group_id

    @property
    def robot_id(self):
        return self.__robot_id

    @property
    def round_review_data(self):
        return self.__round_review_data

    @round_review_data.setter
    def round_review_data(self, data):
        self.__round_review_data = data

    @property
    def record_id(self):
        return self.__record_id

    @property
    def seats(self):
        return self.__seats

    @seats.setter
    def seats(self, seats):
        self.__seats = seats

    @property
    def logger(self):
        return self.share_service().logger

    def __init_record_id(self):
        self.__record_id = "{0}_{1}_{2}".format(utils.timestamp(), self.tid, utils.get_random_num(6))

    def share_service(self):
        return self.__service

    @property
    def start_time(self):
        return self.__start_time

    @start_time.setter
    def start_time(self, time):
        self.__start_time = time

    @property
    def game_type(self):
        return self.__game_type

    @property
    def rule_type(self):
        return self.__rule_type

    @property
    def tid(self):
        return self.__tid

    @property
    def owner(self):
        return self.__owner

    @property
    def diamonds(self):
        return self.__diamonds

    @property
    def consume_type(self):
        return self.__consume_type

    @property
    def status(self):
        return self.__status

    @status.setter
    def status(self, stat):
        self.__status = stat

    @property
    def flow_status(self):
        return self.__flow_status

    @flow_status.setter
    def flow_status(self, stat):
        self.__flow_status = stat

    @property
    def round_index(self):
        return self.__round_index

    @round_index.setter
    def round_index(self, index):
        self.__round_index = index

    @property
    def total_round(self):
        return self.__total_round

    @property
    def rule_details(self):
        return self.__rule_details

    @property
    def is_agent(self):
        return self.__is_agent

    @property
    def owner_player(self):
        return self.__owner_player

    def set_owner_player(self, player):
        self.__owner_player = player
        player.add_relation_tid(self.__tid)

    def inner_broad_cast(self, cmd, data, code=error.OK, not_to_uid=0, record=False):
        body = channel_protocol.packet_client_body(data, code)
        self.add_review_log(cmd, body, record)
        return self.broad_cast(cmd, body, not_to_uid)

    def broad_cast(self, cmd, body, not_to_uid=0):
        """
        桌子内广播
        :param cmd: 命令号
        :param body: 要广播的数据
        :param not_to_uid: 例外的玩家ID
        :return: None
        """
        for p in self.__seats:
            if not p:
                continue
            # if p.offline:  # 广播时不包括已离线的玩家
            #    continue
            if p.tid != self.tid:  # 不包括已进别的房间的玩家
                continue
            if p.uid == not_to_uid:
                continue
            self.share_service().send_body_to_player(p.uid, cmd, body)

    def inner_send(self, p, cmd: int, data: dict or None, code=error.OK, record=False, service_type=None):
        if not p:
            return
        body = channel_protocol.packet_client_body(data, code)
        self.share_service().send_body_to_player(p.uid, cmd, body, service_type=service_type)
        self.add_review_log(cmd, body, record)

    def add_review_log(self, cmd, data, show=True):
        review_log = deepcopy(data)
        if show:
            review_log["type"] = "send"
        else:
            review_log["type"] = "recv"

        message = channel_protocol.packet_client_message(self.__service.service_type, cmd, review_log)
        self.__round_review_data.append(message)

    def add_base_review_data(self):
        self.__round_review_data.clear()

    # 判断玩家是否在桌子内的流程
    def in_table(self, uid):
        if uid <= 0:
            return False
        for p in self.__seats:
            if p and p.uid == uid:
                return True
        return False

    # 统计当前在房间的人数
    @property
    def ready_player_count(self):
        count = 0
        for p in self.__seats:
            if p and p.is_ready:
                count += 1
        return count

    def get_player_by_uid(self, uid):
        for p in self.__seats:
            if not p:
                continue
            if p.uid == uid:
                return p

    def get_player_by_seat_id(self, seat_id):
        if seat_id and type(seat_id) is int and 0 < seat_id < len(self.__seats):
            p = self.__seats[seat_id]
            # if isinstance(p, BasePlayer):
            return p

    @property
    def player_count(self):  # 统计当前在房间玩家数
        count = 0
        for p in self.__seats:
            if p:
                count += 1
        return count

    def get_info(self):
        return {
            'config': {
                'juShu': self.total_round,
                "isAgent": self.is_agent,
                "ruleType": self.rule_type,
                "rules": self.rule_details,
                "matchConfig": self.match_config,
                "consumeType": self.consume_type,
                "matchType": self.match_type,
                "recordID": self.record_id,
            },
            'tid': self.tid,
            'creator': self.owner,
            'roundIndex': self.round_index,
            'status': self.status,
            "clubID": self.club_id,
            'unionID': self.union_id
        }

    def get_game_finish_data(self):
        result = {
            "gid": 1,
            'tableId': self.tid,
            'groupId': self.group_id,
            'robotId': self.robot_id,
            "recordId": self.record_id,
            "gameType": self.game_type,
            "ruleType": self.rule_type,
            "seats": []
        }
        for i in self.seats:
            if not i:
                continue
            result['seats'].append(i.game_over_data)
        finish_data = result
        finish_data['roomInfo'] = self.get_info()
        return finish_data

    def get_all_distances(self):
        result = list()
        p1 = self.get_player_by_seat_id(1)
        p2 = self.get_player_by_seat_id(2)
        p3 = self.get_player_by_seat_id(3)
        p4 = self.get_player_by_seat_id(4)

        def __calc_distance(_p1, _p2):
            if not _p1 or not _p2:
                return earth_position.DISTANCE_UNKNOWN
            x1, y1 = _p1.position
            x2, y2 = _p2.position
            return earth_position.calc_earth_distance(x1, y1, x2, y2)

        seats = len(self.__seats)

        if seats == 3:
            result.append(__calc_distance(p1, p2))
        if seats == 4:
            result.append(__calc_distance(p1, p2))
            result.append(__calc_distance(p1, p3))
            result.append(__calc_distance(p2, p3))
        if seats == 5:
            result.append(__calc_distance(p1, p2))
            result.append(__calc_distance(p1, p3))
            result.append(__calc_distance(p1, p4))
            result.append(__calc_distance(p2, p3))
            result.append(__calc_distance(p2, p4))
            result.append(__calc_distance(p3, p4))
        return result

    def del_player_in_table_info(self, uid):
        need_remove_player = None
        for i in self.__table_info['players']:
            if not i:
                continue
            if i['uid'] == uid:
                need_remove_player = i
                break
        if need_remove_player:
            self.__table_info['players'].remove(need_remove_player)

    def add_player_in_table_info(self, info):
        tid = 0
        if not self.__first_join:
            self.__first_join = True
            tid = self.__service.modify_table_count(self.club_id, self.union_id, self.sub_floor_id)
        find_player = False
        for i in self.__table_info['players']:
            if not i:
                continue
            if i['uid'] == info['uid']:
                find_player = True
                break
        if not find_player:
            self.__table_info['players'].append(info)
        return tid

    def update_table_info_max_player(self, count):
        self.__table_info['max_player'] = count

    def update_table_info(self, is_del=False):
        data = deepcopy(self.__table_info)
        data["is_del"] = int(is_del)
        data["tid"] = self.tid

        if is_del:
            tables_model.del_table_info(self.__tid)
        else:
            tables_model.update_table_info(self.__tid, self.__table_info)

        if self.__dai_kai == 0:
            return

        if self.__club_id != -1:
            self.share_service().club_room_broad_cast(self, self.__status, is_del)
            return

        self.share_service().send_body_to_player(self.__owner_player, commands_system.PUSH_MESSAGE, {
            "type": const.AGENT_UPDATE,
            "data": {
                "tables": {
                    self.tid: data
                }}
        }, service_type=const.SERVICE_SYSTEM)

    def calc_two_same_table_players_count(self):
        # 如果不是俱乐部内游戏 或者 非三、四人游戏，则不统计
        if self.club_id == -1 or self.player_count not in (3, 4,):
            return

        ids = []
        for i in self.seats:
            if not i:
                continue
            current_p = i
            ids.append(str(current_p.uid))
            ref_ids = []
            for p in self.seats:
                if not p:
                    continue
                if current_p == p:
                    continue
                ref_ids.append(str(p.uid))
                club_user_game_model.insert_or_update_same_player_game_count(self.club_id, current_p.uid, p.uid)
            # 将此玩家与其他人的场数清空
            club_user_game_model.remove_same_player_game_count(self.club_id, current_p.uid, ",".join(ref_ids))

        join_ids = ",".join(ids)
        club_user_game_model.remove_same_player_game_count_by_uid(self.club_id, join_ids, join_ids)

        same_table_count = 30
        data = club_user_game_model.query_same_table_player(self.club_id, join_ids, same_table_count)

        filter_data = []
        keys = {}
        for i in data:
            if i['uid'] not in keys:
                keys[i['uid']] = []

            if i['ref_uid'] in keys and i['uid'] not in keys[i['ref_uid']]:
                keys[i['uid']].append(i['ref_uid'])
                filter_data.append(i)

        for i in filter_data:
            p1 = self.get_player_by_uid(i['uid'])
            p2 = self.get_player_by_uid(i['ref_uid'])
            club_user_game_model.insert_same_player_game_logs(p1.uid, p2.uid, p1.nick_name, p2.nick_name, p1.avatar,
                                                              p2.avatar, self.club_id, i['count'])

    def dec_tip(self, winners):
        yuan_bao = math.ceil(self.tip / len(winners))
        for i in winners:
            players_model.dec_yuan_bao(i.uid, yuan_bao)
            # players_model.write_consume_logs(i.uid, self.club_id, yuan_bao, const.PAY_YUAN_BAO,
            #                                  const.REASON_GAME_WINNER_SUB, utils.timestamp(), 0, self.__record_id)
            players_model.write_admin_logs(i.uid, self.tid, self.__owner, yuan_bao, utils.timestamp(), self.__record_id)
            # players_model.add_manage_yuan_bao(self.__owner, yuan_bao)

    def dec_diamonds(self, is_dismiss, dismiss_round_index):
        if is_dismiss and dismiss_round_index == 1:
            return

        winners = list()
        if self.__tip > 0:
            winners_score = 0
            for i in self.seats:
                if not i:
                    continue
                if i.score == winners_score:
                    winners.append(i)
                elif i.score > winners_score:
                    winners.clear()
                    winners.append(i)
                    winners_score = i.score

            if winners_score != 0 and winners_score >= self.__tip_limit:
                # AA支付打赏元宝
                if self.__tip_payment_method == const.TIP_PAY_TYPE_AA:
                    winners.clear()
                    for i in self.seats:
                        if not i:
                            continue
                        winners.append(i)

                self.dec_tip(winners)

        if self.diamonds > 0:
            self.__dec_diamond = self.diamonds
            if self.consume_type == const.PAY_TYPE_CREATOR:
                owner = self.owner_player
                if owner:
                    # if self.match_type == const.DIAMOND_ROOM:
                    #     owner.dec_diamonds(self.diamonds, self.__club_id, self.__record_id)
                    # else:
                    #     owner.dec_la_jiao_dou(self.diamonds, self.__club_id, self.__record_id)
                    owner.dec_diamonds(self.diamonds, self.club_id, self.union_id, self.__record_id)
            elif self.consume_type == const.PAY_TYPE_AA:
                for i in self.seats:
                    if not i:
                        continue
                    i.dec_diamonds(self.calc_aa_diamonds(), self.__club_id, self.union_id, self.__record_id)
            elif self.consume_type == const.PAY_TYPE_WINNER:
                if not winners:
                    winners_score = 0
                    for i in self.seats:
                        if not i:
                            continue
                        if i.score == winners_score:
                            winners.append(i)
                        elif i.score > winners_score:
                            winners.clear()
                            winners.append(i)
                            winners_score = i.score
                self.dec_winner_diamonds(winners)
        self.add_player_score()
        self.calc_two_same_table_players_count()

    def add_player_score(self):
        score = self.calc_score()
        for i in self.seats:
            if not i:
                continue
            players_model.update_player_score_with_reason(i.uid, score, const.REASON_SCORE_GAME_ADD, self.record_id)
            if self.club_id != -1:
                players_model.update_player_club_today_game_count(i.uid, self.club_id)
            players_model.update_player_spring_activity(i.uid)

    def calc_score(self):

        # round_index 此处已经加1

        if self.__round_index > 32:
            return 4
        elif self.__round_index > 24:
            return 3
        elif self.__round_index > 16:
            return 2
        elif self.__round_index > 8:
            return 1

        return 0

    def player_unready(self, p):
        p.is_ready = False
        return True

    def dec_winner_diamonds(self, winners):
        for i in winners:
            i.dec_diamonds(math.ceil(self.diamonds / len(winners)), self.__club_id, self.union_id, self.__record_id)

    def calc_aa_diamonds(self):
        return math.ceil(self.diamonds / (len(self.seats) - 1))

    def calc_aa_tip(self):
        return math.ceil(self.tip / (len(self.seats) - 1))

    def is_empty_judge(self):
        for p in self.__seats:
            if p:
                return False
        return True

    def get_all_player_uid(self):
        uids = set()
        for p in self.seats:
            if not p:
                continue
            uids.add(p.uid)
        return uids

    def check_club_block(self, player):
        if self.club_id == -1:
            return error.OK
        block_list = club_model.query_block_list(self.club_id, player.uid)
        if not block_list:
            return error.OK
        current_table_uids = self.get_all_player_uid()
        for i in block_list:
            if (i['uid'] != player.uid and i['uid'] in current_table_uids) or \
                    (i['ref_uid'] != player.uid and i['ref_uid'] in current_table_uids):
                return error.TABLE_PLAYER_BLOCK
        return error.OK

    def check_union_block(self, player):
        if self.union_id == -1:
            return error.OK
        block_list = union_model.query_block_list(self.union_id, player.uid)
        if not block_list:
            return error.OK
        current_table_uids = self.get_all_player_uid()
        for i in block_list:
            if (i['uid'] != player.uid and i['uid'] in current_table_uids) or \
                    (i['ref_uid'] != player.uid and i['ref_uid'] in current_table_uids):
                return error.TABLE_PLAYER_BLOCK
        return error.OK

    def enter_match_score(self, p, club_id):
        data = club_model.get_player_money_by_club_id(club_id, p.uid)
        score = data['score'] + data['lock_score']
        if score >= self.match_score:
            if data['lock_score'] == 0:
                players_model.update_lock_score_by_club_id_and_uid(club_id, p.uid, self.match_score, self.tid)
            return error.OK
        return error.DOU_ERROR

    def enter_union_energy(self, p, union_id):
        data = union_model.get_my_union_info(database.share_db(), union_id, p.uid)
        if data == None:
            return error.ENERGE_NOT_ENOUGH
        if not data:
            return error.ENERGE_NOT_ENOUGH
        if "energy" not in data:
            return error.ENERGE_NOT_ENOUGH
        energy = data['energy']
        if energy >= self.match_score:
            return error.OK
        return error.ENERGE_NOT_ENOUGH

    def avoid_same_ip(self):
        same_ip_exist = False
        for player in self.__seats:
            if not player:
                continue

            for player2 in self.__seats:
                if not player2 or player == player2:
                    continue

                # 防止相同IP 出现的情况
                if player.session.ip == player2.session.ip:
                    same_ip_exist = True
                    if player.seat_id > player2.seat_id:
                        player.fake_ip(True)
                    else:
                        player2.fake_ip(True)

        for player in self.__seats:
            if not player:
                continue

            if not same_ip_exist:
                player.fake_ip(False)

    # 获取所有玩家公共信息
    def get_all_player_info(self):

        result = []
        for p in self.__seats:
            if not p:
                continue

            data = p.get_all_public_data(self.__status)
            result.append(data)
        return result

    def remove_empty_judge(self):
        if self.sub_floor_id == -1:
            return
        if not self.is_empty_judge():
            return

        if self.club_id != -1:
            game_config = floor_model.get_club_sub_floor_config(self.club_id, self.sub_floor_id)
            if not game_config:
                return
            count = int(database.get_club_sub_floor_count(self.club_id, self.sub_floor_id) or 0)
            if count >= int(tables_model.get_auto_room_by_club_and_sub_floor(self.sub_floor_id)['count'] or 0):
                tables_model.remove(self.tid)
                self.share_service().on_table_game_over(self)
                self.update_table_info(True)
        if self.union_id != -1:
            game_config = union_model.get_union_sub_floor_config(database.share_db(), self.union_id, self.sub_floor_id)
            if not game_config:
                return
            count = int(database.get_union_sub_floor_count(self.union_id, self.sub_floor_id) or 0)
            if count >= int(tables_model.get_auto_room_by_union_and_sub_floor(self.sub_floor_id)['count'] or 0):
                tables_model.remove(self.tid)
                database.share_redis_game().hdel('autotable',self.tid)
                self.share_service().on_table_game_over(self)
                self.update_table_info(True)


    def check_diamond_and_yuan_bao_and_tip(self, player):
        diamond = player.diamond()
        show_yuan_bao = player.yuan_bao
        idle_table_diamond = tables_model.get_total_idle_diamonds_by_uid(database.share_db(), player.uid)
        calc_diamond = int(diamond - idle_table_diamond)
        if calc_diamond < 0:
            show_yuan_bao = max(0, player.yuan_bao + calc_diamond)

        # and show_yuan_bao < self.__tip

        if self.tip > 0:
            if self.__tip_payment_method == const.TIP_PAY_TYPE_AA:
                if player.yuan_bao >= self.calc_aa_tip():
                    return error.OK
                else:
                    return error.YUAN_BAO_NOT_ENOUGH
            else:
                if player.yuan_bao >= self.tip:
                    return error.OK
                else:
                    return error.YUAN_BAO_NOT_ENOUGH

        calc_diamond_and_yuan_bao = show_yuan_bao - self.__tip + diamond
        if self.consume_type == const.PAY_TYPE_AA and calc_diamond_and_yuan_bao < self.calc_aa_diamonds():
            return error.AA_DIAMOND_ERROR
        elif self.consume_type == const.PAY_TYPE_WINNER and calc_diamond_and_yuan_bao < self.diamonds:
            return error.AA_DIAMOND_ERROR
        return error.OK

    def save_club_winner(self):
        if self.club_id is -1:
            return
        max_score = 0
        winners = []
        for i in self.seats:
            if not i:
                continue
            if i.score > max_score:
                max_score = i.score
                winners.clear()
            if i.score == max_score and max_score != 0:
                winners.append(i.uid)

        if max_score != 0:
            for i in winners:
                logs_model.add_club_winner_log(self.record_id, self.club_id, i, max_score,
                                               utils.timestamp(), self.game_type, utils.json_encode(self.rule_details),
                                               self.tid)

    def match_game_over(self):
        data = []
        limit = []
        calc_data = {}
        biggest_score = 0
        same_score_winner = 1

        for p in self.seats:
            if not p:
                continue
            if p.score == 0:
                calc_data[p.uid] = {"uid": p.uid, "score": 0, "game_score": p.score, "limit_score": 0}
                p.return_score(self.club_id)
            else:
                calc_data[p.uid] = {"uid": p.uid, "score": p.score + p.lock_score, "game_score": p.score,
                                    "limit_score": 0}
                before_score = club_model.get_player_money_by_club_id(self.club_id, p.uid)['score']
                if p.score < 0:
                    data.append(
                        {"uid": p.uid, "reason": const.REASON_GAME_SUB, "score": p.score,
                         'before_score': before_score + p.lock_score})
                else:
                    data.append(
                        {"uid": p.uid, "reason": const.REASON_GAME_ADD, "score": p.score,
                         'before_score': before_score + p.lock_score})

                    if p.score >= self.match_limit_score:
                        if biggest_score == p.score:
                            same_score_winner += 1
                        elif biggest_score > p.score:
                            biggest_score = p.score
                            same_score_winner = 1
                        limit.append({"uid": p.uid, "score": p.score, "before_score": before_score + p.lock_score})

        if not self.__already_started:
            return

        if limit:
            limit = _.sort_by(limit, 'score', reverse=True)
            if same_score_winner is not 1:
                limit = limit[0:same_score_winner]
            else:
                limit = limit[0:self.match_limit_type]

        for i in limit:
            adjust_score = math.ceil(i['score'] / same_score_winner)
            score = math.ceil(adjust_score * (self.match_limit_rate / 100))
            data.append({"uid": i['uid'], "reason": const.REASON_GAME_LIMIT_SUB, "score": -score,
                         'before_score': i['before_score'] + i['score']})
            calc_data[i['uid']]['limit_score'] = score
            calc_data[i['uid']]['score'] -= score

        for i in data:
            floor_model.insert_club_user_score_logs(i['uid'], self.club_id, i['reason'], i['before_score'], i['score'],
                                                    self.record_id)

        for k in calc_data:
            u = calc_data[k]
            floor_model.update_club_user_score_and_empty_lock_score(u['uid'], self.club_id, u['score'],
                                                                    u['limit_score'], u['game_score'])

    def record_game_players_info(self):
        for p in self.seats:
            if not p:
                continue
            logs_model.add_player_game_info(self.record_id, p.uid, p.score, self.game_type)

    def union_game_over(self):
        data = []
        limit = []
        calc_data = {}
        biggest_score = 0
        same_score_winner = 1
        winner_uids = {}
        uids = []
        #match_limit_score
        tid = 0
        for p in self.seats:
            if not p:
                continue

            uids.append(p.uid)
            winner_uids[p.uid] =   {"uid":p.uid,"score":0,"iswin":1}
            if tid ==0 :
                tid = p.tid
            if p.score == 0:
                calc_data[p.uid] = {"uid": p.uid, "score": 0, "game_score": p.score, "limit_score": 0}
                # p.return_score(self.club_id)
            else:
                calc_data[p.uid] = {"uid": p.uid, "score": p.score, "game_score": p.score,
                                    "limit_score": 0}
                # 获取俱乐部能量值
                # before_score = club_model.get_player_money_by_club_id(self.club_id, p.uid)['score']
                before_score = union_model.get_player_energy_by_union_id(self.union_id, p.uid)['energy']
                if p.score < 0:
                    data.append(
                        {"uid": p.uid, "reason": const.REASON_GAME_SUB, "score": p.score,
                         'before_score': before_score})
                else:
                    data.append(
                        {"uid": p.uid, "reason": const.REASON_GAME_ADD, "score": p.score,
                         'before_score': before_score})

                    if p.score >= self.match_limit_score:
                        if biggest_score == p.score:
                            same_score_winner += 1
                        elif biggest_score < p.score:
                            biggest_score = p.score
                            same_score_winner = 1
                        limit.append({"uid": p.uid, "score": p.score, "before_score": before_score + p.lock_score})

        if not self.__already_started:
            return

        if limit:
            limit = _.sort_by(limit, 'score', reverse=True)
            if same_score_winner is not 1:
                limit = limit[0:same_score_winner]
            else:
                limit = limit[0:self.match_limit_type]

        all_limit = 0


        i_score=0
        for i in limit:
            adjust_score = math.ceil(i['score'] / same_score_winner)
            #
            score = self.match_limit_rate/same_score_winner# math.ceil(adjust_score * (self.match_limit_rate / 100))

            data.append({"uid": i['uid'], "reason": const.REASON_GAME_LIMIT_SUB, "score": -score,
                         'before_score': i['before_score'] + i['score']})
            calc_data[i['uid']]['limit_score'] = score
            calc_data[i['uid']]['score'] -= score
            i_score = score
            winner_uids[i['uid']]['score'] = score
            all_limit += score

        for i in data:
            # floor_model.insert_club_user_score_logs(i['uid'], self.club_id, i['reason'], i['before_score'], i['score'],
            #                                        self.record_id)
            union_model.insert_union_user_energy_logs(i['uid'], self.union_id, i['reason'], i['before_score'], i['score'],
                                                    self.record_id)
        # 大盟主，应该抽的水
        for k in calc_data:
            u = calc_data[k]
            # floor_model.update_club_user_score_and_empty_lock_score(u['uid'], self.club_id, u['score'],
            #                                                        u['limit_score'], u['game_score'])
            union_model.update_union_user_energy(u['uid'], self.union_id, u['score'],
                                                                    u['limit_score'], u['game_score'])

        #start 2019-11-27
        try:
            union_model.compute_union(  winner_uids,self.union_id,tid,i_score,self.sub_floor_id )
        except Exception as ex:
            print(ex.args)
        else:
            print('顺利抽水')

        #end

        # 推送税收
        tax = {}
        tax['union_id'] = self.union_id
        tax['tid'] = self.tid
        if len(uids) == 0:
            tax['score'] = 0
        else:
            tax['score'] = math.floor(all_limit / len(uids))
        tax['game_kind'] = self.__service.service_type
        tax['timestamp'] = utils.timestamp()
        tax['ids'] = uids
        logs_model.push_union_romm_tax(tax)


    def get_permission(self,relation_data,uid):
        for ii in relation_data:
            i_uid = ii.get('uid')
            i_union_id = ii.get('union_id')
            i_union_user_id = ii.get('union_user_id')
            i_permission = ii.get('permission')
            if uid == i_uid:
                return i_permission , i_union_user_id
        return -1 , -1

    def on_match_game_over(self):
        if self.__match_type == const.DIAMOND_ROOM:
            return self.record_game_players_info()
        if self.__match_type == const.MATCH_ROOM:
            if self.union_id == -1:
                return self.match_game_over()
            else:
                return self.union_game_over()

    def publish_to_channel(self, service, cmd, uid, message):
        self.logger.info("gate publish to channel: %d", cmd)
        body = protocol_utils.pack_to_player_body(cmd, uid, message)
        return self._s2s_send(0, service, 1, body)


