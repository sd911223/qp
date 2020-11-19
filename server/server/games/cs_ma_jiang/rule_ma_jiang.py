import random
from copy import deepcopy

from .rule_base import RuleBase

from games.cs_ma_jiang import ma_jiang
from utils.utils import remove_by_value


class RuleMaJiang(RuleBase):
    @staticmethod
    def random_dice(count):
        return [random.randint(1, 6) for _ in range(count)]

    @staticmethod
    def get_count_list_by_value(cards):
        """统计整组牌张数量"""
        count_list = dict()
        for v in cards:
            if not count_list.get(v):
                count_list[v] = 0

            count_list[v] += 1

        return count_list

    @staticmethod
    def search_pairs(cards):
        """搜索可组成对子牌的列表"""
        count_list = RuleMaJiang.get_count_list_by_value(cards)
        result = list()
        for card, count in count_list.items():
            if count >= 2:
                result.append(card)

        result.sort()
        return result

    @staticmethod
    def calc_ke_zi_list_and_must_list(cards):
        """计算刻子列表，以及必须被满足的牌列表"""
        count_list = RuleMaJiang.get_count_list_by_value(cards)
        ke_zi_list = list()
        must_list = list()
        for value, count in count_list.items():
            if count == 1:
                must_list.append(value)
            elif count == 2:
                must_list.append(value)
                must_list.append(value)
            elif count == 3:
                ke_zi_list.append(value)
            elif count == 4:
                must_list.append(value)
                ke_zi_list.append(value)

        return ke_zi_list, must_list

    @staticmethod
    def is_seven_pairs(cards, nai_zi):
        """判断是否7小对"""
        if not cards or len(cards) != 14:
            return False, []

        cards = list(cards)
        nai_zi_count = remove_by_value(cards, nai_zi, -1)
        count_list = RuleMaJiang.get_count_list_by_value(cards)
        singles = [card for card, count in count_list.items() if count ==
                   1 or count == 3]

        singles_len = len(singles)
        if singles_len <= 0:
            return True, [[card] * count for card, count in count_list.items()]

        singles_path = []
        for card in singles:
            already_count = count_list[card]
            singles_path.append([card] * already_count + [nai_zi])

        if singles_len == nai_zi_count:
            singles_path.extend([[card] * count for card, count in count_list.items() if count ==
                                 2 or count == 4])
            return True, singles_path

        if nai_zi_count - 2 == singles_len:
            singles_path.append([nai_zi] * 2)
            singles_path.extend([[card] * count for card, count in count_list.items() if count ==
                                 2 or count == 4])
            return True, singles_path

        return False, []

    @staticmethod
    def is_group_match_rule(cards):
        """判断牌值的分组是否符合麻将的顺子、刻子的规则"""
        cards_len = len(cards)
        hu_path = []
        if cards_len == 0:
            return True, hu_path

        cards.sort()
        is_shun_zi, path = RuleBase.is_value_shun_zi(cards)
        if RuleBase.is_value_ke_zi(cards) or is_shun_zi:
            hu_path.append(cards)
            return True, hu_path

        ke_zi_list, must_list = RuleMaJiang.calc_ke_zi_list_and_must_list(
            cards)
        hu_path = list(map(lambda value: [value] * 3, ke_zi_list))
        if len(must_list) == 0:
            return True, hu_path

        if len(ke_zi_list) == 0:
            flag, shun_zi_path = RuleBase.is_value_shun_zi(cards)
            hu_path.extend(shun_zi_path)
            return flag, hu_path

        must_list.sort()
        is_shun_zi, shun_zi_path = RuleBase.is_value_shun_zi(must_list)
        if is_shun_zi:
            hu_path.extend(shun_zi_path)
            return True, hu_path

        ke_zi_list.sort()
        for v in ke_zi_list:
            tmp_value = list(must_list)
            tmp_value.extend([v] * 3)
            tmp_value.sort()
            is_shun_zi, shun_zi_path = RuleBase.is_value_shun_zi(tmp_value)
            if is_shun_zi:
                hu_path.extend(shun_zi_path)
                return True, hu_path

        return False, []

    @staticmethod
    def can_hu_by_jiang(cards, card):
        """ 判断能否以此为将牌胡牌 """
        cards = list(cards)
        remove_jiang_count = 2
        remove_by_value(cards, card, remove_jiang_count)
        group = RuleBase.group_by_suit(cards)
        hu_path = []
        for k, v in group.items():
            if len(v) % 3 != 0:
                return False, []
            flag, unit_hu_path = RuleMaJiang.is_group_match_rule(list(v))
            for path in unit_hu_path:
                hu_path.append(list(map(lambda value: k * 10 + value, path)))

            if not flag:
                return False, []

        hu_path.append([card] * remove_jiang_count)
        return True, hu_path

    @staticmethod
    def __can_hu_with_pairs_and_jiang(cards, nai_zi_count, remove_jiang, nai_zi=ma_jiang.NAI_ZI):
        pair_list = RuleMaJiang.search_pairs(cards)
        for jiang in pair_list:
            flag, hu_path =\
                RuleMaJiang.can_hu_with_nai_zi_and_jiang(cards, jiang, nai_zi_count, remove_jiang, nai_zi)
            if flag:
                return True, hu_path

        for jiang in cards:
            flag, hu_path =\
                RuleMaJiang.can_hu_with_nai_zi_and_jiang(cards, jiang, nai_zi_count - 1, remove_jiang - 1, nai_zi)
            if flag:
                return True, hu_path

        return False, []

    @staticmethod
    def can_hu_without_nai_zi(cards, _):
        """ 不带赖子判断胡牌 """
        pair_list = RuleMaJiang.search_pairs(cards)
        for card in pair_list:
            flag, path = RuleMaJiang.can_hu_by_jiang(cards, card)
            if flag:
                return True, path

        return False, []

    @staticmethod
    def can_hu_special_jiang(cards, special_jiang):
        """ 不带赖子判断胡牌 """
        pair_list = RuleMaJiang.search_pairs(cards)
        for card in pair_list:
            if card not in special_jiang:
                continue

            flag, path = RuleMaJiang.can_hu_by_jiang(cards, card)
            if flag:
                return True, path

        return False, []

    @staticmethod
    def can_hu_with_one_nai_zi(cards, nai_zi):
        """
        一个癞子判断胡牌
        手里有将，则先尝试用将牌组合，判断能否胡
        如果没有将，则直接尝试红中补将
        """
        remove_by_value(cards, nai_zi, -1)

        return RuleMaJiang.__can_hu_with_pairs_and_jiang(cards, 1, 2, nai_zi)

    @staticmethod
    def can_hu_with_two_nai_zi(cards, nai_zi):
        """
        两个癞子判断能否胡牌
        2个红中：
        一对作将 -> 不补，直接按现有方式处理
        先找将牌，有的话先遍历一下，看能不能直接用手中的将胡牌
        如果不行，再直接遍历全部手牌拼将，看能不能胡
        """
        remove_by_value(cards, nai_zi, -1)
        flag, hu_path = RuleMaJiang.can_hu_by_jiang(cards, nai_zi)
        if flag:
            return True, hu_path

        return RuleMaJiang.__can_hu_with_pairs_and_jiang(cards, 2, 2, nai_zi)

    @staticmethod
    def can_hu_with_three_nai_zi(cards, nai_zi):
        """
        三个癞子判断能否胡牌
        3个红中：
        3张+0补
        直接按现有算法处理

        一对将+1补
        红中作将，其它的牌按1补的方式来处理

        三张全补
        手牌有将，则先遍历将牌
        手牌无将，则先补一将，三张牌必须全部补下去
        """
        remove_by_value(cards, nai_zi, -1)
        flag, hu_path = RuleMaJiang.can_hu_without_nai_zi(cards, nai_zi)
        if flag:
            return True, hu_path

        flag, hu_path = RuleMaJiang.can_hu_with_nai_zi_and_jiang(cards, nai_zi, 1, 0)
        if flag:
            return True, hu_path

        return RuleMaJiang.__can_hu_with_pairs_and_jiang(cards, 3, 2, nai_zi)

    @staticmethod
    def can_hu_with_four_nai_zi(cards, nai_zi):
        """
        四个癞子判断能否胡牌
        4个红中：
        3张+1补
        红中不能做将，直接按1个红中的情况处理

        一对将+2补
        红中作将，剩下的两张按2个红中补两张的方式来处理

        四张全补
        红中不能作将（但可以补将），四张牌必须全部补下去
        """
        remove_by_value(cards, nai_zi, -1)
        flag, hu_path = RuleMaJiang.can_hu_with_one_nai_zi(cards, nai_zi)
        if flag:
            return True, hu_path

        flag, hu_path = RuleMaJiang.can_hu_with_nai_zi_and_jiang(cards, nai_zi, 2, 0)
        if flag:
            return True, hu_path

        return RuleMaJiang.__can_hu_with_pairs_and_jiang(cards, 4, 2, nai_zi)

    @staticmethod
    def can_hu(cards, hz_count=0, nai_zi=ma_jiang.NAI_ZI):
        """判断胡牌的总循环"""
        if len(cards) % 3 != 2:
            return False, []

        cards = list(cards)

        method_map = {
            0: RuleMaJiang.can_hu_without_nai_zi,
            1: RuleMaJiang.can_hu_with_one_nai_zi,
            2: RuleMaJiang.can_hu_with_two_nai_zi,
            3: RuleMaJiang.can_hu_with_three_nai_zi,
            4: RuleMaJiang.can_hu_with_four_nai_zi,
        }

        if method_map.get(hz_count):
            flag, hu_path = method_map.get(hz_count)(cards, nai_zi)
            if flag:
                hu_path = list(filter(lambda v: v != [], hu_path))

            return flag, hu_path

        return False, []

    @staticmethod
    def get_hu_path(suit, step_data, nai_zi):
        step_data = deepcopy(step_data)
        hu_path = []
        user_cards = []
        for step in reversed(step_data):
            for already_user_card in user_cards:
                if already_user_card in step[3]:
                    step[3].remove(already_user_card)

            user_cards.extend(step[3])
            cards = list(map(lambda v: suit * 10 + v, step[3]))
            hz_cards = list(map(lambda v: suit * 10 + v, step[4]))
            unit_path = (cards + hz_cards)
            unit_path.sort()
            for value in step[4]:
                index = unit_path.index(suit * 10 + value)
                unit_path[index] = nai_zi

            hu_path.append(unit_path)

        return hu_path

    @staticmethod
    def can_hu_with_nai_zi_and_jiang(cards, jiang, nai_zi_count, remove_jiang_count, nai_zi=ma_jiang.NAI_ZI):
        cards = list(cards)
        remove_by_value(cards, jiang, remove_jiang_count)

        group = RuleBase.group_by_suit(cards).items()
        group = sorted(group, key=lambda value: len(value[1]), reverse=True)
        hu_path = []
        for suit, card_list in group:
            flag, nai_zi_count_temp, step_data = RuleMaJiang.check_value_match_rule_with_nai_zi_count(
                list(card_list), 0, list(), nai_zi_count, False)
            if not flag:
                return False, []
            else:
                hu_path.extend(RuleMaJiang.get_hu_path(suit, step_data, nai_zi))
            nai_zi_count = nai_zi_count_temp

        hu_path.append([jiang] * remove_jiang_count)
        for value in hu_path:
            if len(value) == 1:
                value.append(nai_zi)

        return True, hu_path

    @staticmethod
    def check_value_is_valid_with_nai_zi(cards, step_data, index, hz_count):
        """

        :param cards:
        :param step_data:
        :param index:
        :param hz_count:
        :return: 是否组成顺子或刻子, 当前牌, 红中数量，红中所变的牌
        """
        calcCards = list(cards)
        value = cards[0]
        hz_change_value = []
        if not step_data[index][0]:
            step_data[index][0] = True
            if value + 1 in cards and value + 2 in cards:
                remove_by_value(cards, value)
                remove_by_value(cards, value + 1)
                remove_by_value(cards, value + 2)
                return True, cards, hz_count, hz_change_value

            used_hz = 0
            if value + 1 not in cards:
                used_hz += 1
                hz_change_value.append(value + 1)

            if value + 2 not in cards:
                used_hz += 1
                if value + 2 <= 9:
                    hz_change_value.append(value + 2)
                else:
                    hz_change_value.append(value - 1)

            if hz_count >= used_hz > 0:
                hz_count -= used_hz
                remove_by_value(cards, value)
                remove_by_value(cards, value + 1)
                if value + 2 <= 9:
                    remove_by_value(cards, value + 2)
                else:
                    remove_by_value(cards, value - 2)
                return True, cards, hz_count, hz_change_value
            else:
                hz_change_value = []

        if not step_data[index][1]:
            step_data[index][1] = True
            count = RuleBase.calc_value_count(cards, value)
            if 3 <= count:
                remove_by_value(cards, value, 3)
                return True, cards, hz_count, hz_change_value

            if hz_count > 0 and hz_count >= 3 - count:
                remove_by_value(cards, value, 3)
                hz_count -= (3 - count)
                hz_change_value.extend([value] * (3 - count))
                return True, cards, hz_count, hz_change_value

        return False, calcCards, hz_count, hz_change_value

    @staticmethod
    def check_value_match_rule_with_nai_zi_count(cards, index, step_data, hz_count, is_back):
        """
        检测某花色是否符合游戏规则（带红中检测）
        从最左边的牌往右依次来检测，当成顺或成刻时，此路通
        当即不成顺又不成刻时，此路不通
        当此路通时，往下循环，到达终点时则是成功
        当此路不通时，往上回退一步，如果上一步已经检测了顺和刻，则再回退一步，
        直到可以选择下一步或者回到了起点。
        """
        if len(cards) == 0:
            return True, hz_count, step_data,

        cards.sort()
        if index >= len(step_data):
            step_data.append([False, False, 0, {}, []])

        if not is_back:
            step_data[index][2] = hz_count
            step_data[index][3] = deepcopy(cards)

        flag, new_list, new_hz_count, new_hz_change_value = RuleMaJiang.check_value_is_valid_with_nai_zi(
            cards, step_data, index, hz_count)

        step_data[index][4] = new_hz_change_value
        if flag:
            return RuleMaJiang.check_value_match_rule_with_nai_zi_count(
                new_list, index + 1, step_data, new_hz_count, False)

        if index > 0:
            step_data = step_data[0:index]
            old_hz_count, old_list = deepcopy(step_data[index - 1][2]), deepcopy(step_data[index - 1][3])

            return RuleMaJiang.check_value_match_rule_with_nai_zi_count(
                old_list, index - 1, step_data, old_hz_count, True)

        if index == 0:
            return False, hz_count, step_data

        return False, hz_count, step_data
