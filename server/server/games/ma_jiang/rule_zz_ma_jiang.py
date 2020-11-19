from .rule_base import RuleBase

from games.ma_jiang.rule_ma_jiang import RuleMaJiang
from . import ma_jiang
from utils import utils

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
    def can_hu(zhuo_pai, cards, card, allow_seven, nai_zi=ma_jiang.NAI_ZI):
        if card == ma_jiang.NAI_ZI:  # 红中不允许吃胡
            return False, []

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
