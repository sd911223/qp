# coding:utf-8
import random
from base import const
from models import logs_model, floor_model, club_model, union_model, database
from models import players_model
from utils import earth_position
from utils import utils


class BasePlayer(object):
    def __init__(self, uid):
        self.__tid = 0
        self.__relation_tid_set = set()
        self.__uid = int(uid) or 0

        self.__seat_id = -1
        self.__is_quit = False
        self.__is_ready = False
        self.__session = None
        self.__diamond = 0
        self.__yuan_bao = 0
        self.__status = 0
        self.__offline = False
        self.__nick_name = ""
        self.__static_data = ""
        self.__sex = 0
        self.__avatar = ""
        self.__is_lucker = False
        self.__fake_ip = False
        self.__random_ip = None

        self.__x = earth_position.X_NA  # 玩家经度
        self.__y = earth_position.Y_NA  # 玩家纬度

        self.__load_details()

    def __load_details(self):
        """ 加载玩家的游戏数据 """
        info = players_model.get(self.__uid)
        if not info:
            return False

        self.__diamond = int(info.diamond)
        self.__yuan_bao = int(info.yuan_bao)
        self.__nick_name = info.nick_name or info.model
        self.__avatar = info.avatar
        self.__sex = int(info.sex)
        return True

    @property
    def yuan_bao(self):
        return self.__yuan_bao

    @property
    def sex(self):
        return self.__sex

    def add_relation_tid(self, tid: int):
        self.__relation_tid_set.add(tid)

    def remove_relation_tid(self, tid: int):
        try:
            self.__relation_tid_set.remove(tid)
        except Exception as data:
            print(data)

    def can_del(self):
        if len(self.__relation_tid_set) != 0:
            return False

        if self.__tid > 0:
            return False

        return True

    @property
    def tid(self):  # 获得玩家当前所处的桌子ID
        return self.__tid

    @tid.setter
    def tid(self, tid):
        # 设置玩家的桌子ID
        self.__tid = tid

    @property
    def club_info(self):
        data = {
            "uid": self.__uid,
            "nickName": self.__nick_name,
            "remark": "",
            "avatar": self.__avatar,
            "seatID": self.__seat_id,
        }
        return data

    def match_data(self, club_id, match_type):
        if club_id == -1 or match_type == 0:
            match_score = 0
        else:
            data = club_model.get_player_money_by_club_id(club_id, self.uid)
            if data and 'score' in data:
                match_score = data['score'] + data['lock_score']
            else:
                match_score = 0
        return {
            "seatID": self.seat_id,
            "matchScore": match_score
        }

    def union_energy_data(self, union_id):
        if union_id == -1:
            energy = 0
        else:
            data = union_model.get_my_union_info(database.share_db(), union_id, self.uid)
            energy = data['energy']

        return {
            "seatID": self.seat_id,
            "energy": energy
        }

    @property
    def seat_id(self):  # 获得玩家当前的坐位ID
        return self.__seat_id

    @seat_id.setter
    def seat_id(self, seat_id):
        # 设置玩家的坐位ID
        self.__seat_id = seat_id

    @property
    def static_data(self):
        return self.__static_data

    @static_data.setter
    def static_data(self, data):
        self.__static_data = data

    @property
    def status(self):
        return self.__status

    @status.setter
    def status(self, status):
        self.__status = status

    @property
    def offline(self):
        """ 玩家离线标志 """
        return self.__offline

    @offline.setter
    def offline(self, flag):
        self.__offline = flag

    @property
    def session(self):
        return self.__session

    @session.setter
    def session(self, session):
        self.__session = session

    # @property
    # def ip(self):
    #     if not self.__session:
    #         return ''
    #     return self.__session.ip

    @property
    def ip(self):
        if not self.__session:
            return ''
        elif self.__fake_ip:
            return self.__random_ip
        else:
            return self.__session.ip

    def fake_ip(self, is_fake = True):
        if self.__random_ip == None:
            ipsec = str(random.randint(22, 37))
            ipsec2 = str(random.randint(81, 255))
            self.__random_ip = "118.239." + ipsec + '.' + ipsec2

        self.__fake_ip = is_fake

    @property
    def uid(self):
        return self.__uid

    @property
    def nick_name(self):
        return self.__nick_name

    @property
    def avatar(self):
        return self.__avatar

    @property
    def is_ready(self):
        return self.__is_ready

    @is_ready.setter
    def is_ready(self, flag):
        self.__is_ready = (flag is True)

    @property
    def position(self):
        return self.__x, self.__y

    def set_position(self, x, y):
        if x is None or y is None:
            return
        self.__x = utils.check_float(x)
        self.__y = utils.check_float(y)

    def dec_yuan_bao(self, yuan_bao, club_id, record_id):
        players_model.dec_yuan_bao(self.__uid, yuan_bao)
        players_model.write_consume_logs(self.__uid, club_id, yuan_bao, const.PAY_YUAN_BAO,
                                         const.REASON_CREATE_ROOM_SUB, utils.timestamp(), 0, record_id)

    def dec_diamonds(self, num, club_id=-1, union_id=-1, record_id=0):
        """减去玩家钻石"""
        if not num or num <= 0:
            return False
        dec_yuan_bao = 0
        dec_diamond = num
        # 移除扣元宝逻辑
        # if self.__diamond < num:
        #     dec_diamond = self.__diamond
        #     dec_yuan_bao = num - self.__diamond
        #
        # if dec_yuan_bao > 0:
        #     self.dec_yuan_bao(dec_yuan_bao, club_id, record_id)

        if players_model.dec_diamonds(self.__uid, dec_diamond) > 0:
            self.__diamond -= dec_diamond
            players_model.write_consume_logs(self.__uid, club_id, union_id, dec_diamond, const.PAY_DIAMOND,
                                             const.REASON_CREATE_ROOM_SUB, utils.timestamp(), 0, record_id)
            # logs_model.add_diamonds_log(self.uid, num, const.REASON_CREATE_ROOM_SUB, 1, self.__diamond,
            #                             record_id=record_id)
            if club_id != -1:
                logs_model.add_club_diamonds_log(self.__uid, num, club_id, record_id, 0)

            if union_id != -1:
                logs_model.add_union_diamonds_log(self.__uid, num, union_id, record_id)

            return True
        return False

    def dec_la_jiao_dou(self, num, club_id=-1, record_id=0):
        """减去辣椒豆"""
        if not num or num <= 0:
            return False
        if players_model.dec_la_jiao_dou(self.__uid, num) > 0:
            logs_model.add_la_jiao_dou_log(self.uid, num, const.REASON_CREATE_ROOM_LA_JIAO_DOU_SUB, 1, 0,
                                           record_id=record_id)
            if club_id != -1:
                logs_model.add_club_diamonds_log(self.__uid, 0, club_id, record_id, num)
            return True
        return False

    def diamond(self):
        p = players_model.get_diamond_by_uid(self.__uid)
        if not p:
            utils.log("player:" + str(self.__uid) + " is None", 'diamond_exception.log')
            self.__diamond = 0
            return 0
        diamond = int(p['diamond'])
        self.__diamond = diamond
        self.__yuan_bao = int(p['yuan_bao'])
        return diamond

    def clear_session(self):
        """ 清理玩家的session但不触发断线的事件 """
        if self.__session:
            self.__session.clear()
            self.__session = None

    def return_score(self, club_id):
        floor_model.update_club_user_score_by_lock_score(self.uid, club_id)
