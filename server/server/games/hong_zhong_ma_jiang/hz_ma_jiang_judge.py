# coding:utf-8
import random
from copy import deepcopy

from base import const
from base import error
from base.base_judge import BaseJudge
from games.hong_zhong_ma_jiang import flow
from models import logs_model as logs_model
from models import onlines_model
from models import tables_model
from protocol import protocol_utils
from utils import utils
from utils.twisted_tools import DelayCall
from . import commands_game
from . import ma_jiang
from .ma_jiang_card import MaJiangCard
from .player import Player
from .rule_base import RuleBase

ROUND_RATE = 1  # 单局倍率
DISMISS_SECONDS = 180  # 解散房间的等待时间
OPERATOR_TIME_OUT = 120  # 用户操作超时时间

ROUND_OVER_NORMAL = 0  # 正常结束
ROUND_OVER_DISMISS = 1  # 解散结束

ADJUST_SCORE = 20  # 触发调整积分
MIN_ADJUST_SCORE = -10  # 触发调整积分


class ZzMaJiangJudge(BaseJudge):
    def __init__(self, ret, service_type):
        BaseJudge.__init__(self, ret, service_type)
        self.__no_score_seat_id = []
        self.__bird_count = int(self.rule_details.get("birdCount", 0))
        self.__pai_type = int(self.rule_details.get("paiType", 0))
        self.__yi_ma_quan_zhong = bool(self.rule_details.get("yiMaQuanZhong", 0))
        self.__zhuang_type = int(self.rule_details.get("zhuangType", 0))  # 胡牌庄类型 0 为胡牌为庄 1为定庄
        self.__hong_zhong = int(self.rule_details.get("isHongZhong", 0))
        self.__seven_dui = int(self.rule_details.get("isSevenPairs", 0))
        self.__zhuang_xian = int(self.rule_details.get("zhuangXian", 0))
        self.__hu_type = int(self.rule_details.get("huType", 0))
        self.__bird_score = int(self.rule_details.get("birdScore", 1))
        self.__is_fixed_bird = bool(self.rule_details.get("fixedBird", 0))
        self.__can_qiang_gang_hu = int(self.rule_details.get("canQiangGangHu", 0))
        self.__piao_score = int(self.rule_details.get("piaoScore", 0))
        self.__bird_type = 1 == int(self.rule_details.get("birdType", 0))
        self.__add_birds_count = int(self.rule_details.get("addBirdsCount", 0))
        self.__que_yi_men = int(self.rule_details.get("queYiMen", 0)) == 1  # 缺一门(条子)
        self.__si_fang_niao = int(self.rule_details.get("siFangNiao", 0)) == 1  # 二人模式四方算鸟

        #臭杠玩法写固定
        self.__is_chou_gang_pai = 1
        #self.__is_chou_gang_pai = int(self.rule_details.get("isChouGangPai", 0))
        self.__sai_zi = []
        self.__pre_jie_suan_data = None

        self.__wan_fa = self.rule_details.get("wanFa", list([-1]))

        if len(self.__wan_fa) == 1:
            self.__hqxd = False
            self.__pph = False
            self.__qqr = False
            self.__qxd = False
            self.__qys = False
            self.__shqxd = False
            self.__wdw = False
            self.__yh = False
        else:
            self.__hqxd = int(self.__wan_fa["hqxd"])
            self.__pph = int(self.__wan_fa["pph"])
            self.__qqr = int(self.__wan_fa["qqr"])
            self.__qxd = int(self.__wan_fa["qxd"])
            self.__qys = int(self.__wan_fa["qys"])
            self.__shqxd = int(self.__wan_fa["shqxd"])
            self.__wdw = int(self.__wan_fa["wdw"])
            self.__yh = int(self.__wan_fa["yh"])

        # print("rule: ", self.rule_details)
        # print("wanfa: ", self.__wan_fa)
        # print("hqxd: ", self.__hqxd, " pph: ", self.__pph, " qqr: ", self.__qqr, " qxd: ", self.__qxd)
        # print("shqxd: ", self.__shqxd, " qys: ", self.__qys, " wdw: ", self.__wdw, " yh: ", self.__yh)

        self.__rule = self.__fetch_rule()
        self.__mo_pai_total = 0

        self.__chu_pai_count = 0
        self.__dealer = -1  # 庄家ID
        self.__curr_seat_id = 0
        self.__before_seat_id = 0
        self.__total_seat = int(self.rule_details.get("totalSeat", 3)) + 1
        self.__full_pai = int(self.rule_details.get("fullPai", 0))  # 1-全牌， 2-少牌, 0
        self.__round_results = {}
        self.status = flow.T_IDLE
        self.flow_status = flow.T_IN_IDLE  # 流程状态
        self.__dismiss_timer = None  # 解散房间定时器
        self.__cheat_index = []

        self.__gang_record = []

        self.__init_card()
        self.__init_cheat_index()

        self.__agree_seats = set()
        self.__disagree_seats = set()
        self.__is_dismiss = False
        self.__dismiss_round_index = 1
        self.__round_review_data = []
        self.__init_seats()

        self.__winner_list = []
        self.__lose_list = []

        self.__is_huang_zhuang = False
        self.__curr_card = 0  # 当前牌
        self.__curr_card_exist = 0  # 当前牌是否存在
        self.__player_actions = []  # 玩家动作

        self.__fixed_dealer = 0

        self.__prev_winner = 0
        self.__is_ti_hu = False
        self.__is_wei_hu = False
        self.__ti_wei_index = 0
        self.__special_hu_card = 0
        self.__gong_gang_player = None
        self.__gong_gang_from_player = None
        self.update_table_info()
        self.update_table_info_max_player(self.__total_seat)

        self.__ying_hu = False

        self.__real_seats = []
        self.__simulate = []
        self.__curr_simulate_seat_id = 0
        self.__simulate_cards = {}
        # self.__is_request_dismiss_room = False

    def __init_card(self):
        zhong_count = 0
        if self.__hong_zhong == 1:
            zhong_count = 4

        self.__ma_jiang_cards = MaJiangCard(zhong_count=zhong_count)  # 初始化麻将

        if self.__que_yi_men:
            self.__ma_jiang_cards.qu_yi_men(2)

    def get_left_cards(self):
        return deepcopy(self.__ma_jiang_cards.left_cards())

    def lucker_change_card(self, p: Player, change_card):
        # if self.__curr_seat_id != p.seat_id:
        #     return error.NOT_YOUR_TURN
        if not self.__ma_jiang_cards.check_and_move_card(change_card):
            return error.DATA_BROKEN
        p.set_change_card(change_card)
        for index in range(len(self.round_review_data) - 1, -1, -1):
            data = self.round_review_data[index]
            if data.get("cmd", 0) == 1220 and data.get("msg").get("type") == "send":
                self.round_review_data[index]["msg"]["card"] = change_card
                break
        return error.OK

    def get_empty_seat(self):
        empty_seats = []
        for index in range(1, len(self.seats)):
            if not self.seats[index]:
                empty_seats.append(index)
        return empty_seats

    def change_seat(self, p: Player):
        if not p:
            return error.DATA_BROKEN
        empty_seats = self.get_empty_seat()
        if not empty_seats:
            return error.TABLE_FULL
        rand_seat_id = empty_seats[random.randint(0, len(empty_seats) - 1)]
        seat_id = p.seat_id
        p.seat_id = rand_seat_id
        self.seats[rand_seat_id] = p
        self.seats[seat_id] = None
        self.inner_broad_cast(commands_game.CHANGE_SIT, {"fromSeatId": seat_id, "toSeatId": rand_seat_id})
        return error.OK

    def __init_seats(self):
        self.seats = [None] * self.__total_seat

    def __init_cheat_index(self):
        shuffle_round = list(range(1, self.total_round + 1))
        random.shuffle(shuffle_round)
        r = utils.randint(4, 6)
        self.__cheat_index = shuffle_round[0:r]

    def __fetch_rule(self):
        if ma_jiang.ZZ_MA_JIANG == self.rule_type:
            from games.hong_zhong_ma_jiang.rule_hz_ma_jiang import RuleZZMaJiang
            return RuleZZMaJiang

        assert False

    @property
    def in_dismiss(self):
        return len(self.__agree_seats) > 0

    def __set_status(self, status):
        # 设置桌子状态
        self.status = status
        if self.table_info["table_status"] != status:
            self.table_info["table_status"] = status
            self.update_table_info()

    def __set_flow_status(self, status):
        # 设置桌子状态
        self.flow_status = status

    def get_info(self):
        """ 获得房间基本信息 """
        result = BaseJudge.get_info(self)
        result["saiZi"] = self.__sai_zi
        result['preRoundDta'] = self.__pre_jie_suan_data
        if self.status == flow.T_PLAYING:
            result['inFlow'] = self.flow_status
            result['dealer'] = self.__dealer

            result['lastSeatID'] = self.__before_seat_id
            result["turn"] = self.__curr_seat_id

            result['remainSeconds'] = 0
            result["operateSeats"] = self.__get_operate_seats()
            result["leftCount"] = self.__ma_jiang_cards.left_count
            result["lastCard"] = self.__curr_card
            result["isLastCardExist"] = self.__curr_card_exist
        return result

    def __get_operate_seats(self):
        ret = []
        for item in self.__player_actions:
            if item:
                ret.append(item[0])
        return ret

    def __search_empty_seat(self):
        """ 寻找桌子内的空位 """
        for seat_id in range(1, self.__total_seat):
            if not self.seats[seat_id]:
                return seat_id
        return -1

    # 判断玩家是否在桌子内的流程
    def in_table(self, uid):
        if uid <= 0:
            return False
        for p in self.seats:
            if p and p.uid == uid:
                return True
        return False

    # 根据玩家uid来获得玩家的坐位ID
    def get_seat_id(self, uid):
        for i in range(1, self.__total_seat):
            if self.seats[i] and self.seats[i].uid == uid:
                return i
        return -1

    @property
    def ready_player_count(self):  # 统计当前已准备的玩家数
        count = 0
        for p in self.seats:
            if p and p.is_ready:
                count += 1
        return count

    @property
    def player_count(self):  # 统计当前在房间玩家数
        count = 0
        for p in self.seats:
            if p:
                count += 1
        return count

    def notify_distance(self):
        if self.status != flow.T_IN_IDLE:
            return
        if self.player_total_count() != self.player_count:
            return
        data = {"distances": self.get_all_distances()}
        for p in self.seats:
            if not p:
                continue
            if p.is_ready:
                continue
            self.inner_send(p, commands_game.NOTIFY_POSITION, data)

    def try_start_game(self):
        if self.__check_game_start():
            return
        return self.__check_round_start()

    @property
    def dealer(self):  # 庄家坐位ID
        return self.__dealer

    def __set_dealer(self, dealer: int):
        assert type(dealer) is int
        self.__dealer = dealer
        return dealer

    @property
    def curr_seat_id(self):  # 当前玩家的坐位ID
        return self.__curr_seat_id

    def __game_start(self):
        """ 游戏开始 """
        if self.status != flow.T_READY:
            return
        ids = []
        for p in self.seats:
            if not p:
                continue
            ids.append(p.uid)
            p.on_game_start(self.match_score)

        self.__winner_list = []
        self.__lose_list = []
        self.__prev_winner = 0
        self.__huang_zhuang_count = 0
        # 修改数据库中桌子状态
        tables_model.modify_status_by_tid(tables_model.STATUS_PLAYING, self.tid)
        # 修改在线表中桌子内玩家状态
        onlines_model.set_state_by_uid(onlines_model.STATUS_PLAYING, ids)
        self.start_time = utils.timestamp()
        self.already_started = True
        self.__set_status(flow.T_PLAYING)
        self.inner_broad_cast(commands_game.GAME_START, {})
        self.__round_start()

    def __game_over(self):
        """ 游戏结束 """
        self.dec_diamonds(self.__is_dismiss, self.__dismiss_round_index)
        self.__set_status(flow.T_IDLE)
        result = {"gid": 1, "seats": [], "match": [], "union": []}
        ids = []
        for p in self.seats:
            if not p:
                continue
            ids.append(p.uid)
            result["seats"].append(p.game_over_data)
            result["match"].append(p.match_data(self.club_id, self.match_type))
            if self.union_id != -1:
                result["union"].append(p.union_energy_data(self.union_id))

        self.inner_broad_cast(commands_game.GAME_OVER, result)
        finish_data = self.get_game_finish_data()
        finish_data["isDismiss"] = self.__is_dismiss
        onlines_model.set_state_by_uid(onlines_model.STATUS_WAITING, ids)

        self.__save_game_record(finish_data)
        self.save_club_winner()
        self.__do_dismiss()
        # 如果如果游戏结束，广播消息给客户端
        """如果如果游戏结束，广播消息给客户端"""
        from games.hong_zhong_ma_jiang.game import GameServer
        GameServer.share_server().publish(2,6,{'union_id':self.union_id,'uid':1,'selfuid':0,'type':6,
                                               'tid':self.tid,'subfloor':self.sub_floor_id},9999)

    def get_player_data(self, p: Player):
        result = p.get_all_data(self.status)
        if self.__has_do_action(p):
            del result["operates"]

        return result

    def __save_game_record(self, finish_data):
        logs_model.insert_room_log(self.record_id, self.tid, self.game_type, self.seats, self.owner,
                                   self.total_round, self.rule_details, self.club_id,
                                   finish_data, self.group_id, self.dec_diamond, self.match_type, self.floor,
                                   self.sub_floor_id, self.match_config, self.union_id)

    def __add_base_review_data(self):
        BaseJudge.add_base_review_data(self)
        for p in self.seats:
            if not p:
                continue
            data = p.get_all_data(self.status)
            self.add_review_log(commands_game.PLAYER_ENTER_ROOM, data)

        self.add_review_log(commands_game.ROOM_CONFIG, self.get_info())

    def count_cards(self, card, all_cards):
        count = 0
        for i in all_cards:
            if card == i:
                count += 1
        return count

    def __make_player_cards(self):
        cards = [[], [], [], [], []]
        all_cards = self.__ma_jiang_cards.get_cards()
        index = 0
        for i in range(len(self.seats) - 1):
            current_cards = []
            replace_card = utils.randint(1, 3)
            while len(current_cards) < 13:
                random_num = utils.randint(2, 8)
                random_color = utils.randint(1, 3)
                num = random_color * 10 + random_num
                if len(current_cards) == 12:
                    if num in all_cards:
                        card = [num]
                    else:
                        continue
                else:
                    if (num - 1) in all_cards and num in all_cards and (num + 1) in all_cards:
                        card = [num - 1, num, num + 1]
                    else:
                        continue
                for c in card:
                    current_cards.append(c)
                    all_cards.remove(c)

            replace_count = 0
            while replace_count != replace_card:
                random_num = utils.randint(2, 8)
                random_color = utils.randint(1, 3)
                num = random_color * 10 + random_num
                temp_index = utils.randint(0, 12)
                if num in all_cards:
                    card = current_cards[temp_index]
                    current_cards[temp_index] = num
                    all_cards.remove(num)
                    all_cards.append(card)
                    replace_count += 1
                else:
                    continue
            cards[index] = deepcopy(current_cards)
            index += 1
        self.__ma_jiang_cards.set_pop_order(cards)

    def __choose_winner(self):
        players = []
        for i in self.seats:
            if not i:
                continue
            if i.score >= ADJUST_SCORE:
                players.append(i)
        return players

    def __choose_loser(self):
        players = []
        for i in self.seats:
            if not i:
                continue
            if MIN_ADJUST_SCORE <= i.score < 0 and random.randint(1, 10) != 10:
                players.append(i)
        return players

    def __deal_cards(self):
        """ 发牌，每人13张 """
        if self.flow_status not in (flow.T_IN_IDLE,):
            return
        if self.__pai_type == 1:
            self.__make_player_cards()
        self.__ma_jiang_cards.shuffle(self.player_total_count())
        for i in range(13):
            for p in self.seats:
                if not p:
                    continue
                nai_zi_count = p.cards.count(ma_jiang.NAI_ZI)
                exclude_cards = nai_zi_count > 2 and [ma_jiang.NAI_ZI] or []
                c = self.__ma_jiang_cards.pop(exclude_cards)
                p.receive_card(c)
        if self.__full_pai == 2:
            # 去掉26张牌
            for p in self.seats:
                if not p:
                    continue
                self.__real_seats.append(p.seat_id)
                self.__simulate.append(p.seat_id)
                self.__simulate.append(p.seat_id + 2)
                self.__simulate_cards[p.seat_id + 2] = []
            for i in range(13):
                for seat_id in self.__simulate_cards:
                    tmp_card = self.__ma_jiang_cards.pop()
                    self.__simulate_cards[seat_id].append(tmp_card)


        #self.seats[1].cards = [12, 13, 14, 15, 16, 22, 22, 24, 24, 24, 31, 32, 33]
        #self.seats[2].cards = [11, 11, 11, 23, 23, 12, 12, 26, 14, 14, 25, 25, 26]
        #self.seats[3].cards = [21, 33, 26, 23, 23, 12, 12, 26, 14, 14, 25, 25, 26]
        #self.seats[3].cards = [21, 31, 26, 31, 32, 32, 12, 34, 34, 34, 37, 37, 37]

        #test
        #self.__ma_jiang_cards.set_cards([11,11,11,11])


        self.__add_base_review_data()

        result = {"dealerSeatID": self.__dealer, "remainCards": self.__ma_jiang_cards.left_count,
                  "seq": self.round_index + 1}

        for p in self.seats:
            if not p:
                continue
            result["handCards"] = p.cards
            self.inner_send(p, commands_game.DEAL_CARDS, result, error.OK, True)

        self.__mo_pai(self.__dealer)

    def __dealer_turn(self):  # 庄家轮转的逻辑
        if self.__fixed_dealer and self.__fixed_dealer > 0:
            return self.__set_dealer(self.__fixed_dealer)

        dealer = self.get_player_by_seat_id(self.__dealer)
        if not dealer:  # 首局随机庄
            # zhuang = random.randrange(1, flow.TOTAL_SEAT + 1)
            return self.__set_dealer(1)

        # 胡牌者为庄
        if len(self.__winner_list) > 0:
            if len(self.__winner_list) > 1:  # 通炮者为庄
                return self.__set_dealer(self.__lose_list[0].seat_id)
            return self.__set_dealer(self.__winner_list[0].seat_id)

        # 黄庄则轮庄
        if self.__is_huang_zhuang and dealer:
            zhuang_player = self.__next_player(dealer)
            return self.__set_dealer(zhuang_player.seat_id)

        return self.__set_dealer(1)

    def __before_round_start(self):
        self.__dealer_turn()
        self.flow_status = flow.T_IN_IDLE
        self.round_review_data.clear()
        self.__curr_seat_id = self.__dealer
        self.__is_huang_zhuang = False
        self.__special_hu_card = 0
        self.__clear_table_actions()
        self.__ying_hu = False
        self.__real_seats = []
        self.__simulate = []
        self.__simulate_cards = {}
        self.__sai_zi.clear()

    def __check_round_start(self):
        """ 检查下一局是否要开始了 """
        if self.status != flow.T_CHECK_OUT:
            return False
        if self.ready_player_count != self.player_total_count():
            return False
        self.__set_status(flow.T_PLAYING)
        self.__round_start()
        return True

    def __check_game_start(self):
        if self.status != flow.T_IDLE:  # 状态不对
            return False
        if self.player_total_count() != self.player_count:  # 人数未满
            return False
        if self.player_total_count() != self.ready_player_count:  # 全部准备
            return False

        self.__set_status(flow.T_READY)
        self.__game_start()
        return True

    def player_total_count(self):
        return self.__total_seat - 1

    def __round_start(self):
        """ 一局开始 """
        if self.status != flow.T_PLAYING:
            return

        for p in self.seats:  # 开局前清理
            if not p:
                continue
            p.on_round_start(self.__piao_score)

        self.__before_round_start()

        die1 = random.randint(1, 6)
        die2 = random.randint(1, 6)

        if die1 > die2:
            self.__sai_zi.append(die1)
            self.__sai_zi.append(die2)
        else:
            self.__sai_zi.append(die2)
            self.__sai_zi.append(die1)

        result = {"seq": self.round_index, "dealerSeatID": self.__dealer, "saiZi": self.__sai_zi}
        self.inner_broad_cast(commands_game.ROUND_START, result)
        #游戏开始，广播消息给客户端
        """游戏开始，广播消息给客户端"""
        from games.hong_zhong_ma_jiang.game import GameServer
        GameServer.share_server().publish(2,9,{'union_id':self.union_id,'uid':0,'selfuid':0,'type':9,
                          'tid':self.tid,'subfloor':self.sub_floor_id,
                          'round_index':self.round_index},9999)
        self.__deal_cards()

    def __calc_check_out_result(self, winner_list):
        """计算底分，海底，是否自摸等"""
        result = []
        for p in winner_list:
            is_qing_yi_se = False
            is_quan_qiu_ren = False
            is_peng_peng_hu = False
            is_seven_pairs = False
            is_ying_hu = False
            is_wang_diao_wang = False

            is_zi_mo = self.__curr_seat_id == p.seat_id

            hu_cards = self.__curr_card

            gang_count = 0
            for data in p.zhuo_pai:
                if data[0] in (
                        ma_jiang.ACTION_TYPE_MING_GANG, ma_jiang.ACTION_TYPE_GONG_GANG, ma_jiang.ACTION_TYPE_AN_GANG) \
                        and data[1] not in p.gang_peng_cards:
                    gang_count += 1

            is_qiang_gang_hu = self.flow_status in (
                flow.T_IN_MING_GANG_PAI_CALL, flow.T_IN_AN_GANG_PAI_CALL, flow.T_IN_GONG_GANG_PAI_CALL)

            # print("self.curr_cards: ", self.__curr_card)
            # print("p.zhuo_pai: ", p.zhuo_pai)
            # print("p.cards: ", p.cards)
            cards = deepcopy(p.cards)
            if is_qiang_gang_hu and self.flow_status in (
                    flow.T_IN_GONG_GANG_PAI_CALL, flow.T_IN_AN_GANG_PAI_CALL, flow.T_IN_MING_GANG_PAI_CALL):
                cards.append(hu_cards)
                # p.cards = cards

            # if RuleMaJiang.is_card(hu_cards):
            #   cards.append(hu_cards)
            ming_tang = []
            nai_zi_count = RuleBase.calc_value_count(cards, ma_jiang.NAI_ZI)
            if self.__qys:
                is_qing_yi_se, _ = self.__rule.is_qing_yi_se(p.zhuo_pai, cards, nai_zi_count)
                if is_qing_yi_se:
                    ming_tang.append("QingYiSe")

            if self.__qqr:
                is_quan_qiu_ren, _ = self.__rule.is_quan_qiu_ren(p.zhuo_pai, cards)
                if is_quan_qiu_ren:
                    ming_tang.append("QuanQiuRen")

            if self.__pph:
                is_peng_peng_hu, _ = self.__rule.is_peng_peng_hu(p.zhuo_pai, cards, nai_zi_count)
                if is_peng_peng_hu:
                    ming_tang.append("PengPengHu")
            if self.__qxd:
                is_seven_pairs, _ = self.__rule.is_seven_pairs(p.zhuo_pai, cards)
                if is_seven_pairs:
                    ming_tang.append("QiXiaoDui")
            if self.__hqxd or self.__shqxd:
                long_qi_count = self.__rule.get_long_qi_count(p.zhuo_pai, cards)
                if not self.__shqxd and long_qi_count >= 2:
                    long_qi_count = 1
                if long_qi_count == 1:
                    ming_tang.append("HaoHuaQiDui")
                    if "QiXiaoDui" in ming_tang:
                        ming_tang.remove("QiXiaoDui")
                if long_qi_count >= 2:
                    ming_tang.append("ShuangHaoHuaQiDui")
                    if "QiXiaoDui" in ming_tang:
                        ming_tang.remove("QiXiaoDui")
            else:
                long_qi_count = 0

            if self.__yh:
                is_ying_hu = ma_jiang.NAI_ZI not in cards
                if is_ying_hu:
                    ming_tang.append("YingHu")

            if self.__wdw:
                ting_list = self.__rule.get_ting_pai(p.zhuo_pai, cards[0:-1])
                print("len(ting_list): ", len(ting_list), " cards[-1]:", cards[-1])
                is_wang_diao_wang = len(ting_list) >= 28 and cards[-1] == ma_jiang.NAI_ZI
                if is_wang_diao_wang:
                    ming_tang.append("WangDiaoWang")

            score = 2
            zi_mo_score = 2
            if long_qi_count >= 2:
                score *= 8
            elif long_qi_count == 1:
                score *= 4
            elif is_seven_pairs:
                score *= 2

            count_ming_tang_list = [is_qing_yi_se, is_quan_qiu_ren, is_peng_peng_hu, is_ying_hu, is_wang_diao_wang]
            count_ming_tang = count_ming_tang_list.count(True)
            if count_ming_tang > 0:
                score = score * 2 ** count_ming_tang

            if is_qiang_gang_hu:
                qiang_gang_hu_score = score * (self.__total_seat - 2)
                is_zi_mo = False
            else:
                qiang_gang_hu_score = 0

            result.append({
                "score": score - zi_mo_score,
                "zi_mo_score": zi_mo_score,
                "is_hai_di": self.__ma_jiang_cards.left_count <= 0,
                "is_zi_mo": is_zi_mo,
                "zhuang_xian_score": self.__zhuang_xian and 1 or 0,
                "qiang_gang_hu_score": is_qiang_gang_hu and qiang_gang_hu_score or 0,
                "gang_count": gang_count,
                "is_qiang_gang_hu": is_qiang_gang_hu,
                "is_qing_yi_se": is_qing_yi_se,
                "is_quan_qiu_ren": is_quan_qiu_ren,
                "is_peng_peng_hu": is_peng_peng_hu,
                "is_seven_pairs": is_seven_pairs,
                "long_qi_count": long_qi_count,
                "is_ying_hu": is_ying_hu,
                "is_wang_diao_wang": is_wang_diao_wang,
                "winner": p,
                "ming_tang": ming_tang
            })
            print("result: ", result, " \nwinner seat_id:", p.seat_id, "\n")
        return result

    def __has_next_round(self):
        if self.__is_dismiss:
            return False
        if len(self.__no_score_seat_id) > 0:
            return False
        return self.round_index <= self.total_round

    def __dismiss_check_out(self):
        for p in self.seats:
            if not p:
                continue
            p.on_round_over(0, False, False, False, [])
        return [], self.deal_gang_info({}, {})

    def __huang_zhuang_check_out(self):
        return self.__dismiss_check_out()

    def __calc_win_score(self, check_out_result, bird_list, winner_list: list):
        if not winner_list:  # 流局
            return {}, {}

        is_zi_mo = False
        for hu_value in check_out_result:
            is_zi_mo = is_zi_mo or hu_value["is_zi_mo"]

        bird_seat = {1: 0, 2: 0, 3: 0, 4: 0}
        if self.__total_seat == 4:
            bird_seat = {1: 0, 2: 0, 3: 0}
        elif self.__total_seat == 3:
            bird_seat = {1: 0, 2: 0}

        if is_zi_mo:
            for winner in winner_list:
                del bird_seat[winner.seat_id]
        else:
            bird_seat = {self.__curr_seat_id: 0}

        # bird_type = bool(self.__rule_details.get("bird_type", 0))
        # start_seat_id = 0
        if self.__zhuang_type == 0:
            if len(winner_list) == 1:
                start_seat_id = winner_list[0].seat_id
            else:
                start_seat_id = self.__curr_seat_id
        else:
            start_seat_id = self.__dealer

        lose_info = {}
        for seat, _ in bird_seat.items():
            lose_info[seat] = {"score": 0}

        def deal_lose_info(seat_id, name, lose_score):
            if not lose_info[seat_id].get(name):
                lose_info[seat_id][name] = 0

            if self.match_type == 1:
                lose_score *= self.match_enter_score

            lose_info[seat_id][name] -= lose_score
            lose_info[seat_id]["score"] -= lose_score

        win_score_info = {}

        for hu_value in check_out_result:
            winner = hu_value["winner"]
            print("\n winner seat_id:", winner.seat_id, "\n")

            pos_map = [4, 1, 2, 3]
            if self.player_total_count() == 3 and self.__bird_type:
                pos_map = [3, 1, 2]
            elif self.player_total_count() == 2 and self.__bird_type and not self.__si_fang_niao:
                pos_map = [2, 1]

            bird_count = 0
            for seat, _ in bird_seat.items():
                bird_seat[seat] = 0

            bird_once_add_count = 1
            if bool(self.__hong_zhong) and hu_value["is_qiang_gang_hu"]:
                bird_once_add_count = self.__total_seat - 2  # 3
                print("bird_once_add_count:", bird_once_add_count)

            for bird in bird_list:
                pos = pos_map[bird % 10 % len(pos_map)]
                if self.__bird_count == 1 and self.__yi_ma_quan_zhong:  # 一码全中
                    bird_val = 9 if bird == ma_jiang.NAI_ZI else bird % 10
                    for key, value in bird_seat.items():
                        bird_seat[key] += 1 * bird_val
                else:
                    if bool(self.__hong_zhong) and hu_value["is_qiang_gang_hu"]:
                        print(self.__bird_type)
                        if bird == ma_jiang.NAI_ZI:
                            for seat in bird_seat:
                                bird_seat[seat] += bird_once_add_count
                        elif pos == 1:
                            bird_count += bird_once_add_count
                            for key, value in bird_seat.items():
                                bird_seat[key] += bird_once_add_count
                        elif self.__bird_type:
                            seat = pos_map[(start_seat_id + pos - 1) % len(pos_map)]
                            if seat == winner.seat_id:
                                seat = self.__curr_seat_id

                            if seat in bird_seat:
                                bird_seat[seat] += bird_once_add_count
                    elif bird == ma_jiang.NAI_ZI:
                        for seat in bird_seat:
                            bird_seat[seat] += 1
                    else:
                        if pos == 1:
                            bird_count += bird_once_add_count
                            for key, value in bird_seat.items():
                                bird_seat[key] += bird_once_add_count
                        elif self.__bird_type:
						
						#conflics
                            if self.__total_seat - 1 == 2:
                                seat = pos
                            else:
						#
                                seat = pos_map[(start_seat_id + pos - 1) % len(pos_map)]
                            if seat == winner.seat_id:
                                seat = self.__curr_seat_id

                            if seat in bird_seat:
                                bird_seat[seat] += 1

            zhuang_xian_total_score = 0
            qiang_gang_hu_total_score = 0
            gang_total_score = 0
            bird_total_score = 0
            piao_total_score = 0
            hu_score = 0
            zi_mo_hu_score = 0

            for seat, _ in lose_info.items():
                if hu_value["is_qiang_gang_hu"]:
                    continue

                key = hu_value["is_zi_mo"] and "ziMo" or "fangPao"
                deal_lose_info(seat, key, hu_value["zi_mo_score"])
                deal_lose_info(seat, "ming_tang_score", hu_value["score"])
                lose_info[seat]["hu_list"] = hu_value["ming_tang"]
                hu_score += hu_value["score"] + hu_value["zi_mo_score"]
                zi_mo_hu_score += hu_value["zi_mo_score"]

            # for seat, _ in lose_info.items():
            #    lose_p = self.get_player_by_seat_id(seat)
            #    score = winner.piao_score + lose_p.piao_score
            #    deal_lose_info(seat, "piaoScore", score)
            #    piao_total_score += score

            for seat, value in bird_seat.items():
                bird_score = value * self.__bird_score
                deal_lose_info(seat, "zhongNiao", bird_score)
                bird_total_score += bird_score

            if hu_value["zhuang_xian_score"]:
                key = 'zhuangXian'
                zhuang_xian_final_score = hu_value["zhuang_xian_score"]
                if self.__zhuang_type == 1:
                    if winner.seat_id == self.__dealer:
                        for seat, _ in lose_info.items():
                            deal_lose_info(seat, key, zhuang_xian_final_score)
                            zhuang_xian_total_score += zhuang_xian_final_score
                    elif self.__dealer in lose_info:
                        deal_lose_info(self.__dealer, key, zhuang_xian_final_score)
                        zhuang_xian_total_score += zhuang_xian_final_score
                elif self.__zhuang_type == 0:
                    for seat, _ in lose_info.items():
                        deal_lose_info(seat, key, zhuang_xian_final_score)
                        zhuang_xian_total_score += zhuang_xian_final_score

            if hu_value["gang_count"] and not bool(self.__hong_zhong):
                gang_score = 1
                for k, v in lose_info.items():
                    deal_lose_info(k, "haveGang", gang_score * hu_value["gang_count"])
                    gang_total_score += gang_score * hu_value["gang_count"]

            # 抢杠胡分数屏蔽
            if hu_value["is_qiang_gang_hu"]:
                 for k, v in lose_info.items():
                     print("\n>>>>>seat_id:", k, "qiang_gang_hu_score:", hu_value["qiang_gang_hu_score"], "\n")
                     deal_lose_info(k, "qiangGangHu", hu_value["qiang_gang_hu_score"])
                     qiang_gang_hu_total_score += hu_value["qiang_gang_hu_score"]

            win_score_info[winner.seat_id] = {}
            win_score_info[winner.seat_id][
                "score"] = (
                                   zhuang_xian_total_score + qiang_gang_hu_total_score + bird_total_score + hu_score + gang_total_score + piao_total_score) * self.match_enter_score
            win_score_info[winner.seat_id]["hu_list"] = hu_value["ming_tang"]

            if piao_total_score != 0:
                win_score_info[winner.seat_id]["piaoScore"] = piao_total_score * self.match_enter_score
            if gang_total_score != 0:
                win_score_info[winner.seat_id]["haveGang"] = gang_total_score * self.match_enter_score
            if qiang_gang_hu_total_score != 0:
                win_score_info[winner.seat_id]["qiangGangHu"] = qiang_gang_hu_total_score * self.match_enter_score
            if zhuang_xian_total_score != 0:
                win_score_info[winner.seat_id]["zhuangXian"] = zhuang_xian_total_score * self.match_enter_score

            win_score_info[winner.seat_id]["zhongNiao"] = bird_total_score * self.match_enter_score

            if not hu_value["is_qiang_gang_hu"]:
                if hu_value["is_zi_mo"]:
                    win_score_info[winner.seat_id]["ziMo"] = zi_mo_hu_score * self.match_enter_score
                else:
                    win_score_info[winner.seat_id]["jiePao"] = zi_mo_hu_score * self.match_enter_score

        return win_score_info, lose_info

    def deal_gang_info(self, win_score: dict, lose_info: dict, is_effective=True):
        result = deepcopy(win_score)
        result.update(lose_info)
        gang_record = self.__gang_record

        # print("gang_record = ", gang_record)

        def update_result_score(seat_id, act_name, score):
            if not result.get(seat_id):
                result[seat_id] = {"score": 0}
            result[seat_id]["score"] += score

            if not result[seat_id].get(act_name):
                result[seat_id][act_name] = 0
            result[seat_id][act_name] += score

        if not is_effective:
            for gang_info in gang_record:
                score_info = list(map(lambda score: -score, gang_info["score_info"]))
                self.update_player_score(score_info)
            return result

        for gang_info in gang_record:
            act = gang_info["act"]
            score_info = gang_info["score_info"]

            if act == ma_jiang.ACTION_TYPE_AN_GANG:
                for index in range(len(score_info)):
                    value = score_info[index]
                    update_result_score(index + 1, "anGang", value)

            elif act == ma_jiang.ACTION_TYPE_MING_GANG:
                for index in range(len(score_info)):
                    value = score_info[index]
                    update_result_score(index + 1, "mingGang", value)
            elif act == ma_jiang.ACTION_TYPE_GONG_GANG:
                for index in range(len(score_info)):
                    value = score_info[index]
                    if value > 0:
                        update_result_score(index + 1, "jieGang", value)
                    elif value < 0:
                        update_result_score(index + 1, "fangGang", value)

        # print("gang result= ", result)

        return result

    def __do_check_out(self, winner_list: list, is_huang_zhuang, bird_list, is_dismiss: bool):
        """ 结算当局积分 """

        self.__winner_list = winner_list

        if is_dismiss:
            return self.__dismiss_check_out()

        if is_huang_zhuang:
            return self.__huang_zhuang_check_out()

        result = self.__calc_check_out_result(winner_list)
        win_score_from, lose_info = self.__calc_win_score(result, bird_list,
                                                          winner_list)  # win_score, {seat_id: lose_score}

        win_seat_list = list(win_score_from.keys())
        win_seat_list.sort(key=lambda value: win_score_from[value]["score"], reverse=True)
        is_zi_mo = False
        for winner in winner_list:
            score_from = win_score_from[winner.seat_id]
            winner_zi_mo = bool(score_from.get("ziMo"))
            is_zi_mo = is_zi_mo or winner_zi_mo
            if is_zi_mo:
                break

        lose_all_score = 0
        lose_list = []
        for p in self.seats:
            if not p:
                continue
            if p in winner_list:
                continue

            is_dian_pao = False
            if is_zi_mo:
                is_dian_pao = False
            elif lose_info.get(p.seat_id):
                is_dian_pao = True

            if not lose_info.get(p.seat_id):
                lose_info[p.seat_id] = {"score": 0}
            else:
                lose_list.append(p)

            lose_score = lose_info.get(p.seat_id)["score"]

            if self.match_type == 1:
                if p.lock_score + p.score + lose_score < 0:
                    lose_score = -(p.lock_score + p.score)
                    lose_info[p.seat_id]["score"] = lose_score
                    self.__no_score_seat_id.append(p.uid)

            lose_all_score += lose_score
            p.on_round_over(lose_score, is_dian_pao, p.seat_id == self.__dealer, False, [])

        for seat_id in win_seat_list:
            winner = self.get_player_by_seat_id(seat_id)
            score_from = win_score_from[seat_id]
            winner_zi_mo = bool(score_from.get("ziMo"))
            win_score = score_from["score"]
            if lose_all_score + win_score > 0:
                win_score = -lose_all_score
                win_score_from[seat_id]["score"] = -lose_all_score

            lose_all_score += win_score

            winner.on_round_over(win_score, False, seat_id == self.__dealer, winner_zi_mo, [], )

        self.__lose_list = lose_list

        score_from = self.deal_gang_info(win_score_from, lose_info)

        return self.__make_win_info(bird_list=bird_list), score_from

    def __make_win_info(self, bird_list):
        hu_card = self.__curr_card
        ret = []
        for winner in self.__winner_list:
            if self.__qxd or self.__hqxd or self.__shqxd:
                seve_pairs = True
            else:
                seve_pairs = False
            print("player cards:", winner.cards, "====hu_card:", hu_card)
            _, hu_path = winner.can_hu(hu_card, self.__rule, seve_pairs, False)
            print("------hu_path: ", hu_path, " seve_pairs: ", seve_pairs)
            if hu_card == ma_jiang.NULL_CARD:
                hu_card = winner.mo_card

            ret.append({"rate": ROUND_RATE, "huCards": [hu_card], "lastSeat": self.__curr_seat_id, "huPath": hu_path,
                        "birdList": bird_list, "fanList": [], "huCardIndex": 1, "winner": winner.seat_id,
                        "handCardIndex": len(winner.zhuo_pai) + 1, })
        # ret.update(ming_tang)
        return ret

    def __pop_all_cards(self):
        ret = []
        for i in range(self.__ma_jiang_cards.left_count):
            ret.append(self.__ma_jiang_cards.pop())
        return ret

    def clear_all_user_chou_pai(self):
        for p in self.seats:
            if not p:
                continue
            p.clear_chou_pai_for_round()

    def __round_over(self, win_seat_list, is_huang_zhuang, is_dismiss):
        """ 一局结束 """
        if self.status != flow.T_PLAYING:
            return

        self.__ma_jiang_cards.clear_pop_order()
        self.clear_all_user_chou_pai()
        self.__mo_pai_total = 0
        self.__is_huang_zhuang = is_huang_zhuang
        if not self.round_review_data:
            self.__add_base_review_data()
        self.__set_status(flow.T_CHECK_OUT)

        winner_list = [self.get_player_by_seat_id(seat) for seat in win_seat_list or []]
        # if self.__yh:
        for p in winner_list:
            if not p:
                continue
            if ma_jiang.NAI_ZI not in p.cards:
                self.__ying_hu = True
        bird_list = []
        if not is_huang_zhuang and not is_dismiss:
            bird_list = self.__zhong_bird()
            self.inner_broad_cast(commands_game.BIRD_LIST, {"code": 0, "birdList": bird_list}, error.OK, 0, True)
        win_info, score_from = self.__do_check_out(winner_list, is_huang_zhuang, bird_list, is_dismiss)

        finish_type = ROUND_OVER_NORMAL
        if is_dismiss:
            finish_type = ROUND_OVER_DISMISS

        index = self.round_index
        self.round_index += 1
        result = {"seq": index, "hasNextRound": self.__has_next_round(), "seats": [], "finishType": finish_type,
                  "rate": 1, "isHuangZhuang": int(self.__is_huang_zhuang), "leftCards": self.__pop_all_cards(),
                  "winInfo": win_info, }

        if win_seat_list:
            result["winner"] = win_seat_list

        for p in self.seats:
            if not p:
                continue
            over_data = p.round_over_data
            if score_from.get(p.seat_id):
                over_data["scoreFrom"] = score_from[p.seat_id]
            else:
                over_data["scoreFrom"] = []

            result["seats"].append(over_data)
        for key in self.__simulate_cards:
            ret = {
                "seatID": key,
                "handCards": self.__simulate_cards[key],
                "tableCards": [],
                "score": 0,
                "totalScore": 0,
                "chui": -1,
                "scoreFrom": [],
                "auto_chupai":1 if p.is_auto_chupai  else 0
            }
            result["seats"].append(ret)
        result["dealer"] = self.__dealer
        print("round over: ", result)
        result["round_id"] = self.__save_round_log(index)
        self.__pre_jie_suan_data = result
        if not is_dismiss:
            self.inner_broad_cast(commands_game.ROUND_OVER, result, error.OK, 0, True)
        self.__gang_record = []

        self.table_info["round_index"] = self.round_index
        self.update_table_info()

        # self.__update_huang_zhuang_count(is_huang_zhuang)
        if not self.__has_next_round():  # 房间结束
            return self.__game_over()
        #机器人自动开始准备
        print('机器人自动开始准备')
        istrystart = 0
        isrealplaynum = 0
        for p in self.seats:
            if not p:
                continue
            isrealplaynum = isrealplaynum + 1
            if not p.is_auto_chupai:
                continue
            p.delay_ready = DelayCall(2,self.__delay_ready,p)
            if p.is_ready:
                istrystart = istrystart + 1
    def __delay_ready(self,p:Player):
        from games.hong_zhong_ma_jiang.game import GameServer
        GameServer.share_server().player_ready( p.uid)
    def __save_round_log(self, index):
        # if self.__is_request_dismiss_room:
        #     return 0
        round_id = logs_model.insert_round_log(self.record_id, index, self.game_type, self.seats)
        logs_model.add_round_review_log(
            {"record_id": self.record_id, "round_id": round_id, "commands": self.round_review_data})
        self.round_review_data.clear()
        return round_id

    def __is_round_over(self):
        """判断是否一局结束 当庄家打到了上游或者有两家及以上已出完"""
        count = 0
        for p in self.seats:
            if not p:
                continue
            if p.seat_id == self.__dealer and not p.cards:  # 庄家已出完，局结束
                return True
            if not p.cards:
                count += 1
        return count >= 2  # 超过两人出完牌，局结束

    def __call_player_by_start_seat_id(self, seat_id, func):
        if not seat_id or not func:
            return
        for i in range(seat_id, len(self.seats)):
            if not self.seats[i]:
                continue
            func(self.seats[i])
        for i in range(0, seat_id):
            if not self.seats[i]:
                continue
            func(self.seats[i])

    def __curr_player(self):
        return self.get_player_by_seat_id(self.__curr_seat_id)

    def __next_player(self, p) -> Player:
        """ 查找下一玩家 """
        for i in range(p.seat_id + 1, self.__total_seat):
            if self.seats[i]:
                return self.seats[i]
        for i in range(1, p.seat_id):
            if self.seats[i]:
                return self.seats[i]

    def __next_player_in_simulate(self, seat_id) -> Player:
        """ 查找下一玩家 """
        index = self.__simulate.index(seat_id)
        if index == len(self.__simulate) - 1:
            return self.__simulate[0]
        return self.__simulate[index + 1]

    def __chi_de_qi(self, p: Player, card):  # 判断玩家能否吃牌
        """
        判断能否吃得起某张牌
        :param p:
        :return:
        """
        if not p:
            return False
        if self.flow_status == flow.T_IN_PUBLIC_OPRATE:
            if self.__next_player(self.__curr_player()) != p:
                return False
        elif self.flow_status == flow.T_IN_MO_PAI_CALL:
            if p == self.__prev_player(self.__curr_player()):
                return False
        can = p.can_chi(card, self.__rule)
        if can:
            self.user_time_out_operator(p)
        return can

    def __peng_de_qi(self, p: Player, card):
        if not p:
            return False
        can = p.can_peng(card, self.__rule)
        if can:
            self.user_time_out_operator(p)
        return can

    def __hu_de_qi(self, p: Player, card: int, hu_type):
        if not p:
            return False

        # __hu_type 为0 只允许自摸
        if hu_type in (0, 2) and p != self.__curr_player():
            return False
        print("calc is hu de qi    seat_id  =  ", p.seat_id, "  ==  card  == ", card)
        can_hu, _ = p.can_hu(card, self.__rule, bool(self.__qxd))
        print("can hu  result = ", can_hu)
        if can_hu:
            self.user_time_out_operator(p)
        return can_hu

    # 暗杠使用
    def __jian_zi_hu(self, p: Player, card: int):
        if not p:
            return False

        # __hu_type 为0 只允许自摸
        # if hu_type == 0 and p != self.__curr_player():
        #    return False
        ting_list = self.__rule.get_ting_pai(p.zhuo_pai, p.cards)

        return len(ting_list) >= 28

    # 公杠使用
    def __pao_hu_de_qi(self, p: Player, card: int):
        if not p:
            return False

        can_hu, _ = p.can_hu(card, self.__rule, bool(self.__qxd))
        if can_hu:
            self.user_time_out_operator(p)
        return can_hu

    def __ming_gang_de_qi(self, p: Player):
        if not p:
            return False
        is_ming_gang, card = p.can_ming_gang(self.__rule)
        if is_ming_gang:
            self.user_time_out_operator(p)
        return is_ming_gang

    def __an_gang_de_qi(self, p: Player):
        if not p:
            return False
        is_an_gang, card = p.can_an_gang(self.__rule)
        if is_an_gang:
            self.user_time_out_operator(p)
        return is_an_gang

    def __gong_gang_de_qi(self, p: Player, card: int):
        if not p:
            return False
        is_gong_gang, card = p.can_gong_gang(card, self.__rule)
        if is_gong_gang:
            self.user_time_out_operator(p)
        return is_gong_gang

    def __can_operates(self):  # 判断是否有人能碰或吃出牌
        for p in self.seats:
            if not p:
                continue
            if p.hu_de_qi():
                return True
            if p.gong_gang_de_qi():
                return True
            if p.chi_de_qi():
                return True
            if p.peng_de_qi():
                return True
        return False

    def __calc_operates_after_chu_pai(self, p: Player, chu_pai_player: Player):
        result = []
        if not p or not chu_pai_player:
            return result

        if p == chu_pai_player:
            return result

        if self.__chi_de_qi(p, self.__curr_card):
            result.append(ma_jiang.ACTION_TYPE_CHI)
        if self.__peng_de_qi(p, self.__curr_card):
            result.append(ma_jiang.ACTION_TYPE_PENG)
        if self.__gong_gang_de_qi(p, self.__curr_card):
            result.append(ma_jiang.ACTION_TYPE_GONG_GANG)
        if self.__hu_de_qi(p, self.__curr_card, self.__hu_type):
            result.append(ma_jiang.ACTION_TYPE_HU)
        print("=========seat id :", p.seat_id, "==== result:", result)
        return result

    def enter_chu_pai_call(self):
        """ 进入出牌call
        如果是出牌后，先判断跑，有跑直接跑，无跑则判断有没有人碰、吃，如果没有，
        则进入摸牌的流程，有则继续等待玩家操作
        """
        if self.status != flow.T_PLAYING:
            return
        if self.flow_status != flow.T_IN_CHU_PAI:
            return
        self.__set_flow_status(flow.T_IN_PUBLIC_OPRATE)

        chu_pai_player = self.__curr_player()

        record = True
        for p in self.seats:
            if not p:
                continue

            result = {"seatID": self.__curr_seat_id, "cards": self.__curr_card, "seconds": flow.CALL_SECONDS,
                      "leftCount": self.__ma_jiang_cards.left_count, "auto_chupai":1 if p.is_auto_chupai  else 0}
            self.inner_send(p, commands_game.PLAYER_CHU_PAI, result, error.OK, record)

            operates = self.__calc_operates_after_chu_pai(p, chu_pai_player)
            p.operates = operates
            result["operates"] = operates
            self.inner_send(p, commands_game.PUBLIC_OPERATES, result, error.OK, record)
            record = False

        if self.__can_operates():
            return

        return self.__everyone_pass()

    def __clear_operates(self):
        for p in self.seats:
            if not p:
                continue
            p.operates = []

    def __mo_pai_old(self, choice_seat):
        """
        :return:
        """
        self.__clear_table_actions()
        if self.__ma_jiang_cards.left_count <= 0 or (
                self.__is_fixed_bird and self.__ma_jiang_cards.left_count <= self.__bird_count):  # 黄庄了
            return self.__round_over(None, True, False)

        if choice_seat:
            p = self.get_player_by_seat_id(choice_seat)
        else:
            p = self.__next_player(self.__curr_player())

        p.set_lou_hu(False)

        if len(self.__no_score_seat_id) > 0:
            return self.__round_over(None, True, True)

        self.__set_flow_status(flow.T_IN_MO_PAI)
        self.__clear_operates()
        self.__curr_seat_id = p.seat_id
        mo_card = self.__ma_jiang_cards.pop()
        self.__mo_pai_total += 1

        self.__enter_mo_pai_call(mo_card)

    def __mo_pai(self, choice_seat):
        """
        :return:
        """

        real_player_mo_pai = True
        self.__clear_table_actions()
        if self.__ma_jiang_cards.left_count <= 0 or (
                self.__is_fixed_bird and self.__ma_jiang_cards.left_count <= self.__bird_count):  # 黄庄了
            return self.__round_over(None, True, False)

        if choice_seat:
            p = self.get_player_by_seat_id(choice_seat)
        else:
            p = self.__next_player(self.__curr_player())
            if self.__curr_seat_id in self.__real_seats:
                simulate_seat_id = self.__next_player_in_simulate(self.__curr_seat_id)
                print("curr_seat_id = ", self.__curr_seat_id)
                print("simulate_seat_id = ", simulate_seat_id)
                print("__simulate_cards = ", self.__simulate_cards)
                simulate_card = self.__ma_jiang_cards.pop()
                self.__simulate_cards[simulate_seat_id].append(simulate_card)
                if self.__ma_jiang_cards.left_count <= 0:
                    return self.__round_over(None, True, False)

        p.set_lou_hu(False)

        if len(self.__no_score_seat_id) > 0:
            return self.__round_over(None, True, True)

        self.__set_flow_status(flow.T_IN_MO_PAI)
        self.__clear_operates()
        self.__curr_seat_id = p.seat_id
        change_card = p.get_change_card()
        if change_card and self.__ma_jiang_cards.get_last_card() == change_card:
            mo_card = self.__ma_jiang_cards.pop_last_card()
            p.remove_change_card()
        else:
            mo_card = self.__ma_jiang_cards.pop()
        self.__mo_pai_total += 1
        p.mo_card1 = mo_card
        self.user_time_out_operator(p, True)
        self.__enter_mo_pai_call(mo_card)
    def user_time_out_operator(self, player: Player , flag=False):
        if False:
            return
        if player.operator_out_time:
            player.operator_out_time.cancel()
        if not flag:
            for p in self.seats:
                if not p:
                    continue
                if p.uid != player.uid and p.operator_out_time:
                    p.operator_out_time.cancel()
                    p.operator_out_time = None

        print('红中麻将开始托管')
        player.operator_out_time = DelayCall(player.user_operation_timeout, self.__on_operator_time_out, player)


    def __on_operator_time_out(self, p: Player):
        from games.hong_zhong_ma_jiang.game import GameServer
        if not p.is_auto_chupai:
            p.user_operation_timeout = const.Auto_Play_TimeStamp + 1
            p.is_auto_chupai = True
            p.iscacel_auto_chupai = False
            GameServer.share_server().response_ok(p.uid,commands_game.AUTO_ATTACK_ONE,{"is_auto_chupai":p.is_auto_chupai})
        else:
            if p.iscacel_auto_chupai:
                p.iscacel_auto_chupai = False
                return

        from games.hong_zhong_ma_jiang.rule_hz_ma_jiang import RuleZZMaJiang
        data = {"cards":p.mo_card1}
        print(data)
        print( p.operates )
        if len(p.operates) > 0:
            GameServer.share_server().on_player_pass(p.uid,None)
        else:
            # 判断是否红中癞子麻将

            if RuleZZMaJiang.have_hong_zhong([p.mo_card1]):
                for cd in p.cards:
                    if RuleZZMaJiang.have_hong_zhong([cd]):
                        continue
                    data['cards'] = cd
                    break
            GameServer.share_server().on_player_chu_pai( p.uid,data)
    def __can_somebody_hu(self):
        for p in self.seats:
            if not p:
                continue
            if p.hu_de_qi():
                return True
        return False

    def __can_somebody_chi(self):  # 判断是否有人吃得起
        for p in self.seats:
            if not p:
                continue
            if p.chi_de_qi():
                return True
        return False

    def __can_somebody_peng(self):  # 判断是否有人能碰牌
        for p in self.seats:
            if not p:
                continue
            if p.peng_de_qi():
                return True
        return False

    def __can_somebody_ming_gang(self):  # 判断是否有人能杠
        for p in self.seats:
            if not p:
                continue
            if p.ming_gang_de_qi():
                return True
        return False

    def __can_somebody_an_gang(self):  # 判断是否有人能杠
        for p in self.seats:
            if not p:
                continue
            if p.an_gang_de_qi():
                return True
        return False

    def __can_somebody_gong_gang(self):  # 判断是否有人能杠
        for p in self.seats:
            if not p:
                continue
            if p.gong_gang_de_qi():
                return True
        return False

    def __can_somebody_pao(self):  # 判断是否有人能跑起
        for player in self.seats:
            if not player:
                continue
            if player.can_pao(self.__curr_card, self.flow_status == flow.T_IN_MO_PAI_CALL):
                return True
        return False

    def __calc_operates_after_mo_pai(self, p: Player):
        result = []
        if not p:
            return result

        if self.__ming_gang_de_qi(p):
            result.append(ma_jiang.ACTION_TYPE_MING_GANG)
        if self.__an_gang_de_qi(p):
            result.append(ma_jiang.ACTION_TYPE_AN_GANG)
        if self.__hu_de_qi(p, ma_jiang.NULL_CARD, self.__hu_type):
            result.append(ma_jiang.ACTION_TYPE_HU)
        return result

    def __calc_operates_after_ming_gang(self, p: Player, card: int, hu_type):
        result = []
        if not p:
            return result

        if self.__hu_de_qi(p, card, hu_type):
            result.append(ma_jiang.ACTION_TYPE_HU)

        return result

    def __calc_operates_after_an_gang(self, p: Player, card: int):
        result = []
        if not p:
            return result

        if self.__hu_de_qi(p, card, self.__can_qiang_gang_hu):
            result.append(ma_jiang.ACTION_TYPE_HU)
        # elif self.__jian_zi_hu(p, card):
        #     result.append(ma_jiang.ACTION_TYPE_HU)

        return result

    def __enter_ming_gang_call(self, curr_player, card):
        """
        :return:
        """
        if self.flow_status != flow.T_IN_MO_PAI_CALL:
            return

        self.__set_flow_status(flow.T_IN_MING_GANG_PAI_CALL)

        self.__clear_table_actions()
        self.__curr_card = card
        self.__curr_action_player = curr_player

        record = True
        for p in self.seats:
            if not p:
                continue

            if p.seat_id == curr_player.seat_id:
                continue

            operates = self.__calc_operates_after_ming_gang(p, card, 1)

            data = {"leftCount": self.__ma_jiang_cards.left_count, "seconds": flow.CALL_SECONDS, "operates": operates}

            p.operates = operates
            self.inner_send(p, commands_game.PUBLIC_OPERATES, data, error.OK, record)

            record = False

        if self.__can_somebody_hu():  # 有人可以胡，则需要等待
            return

        self.__do_ming_gang_end(card)

    def __do_ming_gang_end(self, card=0):
        curr_player = self.__curr_action_player
        calc_score = -1 * self.match_enter_score
        if self.match_type == 1:
            score = []
            for i in self.seats:
                if not i:
                    continue
                if i == curr_player:
                    continue
                lose_score = calc_score
                if i.lock_score + i.score <= abs(calc_score):
                    lose_score = -(i.lock_score + i.score)
                    self.__no_score_seat_id.append(i.uid)
                score.append(lose_score)
        else:
            score = [calc_score] * (self.player_count - 1)
        score.insert(curr_player.seat_id - 1, -sum(score))

        if card not in curr_player.gang_peng_cards:
            self.__add_gang_record(ma_jiang.ACTION_TYPE_MING_GANG, score)
            self.update_player_score(score)

        self.__mo_pai(curr_player.seat_id)

    def __enter_an_gang_call(self, curr_player, card):
        """
        :return:
        """
        if self.flow_status != flow.T_IN_MO_PAI_CALL:
            return

        self.__set_flow_status(flow.T_IN_AN_GANG_PAI_CALL)

        self.__clear_table_actions()
        self.__curr_card = card
        self.__curr_action_player = curr_player

        record = True
        for p in self.seats:
            if not p:
                continue

            if p.seat_id == curr_player.seat_id:
                continue

            operates = self.__calc_operates_after_an_gang(p, card)

            data = {"leftCount": self.__ma_jiang_cards.left_count, "seconds": flow.CALL_SECONDS, "operates": operates}

            p.operates = operates
            self.inner_send(p, commands_game.PUBLIC_OPERATES, data, error.OK, record)

            record = False

        if self.__can_somebody_hu():  # 有人可以胡，则需要等待
            return

        self.__do_an_gang_end(card)

    def __do_an_gang_end_old(self, card=0):
        curr_player = self.__curr_action_player
        calc_score = -2 * self.match_enter_score
        if self.match_type == 1:
            score = []
            for i in self.seats:
                if not i:
                    continue
                if i == curr_player:
                    continue
                lose_score = calc_score
                if i.lock_score + i.score <= abs(calc_score):
                    lose_score = -(i.lock_score + i.score)
                    self.__no_score_seat_id.append(i.uid)
                score.append(lose_score)
        else:
            score = [calc_score] * (self.player_count - 1)
        score.insert(curr_player.seat_id - 1, -sum(score))

        if card not in curr_player.gang_peng_cards:
            self.__add_gang_record(ma_jiang.ACTION_TYPE_AN_GANG, score)
            self.update_player_score(score)

        self.__mo_pai(curr_player.seat_id)

    def __do_an_gang_end(self, card=0):
        curr_player = self.__curr_action_player
        calc_score = -2 * self.match_enter_score
        if self.match_type == 1:
            score = []
            for i in self.seats:
                if not i:
                    continue
                if i == curr_player:
                    continue
                lose_score = calc_score
                if i.lock_score + i.score <= abs(calc_score):
                    lose_score = -(i.lock_score + i.score)
                    self.__no_score_seat_id.append(i.uid)
                score.append(lose_score)
        else:
            score = [calc_score] * (self.player_count - 1)
        score.insert(curr_player.seat_id - 1, -sum(score))

        self.__add_gang_record(ma_jiang.ACTION_TYPE_AN_GANG, score)
        self.update_player_score(score)

        self.__mo_pai(curr_player.seat_id)

    def __enter_gong_gang_call(self, curr_player, card, from_player):
        """
        :return:
        """
        print("func:  __enter_gong_gang_call")
        print("stat: ", self.flow_status)
        # if self.flow_status != flow.T_IN_CHU_PAI:
        #    return

        self.__set_flow_status(flow.T_IN_GONG_GANG_PAI_CALL)

        self.__clear_table_actions()
        self.__curr_card = card
        self.__curr_action_player = curr_player
        self.__curr_seat_id = curr_player.seat_id

        record = True
        for p in self.seats:
            if not p:
                continue

            if p.seat_id == curr_player.seat_id:
                continue

            operates = self.__calc_operates_after_ming_gang(p, card, self.__can_qiang_gang_hu)
            print("xxxxxxxxxxxxxxxx")
            data = {"leftCount": self.__ma_jiang_cards.left_count, "seconds": flow.CALL_SECONDS, "operates": operates}

            p.operates = operates
            self.inner_send(p, commands_game.PUBLIC_OPERATES, data, error.OK, record)
            print("player seat_id", p.seat_id, "===cards==", p.cards)

            record = False

        if self.__can_somebody_hu():  # 有人可以胡，则需要等待
            return

        self.__do_gong_gang_end(curr_player, from_player, card)

    def __do_gong_gang_end(self, p, from_player, card=0):
        # self.inner_broad_cast(commands_game.PLAYER_GANG, data, error.OK, 0, True)
        score = [0] * self.player_count
        calc_score = -1 * self.match_enter_score * (self.player_count - 1)
        if self.match_type == 1 and from_player.lock_score + from_player.score <= abs(calc_score):
            calc_score = -(from_player.lock_score + from_player.score)
            self.__no_score_seat_id.append(from_player.uid)
        if card in p.gang_peng_cards:
            calc_score = 0
        score[from_player.seat_id - 1] = calc_score
        score[p.seat_id - 1] = -sum(score)
        self.__curr_card_exist = 0

        # if card in p.gang_peng_cards:
        self.__add_gang_record(ma_jiang.ACTION_TYPE_GONG_GANG, score)
        self.update_player_score(score)
        self.__gong_gang_from_player = None
        self.__gong_gang_player = None
        self.__mo_pai(p.seat_id)

    def __get_all_out_cards_len(self):
        out_cards = []
        for i in self.seats:
            if not i:
                continue
            out_cards.append({"seatID": i.seat_id, "outCardLen": i.chu_card_len()})
        return out_cards

    def __enter_mo_pai_call(self, mo_card):
        """
        :return:
        """
        # if self.flow_status != flow.T_IN_MO_PAI:
        #     return

        self.__set_flow_status(flow.T_IN_MO_PAI_CALL)
        curr_player = self.__curr_player()

        curr_player.clear_chou_pai()

        for p in self.seats:
            if not p:
                continue

            data = {"seatID": curr_player.seat_id, "leftCount": self.__ma_jiang_cards.left_count,
                    "seconds": flow.CALL_SECONDS}

            if p.uid == curr_player.uid:
                data["handCards"] = deepcopy(p.cards)
                p.receive_card(mo_card)
                p.mo_card = mo_card
                operates = self.__calc_operates_after_mo_pai(p)
                data["operates"] = operates
                data["card"] = mo_card
                p.operates = operates
                self.inner_send(p, commands_game.PLAYER_MO_PAI, data, error.OK, True)
            else:
                self.inner_send(p, commands_game.PLAYER_MO_PAI, data, error.OK, False)

        if self.__can_somebody_hu():  # 有人可以胡，则需要等待
            return

        if self.__can_somebody_an_gang():  # 有人可以暗杠
            return

        if self.__can_somebody_ming_gang():  # 有人可以明杠
            return

        self.__turn_to_player_chu_pai(curr_player, False)

    def __enter_robot_mo_pai_call(self, mo_card):
        """
        :return:
        """
        # if self.flow_status != flow.T_IN_MO_PAI:
        #     return

        self.__set_flow_status(flow.T_IN_MO_PAI_CALL)
        curr_player = self.__curr_player()

        curr_player.clear_chou_pai()

        for p in self.seats:
            if not p:
                continue

            data = {"seatID": curr_player.seat_id, "leftCount": self.__ma_jiang_cards.left_count,
                    "seconds": flow.CALL_SECONDS}

            if p.uid == curr_player.uid:
                data["handCards"] = p.cards
                p.receive_card(mo_card)
                p.mo_card = mo_card
                operates = self.__calc_operates_after_mo_pai(p)
                data["operates"] = operates
                data["card"] = mo_card
                p.operates = operates
                self.inner_send(p, commands_game.PLAYER_MO_PAI, data, error.OK, True)
            else:
                self.inner_send(p, commands_game.PLAYER_MO_PAI, data, error.OK, False)

        if self.__can_somebody_hu():  # 有人可以胡，则需要等待
            return

        if self.__can_somebody_an_gang():  # 有人可以暗杠
            return

        if self.__can_somebody_ming_gang():  # 有人可以明杠
            return

        self.__turn_to_player_chu_pai(curr_player, False)

    def __turn_to_player_chu_pai(self, p: Player, is_header):
        """ 轮到某玩家出牌 """
        self.__curr_seat_id = p.seat_id
        self.__clear_table_actions()
        self.__set_flow_status(flow.T_IN_CHU_PAI)
        out_cards = self.__get_all_out_cards_len()
        seconds = flow.FIRST_CALL_SECONDS if is_header else flow.CALL_SECONDS
        result = {"seatID": p.seat_id, "remainTime": seconds, 'outCards': out_cards}
        self.inner_broad_cast(commands_game.TURN_TO, result, error.OK, p.uid)
        self.inner_send(p, commands_game.TURN_TO, result)

    def __prev_player(self, p) -> Player:
        """ 查找上一玩家 """
        for i in range(p.seat_id - 1, 0, -1):
            if 0 <= i < self.__total_seat and self.seats[i]:
                return self.seats[i]
        for i in range(self.__total_seat, p.seat_id, -1):
            if 0 <= i < self.__total_seat and self.seats[i]:
                return self.seats[i]

    @property
    def playing_num(self):  # 获得当局中没有被淘汰的玩家数量
        count = 0
        for i in range(1, self.__total_seat):
            if self.seats[i] and self.seats[i].in_playing:
                count += 1
        return count

    def __clear_round_result(self):
        self.__round_results.clear()

    def player_ready(self, p: Player):
        if self.status != flow.T_IDLE and self.status != flow.T_CHECK_OUT:
            return False
        p.is_ready = True
        return True

    def player_chu_pai(self, p: Player, card: int) -> int:
        """
        玩家出牌
        :param p:
        :param card:
        :return int
        """
        if self.status != flow.T_PLAYING:
            return error.RULE_ERROR
        if self.flow_status != flow.T_IN_CHU_PAI:
            return error.RULE_ERROR
        if card not in p.cards:
            return error.DATA_BROKEN
        if p.seat_id != self.__curr_seat_id:
            return error.NOT_YOUR_TURN

        #HONG_ZHONG 红中不允许被打出
        if card == 51:
            return error.RULE_ERROR

        # if p.cards.count(card) >= 3:  # 规则错误，不能出坎上的牌
        #     return error.RULE_ERROR


        p.chu_pai(card)
        p.add_chu_pai(card)
        self.__curr_card = card
        self.__curr_card_exist = 1
        self.__before_seat_id = self.__curr_seat_id
        return error.OK

    def __save_player_action(self, p, action, data=None):
        self.__player_actions.append([p.seat_id, action, data])

    def __has_do_action(self, p):
        for item in self.__player_actions:
            if item[0] == p.seat_id:
                return True
        return False

    def __get_chi_peng_card(self):
        return self.__curr_card if self.flow_status == flow.T_IN_MO_PAI_CALL else self.__curr_card

    def player_chi(self, p: Player, chi_pai) -> int:
        """ 玩家吃牌判断 """
        if self.status != flow.T_PLAYING:
            return error.RULE_ERROR
        if self.flow_status not in (flow.T_IN_PUBLIC_OPRATE, flow.T_IN_MO_PAI_CALL):
            return error.RULE_ERROR
        if self.__has_do_action(p):  # 不能再次操作
            return error.RULE_ERROR
        if not p.chi_de_qi():  # 吃不起
            return error.RULE_ERROR
        if not chi_pai or not self.__rule.is_ma_jiang_card(chi_pai[0]) or not self.__rule.is_ma_jiang_card(chi_pai[1]):
            return error.DATA_BROKEN

        card = self.__curr_card

        if p.is_chou_chi_pai(card):
            return error.RULE_ERROR

        self.__save_player_action(p, ma_jiang.ACTION_TYPE_CHI, (chi_pai,))
        data = {"seatID": p.seat_id, "isFinish": 0}
        self.inner_send(p, commands_game.PLAYER_CHI, data)
        self.user_time_out_operator(p)
        return error.OK

    def player_peng(self, p: Player, data) -> int:
        """ 玩家碰牌 """

        if self.status != flow.T_PLAYING:
            return error.RULE_ERROR
        if self.flow_status not in (flow.T_IN_PUBLIC_OPRATE,):
            return error.RULE_ERROR
        if self.__has_do_action(p):  # 不能再次操作
            return error.RULE_ERROR
        if not p.peng_de_qi():  # 检查能否碰得起
            return error.RULE_ERROR

        if p.ming_gang_de_qi() or p.gong_gang_de_qi():
            p.add_gang_peng_card(self.__curr_card)

        self.__save_player_action(p, ma_jiang.ACTION_TYPE_PENG, data)
        data = {"seatID": p.seat_id, "isFinish": 0}
        self.inner_send(p, commands_game.PLAYER_PENG, data)
        self.user_time_out_operator(p)
        return error.OK

    def player_gang(self, p: Player, data):
        if self.status != flow.T_PLAYING:
            return error.RULE_ERROR
        if self.flow_status not in (flow.T_IN_PUBLIC_OPRATE, flow.T_IN_MO_PAI_CALL):
            return error.RULE_ERROR

        gang_act = None
        if p.seat_id == self.__curr_seat_id:
            if p.ming_gang_de_qi():
                gang_act = ma_jiang.ACTION_TYPE_MING_GANG
            elif p.an_gang_de_qi():
                gang_act = ma_jiang.ACTION_TYPE_AN_GANG
        elif p.gong_gang_de_qi():
            gang_act = ma_jiang.ACTION_TYPE_GONG_GANG

        if not gang_act:
            return error.RULE_ERROR

        self.__save_player_action(p, gang_act, data)
        data = {"seatID": p.seat_id, "isFinish": 0}
        self.inner_send(p, commands_game.PLAYER_GANG, data)
        self.user_time_out_operator(p)
        return error.OK

    def player_pass(self, p: Player) -> int:
        """ 玩家过牌 """
        if self.status != flow.T_PLAYING:
            return error.RULE_ERROR
        if self.flow_status not in (
                flow.T_IN_PUBLIC_OPRATE, flow.T_IN_MO_PAI_CALL, flow.T_IN_MO_PAI, flow.T_IN_MING_GANG_PAI_CALL,
                flow.T_IN_AN_GANG_PAI_CALL, flow.T_IN_GONG_GANG_PAI_CALL):
            return error.RULE_ERROR
        if self.__has_do_action(p):  # 不允许再次操作
            return error.RULE_ERROR

        # if ma_jiang.ACTION_TYPE_PENG in p.operates:
        #     p.add_chou_peng_pai(self.__curr_card)

        if ma_jiang.ACTION_TYPE_HU in p.operates and p.seat_id != self.__curr_seat_id:
            p.set_lou_hu(True)

        if self.__is_chou_gang_pai == 1 and (
                ma_jiang.ACTION_TYPE_GONG_GANG in p.operates or ma_jiang.ACTION_TYPE_MING_GANG in p.operates):
            p.add_chou_gang_pai(self.__curr_card)

        self.__save_player_action(p, ma_jiang.ACTION_TYPE_GUO)
        self.inner_send(p, commands_game.PLAYER_PASS, {"seatID": self.__curr_seat_id})
        if p.operator_out_time:
            p.operator_out_time.cancel()
            p.operator_out_time = None
        return error.OK

    def player_hu(self, p: Player) -> int:
        if self.status != flow.T_PLAYING:
            return error.RULE_ERROR
        if self.flow_status not in (
                flow.T_IN_MO_PAI_CALL, flow.T_IN_MO_PAI, flow.T_IN_PUBLIC_OPRATE, flow.T_IN_MING_GANG_PAI_CALL,
                flow.T_IN_AN_GANG_PAI_CALL, flow.T_IN_GONG_GANG_PAI_CALL):
            return error.RULE_ERROR
        if self.__has_do_action(p):  # 不能再次操作
            return error.RULE_ERROR
        if not p.hu_de_qi():
            return error.RULE_ERROR

        card = self.__curr_card

        if p.is_chou_hu_pai(card):
            return error.RULE_ERROR

        self.__save_player_action(p, ma_jiang.ACTION_TYPE_HU)
        self.inner_send(p, commands_game.PLAYER_HU_PAI, {"huInfo": [{"seatID": p.seat_id, "isFinish": 0}]})
        for player in self.seats:
            if not player:
                continue
            if player.operator_out_time:
                player.operator_out_time.cancel()
                player.operator_out_time = None
        return error.OK

    def __get_hu_pai_shun_wei(self):
        ids = []
        p = self.__curr_player()
        ids.append(p.seat_id)
        np = self.__next_player(p)
        ids.append(np.seat_id)
        np = self.__next_player(np)
        ids.append(np.seat_id)
        return ids

    def __get_not_finish_seat_ids(self):
        seat_ids = list([1, 2, 3])
        for item in self.__player_actions:
            try:
                seat_ids.remove(item[0])
            except ValueError as data:
                print(data, seat_ids, self.__player_actions)
        return seat_ids

    def __is_player_actions_finish(self, operate_list):
        max_operate = self.get_not_operate_player_max_operate()
        priority = 0
        if max_operate:
            remain_max_info = max(list(self.get_not_operate_player_max_operate().items()),
                                  key=lambda v: v[1])  # (seat_id, action)

            priority = ma_jiang.ACTION_PRIORITY[remain_max_info[1]]

        already_max_info = max(list(operate_list.items()),
                               key=lambda v: self.get_action_priority(v[0]))  # (action, [seat_id])

        if priority > self.get_action_priority(already_max_info[0]):
            return False, already_max_info, max_operate

        return True, already_max_info, max_operate

    @property
    def not_operate_player_list(self):
        aready_action_seats = set([action[0] for action in self.__player_actions])
        return [p.seat_id for p in self.seats if p and p.seat_id not in aready_action_seats]

    @staticmethod
    def get_action_priority(act):
        if act not in ma_jiang.ACTION_PRIORITY:
            return 0

        return ma_jiang.ACTION_PRIORITY[act]

    def get_operate_player_max_operate(self):
        result = {}

        for player in self.seats:
            if not player:
                continue
            if player.operates:
                result[player.seat_id] = max(player.operates, key=self.get_action_priority)

        return result

    def get_not_operate_player_max_operate(self):
        result = {}

        for seat_id in self.not_operate_player_list:
            player = self.get_player_by_seat_id(seat_id)
            if player.operates:
                result[seat_id] = max(player.operates, key=self.get_action_priority)

        return result

    def check_action_end(self):
        action_priority = ma_jiang.ACTION_PRIORITY
        operate_list = {}

        for item in self.__player_actions:
            if item[1] in action_priority:
                if item[1] not in operate_list:
                    operate_list[item[1]] = []

                operate_list[item[1]].append(item[0])

        is_finish, max_operate_list, not_operate_max_list = self.__is_player_actions_finish(operate_list)

        if max_operate_list[0] == ma_jiang.ACTION_TYPE_HU:
            operate_list = self.get_operate_player_max_operate()
            hu_list = list(map(lambda value: value[0],
                               filter(lambda value: value[1] == ma_jiang.ACTION_TYPE_HU, operate_list.items())))
            winner_list = [self.get_player_by_seat_id(seat) for seat in hu_list or []]
            for p in winner_list:
                if p:
                    print("\n", p.cards)
            return self.__somebody_hu(hu_list)

        if not is_finish:
            return

        action_map = {ma_jiang.ACTION_TYPE_HU: self.__somebody_hu,
                      ma_jiang.ACTION_TYPE_PENG: self.__somebody_peng,
                      ma_jiang.ACTION_TYPE_CHI: self.__somebody_chi,
                      ma_jiang.ACTION_TYPE_GONG_GANG: self.__somebody_gong_gang,
                      ma_jiang.ACTION_TYPE_MING_GANG: self.__somebody_ming_gang,
                      ma_jiang.ACTION_TYPE_AN_GANG: self.__somebody_an_gang, }

        act = max_operate_list[0]
        self.__check_chou_operates(max_operate_list[0], max_operate_list[1])
        if act in action_map and max_operate_list[1]:
            result = action_map[act](max_operate_list[1])
            if result:
                self.__clear_lou_hu(max_operate_list[1])
            return result

        return self.__everyone_pass()  # 所有人都不要

    def __check_chou_operates(self, operate, seat_list):
        if operate in [ma_jiang.ACTION_TYPE_GONG_GANG, ma_jiang.ACTION_TYPE_MING_GANG]:
            return

        for seat_id in seat_list:
            player = self.get_player_by_seat_id(seat_id)
            if self.__is_chou_gang_pai == 1 and (
                    ma_jiang.ACTION_TYPE_GONG_GANG in player.operates or ma_jiang.ACTION_TYPE_MING_GANG in player.operates):
                player.add_chou_gang_pai(self.__curr_card or player.mo_card)

    def __clear_lou_hu(self, operates_list):
        for p in self.seats:
            if not p:
                continue

            if p.seat_id in operates_list:
                p.set_lou_hu(False)

    def __clear_table_actions(self):
        self.__player_actions.clear()
        self.__clear_operates()
        self.__curr_card = 0
        self.__curr_action_player = None

    def find_first_player(self, seat_ids) -> Player:  # 搜索胡或者吃当中离当前玩家最优先的玩家
        p = self.__curr_player()
        if p.seat_id in seat_ids:
            return p
        for i in range(self.player_total_count() - 1):
            p = self.__next_player(p)
            if p.seat_id in seat_ids:
                return p

    def update_player_score(self, update_info: list):
        """更新玩家分数"""
        result = []
        for index in range(len(update_info)):
            score = update_info[index]
            seat_id = index + 1
            if not score:
                continue

            p = self.get_player_by_seat_id(seat_id)
            if not p:
                continue

            now_score = p.update_score(score)
            result.append({"seatID": seat_id, "updateScore": score, "currScore": now_score})

        self.inner_broad_cast(commands_game.PLAYER_SCORE_UPDATE, {"code": 0, "scoreInfo": result}, error.OK, 0, True)

    def __somebody_hu(self, hu_list: list) -> bool:  # 三人均操作后判断有没有人胡牌
        self.__curr_card_exist = 0
        self.__hu_da_notify(hu_list)
        self.__round_over(hu_list, False, False)
        return True

    def __zhong_bird(self):
        bird_list = []
        bird_count = self.__bird_count

        if self.__ying_hu and self.__bird_count > 1:
            bird_count = self.__bird_count + self.__add_birds_count
        print("__add_birds_count = ", self.__add_birds_count)
        print("bird_count = ", bird_count)
        for i in range(bird_count):
            if self.__ma_jiang_cards.left_count > 0:
                bird_list.append(self.__ma_jiang_cards.pop())
            else:
                break
        print("bird_list = ", bird_list)
        return bird_list

    def __hu_da_notify(self, hu_list):
        """ 胡牌通知客户端 """
        data = []
        hu_card = self.__curr_card
        for seat_id in hu_list:
            p = self.get_player_by_seat_id(seat_id)
            if hu_card == ma_jiang.NULL_CARD:
                hu_card = p.mo_card
            data.append(
                {"huCards": [hu_card], "seatID": p.seat_id, "preSeatID": self.__curr_player().seat_id, "isFinish": 1,
                 "isZiMo": p.seat_id == self.__curr_player().seat_id, "shouPai": p.cards,
                 "isQiangGangHu": self.flow_status in (
                     flow.T_IN_GONG_GANG_PAI_CALL, flow.T_IN_AN_GANG_PAI_CALL, flow.T_IN_MING_GANG_PAI_CALL),
                 "flow": self.flow_status})
        print("broad_cast_hu_info:", data, "\n")
        self.inner_broad_cast(commands_game.PLAYER_HU_PAI, {"huInfo": data}, error.OK, 0, True)

    def __add_gang_record(self, act, score_info):
        self.__gang_record.append({"act": act, "score_info": score_info, })

    def __somebody_an_gang_old(self, gang_list: list) -> bool:
        if len(gang_list) != 1:
            return False

        p = self.get_player_by_seat_id(gang_list[0])
        if not p:
            return False

        is_an_gang, card = p.can_an_gang(self.__rule)
        flag = p.an_gang(card, self.__rule)
        data = {"fromSeatID": self.__curr_seat_id, "seatID": p.seat_id, "isFinish": int(flag), "card": card,
                "act": ma_jiang.ACTION_TYPE_AN_GANG}

        if flag:
            calc_score = -2 * self.match_enter_score
            if self.match_type == 1:
                score = []
                for i in self.seats:
                    if not i:
                        continue
                    if i == p:
                        continue
                    lose_score = calc_score
                    if i.lock_score + i.score <= abs(calc_score):
                        lose_score = -(i.lock_score + i.score)
                        self.__no_score_seat_id.append(i.uid)
                    score.append(lose_score)
            else:
                score = [calc_score] * (self.player_count - 1)
            score.insert(p.seat_id - 1, -sum(score))
            self.__add_gang_record(ma_jiang.ACTION_TYPE_AN_GANG, score)
            self.update_player_score(score)
            self.inner_broad_cast(commands_game.PLAYER_GANG, data, error.OK, 0, True)
            self.__mo_pai(p.seat_id)
            return True
        return False

    def __somebody_ming_gang(self, gang_list: list) -> bool:
        if len(gang_list) != 1:
            return False

        p = self.get_player_by_seat_id(gang_list[0])
        if not p:
            return False

        is_ming_gang, card = p.can_ming_gang(self.__rule)

        flag = p.ming_gang(card, self.__rule)
        data = {"fromSeatId": self.__curr_seat_id, "seatID": p.seat_id, "isFinish": int(flag), "card": card,
                "act": ma_jiang.ACTION_TYPE_MING_GANG}

        if flag:
            self.inner_broad_cast(commands_game.PLAYER_GANG, data, error.OK, 0, True)
            self.__enter_ming_gang_call(p, card)
            return True
        return False

    def __somebody_an_gang(self, gang_list: list) -> bool:
        if len(gang_list) != 1:
            return False

        p = self.get_player_by_seat_id(gang_list[0])
        if not p:
            return False

        is_an_gang, card = p.can_an_gang(self.__rule)
        flag = p.an_gang(card, self.__rule)
        data = {"fromSeatID": self.__curr_seat_id, "seatID": p.seat_id, "isFinish": int(flag), "card": card,
                "act": ma_jiang.ACTION_TYPE_AN_GANG}

        if flag:
            self.inner_broad_cast(commands_game.PLAYER_GANG, data, error.OK, 0, True)
            self.__enter_an_gang_call(p, card)
            return True
        return False

    def __somebody_gong_gang_old(self, gang_list: list) -> bool:
        if len(gang_list) != 1:
            return False

        p = self.get_player_by_seat_id(gang_list[0])
        from_p = self.get_player_by_seat_id(self.__curr_seat_id)
        if not p:
            return False

        card = from_p.pop_chu_pai()
        flag = p.gong_gang(card, self.__rule)
        data = {"fromSeatId": self.__curr_seat_id, "seatID": p.seat_id, "isFinish": int(flag), "card": card,
                "act": ma_jiang.ACTION_TYPE_GONG_GANG}

        from_player = self.__curr_player()
        if flag:
            score = [0] * self.player_count
            calc_score = -1 * self.match_enter_score * (self.player_count - 1)
            if self.match_type == 1 and from_player.lock_score + from_player.score <= abs(calc_score):
                calc_score = -(from_player.lock_score + from_player.score)
                self.__no_score_seat_id.append(from_player.uid)
            if card in p.gang_peng_cards:
                calc_score = 0
            score[from_player.seat_id - 1] = calc_score
            score[p.seat_id - 1] = -sum(score)
            self.__curr_card_exist = 0
            if card in p.gang_peng_cards:
                self.__add_gang_record(ma_jiang.ACTION_TYPE_GONG_GANG, score)
                self.update_player_score(score)
            self.inner_broad_cast(commands_game.PLAYER_GANG, data, error.OK, 0, True)
            self.__mo_pai(p.seat_id)
            return True
        return False

    def __somebody_gong_gang(self, gang_list: list) -> bool:
        if len(gang_list) != 1:
            return False

        p = self.get_player_by_seat_id(gang_list[0])
        from_p = self.get_player_by_seat_id(self.__curr_seat_id)
        if not p:
            return False

        card = from_p.pop_chu_pai()
        flag = p.gong_gang(card, self.__rule)
        data = {"fromSeatId": self.__curr_seat_id, "seatID": p.seat_id, "isFinish": int(flag), "card": card,
                "act": ma_jiang.ACTION_TYPE_GONG_GANG}

        if flag:
            self.__gong_gang_player = p
            self.__gong_gang_from_player = from_p
            self.inner_broad_cast(commands_game.PLAYER_GANG, data, error.OK, 0, True)
            self.__enter_gong_gang_call(p, card, from_p)
            return True
        return False

    def __somebody_peng(self, peng_list: list) -> bool:  # 三人均操作后判断有没有人碰牌
        if len(peng_list) != 1:
            return False

        p = self.get_player_by_seat_id(peng_list[0])
        from_p = self.get_player_by_seat_id(self.__curr_seat_id)
        if not p or not from_p:
            return False

        card = from_p.pop_chu_pai()
        flag = p.peng(card)

        data = {"fromSeatID": self.__curr_seat_id, "seatID": p.seat_id, "isFinish": int(flag), "card": card}
        if flag:
            self.__curr_card_exist = 0
            self.inner_broad_cast(commands_game.PLAYER_PENG, data, error.OK, 0, True)
            self.__turn_to_player_chu_pai(p, False)
            return True
        return False

    def __somebody_chi(self, chi_list):  # 三人均操作后判断有没有人吃牌
        if not chi_list:
            return False

        p = self.find_first_player(chi_list)
        from_p = self.get_player_by_seat_id(self.__curr_seat_id)
        if not p or not from_p:
            return False

        data = None
        for item in self.__player_actions:
            seat_id, action, tmp = item
            if seat_id == p.seat_id and action == commands_game.PLAYER_CHI:
                data = tmp
                break
        if not data or 2 != len(data):
            return False

        chi_pai = data
        card = from_p.pop_chu_pai()
        flag = p.chi(card, chi_pai, self.__rule)
        data = {"fromSeatId": self.__curr_seat_id, "seatID": p.seat_id, "isFinish": int(flag), "card": card,
                "chiPai": chi_pai}

        if not flag:
            return False

        self.__curr_card_exist = 0
        self.inner_broad_cast(commands_game.PLAYER_CHI, data, error.OK, 0, True)
        self.__turn_to_player_chu_pai(p, False)
        return True

    def __everyone_pass(self):
        p = self.__curr_player()
        if self.flow_status == flow.T_IN_MO_PAI_CALL:  # 偎胡则不检查，提胡要检查八皮
            return self.__turn_to_player_chu_pai(p, False)
        elif self.flow_status == flow.T_IN_MING_GANG_PAI_CALL:
            return self.__do_ming_gang_end()
        elif self.flow_status == flow.T_IN_AN_GANG_PAI_CALL:
            return self.__do_an_gang_end()
        elif self.flow_status == flow.T_IN_GONG_GANG_PAI_CALL:
            return self.__do_gong_gang_end(self.__gong_gang_player, self.__gong_gang_from_player)

        return self.__mo_pai(None)  # 继续摸牌

    def player_quit(self, player: Player, reason=error.OK):
        """ 退出房间 """
        p = self.seats[player.seat_id]
        if not p or p != player:
            return error.USER_NOT_EXIST, None
        # if self.is_agent == 0 and player.uid == self.owner:  # 房主不允许退出，只能解散房间
        #     return error.RULE_ERROR, None
        if self.status != flow.T_IDLE:
            return error.RULE_ERROR, None
        self.seats[player.seat_id] = None
        player.on_stand_up()
        if self.match_type == 1:
            player.return_score(self.club_id)
        #self.__reset_player_ready()  # 有人退出房间时清理掉所有准备状态
        if p.uid in self.table_info["player_list"]:
            self.table_info["player_list"].remove(p.uid)
            self.del_player_in_table_info(p.uid)
            self.update_table_info()
        self.remove_empty_judge()
        return error.OK, {"uid": player.uid, "code": reason, "kickTime": 100}

    def __reset_player_ready(self):
        for p in self.seats:  # 有人退出房间时清理掉所有准备状态
            if not p:
                continue
            p.is_ready = False

    def player_join(self, player: Player):
        """ 加入房间 """
        o_seat_id = self.get_seat_id(player.uid)
        seat_id = o_seat_id if o_seat_id > 0 else self.__search_empty_seat()
        if seat_id < 0:
            return error.TABLE_FULL, None,0
        if self.union_id == -1:
            if self.check_club_block(player) != error.OK:
                return error.TABLE_PLAYER_BLOCK, None,0
            code = self.check_diamond_and_yuan_bao_and_tip(player)
            if code != error.OK:
                return code, None,0

        else:
            if self.check_union_block(player) != error.OK:
                return error.TABLE_PLAYER_BLOCK, None,0


        for p in self.seats:  # 有人退出房间时清理掉所有准备状态
            if not p:
                continue
            print("p.is_ready:",p.is_ready)


        #if self.status == flow.T_IDLE and o_seat_id <= 0:
        #    self.__reset_player_ready()

        player.judge_info = {"naiZi": ma_jiang.NAI_ZI}

        player.on_sit_down(self.tid, seat_id)
        player.offline = False
        if not player.is_ready:
            player.is_ready = self.status > flow.T_READY

        self.seats[seat_id] = player
        tid = 0
        if player.uid not in self.table_info["player_list"]:
            self.table_info["player_list"].append(player.uid)
            tid = self.add_player_in_table_info(player.club_info)
            self.update_table_info()
        return error.OK, {"roomID": self.tid}, tid

    def player_request_dismiss(self, player: Player, is_agree: int):
        if player.isround_require and is_agree == 2:
            self.inner_send(player, commands_game.REQUEST_DISMISS,
                            None, error.COMMAND_DENNY)
            return
        if is_agree == 2:
            player.isround_require = True
        if self.status == flow.T_IDLE:
            return
        if is_agree and not self.__dismiss_timer:
            self.__dismiss_timer = DelayCall(DISMISS_SECONDS, self.__on_dismiss_time_out)
        if not self.__dismiss_timer:
            self.inner_send(player, commands_game.REQUEST_DISMISS, None, error.COMMAND_DENNY)
            return

        if is_agree:
            self.__agree_seats.add(player.seat_id)
        else:
            self.__disagree_seats.add(player.seat_id)
        all_agree = len(self.__agree_seats) >= self.player_total_count()
        anyone_disagree = len(self.__disagree_seats) > 0
        is_end = all_agree or anyone_disagree
        if not is_end:
            return self.__send_dismiss_result()

        is_dismiss = all_agree
        if anyone_disagree:
            is_dismiss = False

        self.__do_player_request_dismiss(is_dismiss)

    def __clean_dismiss(self):
        if self.__dismiss_timer:
            self.__dismiss_timer.cancel()
            self.__dismiss_timer = None
        self.__agree_seats.clear()
        self.__disagree_seats.clear()

    def __do_player_request_dismiss(self, is_dismiss):
        self.__send_dismiss_result(is_dismiss)
        if not is_dismiss:
            self.__clean_dismiss()
            return
        # self.__is_request_dismiss_room = True
        self.force_dismiss()

    def force_dismiss(self):
        """强制解散"""
        DelayCall(0.1, self.__clean_dismiss)
        self.__is_dismiss = True
        self.__dismiss_round_index = self.round_index
        if self.status != flow.T_PLAYING:
            return self.__game_over()
        self.__round_over(None, False, True)

    def make_dismiss_data(self, is_dismiss=None):
        left_seconds = DISMISS_SECONDS
        if self.__dismiss_timer:
            left_seconds = self.__dismiss_timer.left_seconds()
        data = {"configTime": DISMISS_SECONDS, "remainTime": left_seconds, "yesSeatIDs": list(self.__agree_seats),
                "noSeatIDs": list(self.__disagree_seats)}
        if not (is_dismiss is None):
            data['result'] = is_dismiss
        return data

    def __send_dismiss_result(self, is_dismiss=None):
        data = self.make_dismiss_data(is_dismiss)
        self.inner_broad_cast(commands_game.REQUEST_DISMISS, data)

    def __on_dismiss_time_out(self):
        self.__do_player_request_dismiss(True)

    def player_connect_changed(self, player: Player) -> None:
        data = {"uid": player.uid, "IP": player.ip, "offline": player.offline}
        self.inner_broad_cast(commands_game.PLAYER_ONLINE, data)

    def set_cards_in_debug(self, cards, dealer):
        if const.IS_DEBUG is not True:
            return error.RULE_ERROR

        if not cards or len(cards) != 5:
            return error.DATA_BROKEN

        all_cards = []
        for l in cards:
            if not l:
                continue
            if type(l) is not list or len(l) > 13:
                return error.DATA_BROKEN
            if not self.__rule.is_correct_cards(l):
                return error.DATA_BROKEN
            all_cards.extend(l)

        self.__ma_jiang_cards.set_pop_order(cards)

        if dealer and 0 < dealer < self.__total_seat:
            self.__fixed_dealer = int(dealer)
        return error.OK

    def __add_review_log(self, cmd, data):
        message = protocol_utils.pack_client_message(const.SERVICE_HZMJ, cmd, deepcopy(data))
        self.__round_review_data.append(message)

    def owner_dismiss(self):
        """房主解散房间"""
        self.__do_dismiss()

    def __do_dismiss(self):
        self.__ma_jiang_cards = None
        self.on_match_game_over()
        for p in self.seats:
            if not p:
                continue
            p.on_game_over()
        self.seats = []
        tables_model.remove(self.tid)
        self.share_service().on_table_game_over(self)
        # self.owner_player.remove_relation_tid(self.tid)
        self.update_table_info(True)

    def debug_cards(self, nickname, from_idx, to_idx):
        logs_model.add_debug_log(self.record_id, self.round_index, self.tid, nickname)
        if self.status != flow.T_PLAYING:
            return 0
        if not self.__ma_jiang_cards:
            return 0
        player_count = len(self.seats) - 1
        return self.__ma_jiang_cards.modify_card_index(from_idx, to_idx, self.__mo_pai_total + player_count * 13)

    def debug_get_players(self):
        data = {"players": []}
        for i in self.seats:
            if not i:
                continue
            data['players'].append(i.get_debug_data())
        data['status'] = self.status
        data['turn'] = self.__curr_seat_id
        data['card'] = self.__ma_jiang_cards.get_cards()
        player_count = len(self.seats) - 1
        data['curr_idx'] = self.__mo_pai_total + player_count * 13
        return data
