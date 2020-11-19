# coding:utf-8
from copy import deepcopy

import pydash

from base import const
from base import error
from base.base_judge import BaseJudge
from games.cs_ma_jiang import ma_jiang, flow
from models import logs_model as logs_model
from models import onlines_model
from models import tables_model
from protocol import protocol_utils
from utils import utils
from utils.twisted_tools import DelayCall
from . import commands_game
from .ma_jiang_card import MaJiangCard
from .player import Player
from .rule_ma_jiang import RuleMaJiang
from models import union_model

ROUND_RATE = 1  # 单局倍率
DISMISS_SECONDS = 180  # 解散房间的等待时间
OPERATOR_TIME_OUT = 10  # 用户操作超时时间
PIAO_TIME_SECONDS = 10  # 飘分倒计时

ROUND_OVER_NORMAL = 0  # 正常结束
ROUND_OVER_DISMISS = 1  # 解散结束
ADJUST_SCORE = 20  # 触发调整积分


class CsMaJiangJudge(BaseJudge):
    def __init__(self, ret, service):
        BaseJudge.__init__(self, ret, service)
        self.__no_score_seat_id = []
        self.__bird_count = int(self.rule_details.get("birdCount", 0))
        self.__limit_score = max(int(self.rule_details.get("limitScore", 0)), 0)
        self.__begin_hu_list = list(self.rule_details.get("beginHuList", []))
        self.__middle_hu_list = list(self.rule_details.get("middleHuList", []))
        self.__hai_di_type = int(self.rule_details.get("haiDiType", 0))  # 0无鸟 1全中鸟
        self.__after_gang_cards_count = int(self.rule_details.get("afterGangCardsCount", 0))  # 杠后几张
        self.__zhuang_type = int(self.rule_details.get("zhuangType", 0))  # 胡牌庄类型 0 为胡牌为庄 1庄闲模式
        self.__bird_score_type = int(self.rule_details.get("birdScoreType", 0))  # 胡牌庄类型 0为加分 1为乘分 2为加分
        self.__lock_cards_type = int(self.rule_details.get("lockCardsType", 0))  # 锁牌类型 0为半开放 1为全开放
        self.__total_seat = int(self.rule_details.get("totalSeat", 4)) + 1  # 当前牌局人数
        self.__piao_type = int(self.rule_details.get("piao_type", 0))  # 飘分类型  0 不飘 1 首局飘分 2 每局飘分
        self.__full_pai = int(self.rule_details.get("fullPai", 0))  # 1-全牌， 2-少牌, 0
        self.__bird_type = 1 == int(self.rule_details.get("birdType", 1))  # 0 159鸟 1 顺序鸟
        self.__que_yi_men = int(self.rule_details.get("queYiMen", 0)) == 1  # 缺一门(条子)
        self.__men_qing = int(self.rule_details.get('menQianQing', 0)) == 1  # 门清
        # self.__que_yi_men = int(self.rule_details.get("queYiMen", 0))  # 缺一门(条子)
        self.__begin_hu_is_zhua_niao = 1 == int(self.rule_details.get("beginHuBird", 1))  # 起手胡是否抓鸟 0 不抓 1 抓

        # 两人长沙麻将 起手胡不抓鸟
        # 庄闲模式 起手胡不抓鸟
        if self.__total_seat - 1 == 2 or self.__zhuang_type == 1:
            self.__begin_hu_is_zhua_niao = False

        self.__rule = self.__fetch_rule()

        self.__mo_pai_total = 0
        self.__chu_pai_count = 0
        self.__round_results = {}
        self.__dealer = -1  # 庄家ID
        self.__curr_seat_id = 0
        self.__before_seat_id = 0
        self.seats = []
        self.__round_results = {}
        self.status = flow.T_IDLE
        self.flow_status = flow.T_IN_IDLE  # 流程状态
        self.__flow_status_history = []
        self.__dismiss_timer = None  # 解散房间定时器
        self.__piao_timer = None  # 玩家飘分定时器

        self.__init_card()

        self.__flow = ""
        self.__service = None
        self.__agree_seats = set()
        self.__disagree_seats = set()
        self.__is_dismiss = False
        self.__dismiss_round_index = 1
        self.__init_seats()

        self.__winner_list = []
        self.__lose_list = []
        self.__is_huang_zhuang = False
        self.__curr_cards = [ma_jiang.NULL_CARD]  # 当前牌
        self.__curr_card_exist = 0  # 当前牌是否存在
        self.__player_actions = []  # 玩家动作
        self.__piao_status = False

        self.__middle_hu_record = []
        self.__dice_record = []

        self.__fixed_dealer = 0
        self.__hai_di_player = None

        self.__prev_winner = 0
        self.__request_hai_di_count = 0
        self.__init_hu_options()
        self.__init_middle_options()

        self.update_table_info()
        self.update_table_info_max_player(self.__total_seat)

        # 两人处理
        self.__real_seats = []
        self.__simulate = []
        self.__curr_simulate_seat_id = 0
        self.__simulate_cards = {}

        self.__is_request_dismiss_room = False
        # if self.__zhuang_type == 1 and self.__bird_score_type == 1:
        #     self.__bird_count = 1


    def __inner_send_from_service(self, p, cmd, data, code=error.OK, service_type=None):
        if not p:
            return
        body = protocol_utils.pack_client_body(data, code)
        self.share_service().send_body_to_player(p.uid, cmd, body, service_type=service_type)

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

    @property
    def curr_cards(self):
        return self.__curr_cards

    @property
    def piao_type(self):
        return self.__piao_type

    @property
    def piao_timer(self):
        return self.__piao_timer

    @curr_cards.setter
    def curr_cards(self, cards: list):
        self.__curr_cards = cards

    def __init_hu_options(self):

        self.__begin_hu_options = self.__rule.get_begin_option(self.__begin_hu_list, is_que_yi_men = self.__que_yi_men)
        # self.__begin_hu_options = self.__rule.get_begin_option(self.__begin_hu_list)

    def __init_middle_options(self):
        self.__middle_hu_options = self.__rule.get_middle_option(self.__middle_hu_list)

    def __init_card(self):
        self.__ma_jiang_cards = MaJiangCard(self.__que_yi_men)  # 初始化麻将

    def __init_seats(self):
        self.seats = [None] * self.__total_seat

    @staticmethod
    def __fetch_rule():
        from .rule_cs_ma_jiang import RuleCSMaJiang
        return RuleCSMaJiang

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
        self.__flow_status_history.append(status)
        self.logger.debug("set flow status: {0}".format(status))

    def get_info(self):
        """ 获得房间基本信息 """
        result = BaseJudge.get_info(self)
        if self.status == flow.T_PLAYING:
            result['inFlow'] = self.flow_status
            result['dealer'] = self.__dealer

            result['lastSeatID'] = self.__before_seat_id
            result["turn"] = self.__curr_seat_id

            result['remainSeconds'] = 0
            result["operateSeats"] = self.__get_operate_seats()
            result["leftCount"] = self.__ma_jiang_cards.left_count
            result["lastCards"] = self.curr_cards[0] == ma_jiang.NULL_CARD and [] or self.curr_cards
            result["isLastCardExist"] = self.__curr_card_exist
            result["middleHu"] = int(len(self.__middle_hu_record) != 0)

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

    # 根据玩家uid来获得玩家的坐位ID
    def get_seat_id(self, uid):
        for i in range(1, self.__total_seat):
            if self.seats[i] and self.seats[i].uid == uid:
                return i
        return -1

    def notify_distance(self):
        if self.status != flow.T_IN_IDLE:
            return
        if (self.__total_seat - 1) != self.player_count:
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

    # 检查是否已经满足条件可以开始游戏
    def __check_game_start(self):
        if self.status != flow.T_IDLE:  # 状态不对
            return False
        if (self.__total_seat - 1) != self.player_count:  # 人数未满
            return False
        if (self.__total_seat - 1) != self.ready_player_count:  # 全部准备
            return False
        if self.__piao_type == 0 or (self.__piao_type == 1 and self.round_index > 1):
            self.__set_status(flow.T_READY)
            self.__game_start()
        else:
            if not self.__piao_status:
                self.__set_status(flow.T_PLAYING)
                for p in self.seats:
                    if not p:
                        continue
                    p.piao_score = -1
                    p.on_round_start()
                self.__piao_status = True
                piao_data = {"piao_time": PIAO_TIME_SECONDS}
                self.inner_broad_cast(commands_game.PIAO_FEN, piao_data)
                if self.__piao_timer:
                    self.__piao_timer.cancel()
                self.__piao_timer = DelayCall(PIAO_TIME_SECONDS, self.__paio_timer)

        return True

    def __paio_timer(self):
        for p in self.seats:
            if not p:
                continue
            if p.piao_score == -1:
                p.piao_score = 0
                data = {"seat_id": p.seat_id, "score": 0}
                self.inner_broad_cast(commands_game.PLAYER_PIAO_FEN, data)
        self.__set_status(flow.T_READY)
        self.__game_start()
        self.__piao_status = False

    def piao_end(self):
        self.__set_status(flow.T_READY)
        self.__game_start()

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

    def get_player_by_seat_id(self, seat_id) -> Player:
        if 0 < seat_id < len(self.seats):
            p = self.seats[seat_id]
            if isinstance(p, Player):
                return p

    def get_player_by_uid(self, uid) -> Player:
        for p in self.seats:
            if not p:
                continue
            if p.uid == uid:
                return p

    def __game_start(self):
        """ 游戏开始 """
        if self.status != flow.T_READY:
            return
        ids = []
        for p in self.seats:
            if not p:
                continue
            ids.append(p.uid)
            if self.union_id != -1:
                energy = union_model.get_player_energy_by_union_id(self.union_id, p.uid)['energy']
                p.on_game_start(energy, self.round_index)
            else:
                p.on_game_start(self.match_score, self.round_index)
        if self.round_index == 1 or self.__is_huang_zhuang:
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
        # result = {"gid": 1, "seats": [], "match": []}
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
        from games.cs_ma_jiang.game import GameServer
        GameServer.share_server().publish(2,6,{'union_id':self.union_id,'uid':1,'selfuid':0,'type':6,
                                               'tid':self.tid,'subfloor':self.sub_floor_id},9999)


    def get_player_data(self, p: Player):

        result = p.get_all_data(self.status)
        if self.__has_do_action(p):
            del result["operates"]
        else:
            result["operates"] = self.__format_operates(result.get("operates", dict()))

        return result

    def __save_game_record(self, finish_data):
        logs_model.insert_room_log(self.record_id, self.tid, self.game_type, self.seats, self.owner,
                                   self.total_round, self.rule_details, self.club_id,
                                   finish_data, self.group_id, self.dec_diamond, self.match_type, self.floor,
                                   self.sub_floor_id, self.match_config, self.union_id)

    def player_total_count(self):
        return self.__total_seat - 1

    def __choose_winner(self):
        players = []
        for i in self.seats:
            if not i:
                continue
            if i.score >= ADJUST_SCORE:
                players.append(i)
        return players

    def __deal_cards(self):
        """ 发牌，每人13张 """
        if self.flow_status not in (flow.T_IN_IDLE,):
            return

        self.__ma_jiang_cards.shuffle(self.player_total_count())
        for i in range(13):
            for p in self.seats:
                if not p:
                    continue
                c = self.__ma_jiang_cards.pop()
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


        #self.seats[1].cards = [12,13,14,15,17,17,18,18,19,19,38,38,38]
        #self.seats[2].cards = [38,11,11,12,12,12,13,13,13,16,16,16,18]
        #self.seats[3].cards = [21,21,21,21,23,23,25,25,13,13,38,38,38]
        #self.seats[4].cards = [11,13,16,17,19,34,26,25,34,36,39,37,37]


        index = self.round_index
        result = {"dealerSeatID": self.__dealer, "remainCards": self.__ma_jiang_cards.left_count,
                  "seq": index + 1}

        for p in self.seats:
            if not p:
                continue
            result["handCards"] = p.cards
            self.inner_send(p, commands_game.DEAL_CARDS, result)

        self.__add_base_review_data()
        self.__mo_pai(self.__dealer)

    def __add_base_review_data(self):
        BaseJudge.add_base_review_data(self)
        for p in self.seats:
            if not p:
                continue

            data = p.get_all_data(self.status)
            self.add_review_log(commands_game.PLAYER_ENTER_ROOM, data)

        self.add_review_log(commands_game.ROOM_CONFIG, self.get_info())

    def __deal_dice(self, hu_info, dealer_player, begin_player, now_player, dice_list):

        dice_list = deepcopy(dice_list)
        result = dict()
        result[now_player.seat_id] = 0

        # begin_player = self.seats[self.__dealer]

        def add_score_info(seat_id, reduce_score):
            if seat_id not in result:
                result[seat_id] = 0

            # if now_player.seat_id == self.__dealer or seat == self.__dealer:  # 庄家翻倍
            #    reduce_score += 1

            result[seat_id] -= reduce_score
            result[now_player.seat_id] += reduce_score

            if seat_id not in score_record:
                score_record[seat_id] = 0
            score_record[seat_id] -= reduce_score
            score_record[now_player.seat_id] += reduce_score

        bird_map = {}
        for player in self.seats:
            if not player:
                continue
            bird_map[player.seat_id] = 0

        if (self.__total_seat - 1) == 4:
            pos_map = [4, 1, 2, 3]
        elif (self.__total_seat - 1) == 3:
            pos_map = [3, 1, 2]
        else:
            pos_map = [4, 1, 3, 2]

        for dice in dice_list:
            pos = pos_map[dice % 10 % len(pos_map)]
            if pos > (self.__total_seat - 1):
                continue

            player = self.__next_player(begin_player, pos - 1)
            bird_map[player.seat_id] += 1

        now_player_seat_id = now_player.seat_id
        for value in hu_info:
            score = value["score"]
            middle_hu_record = {"hu_name": value["hu_name"]}
            score_record = {now_player.seat_id: 0}
            for seat, bird_count in bird_map.items():
                if seat == now_player_seat_id:
                    continue

                # if self.__dealer == seat:
                #     now_score = score + 1
                # else:
                #     now_score = score

                now_score = score
                all_bird_count = bird_map.get(now_player_seat_id, 0) + bird_count

                if self.__bird_score_type == 0:
                    bird_rate = (all_bird_count + 1)
                elif self.__bird_score_type == 1:
                    bird_rate = 2 ** all_bird_count
                elif self.__bird_score_type == 2:
                    bird_rate = (all_bird_count + 1)
                else:
                    bird_rate = all_bird_count

				#4.2 4.8 conflics
#                if (now_player.seat_id == self.__dealer or seat == self.__dealer) and self.__zhuang_type == 1:  # 庄家翻倍
#                    now_score += 1

                # if self.__bird_score_type == 1:
                #     now_score += now_score * all_bird_count
                # elif self.__bird_score_type == 2:

                # now_score = now_score * all_bird_count
                add_score_info(seat, now_score * bird_rate)

            middle_hu_record["score_info"] = score_record
            middle_hu_record["cards"] = value["cards"]
            middle_hu_record["seat"] = now_player_seat_id
            self.__add_middle_hu_record(middle_hu_record)

        self.__dice_record.append(dice_list)

        return result

    def __begin_hu(self):
        result = {}
        dice_list = []
        if self.__begin_hu_is_zhua_niao:
            dice_list = RuleMaJiang.random_dice(self.__bird_count)

        for p in self.seats:
            if not p:
                continue

            hu_info, hu_record = p.get_begin_hu(self.__rule, self.__begin_hu_options)

            if len(hu_info) == 0:
                continue

            p.add_middle_hu_list(hu_record)

            # if self.__zhuang_type == 0:
            #     begin_player = p
            #     dealer_player = p
            # else:
            #     begin_player = self.seats[self.__dealer]
            #     dealer_player = self.seats[self.__dealer]

            dealer_player = self.seats[self.__dealer]
            begin_player = self.seats[self.__dealer]

            hu_cards = self.__rule.get_middle_hu_cards(hu_info)

            #中途胡 按谁胡牌谁为庄 打骰
            if self.__begin_hu_is_zhua_niao:
                dice_result = self.__deal_dice(hu_info, p, p, p, dice_list)
            else:
                dice_result = self.__deal_dice(hu_info, dealer_player, begin_player, p, dice_list)
            for seat_id, score in dice_result.items():
                if seat_id not in result:
                    result[seat_id] = {"score": 0}
                result[seat_id]["score"] += score
                result[seat_id]["seatID"] = seat_id
#
#                print("seat_id:",seat_id)
#                print("score:", result[seat_id]["score"])
#                print("len(hu_info):", len(hu_info))

#                if result[seat_id]["score"] > 0:
#                    result[seat_id]["score"] -= len(hu_info)
#                else:
#                    result[seat_id]["score"] += len(hu_info)

            result[p.seat_id]["cards"] = hu_cards

            result[p.seat_id]["huNameList"] = list()
            for value in hu_info:
                result[p.seat_id]["huNameList"].extend(value["hu_name"])

        if len(result) == 0:
            return

        self.inner_broad_cast(commands_game.PLAYER_SHOW_CARD, {"seats": result, "diceList": dice_list}, error.OK, 0,
                              True)
        update_score_list = [0, 0, 0, 0]
        for seat_id, value in result.items():
            update_score_list[seat_id - 1] = value["score"]
        self.update_player_score(update_score_list)

    def __middle_hu(self):
        result = {}
        dice_list = []
        if self.__begin_hu_is_zhua_niao:
            dice_list = RuleMaJiang.random_dice(self.__bird_count)

        player = self.__curr_player()

        hu_info, hu_record = player.get_middle_hu(self.__rule, self.__middle_hu_options)
        if len(hu_info) == 0:
            return

        player.add_middle_hu_list(hu_record)

        # if self.__zhuang_type == 0:
        #     begin_player = player
        #     dealer_player = player
        # else:
        #     begin_player = self.seats[self.__dealer]
        #     dealer_player = self.seats[self.__dealer]

        dealer_player = self.seats[self.__dealer]
        begin_player = self.seats[self.__dealer]

        hu_cards = self.__rule.get_middle_hu_cards(hu_info)
        #中途胡 按谁胡牌谁为庄 打骰
        if self.__begin_hu_is_zhua_niao:
            dice_result = self.__deal_dice(hu_info, player, player, player, dice_list)
        else:
            dice_result = self.__deal_dice(hu_info, dealer_player, begin_player, player, dice_list)
        for seat_id, score in dice_result.items():
            if seat_id not in result:
                result[seat_id] = {"score": 0}
            result[seat_id]["score"] += score
            result[seat_id]["seatID"] = seat_id

        result[player.seat_id]["cards"] = hu_cards

        result[player.seat_id]["huNameList"] = []
        for value in hu_info:
            result[player.seat_id]["huNameList"].extend(value["hu_name"])

        if len(result) == 0:
            return

        self.inner_broad_cast(commands_game.PLAYER_SHOW_CARD, {"seats": result, "diceList": dice_list}, error.OK, 0,
                              True)
        update_score_list = [0, 0, 0, 0]
        for seat_id, value in result.items():
            update_score_list[seat_id - 1] = value["score"]
        self.update_player_score(update_score_list)

    def __dealer_turn(self):  # 庄家轮转的逻辑
        # if self.__fixed_dealer and self.__fixed_dealer > 0:
        #    return self.__set_dealer(self.__fixed_dealer)

        dealer = self.get_player_by_seat_id(self.__dealer)
        # if not dealer:  # 首局庄
        #    # zhuang = random.randrange(1, self.__total_seat)
        if self.round_index == 1:
            return self.__set_dealer(1)

        # 胡牌者为庄
        if len(self.__winner_list) > 0:
            if len(self.__winner_list) > 1:  # 通炮者为庄
                return self.__set_dealer(self.__lose_list[0].seat_id)
            return self.__set_dealer(self.__winner_list[0].seat_id)

        if self.__hai_di_player:
            return self.__set_dealer(self.__hai_di_player.seat_id)

        # 黄庄则轮庄
        if self.__is_huang_zhuang and dealer:
            zhuang_player = self.__next_player(dealer)
            return self.__set_dealer(zhuang_player.seat_id)

        return self.__set_dealer(1)

    def __before_round_start(self):
        self.__dealer_turn()
        self.flow_status = flow.T_IN_IDLE
        self.__flow_status_history.clear()
        self.round_review_data.clear()
        self.__curr_seat_id = self.__dealer
        self.__is_huang_zhuang = False
        self.__middle_hu_record = []
        self.__hai_di_player = None
        self.__request_hai_di_count = 0
        self.__mo_pai_total = 0
        self.__clear_table_actions()

        self.__real_seats = []
        self.__simulate = []
        self.__simulate_cards = {}

    def __check_round_start(self):
        """ 检查下一局是否要开始了 """
        if self.status != flow.T_CHECK_OUT:
            return False
        if self.ready_player_count != (self.__total_seat - 1):
            return False

        if self.__piao_type == 0 or (self.__piao_type == 1 and self.round_index > 1):
            self.__set_status(flow.T_READY)
            self.__game_start()
        else:
            if not self.__piao_status:
                for p in self.seats:
                    if not p:
                        continue
                    p.piao_score = -1
                    p.on_round_start()
                self.__set_status(flow.T_PLAYING)
                self.__piao_status = True
                piao_data = {"piao_time": PIAO_TIME_SECONDS}
                self.inner_broad_cast(commands_game.PIAO_FEN, piao_data)
                if self.__piao_timer:
                    self.__piao_timer.cancel()
                self.__piao_timer = DelayCall(PIAO_TIME_SECONDS, self.__paio_timer)
        return True

    def __round_start(self):
        """ 一局开始 """
        if self.status != flow.T_PLAYING:
            return

        for p in self.seats:  # 开局前清理
            if not p:
                continue
            p.on_round_start()

        self.__before_round_start()

        result = {"seq": self.round_index, "dealerSeatID": self.__dealer}
        self.inner_broad_cast(commands_game.ROUND_START, result)
        #游戏开始，广播消息给客户端
        """游戏开始，广播消息给客户端"""
        from games.cs_ma_jiang.game import GameServer
        GameServer.share_server().publish(2,9,{'union_id':self.union_id,'uid':0,'selfuid':0,'type':9,
                          'tid':self.tid,'subfloor':self.sub_floor_id,
                          'round_index':self.round_index},9999)
        self.__deal_cards()

    @staticmethod
    def __add_ming_tang_info(result,info):
        if info["score"] == 0:
            return

        result.append(info)

    def __calc_check_out_result(self, winner_list):
        """计算底分，海底，是否自摸等"""
        result = []
        for p in winner_list:
            repeat_count = True
            is_all_bird = self.__curr_seat_id == p.seat_id
            is_zi_mo = self.__curr_seat_id == p.seat_id and self.flow_status in (
                flow.T_IN_MO_PAI_CALL, flow.T_IN_HAI_DI_CALL)

            big_hu = []
            operate_info = p.operates.get(ma_jiang.ACTION_TYPE_HU)
            hu_cards = list(map(lambda value: value["card"], operate_info))
            if is_zi_mo:
                hu_cards = [self.curr_cards[0]]

            base_big_score = 6
            zhuang_xian_score = 1
            if self.__zhuang_type == 0:  # 胡牌为庄
                base_big_score = 7
                zhuang_xian_score = 0

            is_hai_di = self.__flow_status_history[-2:] == [flow.T_IN_HAI_DI,
                                                            flow.T_IN_HAI_DI_CALL] or self.__flow_status_history[
                                                                                      -4:] == [flow.T_IN_HAI_DI,
                                                                                               flow.T_IN_HAI_DI_CALL,
                                                                                               flow.T_IN_CHU_PAI,
                                                                                               flow.T_IN_PUBLIC_OPRATE]
            score = 0
            score_plus_method = 0
            score_mutiple_method = 0
            big_hu_count = 0

            for card in self.curr_cards:
                if card not in hu_cards:
                    continue

                cards = deepcopy(p.cards)

                if RuleMaJiang.is_card(card):
                    cards.append(card)

                is_hao_hua_qi_dui = False
                is_shuang_hao_hua_qi_dui = False
                is_san_hao_hua_qi_dui = False
                is_seven_pairs, _ = self.__rule.is_seven_pairs(p.zhuo_pai_origin, cards)
                long_qi_count = self.__rule.get_long_qi_count(p.zhuo_pai_origin, cards)
                is_qing_yi_se, _ = self.__rule.is_qing_yi_se(p.zhuo_pai_origin, cards)
                is_quan_qiu_ren, _ = self.__rule.is_quan_qiu_ren(p.zhuo_pai_origin, cards)
                is_peng_peng_hu, _ = self.__rule.is_peng_peng_hu(p.zhuo_pai_origin, cards)
                is_jiang_jiang_hu, _ = self.__rule.is_jiang_jiang_hu(p.zhuo_pai_origin, cards)
                is_qiang_gang_hu = self.flow_status == flow.T_IN_MING_GANG_PAI_CALL
                is_gang_shang_pao = self.flow_status == flow.T_IN_OTHER_GANG_PAI_CALL
                is_gang_shang_hua = self.flow_status == flow.T_IN_GANG_PAI_CALL
                is_men_qing_hu = (self.__total_seat - 1 == 2) and (
                            self.__men_qing and self.__rule.is_men_qing_hu(p.zhuo_pai_origin,
                                                                           cards) and not is_seven_pairs)

                # 将将胡成立时 全求人的最后两张可能是不相等的
                if is_jiang_jiang_hu:
                    if len(cards) == 2:
                        is_quan_qiu_ren = True

                score_shuang_hao_qi = 0
                score_san_hao_qi = 0
                if is_seven_pairs and long_qi_count > 0:
                    is_seven_pairs = False
                    if long_qi_count == 1:
                        is_hao_hua_qi_dui = True
                    elif long_qi_count == 2:
                        is_shuang_hao_hua_qi_dui = True
                    else:
                        is_san_hao_hua_qi_dui = True

                    if is_shuang_hao_hua_qi_dui:
                        score_shuang_hao_qi = 4 * base_big_score if self.__bird_score_type == 1 else 3 * base_big_score
                    elif is_san_hao_hua_qi_dui:
                        score_san_hao_qi = 8 * base_big_score if self.__bird_score_type == 1 else 4 * base_big_score

                print("__bird_score_type:",self.__bird_score_type)
                print("hao_hua_qi_dui:", is_hao_hua_qi_dui,score_shuang_hao_qi,score_san_hao_qi)

                # is_que_yi_men = self.__rule.is_que_yi_men(p.zhuo_pai_origin, cards)
                is_tian_hu = self.__mo_pai_total == 1 and p.seat_id == self.__dealer
                is_di_hu = self.__mo_pai_total == 1 and p.seat_id != self.__dealer

                hu_info = [{"name": "qingYiSe", "score": is_qing_yi_se and repeat_count and base_big_score or 0},
                           {"name": "pengPengHu", "score": is_peng_peng_hu and repeat_count and base_big_score or 0},
                           {"name": "sevenPairs", "score": is_seven_pairs and repeat_count and base_big_score or 0},
                           {"name": "quanQiuRen", "score": is_quan_qiu_ren and repeat_count and base_big_score or 0},
                           {"name": "jiangJiangHu", "score": is_jiang_jiang_hu and repeat_count and base_big_score or 0},
                           {"name": "qiangGangHu", "score": is_qiang_gang_hu and repeat_count and base_big_score or 0},
                           {"name": "gangShangPao", "score": is_gang_shang_pao and base_big_score or 0},
                           {"name": "gangShangHua", "score": is_gang_shang_hua and base_big_score or 0},
                           {"name": "menQingHu", "score": is_men_qing_hu and repeat_count and base_big_score or 0},
                           # {"name": "queYiMen", "score": is_que_yi_men and 6 or 0},
                           # {"name": "longQiDui", "score": long_qi_count * base_big_score},
                           {"name": "haoHuaQiXiaoDui", "score": is_hao_hua_qi_dui and 2 * base_big_score or 0},
                           {"name": "shuangHaoHuaQiXiaoDui", "score": score_shuang_hao_qi},
                           {"name": "sanHaoHuaQiXiaoDui","score": score_san_hao_qi},
                           {"name": "tianHu", "score": is_tian_hu and repeat_count and base_big_score or 0},
                           {"name": "diHu", "score": is_di_hu and repeat_count and base_big_score or 0},
                           {"name": "haiDi", "score": is_hai_di and base_big_score or 0},
                           {"name": "hiddenScore", "score": 0},
                           ]

                for info in hu_info:
                    self.__add_ming_tang_info(big_hu, info)

                if is_gang_shang_hua or is_gang_shang_pao:
                    repeat_count = False

                score = 0
                score_extra = 0
                score_plus_method = 0
                score_mutiple_method = 0
                big_hu_count = 0

                for index in range(len(big_hu)):

                    if big_hu[index]["name"] == "shuangHaoHuaQiXiaoDui":
                        score_mutiple_method = score_shuang_hao_qi
                        continue
                    if big_hu[index]["name"] == "sanHaoHuaQiXiaoDui":
                        score_mutiple_method = score_san_hao_qi
                        continue

                    if big_hu[index]["name"] != "hiddenScore":
                        print("00 big_hu_count:", big_hu_count,"score_mutiple_method:",score_mutiple_method)
                        big_hu_count += 1
                        score_mutiple_method = score_mutiple_method * 2 if score_mutiple_method else base_big_score


                score_plus_method = max(2, sum(map(lambda value: value["score"], big_hu)))
                score_mutiple_method = max(2, score_mutiple_method)

                #庄闲模式下 两人自摸加1 放炮加1
                if self.__zhuang_type == 1:
                    if self.player_count == 2:
                        score_mutiple_method = max(1, score_mutiple_method)
                        score_plus_method = max(1, sum(map(lambda value: value["score"], big_hu)))
                    elif self.player_count > 2:
                        if is_zi_mo:
                            score_mutiple_method = max(2, score_mutiple_method)
                            score_plus_method = max(2, sum(map(lambda value: value["score"], big_hu)))
                        else:
                            score_mutiple_method = max(1, score_mutiple_method)
                            score_plus_method = max(1, sum(map(lambda value: value["score"], big_hu)))
                    else:
                        score_mutiple_method = max(2, score_mutiple_method)
                        score_plus_method = max(2, sum(map(lambda value: value["score"], big_hu)))
                else:
                    score_mutiple_method = max(2, score_mutiple_method)
                    score_plus_method = max(2, sum(map(lambda value: value["score"], big_hu)))

                # 1 中鸟翻倍 多个大胡按乘法算 中鸟加分 0 2 多个大胡按加法算
                # if self.__bird_score_type == 1:
                #     score = score_mutiple_method
                #     #if len(big_hu) < 2 or is_hao_hua_qi_dui or is_san_hao_hua_qi_dui or is_shuang_hao_hua_qi_dui:
                #     #    score = score_plus_method
                #     #else:
                #     #    score = score_mutiple_method
                # else:
                #     score = score_plus_method

                # 嗨森要求都按加的方法算分
                score = score_plus_method

            # if self.__bird_score_type == 1:
            #     score_extra = score_mutiple_method - score_plus_method

            # if score_extra > 0:
            #     score = score_plus_method
            #     big_hu.append({"name": "hiddenScore", "score": score_extra})

            print("score_plus_method:", score_plus_method, "score_mutiple_method:", score_mutiple_method)
            print("big_hu_count:",big_hu_count)
            print("big_hu:", big_hu)


            result.append(
                dict(score=score, is_all_bird=is_all_bird, is_zi_mo=is_zi_mo, is_hai_di=is_hai_di,
                     zhuang_xian_score=zhuang_xian_score,
                     hu_cards=hu_cards, winner=p, big_hu=big_hu))

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
        return dict(), self.deal_middle_hu({}, {})

    def __huang_zhuang_check_out(self):
        return self.__dismiss_check_out()

    def __get_bird_seat(self, winner_seat_id, start_seat_id, bird_list, is_all_bird):
        bird_seat = {}
        real_bird_seat = {}
        for player in self.seats:
            if not player:
                continue
            bird_seat[player.seat_id] = 0
            real_bird_seat[player.seat_id] = 0

        if (self.__total_seat - 1) == 4:
            pos_map = [4, 1, 2, 3]
        elif (self.__total_seat - 1) == 3:
            pos_map = [3, 1, 2]
        else:
            pos_map = [4, 1, 3, 2]

        if is_all_bird:
            del bird_seat[winner_seat_id]
        else:
            bird_seat = {self.__curr_seat_id: 0}

        for bird in bird_list:
            pos = pos_map[bird % 10 % len(pos_map)]
            if self.__total_seat - 1 == 2:
                seat = pos
            else:
                seat = pos_map[(start_seat_id + pos - 1) % len(pos_map)]
            if self.__bird_type or (self.__total_seat - 1 == 2):
                if seat == winner_seat_id:
                    real_bird_seat[winner_seat_id] += 1
                    for key, value in bird_seat.items():
                        bird_seat[key] += 1
                else:
                    if seat in bird_seat:
                        if seat is not winner_seat_id:
                            real_bird_seat[seat] += 1
                        bird_seat[seat] += 1
            else:
                if bird % 10 in (1, 5, 9):
                    real_bird_seat[seat] += 1
                    for key, value in bird_seat.items():
                        bird_seat[key] += 1

        return bird_seat, real_bird_seat

    def __calc_win_score(self, check_out_result, bird_list, winner_list: list):
        if not winner_list:  # 流局
            return {}, {}

        limit_score = (self.__limit_score != 0 and self.__limit_score or float("inf")) * self.match_enter_score
        if self.__zhuang_type == 0:
            if len(winner_list) == 1:
                start_seat_id = winner_list[0].seat_id
            else:
                start_seat_id = self.__curr_seat_id
        elif self.__zhuang_type == 1:
            start_seat_id = self.__dealer

        win_score_info = {}
        final_lose_info = {}

        for hu_value in check_out_result:
            winner = hu_value["winner"]
            is_all_bird = hu_value["is_all_bird"]

            is_hai_di = hu_value["is_hai_di"]
            if is_hai_di:
                bird_list.clear()
                hu_cards = hu_value["is_zi_mo"] and [winner.mo_card] or hu_value["hu_cards"]
                if self.__hai_di_type == 0: 
                    bird_list.extend(hu_cards * self.__bird_count)
                elif self.__hai_di_type == 1:
                    bird_list.extend(hu_cards)
                elif self.__hai_di_type == 2:
                    bird_list.extend(hu_cards * self.__bird_count)

            bird_seat, real_bird_seat = self.__get_bird_seat(winner.seat_id, start_seat_id, bird_list, is_all_bird)

            lose_info = {}
            for seat, _ in bird_seat.items():
                lose_info[seat] = {"score": 0, "ming_tang": []}

            def deal_lose_info(lose_seat_id, name, change_score):
                lose_info[lose_seat_id]["ming_tang"].append([name, -change_score * self.match_enter_score])
                lose_info[lose_seat_id]["score"] -= change_score * self.match_enter_score

            ming_tang = []
            ming_tang_unique = []
            if len(hu_value["big_hu"]) == 0:
                hu_key = hu_value["is_zi_mo"] and "ziMo" or "fangPao"
                hu_score = 0
                for seat, _ in lose_info.items():
                    score = hu_value["score"]
                    deal_lose_info(seat, hu_key, score)
                    hu_score += score * self.match_enter_score

                ming_tang.append([hu_key, hu_score])

            else:
                for info in hu_value["big_hu"]:
                    hu_score = 0
                    for seat, _ in lose_info.items():
                        deal_lose_info(seat, info["name"], info["score"])
                        hu_score += info["score"] * self.match_enter_score

                    ming_tang.append([info["name"], hu_score])

#                for item in ming_tang:
#                    if item not in ming_tang_unique:
#                        ming_tang_unique.append(item)

#                ming_tang = ming_tang_unique.copy()

				#4.2 4.8 conflics
                # if self.__bird_score_type == 1 and self.__zhuang_type == 0:
                #     for seat, _ in lose_info.items():
                #         score = abs(lose_info[seat]['score'])
                #         lose_info[seat]['score'] = 7 * (2 ** (int(score / 7) - 1))

            def get_bird_rate(now_seat_id):
                now_bird_count = bird_seat.get(now_seat_id, 0)
                now_bird_rate = now_bird_count
                return now_bird_rate

            if hu_value.get("zhuang_xian_score"):
                hu_score = 0
                key = "zhuangXian"
                zhuang_xian_final_score = hu_value["zhuang_xian_score"] * max(len(hu_value["big_hu"]), 1)

                #豪华七小对 双豪华七小队 三豪华算多个名堂
                for info in hu_value["big_hu"]:
                    if  info["name"] == "haoHuaQiXiaoDui":
                        zhuang_xian_final_score += 1
                    elif  info["name"] == "shuangHaoHuaQiXiaoDui":
                        zhuang_xian_final_score += 2
                    elif  info["name"] == "sanHaoHuaQiXiaoDui":
                        zhuang_xian_final_score += 4

                win_zhuang_xian_score = 0

                if self.__zhuang_type == 1:
                    if winner.seat_id == self.__dealer:
                        for seat, _ in lose_info.items():
                            # bird_rate = get_bird_rate(seat)
                            lose_info[seat]["ming_tang"].append([key, -zhuang_xian_final_score * self.match_enter_score])
                            lose_info[seat]["score"] -= zhuang_xian_final_score * self.match_enter_score
                            hu_score += zhuang_xian_final_score * self.match_enter_score
                            win_zhuang_xian_score += zhuang_xian_final_score * self.match_enter_score
                    elif self.__dealer in lose_info:
                        # bird_rate = get_bird_rate(self.__dealer)
                        lose_info[self.__dealer]["ming_tang"].append([key, -zhuang_xian_final_score * self.match_enter_score])
                        lose_info[self.__dealer][
                            "score"] -= zhuang_xian_final_score * self.match_enter_score
                        hu_score += zhuang_xian_final_score * self.match_enter_score
                        win_zhuang_xian_score += zhuang_xian_final_score * self.match_enter_score
                elif self.__zhuang_type == 0:
                    for seat, _ in lose_info.items():
                        # bird_rate = get_bird_rate(seat)
                        # deal_lose_info(seat, key, zhuang_xian_final_score * bird_rate)
                        lose_info[seat]["ming_tang"].append([key, -zhuang_xian_final_score * self.match_enter_score])
                        lose_info[seat]["score"] -= zhuang_xian_final_score * self.match_enter_score
                        hu_score += zhuang_xian_final_score * self.match_enter_score
                        win_zhuang_xian_score += zhuang_xian_final_score * self.match_enter_score

                ming_tang.append([key, win_zhuang_xian_score])

            for seat_id, _ in lose_info.items():
                bird_count = bird_seat.get(seat_id, 0)

                bird_rate = get_bird_rate(seat_id)

                if self.__zhuang_type == 0:
                    if self.__bird_score_type == 2:
                        # base_score = -2
                        # if lose_info[seat_id]['score'] <= -7:
                        #     base_score = -7
                        lose_info[seat_id]["score"] += lose_info[seat_id]["score"] * bird_rate * self.match_enter_score
                    else:
                        lose_info[seat_id]["score"] = lose_info[seat_id]["score"] * 2 ** bird_rate
                else:
                    if self.__bird_score_type == 2:
                        lose_info[seat_id]["score"] = lose_info[seat_id]["score"] + -1 * bird_rate * self.match_enter_score
                    else:
                        lose_info[seat_id]["score"] = lose_info[seat_id]["score"] * (bird_rate + 1)

                # lose_info[seat_id]["ming_tang"].append(["zhongNiao", real_bird_seat.get(seat_id, 0)])
                # 飘分 算分
                if self.__piao_type == 1 or self.__piao_type == 2:
                    lose_info[seat_id]["score"] -= (self.seats[seat_id].piao_score + self.seats[
                        winner.seat_id].piao_score) * self.match_enter_score
                    lose_info[seat_id]["ming_tang"].append(
                        ["piao", -1 * self.seats[seat_id].piao_score * self.match_enter_score])

            for seat_id, value in lose_info.items():
                lose_info[seat_id]["score"] = -min(abs(value["score"]), limit_score)

            # ming_tang.append(["zhongNiao", real_bird_seat.get(winner.seat_id, 0)])

            if self.__piao_type == 1 or self.__piao_type == 2:
                ming_tang.append(["piao", self.seats[winner.seat_id].piao_score])

            total_hu_score = -sum([value["score"] for _, value in lose_info.items()])

            win_score_info[winner.seat_id] = {"score": 0,
                                              # "is_qiang_gang_hu": hu_value["is_qiang_gang_hu"],
                                              # "is_gang_shang_pao": hu_value["is_gang_shang_pao"],
                                              "ming_tang": ming_tang, }

            if len(lose_info) == 1:
                win_score_info[winner.seat_id]["jiePao"] = 1
            else:
                win_score_info[winner.seat_id]["ziMo"] = 1

            if "qiangGangHu" in ming_tang:
                win_score_info[winner.seat_id]["qiangGangHu"] = 1

            win_score_info[winner.seat_id]["score"] = total_hu_score

            fixed_lose_seat = self.adjust_score(winner, hu_value)
            for seat, lose in lose_info.items():
                if seat not in final_lose_info:
                    final_lose_info[seat] = {"score": 0, "ming_tang": []}
                final_lose_info[seat]["ming_tang"].extend(lose["ming_tang"])
                if fixed_lose_seat:
                    final_lose_info[fixed_lose_seat]["score"] += lose["score"]
                else:
                    final_lose_info[seat]["score"] += lose["score"]


#                ming_tang_unique = []
#                for item in final_lose_info[seat]["ming_tang"]:
#                    if item not in ming_tang_unique:
#                        ming_tang_unique.append(item)
#                    final_lose_info[seat]["ming_tang"] = ming_tang_unique.copy()
#                print(final_lose_info[seat]["ming_tang"])

        return win_score_info, final_lose_info

    @staticmethod
    def adjust_score(winner, hu_value):
        if not bool(hu_value["is_zi_mo"]) or len(hu_value["big_hu"]) == 0:
            return 0

        zhuo_pai_from_seats = dict()
        for zhuo_pai_info in winner.zhuo_pai:
            from_seat = zhuo_pai_info["from_seat"]
            zhuo_pai_from_seats[from_seat] = zhuo_pai_from_seats.get(from_seat, 0) + 1

        zhuo_pai_from_seats = pydash.filter_(zhuo_pai_from_seats, lambda v: v >= 3)
        if len(zhuo_pai_from_seats) == 0:
            return 0

        all_lose_for_seat = pydash.keys(zhuo_pai_from_seats)[0]
        return all_lose_for_seat

    def get_middle_hu_cards(self, p):

        print("get_middle_hu_cards")


        result = {}
        score_from = {}
        hu_info = {}
        for middle_hu_info in self.__middle_hu_record:
            if not middle_hu_info["hu_name"]:
                continue
            hu_key = middle_hu_info["hu_name"][0]
            for seat_id, score in middle_hu_info["score_info"].items():
                if seat_id not in score_from:
                    score_from[seat_id] = {"score": 0, "ming_tang": [], "seatID": seat_id}

                len_hu_name = len(middle_hu_info["hu_name"])
                # for _ in range(len_hu_name):
                #     score_from[seat_id]["ming_tang"].append([hu_key, score // len_hu_name])
                score_from[seat_id]["score"] += score

            seat_id = middle_hu_info["seat"]
            if seat_id not in hu_info:
                hu_info[seat_id] = []
            hu_info[seat_id].append(middle_hu_info)

        for seat_id, value in hu_info.items():
            score_from[seat_id]["huCards"] = self.__rule.get_middle_hu_cards(value)

        result["seats"] = score_from
        result["dice"] = self.__dice_record[0]

        self.inner_send(p, commands_game.GET_MIDDLE_HU, result, error.OK, False)

    def deal_middle_hu(self, win_score: dict, lose_info: dict):
        result = deepcopy(win_score)
        result.update(lose_info)

        for middle_hu_info in self.__middle_hu_record:
            if not middle_hu_info["hu_name"]:
                continue
            hu_key = middle_hu_info["hu_name"][0]
            for seat_id, score in middle_hu_info["score_info"].items():
                if seat_id not in result:
                    result[seat_id] = {"score": 0, "ming_tang": []}

                len_hu_name = len(middle_hu_info["hu_name"])
                # for _ in range(len_hu_name):
                #     result[seat_id]["ming_tang"].append([hu_key, score // len_hu_name])
                # result[seat_id]["score"] += score

        return result

    def __do_check_out(self, winner_list: list, is_huang_zhuang, bird_list, is_dismiss):
        """ 结算当局积分 """

        self.__winner_list = winner_list

        if is_dismiss:
            return self.__dismiss_check_out()

        if is_huang_zhuang:
            for player in self.seats:
                if not player:
                    continue
                if player.operator_out_time:
                    player.operator_out_time.cancel()
                    player.operator_out_time = None
            return self.__huang_zhuang_check_out()

        result = self.__calc_check_out_result(winner_list)
        win_score_from, lose_info = self.__calc_win_score(result, bird_list,
                                                          winner_list)  # win_score, {seat_id: lose_score}

        self.inner_broad_cast(commands_game.BIRD_LIST, {"code": 0, "birdList": bird_list}, error.OK, 0, True)

        win_seat_list = list(win_score_from.keys())
        win_seat_list.sort(key=lambda value: win_score_from[value]["score"], reverse=True)
        is_zi_mo = False
        for hu_value in result:
            winner_zi_mo = hu_value["is_zi_mo"]
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

            if not lose_info.get(p.seat_id):
                lose_info[p.seat_id] = {"score": 0, "ming_tang": []}
            else:
                lose_list.append(p)

            lose_score = lose_info.get(p.seat_id)["score"]

            if self.match_type == 1:
                if p.lock_score + p.score + lose_score < 0:
                    lose_score = -(p.lock_score + p.score)
                    lose_info[p.seat_id]["score"] = lose_score
                    self.__no_score_seat_id.append(p.uid)

            is_fang_pao = not is_zi_mo and lose_info.get(p.seat_id)["score"] < 0

            lose_all_score += lose_score

            #是否有人大胡
            ming_tang = False
            for seat_id in win_seat_list:
                hu_value = pydash.find(result, lambda value: value["winner"].seat_id == seat_id)
                if hu_value["big_hu"]:
                    ming_tang = True

            p.on_round_over(lose_score, is_fang_pao, p.seat_id == self.__dealer, False, ming_tang)

        for seat_id in win_seat_list:
            winner = self.get_player_by_seat_id(seat_id)
            hu_value = pydash.find(result, lambda value: value["winner"].seat_id == seat_id)
            score_from = win_score_from[winner.seat_id]

            winner_zi_mo = hu_value["is_zi_mo"]

            win_score = score_from["score"]
            if lose_all_score + win_score > 0:
                win_score = -lose_all_score
                win_score_from[seat_id]["score"] = -lose_all_score

            lose_all_score += win_score

            winner.on_round_over(win_score, False, winner.seat_id == self.__dealer, winner_zi_mo,
                                 hu_value["big_hu"])

        self.__lose_list = lose_list

        score_from = self.deal_middle_hu(win_score_from, lose_info)

        return self.__make_win_info(result, bird_list=bird_list), score_from

    def __make_win_info(self, hu_result, bird_list):
        ret = []
        for hu_value in hu_result:
            winner = hu_value["winner"]
            hu_cards = hu_value["hu_cards"]
            hand_cards = winner.cards
            if hu_cards == [ma_jiang.NULL_CARD]:
                hu_cards = [winner.mo_card]
                utils.remove_by_value(hand_cards, winner.mo_card, 1)

            ret.append({"rate": ROUND_RATE, "huCards": hu_cards, "lastSeat": self.__curr_seat_id, "birdList": bird_list,
                        "huCardIndex": 1, "winner": winner.seat_id, "handCardIndex": len(winner.zhuo_pai) + 1,
                        "handCards": hand_cards, })
        return ret

    def __pop_all_cards(self):
        ret = []
        for i in range(self.__ma_jiang_cards.left_count):
            ret.append(self.__ma_jiang_cards.pop())
        return ret

    def __round_over(self, win_seat_list, is_huang_zhuang, is_dismiss):
        """ 一局结束 """
        if self.status != flow.T_PLAYING:
            return
        self.__piao_status = False
        self.__ma_jiang_cards.clear_pop_order()
        self.__set_status(flow.T_CHECK_OUT)

        self.__is_huang_zhuang = is_huang_zhuang
        if not self.round_review_data:
            self.__add_base_review_data()

        bird_list = []
        if not is_huang_zhuang and not is_dismiss:
            bird_list = is_dismiss and [] or self.__pop_card(self.__bird_count)
        winner_list = [self.get_player_by_seat_id(seat) for seat in win_seat_list or []]
        win_info, score_from = self.__do_check_out(winner_list, is_huang_zhuang, bird_list, is_dismiss)

        finish_type = ROUND_OVER_NORMAL
        if is_dismiss:
            finish_type = ROUND_OVER_DISMISS

        index = self.round_index
        self.round_index += 1
        result = {"seq": index, "hasNextRound": self.__has_next_round(), "seats": [], "finishType": finish_type,
                  "rate": 1, "isHuangZhuang": int(self.__is_huang_zhuang), "leftCards": self.__pop_all_cards(),
                  "winInfo": win_info, "dealer": self.__dealer, }

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
        result["roun_id"] = self.__save_round_log(index)
        if not is_dismiss:
            self.inner_broad_cast(commands_game.ROUND_OVER, result, error.OK, 0, True)

        self.table_info["round_index"] = self.round_index
        self.update_table_info()

        # 一局结束 清空用户飘分
        if self.__piao_type != 1:
            for p in self.seats:
                if not p:
                    continue
                p.piao_score = -1

        # self.__update_huang_zhuang_count(is_huang_zhuang)
        isgameover = False
        if not self.__has_next_round():  # 房间结束
            isgameover = True
            return self.__game_over()
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
        from games.cs_ma_jiang.game import GameServer
        GameServer.share_server().player_ready( p.uid)
    def __save_round_log(self, index):
        if self.__is_request_dismiss_room:
            return 0
        round_id = logs_model.insert_round_log(self.record_id, index, const.SERVICE_CSMJ, self.seats)
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

    def __hu_by_priority(self) -> bool:  # 按优先顺序判断进行胡牌
        hu_list = []
        for p in self.seats:
            if not p:
                continue
            if p.hu_de_qi():
                hu_list.append(p.seat_id)
        if not hu_list:
            return False
        return self.__somebody_hu(hu_list)

    def __curr_player(self):
        return self.get_player_by_seat_id(self.__curr_seat_id)

    def __next_player(self, p, count=1) -> Player:
        """ 查找下一玩家 """
        now_player = p
        for index in range(count):
            for i in range(now_player.seat_id + 1, self.__total_seat):
                if self.seats[i]:
                    now_player = self.seats[i]
                    break
            else:
                for i in range(1, now_player.seat_id):
                    if self.seats[i]:
                        now_player = self.seats[i]
                        break

        return now_player

    def __next_player_in_simulate(self, seat_id) -> Player:
        """ 查找下一玩家 """
        index = self.__simulate.index(seat_id)
        if index == len(self.__simulate) - 1:
            return self.__simulate[0]
        return self.__simulate[index + 1]

    def __next_player_bird(self, p, count=1) -> Player:
        now_player = p
        for index in range(count):
            for i in range(now_player.seat_id + 1, self.__total_seat):
                if self.seats[i]:
                    now_player = self.seats[i]
                    break
            else:
                for i in range(1, now_player.seat_id):
                    if self.seats[i]:
                        now_player = self.seats[i]
                        break

        return now_player

    def __chi_de_qi(self, chu_pai_player: Player, p: Player, cards: list):  # 判断玩家能否吃牌
        """
        判断能否吃得起某张牌
        :param p:
        :return:
        """
        if not p:
            return []

        if self.flow_status not in (flow.T_IN_PUBLIC_OPRATE, flow.T_IN_OTHER_GANG_PAI_CALL):
            return []

        if self.__next_player(chu_pai_player).seat_id != p.seat_id:
            return []

        chi_cards = []
        for card in cards:
            info = p.can_chi(card, self.__rule)
            if len(info) != 0:
                chi_cards.append({"card": card, "operateCards": info})
                self.user_time_out_operator(p)
        return chi_cards

    def __peng_de_qi(self, p: Player, cards):
        peng_cards = []
        if not p:
            return False, peng_cards

        for card in cards:
            peng_info = p.can_peng(card, self.__rule)
            if len(peng_info) != 0:
                peng_cards.append({"card": card, "operateCards": peng_info})
                self.user_time_out_operator(p)
        return peng_cards

    def __hu_de_qi(self, p: Player, cards: list, check_lou_hu=True):
        hu_cards = []
        if not p:
            return hu_cards

        for card in cards:
            is_hu, path = p.can_hu(card, self.__rule, True, check_lou_hu)
            if is_hu:
                hu_cards.append({"card": card, "operateCards": [path]})
                self.user_time_out_operator(p)
        return hu_cards

    def __ming_gang_de_qi(self, p: Player, cards=list([ma_jiang.NULL_CARD])):
        operate_info = []
        if not p:
            return operate_info

        if self.__ma_jiang_cards.left_count <= 0:
            return operate_info

        for card in cards:
            info = p.can_ming_gang(card, self.__rule)

            for gang_info in info:
                operate_info.append({"card": gang_info[0], "operateCards": [gang_info]})
                self.user_time_out_operator(p)
        return operate_info


    def __an_gang_de_qi(self, p: Player, cards=list([ma_jiang.NULL_CARD])):
        operate_info = []
        if not p:
            return operate_info

        if self.__ma_jiang_cards.left_count <= 0:
            return operate_info

        for card in cards:

            info = p.can_an_gang(card, self.__rule)
            for gang_info in info:
                #
                # print("gang_info:",gang_info)
                # cards_tmp = deepcopy(p.cards)
                # utils.remove_by_value(cards_tmp, gang_info[0], -1)  # 删除所有card
                #
                # print("cards_tmp:",cards_tmp)
                # hu_de_qi = self.__hu_de_qi(p, cards_tmp)
                #
                # if hu_de_qi:
                operate_info.append({"card": gang_info[0], "operateCards": [gang_info]})
                self.user_time_out_operator(p)

        return operate_info

    def __gong_gang_de_qi(self, p: Player, cards=list([ma_jiang.NULL_CARD])):
        operate_info = []
        if not p:
            return operate_info

        if self.__ma_jiang_cards.left_count <= 0:
            return operate_info

        for card in cards:
            info = p.can_gong_gang(card, self.__rule)
            if len(info) != 0:
                operate_info.append({"card": card, "operateCards": info})
                self.user_time_out_operator(p)
        return operate_info

    def __can_operates(self):  # 判断是否有人能碰或吃出牌
        for p in self.seats:
            if not p:
                continue
            if p.hu_de_qi():
                return True
            if p.chi_de_qi():
                return True
            if p.peng_de_qi():
                return True
            if p.an_bu_de_qi():
                return True
            if p.gong_bu_de_qi():
                return True
            if p.ming_bu_de_qi():
                return True
            if p.gong_gang_de_qi():
                return True
            if p.ming_gang_de_qi():
                return True
            if p.an_gang_de_qi():
                return True
        return False

    def __calc_operates_after_chu_pai(self, p: Player, chu_pai_player: Player):
        result = dict()
        if not p or not chu_pai_player:
            return result

        if p == chu_pai_player:
            return result

        cards = self.curr_cards
        if self.__ma_jiang_cards.left_count > 0:
            info = self.__gong_gang_de_qi(p, self.curr_cards)

            if len(info) != 0:
                can_gang = self.__can_gang_check(p, info)
                if not p.lock or (can_gang and self.__lock_cards_type == 1):
                    self.add_operates_info(result, ma_jiang.ACTION_TYPE_GONG_BU, info)
                if can_gang:
                    if not p.lock or self.__lock_cards_type == 1:
                        self.add_operates_info(result, ma_jiang.ACTION_TYPE_GONG_GANG, info)

            if not p.lock:
                info = self.__chi_de_qi(chu_pai_player, p, cards)
                self.add_operates_info(result, ma_jiang.ACTION_TYPE_CHI, info)

                info = self.__peng_de_qi(p, cards)
                self.add_operates_info(result, ma_jiang.ACTION_TYPE_PENG, info)

        info = self.__hu_de_qi(p, self.curr_cards)
        self.add_operates_info(result, ma_jiang.ACTION_TYPE_HU, info)

        return result

    @staticmethod
    def __format_operates(operates: dict):
        result = []
        for action_type, operate_info in operates.items():
            result.append({"operate": action_type, "operate_info": operate_info})

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

            result = {"seatID": self.__curr_seat_id, "cards": self.curr_cards[0], "seconds": flow.CALL_SECONDS,
                      "leftCount": self.__ma_jiang_cards.left_count, "auto_chupai":1 if p.is_auto_chupai  else 0}
            self.inner_send(p, commands_game.PLAYER_CHU_PAI, result, error.OK, record)

            operates = self.__calc_operates_after_chu_pai(p, chu_pai_player)
            p.operates = operates
            result["operates"] = self.__format_operates(operates)
            self.inner_send(p, commands_game.PUBLIC_OPERATES, result, error.OK, record)

            record = False

        if self.__can_operates():
            return

        if chu_pai_player.operator_out_time:
            chu_pai_player.operator_out_time.cancel()
            chu_pai_player.operator_out_time = None

        return self.__everyone_pass()

    def __clear_operates(self):
        for p in self.seats:
            if not p:
                continue
            p.operates = []

    def __mo_pai(self, choice_seat=None):
        """
        :return:
        """

        #test
        #self.__ma_jiang_cards.set_cards([38])


        self.__clear_table_actions()
        self.__clear_operates()
        if self.__ma_jiang_cards.left_count <= 0 or self.__request_hai_di_count >= self.__total_seat - 1:  # 黄庄了
            return self.__round_over(None, True, False)
        if choice_seat:
            p = self.get_player_by_seat_id(choice_seat)
        else:
            p = self.__next_player(self.__curr_player())
            if self.__curr_seat_id in self.__real_seats:
                simulate_seat_id = self.__next_player_in_simulate(self.__curr_seat_id)

                simulate_card = self.__ma_jiang_cards.pop()
                # TODO : HACK
                if simulate_seat_id not in (3, 4):
                    simulate_seat_id = 3
                self.__simulate_cards[simulate_seat_id].append(simulate_card)
                if self.__ma_jiang_cards.left_count <= 0:
                    return self.__round_over(None, True, False)

        if len(self.__no_score_seat_id) > 0:
            return self.__round_over(None, True, True)

        self.__curr_seat_id = p.seat_id

        if self.__ma_jiang_cards.left_count == 1:
            return self.__request_hai_di(p)

        self.__set_flow_status(flow.T_IN_MO_PAI)
        change_card = p.get_change_card()
        if change_card and self.__ma_jiang_cards.get_last_card() == change_card:
            mo_card = self.__ma_jiang_cards.pop_last_card()
            p.remove_change_card()
        else:
            mo_card = self.__ma_jiang_cards.pop()
        self.__mo_pai_total += 1
        p.mo_card1 = mo_card
        self.user_time_out_operator(p, True)
        '''
        for player in self.seats:
            if player.seat_id == p.seat_id:
                self.user_time_out_operator(p)
            else:
                if player.operator_out_time:
                    player.operator_out_time.cancel()
                    player.operator_out_time = None
        '''
        self.__enter_mo_pai_call(mo_card)

    def __request_hai_di(self, now_player):
        self.__set_flow_status(flow.T_IN_HAI_DI)
        self.__request_hai_di_count += 1
        if not self.__rule.is_ting_pai(now_player.zhuo_pai_origin, now_player.cards):  # 未听牌不可要海底
            self.__mo_pai()
        else:
            self.inner_broad_cast(commands_game.PLAYER_HAI_DI,
                                  {"seatID": now_player.seat_id, "seconds": flow.CALL_SECONDS, }, error.OK, True)

    def player_hai_di(self, p, data):
        if p.seat_id != self.__curr_seat_id:
            return error.RULE_ERROR

        self.__set_flow_status(flow.T_IN_HAI_DI)
        is_need = bool(data.get("isNeed", 0))
        data["isFinish"] = 1
        self.inner_send(p, commands_game.PLAYER_HAI_DI, data, error.OK, False)
        if not is_need:
            return self.__mo_pai()
        else:
            return self.__player_need_hai_di(p)

    def __player_need_hai_di(self, player: Player):
        if self.__ma_jiang_cards.left_count != 1:
            return error.RULE_ERROR

        self.__hai_di_player = player

        player.lock = True
        self.__clear_table_actions()
        self.__clear_operates()
        self.__set_flow_status(flow.T_IN_HAI_DI)

        self.__curr_seat_id = player.seat_id
        mo_card = self.__ma_jiang_cards.pop()
        self.__mo_pai_total += 1

        self.__enter_hai_di_pai_call(mo_card)

    def __enter_hai_di_pai_call(self, mo_card):
        if self.flow_status != flow.T_IN_HAI_DI:
            return error.RULE_ERROR

        self.__set_flow_status(flow.T_IN_HAI_DI_CALL)
        curr_player = self.__curr_player()

        curr_player.clear_chou_pai()

        record = True
        for p in self.seats:
            if not p:
                continue

            data = {"seatID": curr_player.seat_id, "leftCount": self.__ma_jiang_cards.left_count,
                    "seconds": flow.CALL_SECONDS, "card": mo_card, }

            if p.uid == curr_player.uid:
                p.receive_card(mo_card)
                p.mo_card = mo_card
                operates = self.__calc_operates_after_hai_di_pai(p)
                data["operates"] = self.__format_operates(operates)
                p.operates = operates
                self.inner_send(p, commands_game.PLAYER_MO_PAI, data, error.OK, record)
            else:
                self.inner_send(p, commands_game.PLAYER_MO_PAI, data, error.OK, record)

            record = False

        if self.__can_operates():
            return True

        self.__turn_to_player_chu_pai(curr_player, False)

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

    def __can_somebody_an_bu(self):  # 判断是否有人能补
        for p in self.seats:
            if not p:
                continue
            if p.an_bu_de_qi():
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

    def __can_gang_check(self, p, gang_info: list):

        for info in gang_info:

            cards = deepcopy(p.cards)
            utils.remove_by_value(cards, info["card"], -1)  # 删除所有card

            print("info.operateCards:", info["operateCards"][0])
            print("cards:", cards)

            if len(info["operateCards"][0]) == 1:
                is_ting = self.__rule.is_ting_pai(p.zhuo_pai_origin, cards)
            else:
                is_ting = self.__rule.is_ting_pai(info["operateCards"], cards)

            if is_ting:
                return True

        return False

    @staticmethod
    def add_operates_info(info_map, action_type, action_info: list):
        if len(action_info) == 0:
            return

        if action_type not in info_map:
            info_map[action_type] = []

        info_map[action_type].extend(deepcopy(action_info))

    def __calc_operates_after_hai_di_pai(self, p: Player):
        result = dict()
        if not p:
            return result

        cards = self.curr_cards

        info = self.__hu_de_qi(p, cards)
        if info:
            self.add_operates_info(result, ma_jiang.ACTION_TYPE_HU, info)

        return result

    def __calc_operates_after_mo_pai(self, p: Player):
        result = dict()
        if not p:
            return result

        cards = self.curr_cards

        ming_gang_info = self.__ming_gang_de_qi(p, cards)
        if ming_gang_info:
            can_gang = self.__can_gang_check(p, ming_gang_info)
            if not p.lock or can_gang:
                self.add_operates_info(result, ma_jiang.ACTION_TYPE_MING_BU, ming_gang_info)
            if can_gang:
                self.add_operates_info(result, ma_jiang.ACTION_TYPE_MING_GANG, ming_gang_info)

        info = self.__an_gang_de_qi(p, cards)
        if info:
            can_gang = self.__can_gang_check(p, info)
            if not p.lock or can_gang:
                self.add_operates_info(result, ma_jiang.ACTION_TYPE_AN_BU, info)
            if can_gang:
                self.add_operates_info(result, ma_jiang.ACTION_TYPE_AN_GANG, info)

        info = self.__hu_de_qi(p, cards)
        if info:
            self.add_operates_info(result, ma_jiang.ACTION_TYPE_HU, info)

        return result

    def __calc_operates_before_chu_pai(self, p: Player):
        result = dict()
        if not p:
            return result

        cards = self.curr_cards

        ming_gang_info = self.__ming_gang_de_qi(p, cards)
        if ming_gang_info:
            if not p.lock:
                self.add_operates_info(result, ma_jiang.ACTION_TYPE_MING_BU, ming_gang_info)
            if self.__can_gang_check(p, ming_gang_info):
                self.add_operates_info(result, ma_jiang.ACTION_TYPE_MING_GANG, ming_gang_info)

        info = self.__an_gang_de_qi(p, cards)
        if info:
            if not p.lock:
                self.add_operates_info(result, ma_jiang.ACTION_TYPE_AN_BU, info)
            if self.__can_gang_check(p, info):
                self.add_operates_info(result, ma_jiang.ACTION_TYPE_AN_GANG, info)

        return result

    def __calc_operates_after_ming_gang(self, p: Player):
        result = dict()
        info = self.__hu_de_qi(p, self.curr_cards)
        self.add_operates_info(result, ma_jiang.ACTION_TYPE_HU, info)
        return result

    def __enter_ming_gang_call(self, curr_player, card):
        """
        :return:
        """
        if self.flow_status not in (
                flow.T_IN_MO_PAI_CALL, flow.T_IN_GANG_PAI_CALL, flow.T_IN_OTHER_GANG_PAI_CALL,
                flow.T_IN_BEFORE_CHU_PAI):
            return

        self.__set_flow_status(flow.T_IN_MING_GANG_PAI_CALL)

        self.__clear_table_actions()
        self.__curr_action_player = curr_player
        self.curr_cards = [card]

        record = True
        for p in self.seats:
            if not p:
                continue

            if p.seat_id == curr_player.seat_id:
                continue

            operates = self.__calc_operates_after_ming_gang(p)

            data = {"leftCount": self.__ma_jiang_cards.left_count, "seconds": flow.CALL_SECONDS,
                    "operates": self.__format_operates(operates)}

            p.operates = operates
            self.inner_send(p, commands_game.PUBLIC_OPERATES, data, error.OK, record)

            record = False

        if self.__can_somebody_hu():  # 有人可以胡，则需要等待
            return

        self.__do_ming_gang_end()

    def __do_ming_gang_end(self):
        curr_player = self.__curr_action_player
        self.__enter_gang_pai_call(curr_player)

    def __enter_gang_pai_call(self, player: Player):
        if self.flow_status not in (
                flow.T_IN_MO_PAI, flow.T_IN_MO_PAI_CALL, flow.T_IN_PUBLIC_OPRATE, flow.T_IN_MING_GANG_PAI_CALL,
                flow.T_IN_OTHER_GANG_PAI_CALL, flow.T_IN_BEFORE_CHU_PAI):
            return

        self.__clear_table_actions()
        self.__curr_seat_id = player.seat_id
        player.set_lou_hu(False)

        if self.__ma_jiang_cards.left_count <= 0:
            return

        self.__set_flow_status(flow.T_IN_GANG_PAI_CALL)

        after_gang_cards_count = self.__after_gang_cards_count or 0

        #test
        #self.__ma_jiang_cards.set_cards([18,18])

        cards = self.__pop_card(min(after_gang_cards_count, self.__ma_jiang_cards.left_count - 1))
        for card in cards:
            player.add_chu_pai(card)
        self.curr_cards = list(cards)

        self.inner_broad_cast(commands_game.AFTER_GANG_CARD, {"cards": cards, "seatID": player.seat_id}, error.OK,
                              True)

        operates = {}
        info = self.__hu_de_qi(player, cards)
        if len(info) != 0:
            self.add_operates_info(operates, ma_jiang.ACTION_TYPE_HU, info)

        data = {"seatID": player.seat_id, "leftCount": self.__ma_jiang_cards.left_count, "seconds": flow.CALL_SECONDS,
                "cards": cards, }

        if len(operates) != 0:
            record = False
            for p in self.seats:
                if not p:
                    continue

                if "operates" in data:
                    del data["operates"]

                if p.uid == player.uid:
                    data["operates"] = self.__format_operates(operates)
                    p.operates = operates
                    self.inner_send(p, commands_game.PUBLIC_OPERATES, data, error.OK, record)
                else:
                    p.operates = []
                    self.inner_send(p, commands_game.PUBLIC_OPERATES, data, error.OK, record)

            self.__curr_seat_id = player.seat_id
            return

        self.__enter_other_gang_pai_call(player, cards)

    def __calc_other_operates_after_gang_pai(self, p: Player, gang_pai_player, cards):
        result = {}
        if not p or not gang_pai_player:
            return result

        if p.seat_id != gang_pai_player.seat_id:
            if not p.lock:
                info = self.__chi_de_qi(gang_pai_player, p, cards)
                if len(info) != 0:
                    self.add_operates_info(result, ma_jiang.ACTION_TYPE_CHI, info)

                info = self.__peng_de_qi(p, cards)
                if len(info) != 0:
                    self.add_operates_info(result, ma_jiang.ACTION_TYPE_PENG, info)

            info = self.__gong_gang_de_qi(p, cards)
            if len(info) != 0:
                can_gang = self.__can_gang_check(p, info)
                if not p.lock or (can_gang and self.__lock_cards_type == 1):
                    self.add_operates_info(result, ma_jiang.ACTION_TYPE_GONG_BU, info)
                if can_gang:
                    if not p.lock or self.__lock_cards_type == 1:
                        self.add_operates_info(result, ma_jiang.ACTION_TYPE_GONG_GANG, info)

            info = self.__hu_de_qi(p, cards, False)
            if len(info) != 0:
                self.add_operates_info(result, ma_jiang.ACTION_TYPE_HU, info)
        else:
            info = self.__ming_gang_de_qi(p, cards)
            if len(info) != 0:
                can_gang = self.__can_gang_check(p, info)
                if not p.lock or can_gang:
                    self.add_operates_info(result, ma_jiang.ACTION_TYPE_MING_BU, info)
                if can_gang:
                    self.add_operates_info(result, ma_jiang.ACTION_TYPE_MING_GANG, info)

            info = self.__an_gang_de_qi(p, cards)
            if len(info) != 0:
                can_gang = self.__can_gang_check(p, info)
                if not p.lock or can_gang:
                    self.add_operates_info(result, ma_jiang.ACTION_TYPE_AN_BU, info)
                if can_gang:
                    self.add_operates_info(result, ma_jiang.ACTION_TYPE_AN_GANG, info)

        return result

    def __enter_other_gang_pai_call(self, player: Player, cards):

        if self.flow_status not in (flow.T_IN_GANG_PAI_CALL,):
            return

        # 如果玩家本身不能胡，锁定玩家牌
        player.lock = True

        self.__set_flow_status(flow.T_IN_OTHER_GANG_PAI_CALL)
        self.__player_actions.clear()
        self.__clear_operates()
        self.__curr_action_player = None

        data = {"seatID": player.seat_id, "leftCount": self.__ma_jiang_cards.left_count, "seconds": flow.CALL_SECONDS,
                "cards": cards, }

        record = False
        for p in self.seats:
            if not p:
                continue

            if "operates" in data:
                del data["operates"]

            operates = self.__calc_other_operates_after_gang_pai(p, player, cards)
            data["operates"] = self.__format_operates(operates)
            p.operates = operates
            self.inner_send(p, commands_game.PUBLIC_OPERATES, data, error.OK, record)

        if self.__can_operates():
            return

        return self.__everyone_pass()

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
        if self.flow_status != flow.T_IN_MO_PAI:
            return

        self.__set_flow_status(flow.T_IN_MO_PAI_CALL)
        curr_player = self.__curr_player()

        curr_player.clear_chou_pai()

        for p in self.seats:
            if not p:
                continue

            data = {
                "seatID": curr_player.seat_id,
                "leftCount": self.__ma_jiang_cards.left_count,
                "seconds": flow.CALL_SECONDS,
                "card": ma_jiang.NULL_CARD,
                "index": self.__mo_pai_total
            }

            if p.uid == curr_player.uid:
                data["handCards"] = deepcopy(p.cards)
                p.receive_card(mo_card)
                p.mo_card = mo_card
                p.set_lou_hu(False)
                operates = self.__calc_operates_after_mo_pai(p)
                data["card"] = mo_card
                data["operates"] = self.__format_operates(operates)
                p.operates = operates
                p.is_show_cards = False
                self.inner_send(p, commands_game.PLAYER_MO_PAI, data, error.OK, True)
            else:
                self.inner_send(p, commands_game.PLAYER_MO_PAI, data, error.OK, False)

        if self.__mo_pai_total == 1:
            self.__begin_hu()
        else:
            self.__middle_hu()

        if self.__can_operates():
            return True

        self.__turn_to_player_chu_pai(curr_player, False)

    def __before_turn_to_player_chu_pai(self, p: Player, is_header):
        """ 轮到某玩家出牌 """
        self.__curr_seat_id = p.seat_id
        self.__clear_table_actions()
        self.__set_flow_status(flow.T_IN_BEFORE_CHU_PAI)

        operates = self.__calc_operates_before_chu_pai(p)
        if len(operates) != 0:
            data = {"seatID": p.seat_id, "leftCount": self.__ma_jiang_cards.left_count, "seconds": flow.CALL_SECONDS,
                    "operates": self.__format_operates(operates)}

            p.operates = operates
            self.inner_send(p, commands_game.PLAYER_OPERATES, data, error.OK, True)
        else:
            self.__turn_to_player_chu_pai(p, is_header)

    def __turn_to_player_chu_pai(self, p: Player, is_header):
        """ 轮到某玩家出牌 """
        self.__curr_seat_id = p.seat_id
        self.__clear_table_actions()
        p.set_lou_hu(False)
        out_cards = self.__get_all_out_cards_len()
        self.__set_flow_status(flow.T_IN_CHU_PAI)
        seconds = flow.FIRST_CALL_SECONDS if is_header else flow.CALL_SECONDS
        result = {"seatID": p.seat_id, "remainTime": seconds, "outCards": out_cards}

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
        if p.seat_id != self.__curr_seat_id:
            return error.NOT_YOUR_TURN
        if card not in p.cards:
            return error.DATA_BROKEN
        if p.lock and card != p.mo_card:  # 牌被锁住只能出当前摸到的牌
            return error.RULE_ERROR

        p.chu_pai(card)
        p.add_chu_pai(card)
        self.curr_cards = [card]
        self.__curr_card_exist = 1
        self.__before_seat_id = self.__curr_seat_id
        if p.operator_out_time:
            p.operator_out_time.cancel()
            p.operator_out_time = None
        return error.OK

    def __save_player_action(self, p, action, data=None):
        self.__player_actions.append([p.seat_id, action, data])

    def __has_do_action(self, p):
        for item in self.__player_actions:
            if item[0] == p.seat_id:
                return True
        return False

    def __get_chi_peng_card(self):
        return self.curr_cards if self.flow_status == flow.T_IN_MO_PAI_CALL else self.curr_cards

    def player_chi(self, p: Player, chi_info) -> int:
        """ 玩家吃牌判断 """
        if self.status != flow.T_PLAYING:
            return error.RULE_ERROR
        if self.flow_status not in (flow.T_IN_PUBLIC_OPRATE, flow.T_IN_OTHER_GANG_PAI_CALL):
            return error.FLOW_ERROR
        if self.__has_do_action(p):  # 不能再次操作
            return error.OPERATES_DUPLICATE
        if not p.chi_de_qi():  # 吃不起
            return error.OPERATES_ILLEGAL
        if not chi_info or not self.__rule.is_ma_jiang_card(
                chi_info["operateCards"][0]) or not self.__rule.is_ma_jiang_card(chi_info["operateCards"][1]):
            return error.DATA_BROKEN
        if chi_info["card"] not in self.__curr_cards:  # 吃不起
            return error.RULE_ERROR

        self.__save_player_action(p, ma_jiang.ACTION_TYPE_CHI, chi_info)
        data = {"seatID": p.seat_id, "isFinish": 0}
        self.inner_send(p, commands_game.PLAYER_CHI, data)
        self.user_time_out_operator(p, True)
        return error.OK

    def player_peng(self, p: Player, data) -> int:
        """ 玩家碰牌 """

        if self.status != flow.T_PLAYING:
            return error.RULE_ERROR
        if self.flow_status not in (flow.T_IN_PUBLIC_OPRATE, flow.T_IN_OTHER_GANG_PAI_CALL):
            return error.FLOW_ERROR
        if self.__has_do_action(p):  # 不能再次操作
            return error.OPERATES_DUPLICATE
        if not p.peng_de_qi():  # 检查能否碰得起
            return error.OPERATES_ILLEGAL
        if data["card"] not in self.__curr_cards:  # 吃不起
            return error.RULE_ERROR

        self.__save_player_action(p, ma_jiang.ACTION_TYPE_PENG, data)
        data = {"seatID": p.seat_id, "isFinish": 0}
        self.inner_send(p, commands_game.PLAYER_PENG, data)
        self.user_time_out_operator(p, True)
        return error.OK

    def player_gong_gang(self, p: Player, data):
        if self.status != flow.T_PLAYING:
            return error.RULE_ERROR
        if self.flow_status not in (
                flow.T_IN_PUBLIC_OPRATE, flow.T_IN_MO_PAI_CALL, flow.T_IN_GANG_PAI_CALL, flow.T_IN_OTHER_GANG_PAI_CALL,
                flow.T_IN_BEFORE_CHU_PAI):
            return error.FLOW_ERROR
        if self.__has_do_action(p):  # 不能再次操作
            return error.OPERATES_DUPLICATE
        if not p.gong_gang_de_qi():
            return error.OPERATES_ILLEGAL

        self.__save_player_action(p, ma_jiang.ACTION_TYPE_GONG_GANG, data)
        data = {"seatID": p.seat_id, "isFinish": 0}
        self.inner_send(p, commands_game.PLAYER_GONG_GANG, data)
        self.user_time_out_operator(p, True)
        return error.OK

    def player_ming_gang(self, p: Player, data):
        if self.status != flow.T_PLAYING:
            return error.RULE_ERROR
        if self.flow_status not in (
                flow.T_IN_PUBLIC_OPRATE, flow.T_IN_MO_PAI_CALL, flow.T_IN_GANG_PAI_CALL, flow.T_IN_OTHER_GANG_PAI_CALL,
                flow.T_IN_BEFORE_CHU_PAI):
            return error.FLOW_ERROR
        if self.__has_do_action(p):  # 不能再次操作
            return error.OPERATES_DUPLICATE
        if not p.ming_gang_de_qi():
            return error.OPERATES_ILLEGAL

        self.__save_player_action(p, ma_jiang.ACTION_TYPE_MING_GANG, data)
        data = {"seatID": p.seat_id, "isFinish": 0}
        self.inner_send(p, commands_game.PLAYER_MING_GANG, data)
        self.user_time_out_operator(p, True)
        return error.OK

    def player_an_gang(self, p: Player, data):
        if self.status != flow.T_PLAYING:
            return error.RULE_ERROR
        if self.flow_status not in (
                flow.T_IN_PUBLIC_OPRATE, flow.T_IN_MO_PAI_CALL, flow.T_IN_GANG_PAI_CALL, flow.T_IN_OTHER_GANG_PAI_CALL,
                flow.T_IN_BEFORE_CHU_PAI):
            return error.FLOW_ERROR
        if self.__has_do_action(p):  # 不能再次操作
            return error.OPERATES_DUPLICATE
        if not p.an_gang_de_qi():
            return error.OPERATES_ILLEGAL

        self.__save_player_action(p, ma_jiang.ACTION_TYPE_AN_GANG, data)
        data = {"seatID": p.seat_id, "isFinish": 0}
        self.inner_send(p, commands_game.PLAYER_AN_GANG, data)
        self.user_time_out_operator(p, True)
        return error.OK

    def player_gong_bu(self, p: Player, data):
        if self.status != flow.T_PLAYING:
            return error.RULE_ERROR
        if self.flow_status not in (flow.T_IN_PUBLIC_OPRATE, flow.T_IN_MO_PAI_CALL, flow.T_IN_OTHER_GANG_PAI_CALL,
                                    flow.T_IN_BEFORE_CHU_PAI):
            return error.FLOW_ERROR
        if self.__has_do_action(p):  # 不能再次操作
            return error.OPERATES_DUPLICATE
        if not p.gong_bu_de_qi():
            return error.OPERATES_ILLEGAL

        self.__save_player_action(p, ma_jiang.ACTION_TYPE_GONG_BU, data)
        data = {"seatID": p.seat_id, "isFinish": 0}
        self.inner_send(p, commands_game.PLAYER_GONG_BU, data)
        self.user_time_out_operator(p, True)
        return error.OK

    def player_ming_bu(self, p: Player, data):
        if self.status != flow.T_PLAYING:
            return error.RULE_ERROR
        if self.flow_status not in (flow.T_IN_PUBLIC_OPRATE, flow.T_IN_MO_PAI_CALL, flow.T_IN_OTHER_GANG_PAI_CALL,
                                    flow.T_IN_BEFORE_CHU_PAI):
            return error.FLOW_ERROR
        if self.__has_do_action(p):  # 不能再次操作
            return error.OPERATES_DUPLICATE
        if not p.ming_bu_de_qi():
            return error.OPERATES_ILLEGAL

        self.__save_player_action(p, ma_jiang.ACTION_TYPE_MING_BU, data)
        data = {"seatID": p.seat_id, "isFinish": 0}
        self.inner_send(p, commands_game.PLAYER_MING_BU, data)
        self.user_time_out_operator(p, True)
        return error.OK

    def player_an_bu(self, p: Player, data):
        if self.status != flow.T_PLAYING:
            return error.RULE_ERROR
        if self.flow_status not in (flow.T_IN_PUBLIC_OPRATE, flow.T_IN_MO_PAI_CALL, flow.T_IN_OTHER_GANG_PAI_CALL,
                                    flow.T_IN_BEFORE_CHU_PAI):
            return error.FLOW_ERROR
        if self.__has_do_action(p):  # 不能再次操作
            return error.OPERATES_DUPLICATE
        if not p.an_bu_de_qi():
            return error.OPERATES_ILLEGAL

        self.__save_player_action(p, ma_jiang.ACTION_TYPE_AN_BU, data)
        data = {"seatID": p.seat_id, "isFinish": 0}
        self.inner_send(p, commands_game.PLAYER_AN_BU, data)
        self.user_time_out_operator(p, True)
        return error.OK

    def player_pass(self, p: Player) -> int:
        """ 玩家过牌 """
        if self.status != flow.T_PLAYING:
            return error.RULE_ERROR
        if self.flow_status not in (
                flow.T_IN_PUBLIC_OPRATE, flow.T_IN_MO_PAI_CALL, flow.T_IN_MO_PAI, flow.T_IN_MING_GANG_PAI_CALL,
                flow.T_IN_MING_BU_PAI_CALL,
                flow.T_IN_GANG_PAI_CALL, flow.T_IN_OTHER_GANG_PAI_CALL, flow.T_IN_BEFORE_CHU_PAI):
            return error.FLOW_ERROR
        if self.__has_do_action(p):  # 不允许再次操作
            return error.OPERATES_DUPLICATE

        if ma_jiang.ACTION_TYPE_HU in p.operates:
            p.set_lou_hu(True)

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
                flow.T_IN_MING_BU_PAI_CALL,
                flow.T_IN_GANG_PAI_CALL, flow.T_IN_OTHER_GANG_PAI_CALL, flow.T_IN_HAI_DI_CALL):
            return error.FLOW_ERROR
        if self.__has_do_action(p):  # 不能再次操作
            return error.OPERATES_DUPLICATE
        if not p.hu_de_qi():
            return error.OPERATES_ILLEGAL

        hu_cards = []
        for hu_card in self.curr_cards:
            if p.is_chou_hu_pai(hu_card):
                continue
            hu_cards.append(hu_card)

        if len(hu_cards) == 0:
            return error.RULE_ERROR

        self.__save_player_action(p, ma_jiang.ACTION_TYPE_HU)
        self.inner_send(p, commands_game.PLAYER_HU_PAI, {"seatID": p.seat_id, "isFinish": 0})
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

        seat_priority_map = []
        curr_player = self.__curr_player()
        for i in range(self.__total_seat - 1):
            curr_player = self.__prev_player(curr_player)
            seat_priority_map.append(curr_player.seat_id)

        max_operate = self.get_not_operate_player_max_operate()
        priority = -1
        seat_id_priority = -1
        if max_operate:
            remain_max_info = max(list(self.get_not_operate_player_max_operate().items()),
                                  key=lambda v: v[1] * 10 + seat_priority_map.index(v[0]))  # (seat_id, action)

            priority = ma_jiang.ACTION_PRIORITY[remain_max_info[1]]
            seat_id_priority = seat_priority_map.index(remain_max_info[0])

        already_max_info = max(list(operate_list.items()),
                               key=lambda v: self.get_action_priority(v[0]))  # (action, [seat_id])

        already_seat_id_priority = max(map(lambda v: seat_priority_map.index(v), already_max_info[1]))
        already_action_priority = self.get_action_priority(already_max_info[0])

        if priority > already_action_priority:
            return False, already_max_info, max_operate
        elif priority == already_action_priority:
            if seat_id_priority > already_seat_id_priority:
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
            return self.__somebody_hu(hu_list)

        if not is_finish:
            return

        action_map = {ma_jiang.ACTION_TYPE_AN_BU: self.__somebody_an_bu,
                      ma_jiang.ACTION_TYPE_MING_BU: self.__somebody_ming_bu,
                      ma_jiang.ACTION_TYPE_GONG_BU: self.__somebody_gong_bu,
                      ma_jiang.ACTION_TYPE_HU: self.__somebody_hu, ma_jiang.ACTION_TYPE_PENG: self.__somebody_peng,
                      ma_jiang.ACTION_TYPE_CHI: self.__somebody_chi,
                      ma_jiang.ACTION_TYPE_GONG_GANG: self.__somebody_gong_gang,
                      ma_jiang.ACTION_TYPE_MING_GANG: self.__somebody_ming_gang,
                      ma_jiang.ACTION_TYPE_AN_GANG: self.__somebody_an_gang, }

        act = max_operate_list[0]
        if act in action_map and max_operate_list[1]:
            result = action_map[act](max_operate_list[1])
            self.__clear_chou_pai()
            return result

        return self.__everyone_pass()  # 所有人都不要

    def __clear_chou_pai(self):
        for p in self.seats:
            if not p:
                continue

            p.clear_chou_pai()

    def __clear_table_actions(self):
        self.__player_actions.clear()
        self.__clear_operates()
        self.curr_cards = [ma_jiang.NULL_CARD]
        self.__curr_action_player = None

    def find_first_player(self, seat_ids) -> Player:  # 搜索胡或者吃当中离当前玩家最优先的玩家
        p = self.__curr_player()
        if p.seat_id in seat_ids:
            return p
        for i in range(self.__total_seat - 2):
            p = self.__next_player(p)
            if p.seat_id in seat_ids:
                return p

    def update_player_score(self, update_info: list):
        """更新玩家分数"""

        lose_all_score = 0
        result = []
        for index in range(len(update_info)):
            score = update_info[index]
            seat_id = index + 1
            if not score or score > 0:
                continue

            p = self.get_player_by_seat_id(seat_id)
            if not p:
                continue

            score = score * self.match_enter_score
            if self.match_type == 1:
                if p.lock_score + p.score + score < 0:
                    score = -(p.lock_score + p.score)
                    self.__no_score_seat_id.append(p.uid)

            lose_all_score += score
            now_score = p.update_score(score)
            result.append({"seatID": seat_id, "updateScore": score, "currScore": now_score})

        for index in range(len(update_info)):
            score = update_info[index]
            seat_id = index + 1
            if not score or score <= 0:
                continue

            p = self.get_player_by_seat_id(seat_id)
            if not p:
                continue

            score = score * self.match_enter_score
            if score + lose_all_score > 0:
                score = -lose_all_score

            lose_all_score += score
            now_score = p.update_score(score)
            result.append({"seatID": seat_id, "updateScore": score, "currScore": now_score})

        self.inner_broad_cast(commands_game.PLAYER_SCORE_UPDATE, {"code": 0, "scoreInfo": result}, error.OK, 0, True)

        if len(self.__no_score_seat_id) > 0:
            return self.__round_over(None, True, True)

    def __somebody_hu(self, hu_list: list) -> bool:  # 三人均操作后判断有没有人胡牌
        self.__curr_card_exist = 0
        self.__hu_da_notify(hu_list)
        self.__round_over(hu_list, False, False)
        return True

    def __pop_card(self, count):
        cards = []
        for i in range(count):
            if self.__ma_jiang_cards.left_count > 0:
                cards.append(self.__ma_jiang_cards.pop())
            else:
                break

        return cards

    def __hu_da_notify(self, hu_list):
        """ 胡牌通知客户端 """
        data = []
        hu_card = self.curr_cards
        for seat_id in hu_list:
            p = self.get_player_by_seat_id(seat_id)
            if hu_card == ma_jiang.NULL_CARD:
                hu_card = p.mo_card

            hu_cards = [v["card"] for v in p.operates[ma_jiang.ACTION_TYPE_HU]]

            data.append({"huCards": hu_cards, "seatID": p.seat_id, "isFinish": 1,
                         "isZiMo": p.seat_id == self.__curr_player().seat_id, "shouPai": p.cards,
                         "preSeatID": self.__curr_player().seat_id, "isQiangGangHu": self.flow_status in (
                    flow.T_IN_MING_GANG_PAI_CALL, flow.T_IN_GONG_GANG_PAI_CALL, flow.T_IN_AN_GANG_PAI_CALL),
                         "flow": self.flow_status, })

        self.inner_broad_cast(commands_game.PLAYER_HU_PAI, {"huInfo": data}, error.OK, 0, True)

    def __somebody_an_bu(self, gang_list: list) -> bool:
        p = self.get_player_by_seat_id(gang_list[0])
        if not p:
            return False

        if p.seat_id != self.__curr_seat_id:
            return False

        data = self.__get_operates_data(ma_jiang.ACTION_TYPE_AN_BU, p.seat_id)
        if not data or not data.get("card") or not data.get("operateCards"):
            return False

        an_gang_list = p.can_an_gang(self.curr_cards, self.__rule)
        if len(an_gang_list) == 0:
            return False

        flag = p.an_bu(data["card"], self.__rule)
        if flag:
            send_result = {"fromSeatID": self.__curr_seat_id, "seatID": p.seat_id, "isFinish": int(flag),
                           "act": ma_jiang.ACTION_TYPE_AN_BU}
            send_result.update(data)
            self.inner_broad_cast(commands_game.PLAYER_AN_BU, send_result, error.OK, 0, True)
            self.__mo_pai(p.seat_id)
            return True

        return False

    def __somebody_gong_bu(self, gang_list: list) -> bool:
        if len(gang_list) != 1:
            return False

        p = self.get_player_by_seat_id(gang_list[0])
        from_p = self.get_player_by_seat_id(self.__curr_seat_id)
        if not p or not from_p:
            return False

        data = self.__get_operates_data(ma_jiang.ACTION_TYPE_GONG_BU, p.seat_id)
        if not data or not data.get("card") or not data.get("operateCards"):
            return False

        # gang_list = p.can_gong_gang(self.curr_cards, self.__rule)
        # if len(gang_list) == 0:
        #     return False

        card = from_p.pop_chu_pai(data["card"])
        flag = p.gong_bu(card, self.__rule, self.__curr_seat_id)
        if flag:
            send_result = {"fromSeatID": self.__curr_seat_id, "seatID": p.seat_id, "isFinish": int(flag),
                           "act": ma_jiang.ACTION_TYPE_GONG_BU}
            send_result.update(data)
            self.inner_broad_cast(commands_game.PLAYER_GONG_BU, send_result, error.OK, 0, True)
            self.__mo_pai(p.seat_id)
            return True

        return False

    def __somebody_ming_bu(self, gang_list: list) -> bool:
        if len(gang_list) != 1:
            return False

        p = self.get_player_by_seat_id(gang_list[0])
        if not p:
            return False

        if p.seat_id != self.__curr_seat_id:
            return False

        data = self.__get_operates_data(ma_jiang.ACTION_TYPE_MING_BU, p.seat_id)
        if not data or not data.get("card") or not data.get("operateCards"):
            return False

        gang_list = p.can_ming_gang(self.curr_cards, self.__rule)
        if len(gang_list) == 0:
            return False

        flag = p.ming_bu(data["card"], self.__rule)
        if flag:
            send_result = {"fromSeatID": self.__curr_seat_id, "seatID": p.seat_id, "isFinish": int(flag),
                           "act": ma_jiang.ACTION_TYPE_MING_BU}
            send_result.update(data)
            self.inner_broad_cast(commands_game.PLAYER_MING_BU, send_result, error.OK, 0, True)
            self.__enter_bu_pai_call(p, data['card'])
            return True

        return False

    def __enter_bu_pai_call(self, player, card):
        if self.flow_status not in (
                flow.T_IN_MO_PAI_CALL, flow.T_IN_GANG_PAI_CALL, flow.T_IN_OTHER_GANG_PAI_CALL,
                flow.T_IN_BEFORE_CHU_PAI):
            return

        self.__set_flow_status(flow.T_IN_MING_BU_PAI_CALL)

        self.__clear_table_actions()
        self.__curr_action_player = player
        self.curr_cards = [card]

        record = True
        for p in self.seats:
            if not p:
                continue

            if p.seat_id == player.seat_id:
                continue

            operates = self.__calc_operates_after_ming_gang(p)

            data = {"leftCount": self.__ma_jiang_cards.left_count, "seconds": flow.CALL_SECONDS,
                    "operates": self.__format_operates(operates)}

            p.operates = operates
            self.inner_send(p, commands_game.PUBLIC_OPERATES, data, error.OK, record)

            record = False

        if self.__can_somebody_hu():  # 有人可以胡，则需要等待
            return
        self.__mo_pai(player.seat_id)

    def __somebody_an_gang(self, gang_list: list) -> bool:
        if len(gang_list) != 1:
            return False

        p = self.get_player_by_seat_id(gang_list[0])
        if not p:
            return False

        data = self.__get_operates_data(ma_jiang.ACTION_TYPE_AN_GANG, p.seat_id)
        if not data or not data.get("card") or not data.get("operateCards"):
            return False

        if self.flow_status == flow.T_IN_OTHER_GANG_PAI_CALL:
            p.pop_chu_pai(data["card"])

        flag = p.an_gang(data["card"], self.__rule)
        send_result = {"seatID": p.seat_id, "isFinish": int(flag), "act": ma_jiang.ACTION_TYPE_AN_GANG}

        send_result.update(data)

        if flag:
            self.inner_broad_cast(commands_game.PLAYER_AN_GANG, send_result, error.OK, 0, True)
            self.__enter_gang_pai_call(p)
            return True
        return False

    def __somebody_ming_gang(self, gang_list: list) -> bool:
        if len(gang_list) != 1:
            return False

        p = self.get_player_by_seat_id(gang_list[0])
        if not p:
            return False

        data = self.__get_operates_data(ma_jiang.ACTION_TYPE_MING_GANG, p.seat_id)
        if not data or not data.get("card") or not data.get("operateCards"):
            return False

        card = data["card"]
        flag = p.ming_gang(card, self.__rule)
        send_result = {"fromSeatId": self.__curr_seat_id, "seatID": p.seat_id, "isFinish": int(flag),
                       "act": ma_jiang.ACTION_TYPE_MING_GANG}

        send_result.update(data)

        if flag:
            self.inner_broad_cast(commands_game.PLAYER_AN_GANG, send_result, error.OK, 0, True)
            self.__enter_ming_gang_call(p, card)
            return True
        return False

    def __somebody_gong_gang(self, gang_list: list) -> bool:
        if len(gang_list) != 1:
            return False

        p = self.get_player_by_seat_id(gang_list[0])
        from_p = self.get_player_by_seat_id(self.__curr_seat_id)
        if not p:
            return False

        data = self.__get_operates_data(ma_jiang.ACTION_TYPE_GONG_GANG, p.seat_id)
        if not data or not data.get("card") or not data.get("operateCards"):
            return False

        card = from_p.pop_chu_pai(data["card"])
        flag = p.gong_gang(card, self.__rule, self.__curr_seat_id)
        send_result = {"fromSeatId": self.__curr_seat_id, "seatID": p.seat_id, "isFinish": int(flag),
                       "act": ma_jiang.ACTION_TYPE_GONG_GANG}

        send_result.update(data)

        if flag:
            self.inner_broad_cast(commands_game.PLAYER_AN_GANG, send_result, error.OK, 0, True)
            self.__enter_gang_pai_call(p)
            return True
        return False

    def __somebody_peng(self, peng_list: list) -> bool:  # 三人均操作后判断有没有人碰牌
        p = self.get_player_by_seat_id(peng_list[0])
        from_p = self.get_player_by_seat_id(self.__curr_seat_id)
        if not p or not from_p:
            return False

        data = self.__get_operates_data(ma_jiang.ACTION_TYPE_PENG, p.seat_id)

        if 2 != len(data["operateCards"]) or not data.get("card"):
            return False

        card = from_p.pop_chu_pai(data["card"])
        flag = p.peng(card, self.curr_seat_id)

        send_result = {"fromSeatID": self.__curr_seat_id, "seatID": p.seat_id, "isFinish": int(flag), }
        send_result.update(data)
        if flag:
            self.__curr_card_exist = 0
            self.inner_broad_cast(commands_game.PLAYER_PENG, send_result, error.OK, 0, True)
            self.__before_turn_to_player_chu_pai(p, False)
            return True
        return False

    def __somebody_chi(self, chi_list):
        if not chi_list:
            return False

        p = self.find_first_player(chi_list)
        from_p = self.get_player_by_seat_id(self.__curr_seat_id)
        if not p or not from_p:
            return False

        data = self.__get_operates_data(ma_jiang.ACTION_TYPE_CHI, p.seat_id)
        if not data:
            return False

        if 2 != len(data["operateCards"]) or not data.get("card"):
            return False

        chi_pai = data["operateCards"]
        card = from_p.pop_chu_pai(data["card"])
        flag = p.chi(card, chi_pai, self.__rule, self.curr_seat_id)

        if not flag:
            return False

        send_result = {"fromSeatId": self.__curr_seat_id, "seatID": p.seat_id, "isFinish": int(flag), }

        send_result.update(data)

        self.__curr_card_exist = 0
        self.inner_broad_cast(commands_game.PLAYER_CHI, send_result, error.OK, 0, True)
        self.__before_turn_to_player_chu_pai(p, False)
        return True

    def __get_operates_data(self, player_action, player_seat_id):
        for item in self.__player_actions:
            seat_id, action, tmp = item
            if player_seat_id == seat_id and action == player_action:
                return tmp

    def __everyone_pass(self):
        p = self.__curr_player()
        if self.flow_status == flow.T_IN_MO_PAI_CALL:  # 摸牌后进入出牌阶段
            return self.__turn_to_player_chu_pai(p, False)
        elif self.flow_status == flow.T_IN_MING_GANG_PAI_CALL:  #
            return self.__do_ming_gang_end()
        elif self.flow_status == flow.T_IN_MING_BU_PAI_CALL:
            return self.__mo_pai(p.seat_id)
        elif self.flow_status == flow.T_IN_GANG_PAI_CALL:
            return self.__enter_other_gang_pai_call(self.__curr_player(), self.curr_cards)
        elif self.flow_status == flow.T_IN_OTHER_GANG_PAI_CALL:  # 其他玩家不可操作时，进入下一玩家摸牌阶段
            return self.__mo_pai(None)
        elif self.flow_status == flow.T_IN_BEFORE_CHU_PAI:  # 其他玩家不可操作时，进入下一玩家摸牌阶段
            return self.__turn_to_player_chu_pai(p, False)

        return self.__mo_pai(None)  # 继续摸牌

    def player_quit(self, player: Player, reason=error.OK):
        """ 退出房间 """
        p = self.seats[player.seat_id]
        if not p or p != player:
            return error.USER_NOT_EXIST, None
        # if p.uid == self.owner and self.is_agent == 0:  # 房主不允许退出，只能解散房间(代开模式下,可以退出房间)
        #     return error.RULE_ERROR, None
        if self.status != flow.T_IDLE:
            return error.RULE_ERROR, None
        self.seats[player.seat_id] = None
        player.on_stand_up()
        if self.match_type == 1 and self.club_id != -1:
            player.return_score(self.club_id)
        if p.uid in self.table_info["player_list"]:
            self.table_info["player_list"].remove(p.uid)
            self.del_player_in_table_info(p.uid)
            self.update_table_info()
        # self.__reset_player_ready()  # 有人退出房间时清理掉所有准备状态
        if player.operator_out_time:
            player.operator_out_time.cancel()
            player.operator_out_time = None
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

        #if self.status == flow.T_IDLE and o_seat_id <= 0:
        #    self.__reset_player_ready()

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
        all_agree = len(self.__agree_seats) >= (self.__total_seat - 1)
        anyone_disagree = len(self.__disagree_seats) > 0
        is_end = all_agree or anyone_disagree
        if not is_end:
            return self.__send_dismiss_result()

        is_dismiss = all_agree
        if anyone_disagree:
            is_dismiss = False
        if not is_dismiss:
            for p in self.seats:
                if not p:
                    continue
                if p.operator_out_time:
                    self.user_time_out_operator(p)

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
        self.__is_request_dismiss_room = True
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

    def user_time_out_operator(self, player: Player , flag=False):
        if player.operator_out_time:
           player.operator_out_time.cancel()
        if not flag:
            for p in self.seats:
                if not p:
                    continue
                if p.uid != player.uid and p.operator_out_time:
                    p.operator_out_time.cancel()
                    p.operator_out_time = None

        print('长沙麻将开始托管')
        player.operator_out_time = DelayCall(player.user_operation_timeout, self.__on_operator_time_out, player)


    def __on_operator_time_out(self, p: Player):
        from games.cs_ma_jiang.game import GameServer
        if not p.is_auto_chupai and not p.iscacel_auto_chupai:
            p.user_operation_timeout = const.Auto_Play_TimeStamp + 1
            p.is_auto_chupai = True
            p.iscacel_auto_chupai = False
            GameServer.share_server().response_ok(p.uid,commands_game.AUTO_ATTACK_ONE,{"is_auto_chupai":p.is_auto_chupai})
        else:
            if p.iscacel_auto_chupai:
                p.iscacel_auto_chupai = False
                return
        data = {"cards":p.mo_card1}
        print(data)
        print( p.operates )
        if len(p.operates) > 0:
            GameServer.share_server().on_player_pass(p.uid,None)
        else:
            GameServer.share_server().on_player_chu_pai( p.uid,data)

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

    def __add_middle_hu_record(self, hu_info):
        self.__middle_hu_record.append(hu_info)

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
        self.update_table_info(True)
