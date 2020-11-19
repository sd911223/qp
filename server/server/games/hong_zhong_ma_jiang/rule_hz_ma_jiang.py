from collections import Counter
from functools import reduce

from games.hong_zhong_ma_jiang.rule_ma_jiang import RuleMaJiang
from utils import utils
from . import ma_jiang
from .rule_base import RuleBase

# 名堂胡加番
BASE_FAN_SHU = {
    "QIANG_GANG_HU": 6,
    "QING_YI_SE": 6,
    "SEVEN_PAIRS": 6,
    "PENG_PENG_HU": 8,
    "TIAN_HU": 6,
    "DI_HU": 6,
}


class RuleZZMaJiang(RuleBase):
    @staticmethod
    def calc_hu(open_huang_fan, huang_zhuang_count):
        pass

    @staticmethod
    def is_ma_jiang_card(card):
        return RuleBase.is_card(card)

    @staticmethod
    def get_hu_pai_option(no_open_option):
        return dict()

    @staticmethod
    def qi_shou_hu(cards: list, option: dict) -> dict:
        """
        起手中了套路
        :param cards:  排
        :param option:  套路开关
        :return:
            {
                组成的套路: [排]
            }
        """
        result = dict()
        return result

    @staticmethod
    def mo_pai_hu(cards: list, option: dict):
        """
        中途套路
        :param cards:
        :param option:
        :return:
        """
        return dict()

    @staticmethod
    def is_correct_cards(cards):
        for card in cards:
            if not RuleBase.is_card(card):
                return False
        return True

    @staticmethod
    def get_ting_pai(cheng_pai, cards):
        all_card = list(ma_jiang.ALL_PAPER_CARDS)

        ting_card = []

        for card in all_card:
            is_hu, _ = RuleZZMaJiang.can_hu(cheng_pai, cards, card, True)
            if is_hu:
                ting_card.append(card)

        return ting_card

    @staticmethod
    def can_hu_new(cheng_pai, cards, card, allow_seven=True):
        nai_zi = ma_jiang.NAI_ZI

        def nai_zi_2_hong_zhong(value):
            if value == nai_zi:
                return ma_jiang.NAI_ZI
            return value

        def hong_zhong_2_nai_zi(value):
            if value == ma_jiang.HONG_ZHONG:
                return nai_zi
            return value

        if nai_zi != ma_jiang.NAI_ZI:
            cards = list(map(nai_zi_2_hong_zhong, cards))

        cards = list(cards)

        nai_zi_count = RuleBase.calc_value_count(cards, ma_jiang.NAI_ZI)

        if RuleBase.is_card(card):
            cards.append(card)

        is_hu, hu_path = RuleZZMaJiang.is_peng_peng_hu(cheng_pai, cards, nai_zi_count)
        if is_hu:
            return True, hu_path

        is_hu, hu_path = RuleZZMaJiang.is_quan_qiu_ren(cheng_pai, cards)
        if is_hu:
            return True, hu_path

        is_hu, hu_path = RuleZZMaJiang.is_qing_yi_se(cheng_pai, cards, nai_zi_count)
        if is_hu:
            return True, hu_path

        is_hu, hu_path = RuleZZMaJiang.is_seven_pairs(cheng_pai, cards)
        if is_hu:
            return True, hu_path

        is_hu, path = RuleMaJiang.can_hu(cards, nai_zi_count, ma_jiang.NAI_ZI)
        if is_hu:
            return True, list(map(lambda v: list(map(hong_zhong_2_nai_zi, v)), path))
        return False, []

    @staticmethod
    def can_hu(zhuo_pai, cards, card, allow_seven=True, nai_zi=ma_jiang.NAI_ZI):
        # if card == ma_jiang.NAI_ZI:  # 红中不允许吃胡
        #    return False, []

        def nai_zi_2_hong_zhong(value):
            if value == nai_zi:
                return ma_jiang.NAI_ZI
            return value

        def hong_zhong_2_nai_zi(value):
            if value == ma_jiang.HONG_ZHONG:
                return nai_zi
            return value

        if nai_zi != ma_jiang.NAI_ZI:
            cards = list(map(nai_zi_2_hong_zhong, cards))

        cards = list(cards)

        if RuleBase.is_card(card):
            cards.append(card)

        nai_zi_count = RuleBase.calc_value_count(cards, ma_jiang.NAI_ZI)
        if nai_zi_count >= 4:
            cards = list(cards)
            count = utils.remove_by_value(cards, nai_zi, -1)
            sorted(cards)
            path = [[nai_zi] * count, cards]
            return True, path

        if allow_seven:
            flag, path = RuleMaJiang.is_seven_pairs(cards, ma_jiang.NAI_ZI)
            if flag:
                return True, list(map(lambda v: list(map(hong_zhong_2_nai_zi, v)), path))

        is_hu, path = RuleMaJiang.can_hu(cards, nai_zi_count, ma_jiang.NAI_ZI)
        if is_hu:
            return True, list(map(lambda v: list(map(hong_zhong_2_nai_zi, v)), path))

        return False, []

    @staticmethod
    def can_chi(zhuo_card, cards: list, card):
        return False
        # result = []
        # if card + 1 in cards and card + 2 in cards:
        #     result.extend([card + 1, card + 2])

        # if card + 1 in cards and card - 1 in cards:
        #     result.extend([card + 1, card - 1])

        # if card - 1 in cards and card - 2 in cards:
        #     result.extend([card - 1, card - 2])

        # return result

    @staticmethod
    def can_gong_gang(cards: list, card):
        if card == ma_jiang.NAI_ZI:
            return False, 0

        if RuleBase.calc_value_count(cards, card) >= 3:
            return True, card

        return False, 0

    @staticmethod
    def have_hong_zhong(cards):
        for card in cards:
            if card == ma_jiang.HONG_ZHONG:
                return True
        return False

    @staticmethod
    def can_ming_gang(cards: list, card):
        return False

    @staticmethod
    def can_an_gang(cards: list):
        for card in cards:
            if card == ma_jiang.NAI_ZI:
                continue

            if RuleBase.calc_value_count(cards, card) >= 4:
                return True, card

        return False, 0

    @staticmethod
    def can_peng(zhuo_pai_list, cards: list, card):
        if card == ma_jiang.NAI_ZI:
            return False

        return RuleBase.calc_value_count(cards, card) >= 2

    @staticmethod
    def get_card_type_of_three(card):
        if RuleMaJiang.is_value_ke_zi(card):
            return ma_jiang.ACTION_TYPE_PENG

        if RuleMaJiang.is_value_shun_zi(card):
            return ma_jiang.ACTION_TYPE_CHI

        return

    @staticmethod
    def search_hu_path(zhuo_cards, hand_cards, nai_zi):
        nai_zi_count = utils.remove_by_value(hand_cards, nai_zi, -1)

        gourp_cards = RuleBase.group_by_suit(hand_cards)

    @staticmethod
    def is_peng_peng_hu(cheng_cards, cards, hz_count=0):
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
        lai_zi_count = hz_count
        less_two_number = 0
        for card, count in counter.most_common():
            if card == ma_jiang.NAI_ZI:
                continue

            if count == 2:
                if lai_zi_count >= 1:
                    lai_zi_count -= 1
                    continue
                less_two_number += 1
                if less_two_number > 1:
                    return False, []
            elif count == 1:
                if lai_zi_count >= 1:
                    if less_two_number == 0:
                        lai_zi_count -= 1
                        less_two_number += 1
                    else:
                        if lai_zi_count < 2:
                            return False, []
                        lai_zi_count -= 2
                    continue
                return False, []

        ret = RuleMaJiang.can_hu(cards, hz_count)
        return ret

    @staticmethod
    def is_quan_qiu_ren(_, cards):
        """全求人"""
        if len(cards) == 2:
            if ma_jiang.NAI_ZI in cards:
                return True, [cards]
            return cards[0] == cards[1], [cards]
        return False, []

    @staticmethod
    def is_qing_yi_se(cheng_cards, cards, hz_count=0):
        """清一色"""
        is_hu, hu_path = RuleMaJiang.can_hu(cards, hz_count)

        if not is_hu:
            return False, []

        cards = reduce(lambda result, v: result + v[1:], cheng_cards, cards)
        tmp_cards = []
        for card in cards:
            if card != ma_jiang.NAI_ZI:
                tmp_cards.append(card)

        hua_se = set(map(lambda value: value // 10, tmp_cards))
        return len(hua_se) == 1, hu_path

    @staticmethod
    def is_seven_pairs(zhuo_pai, cards):
        if len(zhuo_pai) != 0:
            return False, []

        return RuleMaJiang.is_seven_pairs(cards)

    @staticmethod
    def get_long_qi_count_bad(zhuo_pai, cards):
        is_ok, _ = RuleZZMaJiang.is_seven_pairs(zhuo_pai, cards)
        if not is_ok:
            return 0

        counter = Counter(cards)

        sorted(counter.items(), key=lambda x: x[1], reverse=True)
        if ma_jiang.NAI_ZI in counter:
            nai_zi_count = counter[ma_jiang.NAI_ZI]
        else:
            nai_zi_count = 0

        four_count = 0

        for card, count in counter.most_common():
            if card == ma_jiang.NAI_ZI:
                continue
            if count == 4:
                four_count += 1
            elif count == 3:
                if nai_zi_count >= 1:
                    four_count += 1
                    nai_zi_count -= 1
            elif count == 2:
                if nai_zi_count >= 2:
                    four_count += 1
                    nai_zi_count -= 2
            elif count == 1:
                if nai_zi_count >= 3:
                    four_count += 1
                    nai_zi_count -= 3

        return four_count

    @staticmethod
    def get_long_qi_count(zhuo_pai, cards):
        is_ok, result = RuleZZMaJiang.is_seven_pairs(zhuo_pai, cards)

        if not is_ok:
            return 0

        print("!!!!!result: ", result)
        # counter = Counter(cards)

        # count_info = list(filter(lambda v: v[1] > 3, counter.most_common()))
        four_count = 0
        for ret in result:
            if len(ret) == 4:
                four_count += 1
        hz_pair = [ma_jiang.NAI_ZI, ma_jiang.NAI_ZI]
        four_count += result.count(hz_pair)
        return four_count
