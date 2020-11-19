# coding:utf-8
import random
from copy import deepcopy

from games.ma_jiang.rule_base import RuleBase


class MaJiangCard:
    def __init__(self, *args, **kwargs):
        self.__cards = RuleBase.make_majiang_card(*args, **kwargs)
        self.__cursor = 0  # 当前所发到的牌的位置
        self.__pop_orders = []

    def shuffle(self, count=3):
        self.__cursor = 0
        if self.__pop_orders:
            self.__shuffle_by_order(count)
        else:
            random.shuffle(self.__cards)
            random.shuffle(self.__cards)

    def pop(self, exclude_cards=list()):
        if self.__cursor >= len(self.__cards):
            return 0
        c = self.__cards[self.__cursor]
        if c in exclude_cards and set(self.__cards[self.__cursor:]) != set(exclude_cards):
            self.__cards.pop(self.__cursor)
            self.__cards.append(c)
            c = self.pop(exclude_cards)
        else:
            self.__cursor += 1
        return c

    def set_pop_order(self, cards):
        assert len(cards) == 5
        self.__pop_orders = cards

    def __shuffle_by_order(self, count=3):
        all_cards = deepcopy(self.__cards)
        random.shuffle(all_cards)
        order_cards = []
        tail_cards = []

        for i in range(count):
            l = self.__pop_orders[i] or []
            for c in l:
                if c in all_cards:
                    all_cards.remove(c)

        for c in self.__pop_orders[count] or []:
            tail_cards.append(c)
            all_cards.remove(c)

        for i in range(13):
            for j in range(count):
                data = self.__pop_orders[j]
                if i < len(data):
                    order_cards.append(data[i])
                else:
                    order_cards.append(all_cards.pop(0))
        order_cards.extend(tail_cards)
        order_cards.extend(all_cards)
        self.__cards = order_cards

    def get_cards(self):
        return deepcopy(self.__cards)

    def clear_pop_order(self):
        self.__pop_orders = []

    def modify_card_index(self, from_idx, to_idx, curr_idx):
        if to_idx > len(self.__cards) - 1 or from_idx > \
                len(self.__cards) - 1 or from_idx < curr_idx or to_idx < curr_idx:
            return 0
        tmp_card = self.__cards[from_idx]
        self.__cards[from_idx] = self.__cards[to_idx]
        self.__cards[to_idx] = tmp_card
        return 1

    @property
    def left_count(self):  # 剩余张数
        return max(len(self.__cards) - self.__cursor, 0)

    def qu_yi_men(self, type):
        for card in self.__cards:
            if card % 10 == type:
                self.__cards.remove(card)