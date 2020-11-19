from collections import Counter
from functools import reduce

from .rule_base import RuleBase
from utils import utils

import pydash

from games.cs_ma_jiang.rule_ma_jiang import RuleMaJiang
from . import ma_jiang

CS_MA_JIANG_JIANG = [
    12, 15, 18,
    22, 25, 28,
    32, 35, 38,
]

MAX_LOOP_COUNT = 1000


class RuleCSMaJiang(RuleBase):
    @staticmethod
    def is_ma_jiang_card(card):
        return RuleBase.is_card(card)

    @staticmethod
    def get_ting_pai(cheng_pai, cards):
        all_card = list(ma_jiang.ALL_PAPER_CARDS)

        ting_card = []
        for card in all_card:
            is_hu, _ = RuleCSMaJiang.can_hu(cheng_pai, cards, card, True)
            if is_hu:
                ting_card.append(card)

        return ting_card

    @staticmethod
    def is_ting_pai(cheng_pai, cards):
        all_card = list(ma_jiang.ALL_PAPER_CARDS)

        for card in all_card:
            is_hu, _ = RuleCSMaJiang.can_hu(cheng_pai, cards, card, True)
            if is_hu:
                return True

        return False

    @staticmethod
    def get_begin_option(open_options, is_all=False,is_que_yi_men=False):
    # def get_begin_option(open_options, is_all=False):
        options = {
            "danSeYiZhiHua": {
                "func": RuleCSMaJiang.is_dan_se_yi_zhi_hua,
                "score": 2
            },
            "jiangYiZhiHua": {
                "func": RuleCSMaJiang.is_jiang_yi_zhi_hua,
                "score": 2
            },
            "yiZhiNiao": {
                "func": RuleCSMaJiang.is_yi_zhi_niao,
                "score": 2,
            },
            "liuLiuShun": {
                "func": RuleCSMaJiang.is_liu_liu_shun,
                "score": 2,
            },
            "sanTong": {
                "func": RuleCSMaJiang.is_san_tong,
                "score": 2,
            },
            "jieJieGao": {
                "func": RuleCSMaJiang.is_jie_jie_gao,
                "score": 2
            },
            "qiShouSiZhang": {
                "func": RuleCSMaJiang.is_si_xi,
                "score": 2
            },
            "banBanHu": {
                "func": RuleCSMaJiang.is_ban_ban_hu,
                "score": 2
            },
            # "queYiSe": {
            #     "func": RuleCSMaJiang.is_que_yi_se,
            #     "score": 1
            # },
        }

        if not is_que_yi_men:
            options["queYiSe"] = {
                "func": RuleCSMaJiang.is_que_yi_se,
                "score": 2
            }

        if is_all:
            return options

        result = {}
        for open_option in open_options:
            if open_option in options:
                result[open_option] = options[open_option]

        return result

    @staticmethod
    def check_count_hu(key, hu_record, count=0):
        count_map = pydash.count_by(hu_record, lambda value: value[0])
        now_count = key in count_map and count_map[key] or 0
        return now_count <= count

    @staticmethod
    def check_not_same_value(key, hu_record: list, cards: list = None):
        if cards is None:
            cards = []

        index = pydash.find_index(hu_record,
                                  lambda value: value[0] == key and len(pydash.intersection(cards, value[1])) != 0)

        if index == -1:
            return True

        return False

    @staticmethod
    def get_middle_option(open_options, is_all=False):
        options = {
            "zhongTuSiZhang": {
                "func": RuleCSMaJiang.is_si_xi,
                "check": lambda hu_record, cards: RuleCSMaJiang.check_not_same_value("qiShouSiZhang", hu_record,
                                                                                     cards),
                "second_check":
                    lambda hu_record, cards: RuleCSMaJiang.check_not_same_value("zhongTuSiZhang", hu_record, cards),
                "score": 2
            },
            "zhongTuLiuLiuShun": {
                "func": RuleCSMaJiang.is_liu_liu_shun,
                "check": lambda hu_record, cards: RuleCSMaJiang.check_count_hu("liuLiuShun", hu_record),
                "second_check": lambda hu_record, cards: RuleCSMaJiang.check_count_hu("zhongTuLiuLiuShun", hu_record),
                "score": 2
            },
        }

        if is_all:
            return options

        result = {}
        for open_option in open_options:
            if open_option in options:
                result[open_option] = options[open_option]

        return result

    @staticmethod
    def get_middle_hu(options, cards: list, card=ma_jiang.NULL_CARD, hu_record=None):
        """
        :param options: 胡牌配置
        :param cards: 手牌
        :param card: 摸牌
        :param hu_record: 胡牌记录
        :return:
        """

        new_hu_record = []
        if hu_record is None:
            hu_record = []

        cards = list(cards)

        hu_info = []
        for hu_name, option in options.items():
            tmp_cards = list(cards)
            hu_cards_list = []
            all_count = 0
            for _ in range(MAX_LOOP_COUNT):
                ok, hu_cards, num = option["func"](tmp_cards, card)
                if not ok:
                    break

                if not option.get("check") is None:
                    ok = option["check"](hu_record, tmp_cards + [card])

                if not ok:
                    break

                if not option.get("second_check") is None:
                    ok = option["second_check"](hu_record, tmp_cards + [card])

                if not ok:
                    break

                new_hu_record.append([hu_name, hu_cards])
                all_count += num
                if hu_name not in ("danSeYiZhiHua", "jiangYiZhiHua", "yiZhiNiao", "queYiSe", "banBanHu"):
                    hu_cards_list.append(list(hu_cards))
                else:
                    hu_cards_list.append(cards)

                if card in hu_cards:
                    hu_cards.remove(card)

                for hu_card in hu_cards:
                    if hu_card in tmp_cards:
                        tmp_cards.remove(hu_card)

            if len(hu_cards_list) == 0:
                continue

            print("hu_name:",hu_name)

            hu_info.append(
                {"hu_name": [hu_name] * all_count, "score": option["score"] * all_count, "cards": hu_cards_list})

        return hu_info, new_hu_record

    @staticmethod
    def get_middle_hu_cards(hu_info):
        """
        将胡牌信息整理
        :param hu_info:
        :return: 返回去重后的牌
        """
        format_cards = []
        for cell_hu_info in hu_info:
            hu_cards = [card for value in cell_hu_info["cards"] for card in value]
            tmp_format_cards = list(format_cards)
            for card in hu_cards:
                if card in tmp_format_cards:
                    tmp_format_cards.remove(card)
                else:
                    format_cards.append(card)

        format_cards.sort()
        return format_cards

    @staticmethod
    def is_si_xi(cards, card=ma_jiang.NULL_CARD):

        if card != ma_jiang.NULL_CARD:
            cards = cards + [card]

        counter = Counter(cards)

        count_info = list(filter(lambda v: v[1] > 3, counter.most_common()))
        if len(count_info) <= 0:
            return False, [], 0

        return True, [count_info[0][0]] * 4, 1

    @staticmethod
    def is_ban_ban_hu(cards, _):
        if not cards:
            return False, [], 0

        value_set = set([RuleMaJiang.get_value(card) for card in cards])
        jiang_list = [2, 5, 8]
        is_ok = len(value_set & set(jiang_list)) == 0
        if is_ok:
            return is_ok, list(cards), 1
        return is_ok, [], 0

    @staticmethod
    def is_que_yi_se(cards, _):
        if not cards:
            return False, [], 0

        suit_set = set([RuleMaJiang.get_suit(card) for card in cards])
        is_ok = len(suit_set) < 3
        if is_ok:
            return is_ok, list(cards), 3 - len(suit_set)
        return is_ok, [], 0

    @staticmethod
    def is_jie_jie_gao(cards, _):
        counter = Counter(cards)

        count_info = list(filter(lambda v: v[1] > 1, counter.most_common()))
        if len(count_info) < 3:
            return False, [], 0

        count_info.sort(key=lambda value: value[0])
        cards_map = dict(count_info)
        result = []
        for card, count in count_info:
            if (card + 1) not in cards_map or (card + 2) not in cards_map:
                continue

            result.extend([card] * 2 + [card + 1] * 2 + [card + 2] * 2)
            break

        is_ok = bool(result)
        return is_ok, result, int(is_ok)

    @staticmethod
    def is_san_tong(cards, _):
        counter = Counter(cards)

        cards_info = {}
        for card, count in counter.most_common():
            if count < 2:
                continue

            value = RuleMaJiang.get_value(card)
            if value not in cards_info:
                cards_info[value] = []
            cards_info[value].append([card, count])

        for value, cards in cards_info.items():
            if len(cards) < 3:
                continue

            hu_cards = [cards.pop(0)[0]] * 2 + [cards.pop(0)[0]] * 2 + [cards.pop(0)[0]] * 2
            return True, hu_cards, 1

        return False, [], 0

    @staticmethod
    def is_liu_liu_shun(cards, card=ma_jiang.NULL_CARD):
        if card != ma_jiang.NULL_CARD:
            cards = cards + [card]
        counter = Counter(cards)

        count_info = list(filter(lambda v: v[1] > 2, counter.most_common()))
        result = []
        if len(count_info) < 2:
            return False, result, 0

        for i in range(2):
            card, count = count_info[i]
            result.extend([card] * 3)

        return bool(result), result, 1

    @staticmethod
    def is_yi_zhi_niao(cards, _):
        group = RuleMaJiang.group_by_suit(cards)
        if 2 not in group or len(group[2]) != 1 or group[2][0] != 1:
            return False, [], 0

        return True, [21], 1

    @staticmethod
    def is_jiang_yi_zhi_hua(cards, _):
        signal_jiang = 0
        result = []
        for v in CS_MA_JIANG_JIANG:
            if cards.count(v) == 1:
                signal_jiang += 1
                result.append(v)
            elif cards.count(v) == 0:
                continue
            else:
                return False, [], 0

        if signal_jiang == 1 and result[0] % 10 == 5:
            return True, result, 1

        return False, [], 0

    @staticmethod
    def is_dan_se_yi_zhi_hua(cards, _):
        wan = 0
        tiao = 0
        tong = 0
        wan_pos = 0
        tiao_pos = 0
        tong_pos = 0
        pos = 0
        result = []
        for card in cards:
            color = card // 10
            if color == 1:
                wan += 1
                wan_pos = pos
            elif color == 2:
                tiao += 1
                tiao_pos = pos
            else:
                tong += 1
                tong_pos = pos

            pos += 1

        if wan == 1 and cards[wan_pos] % 10 == 5:
            result.append(cards[wan_pos])

        if tiao == 1 and cards[tiao_pos] % 10 == 5:
            result.append(cards[tiao_pos])

        if tong == 1 and cards[tong_pos] % 10 == 5:
            result.append(cards[tong_pos])

        if len(result) is not 0:
            return True, result, 1

        return False, [], 0

    @staticmethod
    def middle_hu(cards: list, options: dict) -> dict:
        result = dict()
        for name, func in options.items():
            is_middle_hu, card = func(list(cards))
            if is_middle_hu:
                result[name] = card

        return result

    @staticmethod
    def is_correct_cards(cards):
        for card in cards:
            if not RuleBase.is_card(card):
                return False
        return True

    @staticmethod
    def is_jiang_jiang_hu(cheng_cards, cards):
        """将将胡"""
        cards = reduce(lambda result, v: result + v[1:], cheng_cards, cards)
        for card in cards:
            if card not in CS_MA_JIANG_JIANG:
                return False, []

        return True, [cards]

    @staticmethod
    def is_men_qing_hu(cheng_cards, cards):
        """门清胡"""
        if len(cheng_cards) != 0:
                return False

        return True

    # @staticmethod
    # def is_que_yi_men(cheng_cards, cards):
    #     """缺一门胡"""
    #     if len(cheng_cards) != 0:
    #         return False, []
    #
    #     return True, [cards]

    @staticmethod
    def is_qing_yi_se(cheng_cards, cards):
        """清一色"""
        is_hu, hu_path = RuleMaJiang.can_hu(cards, 0)

        if not is_hu:
            return False, []

        cards = reduce(lambda result, v: result + v[1:], cheng_cards, cards)
        hua_se = set(map(lambda value: value // 10, cards))
        return len(hua_se) == 1, hu_path

    @staticmethod
    def is_quan_qiu_ren(_, cards):
        """全求人"""
        return len(cards) == 2 and cards[0] == cards[1], [cards]

    @staticmethod
    def is_peng_peng_hu(cheng_cards, cards):
        """碰碰胡"""
        for cheng_card in cheng_cards:
            if cheng_card[0] not in (
                    ma_jiang.ACTION_TYPE_PENG,
                    ma_jiang.ACTION_TYPE_AN_GANG,
                    ma_jiang.ACTION_TYPE_MING_GANG,
                    ma_jiang.ACTION_TYPE_GONG_GANG
            ):
                return False, []

        counter = Counter(cards)

        less_two_number = 0
        for card, count in counter.most_common():
            if count == 2:
                less_two_number += 1
                if less_two_number > 1:
                    return False, []
            elif count == 1:
                return False, []

        return RuleMaJiang.can_hu(cards)

    @staticmethod
    def get_long_qi_count(zhuo_pai, cards):
        is_ok, _ = RuleCSMaJiang.is_seven_pairs(zhuo_pai, cards)
        if not is_ok:
            return 0

        counter = Counter(cards)

        count_info = list(filter(lambda v: v[1] > 3, counter.most_common()))
        return len(count_info)

    @staticmethod
    def is_seven_pairs(zhuo_pai, cards):
        if len(zhuo_pai) != 0:
            return False, []

        return RuleMaJiang.is_seven_pairs(cards, 0)

    @staticmethod
    def can_hu(cheng_pai, cards, card, allow_seven):
        cards = list(cards)

        if RuleBase.is_card(card):
            cards.append(card)

        if len(cards) % 3 != 2:
            return False, []

        is_hu, hu_path = RuleCSMaJiang.is_jiang_jiang_hu(cheng_pai, cards)
        if is_hu:
            return True, hu_path

        is_hu, hu_path = RuleCSMaJiang.is_peng_peng_hu(cheng_pai, cards)
        if is_hu:
            return True, hu_path

        is_hu, hu_path = RuleCSMaJiang.is_quan_qiu_ren(cheng_pai, cards)
        if is_hu:
            return True, hu_path

        is_hu, hu_path = RuleCSMaJiang.is_qing_yi_se(cheng_pai, cards)
        if is_hu:
            return True, hu_path

        if allow_seven:
            is_hu, hu_path = RuleCSMaJiang.is_seven_pairs(cheng_pai, cards)
            if is_hu:
                return True, hu_path

        return RuleMaJiang.can_hu_special_jiang(cards, CS_MA_JIANG_JIANG)

    @staticmethod
    def can_chi(_, cards: list, card):
        result = []
        if card - 1 in cards and card - 2 in cards:
            result.append([card - 2, card - 1])

        if card + 1 in cards and card - 1 in cards:
            result.append([card - 1, card + 1])

        if card + 1 in cards and card + 2 in cards:
            result.append([card + 1, card + 2])

        return result

    @staticmethod
    def can_gong_gang(_, cards: list, card=ma_jiang.NULL_CARD):
        cards = list(cards)
        if not card or card == ma_jiang.NULL_CARD:
            return []

        if RuleBase.calc_value_count(cards, card) >= 3:
            return [[card] * 3]

        return []

    @staticmethod
    def can_an_gang(_, cards: list, card=ma_jiang.NULL_CARD):
        cards = list(cards)
        if card and card != ma_jiang.NULL_CARD:
            cards.append(card)

        can_an_gang_list = []
        for card in cards:
            if RuleBase.calc_value_count(cards, card) >= 4:
                count = utils.remove_by_value(cards, card, 4)
                if count != 4:
                    continue
                can_an_gang_list.append([card] * 4)

        return can_an_gang_list

    @staticmethod
    def can_ming_gang(zhuo_pai_list, cards: list, card=ma_jiang.NULL_CARD):
        cards = list(cards)
        if card and card != ma_jiang.NULL_CARD:
            cards.append(card)

        can_gang_list = []
        for card in cards:
            for i in range(len(zhuo_pai_list)):
                card_type = zhuo_pai_list[i][0]
                first_card = zhuo_pai_list[i][1]
                if card_type not in (ma_jiang.ACTION_TYPE_PENG,):
                    continue
                if first_card != card:
                    continue

                can_gang_list.append([card])

        return can_gang_list

    @staticmethod
    def can_peng(_, cards: list, card):
        if RuleBase.calc_value_count(cards, card) >= 2:
            return [[card] * 2]

        return []

    @staticmethod
    def get_card_type_of_three(card):
        if RuleMaJiang.is_value_ke_zi(card):
            return ma_jiang.ACTION_TYPE_PENG

        if RuleMaJiang.is_value_shun_zi(card):
            return ma_jiang.ACTION_TYPE_CHI

        return
