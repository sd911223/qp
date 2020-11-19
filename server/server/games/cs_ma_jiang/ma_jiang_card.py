# coding:utf-8
import random
from copy import deepcopy

from games.cs_ma_jiang.rule_base import RuleBase


class MaJiangCard:
    def __init__(self, *args, **kwargs):
        self.__cards = RuleBase.make_majiang_card_new(*args, **kwargs)
        self.__cursor = 0  # 当前所发到的牌的位置
        self.__pop_orders = []

    def shuffle(self, count=3):
        self.__cursor = 0
        if self.__pop_orders:
            self.__shuffle_by_order(count)
        else:
            random.shuffle(self.__cards)
            random.shuffle(self.__cards)
    #test func
    def set_cards(self,cards):
        for index in range(len(cards)):
            self.__cards[self.__cursor + index] = cards[index]

    def pop(self):
        if self.__cursor >= len(self.__cards):
            return 0
        c = self.__cards[self.__cursor]
        self.__cursor += 1
        return c

    def set_pop_order(self, cards):
        assert len(cards) == 5
        self.__pop_orders = cards

    def clear_pop_order(self):
        self.__pop_orders = []

    def left_cards(self):
        cards = []
        for index in range(self.__cursor, len(self.__cards)):
            cards.append(self.__cards[index])
        return cards

    def check_and_move_card(self, check_card):
        flag = False
        curr_index = -1
        for index in range(self.__cursor, len(self.__cards)):
            if self.__cards[index] == check_card:
                curr_index = index
                flag = True
                break
        if flag:
            self.__cards[curr_index], self.__cards[-1] = self.__cards[-1], self.__cards[curr_index]
        return flag

    def __shuffle_by_order(self, count=3):
        all_cards = deepcopy(self.__cards)
        random.shuffle(all_cards)
        order_cards = []
        tail_cards = []

        for i in range(count):
            card_list = self.__pop_orders[i] or []
            for c in card_list:
                if c in all_cards:
                    all_cards.remove(c)

        for c in self.__pop_orders[count] or []:
            tail_cards.append(c)
            if c in all_cards:
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

    def get_last_card(self):
        return self.__cards[-1]

    def pop_last_card(self):
        if self.__cursor >= len(self.__cards):
            return 0
        self.__cards[self.__cursor], self.__cards[-1] = self.__cards[-1], self.__cards[self.__cursor]
        card = self.__cards[self.__cursor]
        self.__cursor += 1
        return card

    @property
    def left_count(self):  # 剩余张数
        return max(len(self.__cards) - self.__cursor, 0)
