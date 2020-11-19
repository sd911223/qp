# coding:utf-8

import logging

from configs import const
from configs import error
from models import base_redis
from models import club_model
from models import game_room_model
from models import player_model
from models import room_config_model
from models import tables_model
from models.base_redis import share_connect as redis_conn
from utils import utils
from .base_handler import BaseHandler


class CheckRoomHandler(BaseHandler):
    def prepare(self):
        if not self.check_fixed_params(True):
            return self.write_json(error.DATA_BROKEN)
        if not self.check_sign():
            return self.write_json(error.SIGN_FAIL)

    def get(self):
        return self._request()

    def post(self):
        return self._request()

    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode(self.get_string('params'))
        if not params or not params.get('roomID'):
            return self.write_json(error.DATA_BROKEN)

        info = tables_model.get_table_id(self.share_db(), params['roomID'])
        if info:
            return self.write_json(error.OK, info)
        return self.write_json(error.ROOM_NOT_EXIST)


class OpenRoomInfoHandler(BaseHandler):
    def prepare(self):
        if not self.check_fixed_params(True):
            return self.write_json(error.DATA_BROKEN)
        if not self.check_sign():
            return self.write_json(error.SIGN_FAIL)

    def get(self):
        return self._request()

    def post(self):
        return self._request()

    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode(self.get_string('params'))
        if not params or not params.get('gameID'):
            return self.write_json(error.DATA_BROKEN)

        info = room_config_model.get_room_config(self.share_db(), params.get('gameID'))
        if info:
            return self.write_json(error.OK, info)
        return self.write_json(error.DATA_BROKEN)


class CreateRoomHandler(BaseHandler):
    def prepare(self):
        if not self.check_fixed_params(True):
            return self.write_json(error.DATA_BROKEN)
        if not self.check_sign():
            return self.write_json(error.SIGN_FAIL)

    def get(self):
        return self._request()

    def post(self):
        return self._request()

    def __calc_diamonds(self, round_count: int, game_type):
        data = room_config_model.get_room_config(self.share_db(), game_type)
        diamonds = utils.json_decode(data['data'])
        for i in diamonds["diamondInfo"]:
            if i['count'] == round_count:
                return i['diamond']
        return -1

    def __calc_diamonds_with_player_count(self, round_count: int, game_type: int, player_count: int):
        data = room_config_model.get_room_config(self.share_db(), game_type)
        diamonds = utils.json_decode(data['data'])
        for i in diamonds["diamondInfo"]:
            if i['count'] == round_count and i['playerCount'] == player_count:
                return i['diamond']
        return -1

    @staticmethod
    def __make_game_rules(rule_details):
        return dict({
            "openChui": utils.check_int(rule_details.get("openChui")) or 0,
            "suit510k": utils.check_int(rule_details.get("suit510k")) or 0,
            "peiDou": utils.check_int(rule_details.get("peiDou")) or 0,
            "baoZhang": utils.check_int(rule_details.get("baoZhang")) or 0,
            "fanTiLimit": utils.check_int(rule_details.get("fanTiLimit")) or 0,
        })

    @staticmethod
    def __make_bo_pi_rules(rule_details):
        limit_score = utils.check_int(rule_details.get("limitScore")) or 0
        base_tun = utils.check_int(rule_details.get("baseTun")) or 1
        total_seat = utils.check_int(rule_details.get("totalSeat")) or 0
        qu_pai = utils.check_int(rule_details.get("quPai")) or 0
        lian_zhuang = utils.check_int(rule_details.get("lianZhuang")) or 0
        fan_bei = utils.check_int(rule_details.get("fanBei")) or 0
        tian_di_hu = utils.check_int(rule_details.get("tianDiHu")) or 1
        chong_cao = utils.check_int(rule_details.get("chongCao")) or 0
        if total_seat not in (3, 2, 4):
            total_seat = 3
        if limit_score not in (0, 20, 40, 60, 100, 120, 150, 200):
            limit_score = 0
        if base_tun not in (1, 3, 5):
            base_tun = 1
        if qu_pai not in(0, 1, 2):
            qu_pai = 0
        if lian_zhuang not in(0, 1):
            lian_zhuang = 0
        if fan_bei not in(0, 1):
            fan_bei = 0
        if tian_di_hu not in(1, 2, 3):
            tian_di_hu = 1
        if chong_cao not in(0, 1):
            chong_cao = 0
        return dict({
            "totalSeat": total_seat,
            "limitScore": limit_score,
            "baseTun": base_tun,
            "lianZhuang": lian_zhuang, #连庄 0 不连庄 1 连庄
            "fanBei": fan_bei, #翻倍 0 不翻倍 1 翻倍
            "tianDiHu": tian_di_hu, #天地胡 1 十胡 2 翻倍 3 切牌
            "quPai": qu_pai, #去牌 0 不去牌 1 去十张 2 去二十张
            "chongCao": chong_cao, #冲槽 0/1
        })

    @staticmethod
    def __make_xt_pao_hu_rules(rule_details):
        red_count = utils.check_int(rule_details.get("redCount"))
        wei_type = utils.check_int(rule_details.get("weiType"))
        if red_count not in (10, 12):
            red_count = 12
        if wei_type not in (1, 2):
            wei_type = 1
        return dict({
            "ziMo": utils.check_int(rule_details.get("ziMo")) or 0,
            "hongHeiHu": utils.check_int(rule_details.get("hongHeiHu")) or 0,
            "huFanBei": utils.check_int(rule_details.get("huFanBei")) or 0,
            "weiType": wei_type,
            "yiWuShi": utils.check_int(rule_details.get("yiWuShi")) or 0,
            "zhangXi": utils.check_int(rule_details.get("zhangXi")) or 0,
            "pengPaiHu": utils.check_int(rule_details.get("pengPaiHu")) or 0,
            "yiDianHong": utils.check_int(rule_details.get("yiDianHong")) or 0,
            "daXiaoZi": utils.check_int(rule_details.get("daXiaoZi")) or 0,
            "sanAn": utils.check_int(rule_details.get("sanAn")) or 0,
            "redCount": red_count
        })

    @staticmethod
    def __make_huai_hua_quan_ming_tang_rules(rule_details):
        limit_score = utils.check_int(rule_details.get("limitScore")) or 0
        base_tun = utils.check_int(rule_details.get("baseTun")) or 1
        if limit_score not in (0, 20, 40, 60, 100, 120, 150, 200):
            limit_score = 0
        if base_tun not in (1, 2, 3, 4, 5):
            base_tun = 1
        total_seat = utils.check_int(rule_details.get("totalSeat")) or 0
        if total_seat not in (2, 3):
            total_seat = 3
        qu_pai = utils.check_int(rule_details.get("quPai"))
        if qu_pai not in (0, 1):
            qu_pai = 1
        return dict({
            "limitScore": limit_score,
            "baseTun": base_tun,
            "quPai": qu_pai,
            "santi5kan": utils.check_int(rule_details.get("santi5kan")) or 0,
            "shuaHou": utils.check_int(rule_details.get("shuaHou")) or 0,
            "huangFan": utils.check_int(rule_details.get("huangFan")) or 0,
            "hangHangXi": utils.check_int(rule_details.get("hangHangXi")) or 0,
            "jiaHangHang": utils.check_int(rule_details.get("jiaHangHang")) or 0,
            "siQiHong": utils.check_int(rule_details.get("siQiHong")) or 0,
            "daTuanYuan": utils.check_int(rule_details.get("daTuanYuan")) or 0,
            "tingHu": utils.check_int(rule_details.get("tingHu")) or 0,
            "duiDuiHu": utils.check_int(rule_details.get("duiZiHu")) or 0,
            "totalSeat": total_seat,
            "twoPlayerBaseXi": utils.check_int(rule_details.get("twoPlayerBaseXi")) or 0,
            "qiShouTi": utils.check_int(rule_details.get("qiShouTi")) or 0,
        })

    @staticmethod
    def __make_pao_hu_rules(rule_details):
        limit_score = utils.check_int(rule_details.get("limitScore")) or 0
        base_tun = utils.check_int(rule_details.get("baseTun")) or 1
        if limit_score not in (0, 20, 40, 60, 100, 120, 150, 200):
            limit_score = 0
        if base_tun not in (1, 2, 3, 4, 5):
            base_tun = 1
        total_seat = utils.check_int(rule_details.get("totalSeat")) or 0
        if total_seat not in (2, 3):
            total_seat = 3
        qu_pai = utils.check_int(rule_details.get("quPai"))
        if qu_pai not in (0, 1):
            qu_pai = 1
        return dict({
            "limitScore": limit_score,
            "baseTun": base_tun,
            "quPai": qu_pai,
            "santi5kan": utils.check_int(rule_details.get("santi5kan")) or 0,
            "shuaHou": utils.check_int(rule_details.get("shuaHou")) or 0,
            "huangFan": utils.check_int(rule_details.get("huangFan")) or 0,
            "hangHangXi": utils.check_int(rule_details.get("hangHangXi")) or 0,
            "jiaHangHang": utils.check_int(rule_details.get("jiaHangHang")) or 0,
            "siQiHong": utils.check_int(rule_details.get("siQiHong")) or 0,
            "daTuanYuan": utils.check_int(rule_details.get("daTuanYuan")) or 0,
            "tingHu": utils.check_int(rule_details.get("tingHu")) or 0,
            "duiDuiHu": utils.check_int(rule_details.get("duiZiHu")) or 0,
            "totalSeat": total_seat,
            "twoPlayerBaseXi": utils.check_int(rule_details.get("twoPlayerBaseXi")) or 0,
            "qiShouTi": utils.check_int(rule_details.get("qiShouTi")) or 0,
        })

    @staticmethod
    def __make_han_shou_pao_hu_rules(rule_details):
        limit_score = utils.check_int(rule_details.get("limitScore")) or 0
        base_tun = utils.check_int(rule_details.get("baseTun")) or 1
        if limit_score not in (0, 20, 40, 60, 100, 120, 150, 200):
            limit_score = 0
        if base_tun not in (1, 2, 3, 4, 5):
            base_tun = 1
        total_seat = utils.check_int(rule_details.get("totalSeat")) or 0
        if total_seat not in (2, 3):
            total_seat = 3
        qu_pai = utils.check_int(rule_details.get("quPai"))
        if qu_pai not in (0, 1):
            qu_pai = 1


        return dict({
            "limitScore": limit_score,
            "baseTun": base_tun,
            "quPai": qu_pai,
            "daoShu":utils.check_int(rule_details.get("daoShu")) or 0,
            "santi5kan": utils.check_int(rule_details.get("santi5kan")) or 0,
            "shuaHou": utils.check_int(rule_details.get("shuaHou")) or 0,
            "huangFan": utils.check_int(rule_details.get("huangFan")) or 0,
            "hangHangXi": utils.check_int(rule_details.get("hangHangXi")) or 0,
            "jiaHangHang": utils.check_int(rule_details.get("jiaHangHang")) or 0,
            "siQiHong": utils.check_int(rule_details.get("siQiHong")) or 0,
            "daTuanYuan": utils.check_int(rule_details.get("daTuanYuan")) or 0,
            "tingHu": utils.check_int(rule_details.get("tingHu")) or 0,
            "duiDuiHu": utils.check_int(rule_details.get("duiZiHu")) or 0,
            "totalSeat": total_seat,
            "twoPlayerBaseXi": utils.check_int(rule_details.get("twoPlayerBaseXi")) or 0,
            "qiShouTi": utils.check_int(rule_details.get("qiShouTi")) or 0,
        })

    @staticmethod
    def __make_yzchz_rules(rule_details):
        limit_score = utils.check_int(rule_details.get("limitScore")) or 0
        base_tun = utils.check_int(rule_details.get("baseTun")) or 1
        if limit_score not in (0, 20, 40, 60, 100, 120, 150, 200):
            limit_score = 0
        if base_tun not in (1, 2, 3, 4, 5):
            base_tun = 1
        total_seat = utils.check_int(rule_details.get("totalSeat")) or 0
        if total_seat not in (2, 3, 4):
            total_seat = 3
        qu_pai = utils.check_int(rule_details.get("quPai"))
        if qu_pai not in (0, 1):
            qu_pai = 1
        return dict({
            "limitScore": limit_score,
            "baseTun": base_tun,
            "quPai": qu_pai,
            "huangFan": utils.check_int(rule_details.get("huangFan")) or 0,
            "tingHu": utils.check_int(rule_details.get("tingHu")) or 0,
            "duiDuiHu": utils.check_int(rule_details.get("duiZiHu")) or 0,
            "wangCount": utils.check_int(rule_details.get("wangCount")) or 0,
            "xingType": utils.check_int(rule_details.get("xingType")) or 1,
            "huType": utils.check_int(rule_details.get("huType")) or 0,
            "shuangXing": utils.check_int(rule_details.get("shuangXing")) or 0,
            "redBlack": utils.check_int(rule_details.get("redBlack")) or 0,
            "totalSeat": total_seat,
            "minHuXi": utils.check_int(rule_details.get("minHuXi")) or 15,
            "xiTunCalc": utils.check_int(rule_details.get("xiTunCalc")) or 3,
            "wuWangBiHu": utils.check_int(rule_details.get("wuWangBiHu")) or 0,
        })

    @staticmethod
    def __make_czphz_rules(rule_details):
        limit_score = utils.check_int(rule_details.get("limitScore")) or 0
        base_tun = utils.check_int(rule_details.get("baseTun")) or 1
        if limit_score not in (0, 20, 40, 60, 100, 120, 150, 200):
            limit_score = 0
        if base_tun not in (1, 2, 3, 4, 5):
            base_tun = 1
        total_seat = utils.check_int(rule_details.get("totalSeat")) or 0
        if total_seat not in (2, 3, 4):
            total_seat = 3
        qu_pai = utils.check_int(rule_details.get("quPai"))
        if qu_pai not in (0, 1):
            qu_pai = 1
        return dict({
            "limitScore": limit_score,
            "baseTun": base_tun,
            "quPai": qu_pai,
            "wangCount": utils.check_int(rule_details.get("wangCount")) or 0,
            "huType": utils.check_int(rule_details.get("huType")) or 0,
            "redBlack": utils.check_int(rule_details.get("redBlack")) or 0,
            "minHuXi": utils.check_int(rule_details.get("minHuXi")) or 3,
            "xiTun": utils.check_int(rule_details.get("xiTun")) or 1,
            "maoHu": utils.check_int(rule_details.get("maoHu")) or 0,
            "ziMoDouble": utils.check_int(rule_details.get("ziMoDouble")) or 0,
            "piaoType": utils.check_int(rule_details.get("piaoType")) or 0,
            "dealCardType": utils.check_int(rule_details.get("dealCardType")) or 0,
            "totalSeat": total_seat,
            "haveWangHuType": utils.check_int(rule_details.get("haveWangHuType")) or 1,
        })

    @staticmethod
    def __make_er_ba_gang_rules(rule_details):
        player_count = utils.check_int(rule_details.get("totalSeat")) or 2
        if player_count not in (2, 3, 4, 5, 6, 7, 8, 9, 10):
            player_count = 2
        zhuang_type = utils.check_int(rule_details.get("zhuangType")) or 1
        # 1 自由抢庄，2 九点上庄，3 固定
        if zhuang_type not in (1, 2, 3):
            zhuang_type = 1
        score = utils.check_int(rule_details.get("score")) or 1
        if score not in (1, 2, 3, 4, 5):
            score = 1
        max_qiang = utils.check_int(rule_details.get("maxQiang")) or 4
        if max_qiang not in (1, 2, 3, 4):
            max_qiang = 1
        tui_zhu = utils.check_int(rule_details.get("tuiZhu")) or 0
        if tui_zhu not in (0, 1, 2, 3):
            tui_zhu = 0
        return dict({
            "totalSeat": player_count,
            "zhuangType": zhuang_type,
            "specType": utils.check_list(rule_details.get("specType")) or [-1],
            "score": score,
            "tuiZhu": tui_zhu,
            "maxQiang": max_qiang,
            "fanBeiType": utils.check_int(rule_details.get("fanBeiType")) or 1,
            "prohibitFanCard": utils.check_int(rule_details.get("prohibitFanCard")) or 0,
            "prohibitEnter": utils.check_int(rule_details.get("prohibitEnter")) or 0,
            "prohibitLook": utils.check_int(rule_details.get("prohibitLook")) or 0,
        })

    @staticmethod
    def __make_san_da_ha_rules(rule_details):
        xiao_guang = utils.check_int(rule_details.get("xiaoGuang"))
        chu_6 = utils.check_int(rule_details.get("chu6"))
        qi_jiao_60 = utils.check_int(rule_details.get("qiJiao60"))
        bao_fu = utils.check_int(rule_details.get("baoFu"))
        player_count = utils.check_int(rule_details.get("playerCount")) or 3
        shuang_jin = utils.check_int(rule_details.get("shuangJin"))
        bi_chang_zhu = utils.check_int(rule_details.get("biChangZhu"))
        if player_count not in (3, 4):
            player_count = 3
        if xiao_guang not in (25, 30):
            xiao_guang = 25
        if chu_6 not in (0, 1):
            chu_6 = 0
        if qi_jiao_60 not in (0, 1):
            qi_jiao_60 = 0
        if bao_fu not in (0, 1):
            bao_fu = 0
        if shuang_jin not in (0, 1):
            shuang_jin = 0
        if bi_chang_zhu not in (0, 1):
            bi_chang_zhu = 0
        return dict({
            "xiaoGuang": xiao_guang,
            "chu6": chu_6,
            "qiJiao60": qi_jiao_60,
            "playerCount": player_count,
            "baoFu": bao_fu,
            "shuangJin": shuang_jin,
            "biChangZhu": bi_chang_zhu
        })

    @staticmethod
    def __make_tianzha_rules(rule_details):
        return dict({
            "openChui": utils.check_int(rule_details.get("openChui")) or 0,
            "suit510k": utils.check_int(rule_details.get("suit510k")) or 0,
            "peiDou": utils.check_int(rule_details.get("peiDou")) or 0,
            "baoZhang": utils.check_int(rule_details.get("baoZhang")) or 0,
            "fanTiLimit": utils.check_int(rule_details.get("fanTiLimit")) or 0,
        })

    @staticmethod
    def __make_ma_jiang_rules(rule_details):
        bird_count = utils.check_int(rule_details.get("birdCount")) or 0
        if bird_count not in (0, 1, 2, 4, 6):
            bird_count = 0
        total_seat = utils.check_int(rule_details.get("totalSeat")) or 4
        if total_seat not in (2, 3, 4):
            total_seat = 4
        zhuang_type = utils.check_int(rule_details.get("zhuangType")) or 0
        if zhuang_type not in (0, 1):
            zhuang_type = 0
        return dict({
            "huType": utils.check_int(rule_details.get("huType")) or 0,  # 胡牌类型
            "paiType": utils.check_int(rule_details.get("paiType")) or 0,
            "limitScore": utils.check_int(rule_details.get("limitScore")) or 0,  # 单局得分上限
            "qiangZhiHu": utils.check_int(rule_details.get("qiangZhiHu")) or 0,  # 强制胡
            "yiMaQuanZhong": utils.check_int(rule_details.get("yiMaQuanZhong")) or 0,  # 一码全中
            "birdCount": bird_count,  # 抓几鸟
            "isSevenPairs": utils.check_int(rule_details.get("isSevenPairs")) or 0,  # 可胡七对
            "isHongZhong": utils.check_int(rule_details.get("isHongZhong")) or 0,  # 是否带红中
            "zhuangXian": utils.check_int(rule_details.get("zhuangXian")) or 0,  # 庄闲是否算分
            "birdScore": utils.check_int(rule_details.get("birdScore")) or 0,  # 鸟分?
            "fixedBird": utils.check_int(rule_details.get("fixedBird")) or 0,  # 固定鸟数
            "canQiangGangHu": utils.check_int(rule_details.get("canQiangGangHu")) or 0,  # 抢杠胡
            "piaoScore": utils.check_int(rule_details.get("piaoScore")) or 0,  # 飘几分
            "birdType": utils.check_int(rule_details.get("birdType")) or 0,  # 鸟类型
            "fengPai": utils.check_int(rule_details.get("fengPai")) or 0,  # 鸟类型
            "fullPai": utils.check_int(rule_details.get("fullPai")) or 0,
            "totalSeat": total_seat,
            "zhuangType": zhuang_type,
            "queYiMen": utils.check_int(rule_details.get("queYiMen", 0)),  # 缺一门(条子)
            "siFangNiao": utils.check_int(rule_details.get("siFangNiao", 0)),  # 二人模式四方算鸟
        })

    @staticmethod
    def __make_feng_huang_hong_zhong_rules(rule_details):
        total_seat = utils.check_int(rule_details.get("totalSeat")) or 4
        if total_seat not in (2, 3, 4):
            total_seat = 4
        auto_ready = utils.check_int(rule_details.get("autoReady")) or 0
        return dict({
            "huType": utils.check_int(rule_details.get("huType")) or 0,  # 胡牌类型
            "limitScore": utils.check_int(rule_details.get("limitScore")) or 0,  # 单局得分上限
            "piaoScore": utils.check_int(rule_details.get("piaoScore")) or 0,  # 飘几分
            "fengPai": 0,
            "totalSeat": total_seat,
            "autoReady": auto_ready,
            "biHu": 0,
            "fullPai": utils.check_int(rule_details.get("fullPai")) or 0,
            "pengPengHu": 0,
            "genZhuang": 0,
            "huangZhuang": 0,
            "yiPaoSanXiang": 0,
            "tuiGangFen": 0,
            "wanFa": utils.check_list(rule_details.get("wanFa")) or [-1],
        })

    @staticmethod
    def __make_feng_huang_hua_shui_rules(rule_details):
        total_seat = utils.check_int(rule_details.get("totalSeat")) or 4
        if total_seat not in (2, 3, 4):
            total_seat = 4
        auto_ready = utils.check_int(rule_details.get("autoReady")) or 0
        return dict({
            "huType": utils.check_int(rule_details.get("huType")) or 0,  # 胡牌类型
            "paiType": utils.check_int(rule_details.get("paiType")) or 0,
            "limitScore": utils.check_int(rule_details.get("limitScore")) or 0,  # 单局得分上限
            "piaoScore": utils.check_int(rule_details.get("piaoScore")) or 0,  # 飘几分
            "fengPai": utils.check_int(rule_details.get("fengPai")) or 0,  # 风牌
            "totalSeat": total_seat,
            "autoReady": auto_ready,
            "biHu": utils.check_int(rule_details.get("biHu")) or 0,  # 逢胡必胡
            "fullPai": utils.check_int(rule_details.get("fullPai")) or 0,
            "pengPengHu": utils.check_int(rule_details.get("pengPengHu")) or 0,  # 碰碰胡
            "genZhuang": utils.check_int(rule_details.get("genZhuang")) or 0,  # 跟庄
            "huangZhuang": utils.check_int(rule_details.get("huangZhuang")) or 0,  # 黄庄
            "yiPaoSanXiang": utils.check_int(rule_details.get("yiPaoSanXiang")) or 0,  # 一炮三响
            "tuiGangFen": utils.check_int(rule_details.get("tuiGangFen")) or 0,  # 黄庄退杠分
        })

    @staticmethod
    def __make_hz_ma_jiang_rules(rule_details):
        bird_count = utils.check_int(rule_details.get("birdCount")) or 0
        if bird_count not in (0, 1, 2, 4, 6):
            bird_count = 0
        total_seat = utils.check_int(rule_details.get("totalSeat")) or 4
        if total_seat not in (2, 3, 4):
            total_seat = 4
        zhuang_type = utils.check_int(rule_details.get("zhuangType")) or 0
        if zhuang_type not in (0, 1):
            zhuang_type = 0
        return dict({
            "huType": utils.check_int(rule_details.get("huType")) or 0,  # 胡牌类型
            "paiType": utils.check_int(rule_details.get("paiType")) or 0,
            "limitScore": utils.check_int(rule_details.get("limitScore")) or 0,  # 单局得分上限
            "qiangZhiHu": utils.check_int(rule_details.get("qiangZhiHu")) or 0,  # 强制胡
            "yiMaQuanZhong": utils.check_int(rule_details.get("yiMaQuanZhong")) or 0,  # 一码全中
            "birdCount": bird_count,  # 抓几鸟
            "isSevenPairs": utils.check_int(rule_details.get("isSevenPairs")) or 0,  # 可胡七对
            "isHongZhong": utils.check_int(rule_details.get("isHongZhong")) or 0,  # 是否带红中
            "zhuangXian": utils.check_int(rule_details.get("zhuangXian")) or 0,  # 庄闲是否算分
            "birdScore": utils.check_int(rule_details.get("birdScore")) or 0,  # 鸟分?
            "fixedBird": utils.check_int(rule_details.get("fixedBird")) or 0,  # 固定鸟数
            "canQiangGangHu": utils.check_int(rule_details.get("canQiangGangHu")) or 0,  # 抢杠胡
            "piaoScore": utils.check_int(rule_details.get("piaoScore")) or 0,  # 飘几分
            "birdType": utils.check_int(rule_details.get("birdType")) or 0,  # 鸟类型
            "fengPai": utils.check_int(rule_details.get("fengPai")) or 0,  # 鸟类型
            "totalSeat": total_seat,
            "zhuangType": zhuang_type,
            "addBirdsCount": utils.check_int(rule_details.get("addBirdsCount")) or 0,
            "fullPai": utils.check_int(rule_details.get("fullPai")) or 0,
            "wanFa": utils.check_list(rule_details.get("wanFa")) or [-1],
            "queYiMen": utils.check_int(rule_details.get("queYiMen", 0)),  # 缺一门(条子)
            "siFangNiao": utils.check_int(rule_details.get("siFangNiao", 0)),  # 二人模式四方算鸟
        })

    @staticmethod
    def __make_cs_ma_jiang_rules(rule_details):
        bird_count = utils.check_int(rule_details.get("birdCount")) or 0
        if bird_count not in (0, 1, 2, 4, 6):
            bird_count = 0

        after_gang_cards_count = utils.check_int(rule_details.get("afterGangCardsCount")) or 0
        if after_gang_cards_count not in (0, 1, 2, 4):
            after_gang_cards_count = 0

        zhuang_type = utils.check_int(rule_details.get("zhuangType")) or 0
        if zhuang_type not in (0, 1):
            zhuang_type = 0

        bird_score_type = utils.check_int(rule_details.get("birdScoreType")) or 0
        if bird_score_type not in (0, 1, 2):
            bird_score_type = 0

        lock_cards_type = utils.check_int(rule_details.get("lockCardsType")) or 0
        if lock_cards_type not in (0, 1):
            lock_cards_type = 0

        total_seat = utils.check_int(rule_details.get("totalSeat")) or 0
        if total_seat not in (2, 3, 4):
            total_seat = 4

        return dict({
            "limitScore": utils.check_int(rule_details.get("limitScore")) or 0,  # 单局得分上限
            "birdCount": bird_count,  # 抓几鸟
            "beginHuList": utils.check_list(rule_details.get("beginHuList")) or [],  # 单局得分上限
            "middleHuList": utils.check_list(rule_details.get("middleHuList")) or [],  # 单局得分上限
            "haiDiType": utils.check_int(rule_details.get("haiDiType")) or 0,  # 单局得分上限
            "afterGangCardsCount": after_gang_cards_count,  # 单局得分上限
            "zhuangType": zhuang_type,  # 单局得分上限
            "birdScoreType": bird_score_type,
            "lockCardsType": lock_cards_type,
            "totalSeat": total_seat,
            "piao_type": utils.check_int(rule_details.get("piao_type")) or 0,  # 长沙麻将飘分类型 0 不飘 1 首局飘 2 每局飘
            "fullPai": utils.check_int(rule_details.get("fullPai")) or 0,
            "birdType": utils.check_int(rule_details.get("birdType", 1)),  # 鸟类型
            "queYiMen": utils.check_int(rule_details.get("queYiMen", 0)),  # 缺一门(条子)
            "beginHuBird": utils.check_int(rule_details.get("beginHuBird", 1)),  # 起手胡是否抓鸟
            "menQianQing": utils.check_int(rule_details.get("menQianQing", 0)),  # 门清选项
        })

    @staticmethod
    def __make_heng_yang_mo_mo_rules(rule_details):
        bird_count = utils.check_int(rule_details.get("birdCount")) or 1
        if bird_count not in (1, 2, 3):
            bird_count = 1

        bird_score_type = utils.check_int(rule_details.get("birdScoreType")) or 0
        if bird_score_type not in (0, 1, 2):
            bird_score_type = 0

        total_seat = utils.check_int(rule_details.get("totalSeat")) or 0
        if total_seat not in (2, 3, 4):
            total_seat = 4

        dou_qi_type = utils.check_int(rule_details.get("douQiType")) or 0
        if dou_qi_type not in (0, 1):
            dou_qi_type = 0

        dice_count = utils.check_int(rule_details.get("diceCount")) or 0
        qiang_zhi_hu_pai = utils.check_int(rule_details.get("qiangZhiHuPai")) or 0

        if qiang_zhi_hu_pai not in (0, 1,):
            qiang_zhi_hu_pai = 0

        bao_pei = utils.check_int(rule_details.get("baoPei")) or 0
        if bao_pei not in (0, 1,):
            bao_pei = 0

        ban_ban_hu_round_over = utils.check_int(rule_details.get("banBanHuRoundOver")) or 0
        if ban_ban_hu_round_over not in (0, 1,):
            ban_ban_hu_round_over = 0

        hu_count = utils.check_int(rule_details.get('huCount')) or 0
        if hu_count not in (0, 1,):
            hu_count = 0

        return dict({
            "limitScore": utils.check_int(rule_details.get("limitScore")) or 0,  # 单局得分上限
            "birdCount": bird_count,  # 抓几鸟 1 \ 2 \ 3
            "diceCount": dice_count,  # 摇色子 1 \ 2
            "huCount": hu_count,  # 摇色子后胡牌次数 1 \ 2
            "qiangZhiHuPai": qiang_zhi_hu_pai,  # 是否强制胡牌
            "baoPei": bao_pei,  # 是否包赔
            "douQiType": dou_qi_type,  # 跟庄模式 0 无限跟庄 1 有限跟庄
            "beginHuList": utils.check_list(rule_details.get("beginHuList")) or [],  # 起手胡牌类型
            "middleHuList": utils.check_list(rule_details.get("middleHuList")) or [],  # 中途胡牌类型
            "haiDiType": utils.check_int(rule_details.get("haiDiType")) or 0,  # 海底类型
            "birdScoreType": bird_score_type,
            "totalSeat": total_seat,
            "fullPai": utils.check_int(rule_details.get("fullPai")) or 0,
            "banBanHuRoundOver": ban_ban_hu_round_over,  # 板板胡立即结束 0 不立即结束 1 立即结束
        })

    @staticmethod
    def __make_niu_gui_rules(rule_details):
        score_type = utils.check_int(rule_details.get("baseScore"))
        if score_type not in (0, 1, 2):
            score_type = 1
        return dict({
            "scoreType": score_type,
        })

    @staticmethod
    def __make_pao_de_kuai_rules(rule_details):
        player_count = utils.check_int(rule_details.get("playerCount")) or 3
        if player_count not in (2, 3):
            player_count = 3
        card_count = utils.check_int(rule_details.get("cardCount")) or 16
        if card_count not in (15, 16):
            card_count = 16
        score = utils.check_int(rule_details.get("score")) or 1
        if score not in (1, 5, 10):
            score = 1
        return dict({
            "cardCount": card_count,
            "score": score,
            "playerCount": player_count,  # 游戏人数
            "red10": utils.check_int(rule_details.get("red10")) or 0,  # 红桃10猴子
            "bombScore10": utils.check_int(rule_details.get("bombScore10")) or 1,  # 炸弹10分
            "fangQiangGuan": utils.check_int(rule_details.get("fangQiangGuan")) or 0,  # 防强关
            "tail3With1": utils.check_int(rule_details.get("tail3With1")) or 0,  # 最后三带一
            "threeABomb": utils.check_int(rule_details.get("threeABomb")) or 0,  # 三A算炸
            "denySplitBomb": utils.check_int(rule_details.get("denySplitBomb")) or 0,  # 不能拆分炸弹
            "baoShuang": utils.check_int(rule_details.get("baoShuang")) or 0,  # 可报双
            "xianPai": utils.check_int(rule_details.get("xianPai")) or 0,  # 显示牌张数
            "siDaiSan": utils.check_int(rule_details.get("siDaiSan")) or 0,  # 允许四带三
            "siDaiEr": utils.check_int(rule_details.get("siDaiEr")) or 0,  # 允许四带二
            "xian_chu_type": utils.check_int(rule_details.get("xian_chu_type")) or 0,  # 赢家\黑三先出
            "hander_xian_chu_type": utils.check_int(rule_details.get("hander_xian_chu_type")) or 0,  # 首局 比牌\黑三先出
            "bao_dan_type": utils.check_int(rule_details.get("bao_dan_type")) or 0,  # 报单顶\包赔
            "same_card_count": utils.check_int(rule_details.get("same_card_count")) or 0,  # 是否甩尾
            "fang_zuo_bi": utils.check_int(rule_details.get("fang_zuo_bi")) or 0,  # 防作弊
            "simple_fang_zuo_bi": utils.check_int(rule_details.get("simple_fang_zuo_bi")) or 0,  # 单局防作弊
        })

    @staticmethod
    def __make_zhuo_lao_ma_zi_rules(rule_details):
        player_count = utils.check_int(rule_details.get("playerCount")) or 3
        if player_count not in (2, 3):
            player_count = 3
        card_count = utils.check_int(rule_details.get("cardCount")) or 15
        if card_count not in (15, 16):
            card_count = 15
        score = utils.check_int(rule_details.get("score")) or 1
        if score not in (1, 5, 10):
            score = 1
        return dict({
            "cardCount": card_count,
            "score": score,
            "playerCount": player_count,  # 游戏人数
            "red10": utils.check_int(rule_details.get("red10")) or 0,  # 红桃10猴子
            "bombScore10": utils.check_int(rule_details.get("bombScore10")) or 1,  # 炸弹10分
            "fangQiangGuan": utils.check_int(rule_details.get("fangQiangGuan")) or 0,  # 防强关
            "tail3With1": utils.check_int(rule_details.get("tail3With1")) or 0,  # 最后三带一
            "threeABomb": utils.check_int(rule_details.get("threeABomb")) or 0,  # 三A算炸
            "denySplitBomb": utils.check_int(rule_details.get("denySplitBomb")) or 0,  # 不能拆分炸弹
            "baoShuang": utils.check_int(rule_details.get("baoShuang")) or 0,  # 可报双
            "xianPai": utils.check_int(rule_details.get("xianPai")) or 0,  # 显示牌张数
            "siDaiSan": utils.check_int(rule_details.get("siDaiSan")) or 0,  # 允许四带三
            "siDaiEr": utils.check_int(rule_details.get("siDaiEr")) or 0,  # 允许四带二
            "xian_chu_type": utils.check_int(rule_details.get("xian_chu_type")) or 0,  # 赢家\黑三先出
            "bao_dan_type": utils.check_int(rule_details.get("bao_dan_type")) or 0,  # 报单顶\包赔
            "same_card_count": utils.check_int(rule_details.get("same_card_count")) or 0,  # 是否甩尾
            "fang_zuo_bi": utils.check_int(rule_details.get("fang_zuo_bi")) or 0,  # 防作弊
            "simple_fang_zuo_bi": utils.check_int(rule_details.get("simple_fang_zuo_bi")) or 0,  # 单局防作弊
            "youZhaBiZha": utils.check_int(rule_details.get("youZhaBiZha")) or 0,  # 有炸必炸
            "sanADaiYi": utils.check_int(rule_details.get("sanADaiYi")) or 0,  # 三A带一
            "siDaiType": utils.check_int(rule_details.get("siDaiType")) or 0,  # 炸弹带牌与否
            "singleAttack2": utils.check_int(rule_details.get("singleAttack2")) or 0,  # 不可单出2
        })

    @staticmethod
    def __make_tui_dao_hu_rules(rule_details):
        bird_count = utils.check_int(rule_details.get("birdCount")) or 0
        if bird_count not in (0, 1, 2, 4, 6):
            bird_count = 0

        after_gang_cards_count = utils.check_int(rule_details.get("afterGangCardsCount")) or 0
        if after_gang_cards_count not in (0, 1, 2, 4):
            after_gang_cards_count = 0

        zhuang_type = utils.check_int(rule_details.get("zhuangType")) or 0
        if zhuang_type not in (0, 1):
            zhuang_type = 0

        bird_score_type = utils.check_int(rule_details.get("birdScoreType")) or 0
        if bird_score_type not in (0, 1, 2):
            bird_score_type = 0

        lock_cards_type = utils.check_int(rule_details.get("lockCardsType")) or 0
        if lock_cards_type not in (0, 1):
            lock_cards_type = 0

        total_seat = utils.check_int(rule_details.get("totalSeat")) or 0
        if total_seat not in (2, 3, 4):
            total_seat = 4

        return dict({
            "limitScore": utils.check_int(rule_details.get("limitScore")) or 0,  # 单局得分上限
            "birdCount": bird_count,  # 抓几鸟
            "beginHuList": utils.check_list(rule_details.get("beginHuList")) or [],  # 单局得分上限
            "middleHuList": utils.check_list(rule_details.get("middleHuList")) or [],  # 单局得分上限
            "haiDiType": utils.check_int(rule_details.get("haiDiType")) or 0,  # 单局得分上限
            "afterGangCardsCount": after_gang_cards_count,  # 单局得分上限
            "zhuangType": zhuang_type,  # 单局得分上限
            "birdScoreType": bird_score_type,
            "lockCardsType": lock_cards_type,
            "totalSeat": total_seat,
            "piao_type": utils.check_int(rule_details.get("piao_type")) or 0,  # 长沙麻将飘分类型 0 不飘 1 首局飘 2 每局飘
            "fullPai": utils.check_int(rule_details.get("fullPai")) or 0,
            "birdType": utils.check_int(rule_details.get("birdType", 1)),  # 鸟类型
            "menQianQing": utils.check_int(rule_details.get("menQianQing", 0)),  # 门前清
            "qiangGangHu": utils.check_int(rule_details.get("qiangGangHu", 0)),  # 抢杠胡
            "queYiMen": utils.check_int(rule_details.get("queYiMen", 0)),  # 缺一门(条子)
            "siFangNiao": utils.check_int(rule_details.get("siFangNiao", 0)),  # 二人模式四方算鸟
            "tuoGuanTime": utils.check_int(rule_details.get("tuoGuanTime", 0)),  # 托管时间 --->秒
            "fangZuoBiDistance": utils.check_int(rule_details.get("fangZuoBiDistance", 0)),  # 防作弊距离 -->米
            "autoReady": utils.check_int(rule_details.get("autoReady", 0)),  # 自动准备
            "jiangJiangHuZiMo": utils.check_int(rule_details.get("jiangJiangHuZiMo", 0)),
            "qingYiSeKeChi": utils.check_int(rule_details.get("qingYiSeKeChi", 0))
        })

    @staticmethod
    def __make_gui_hu_zi_rules(rule_details):
        limit_score = utils.check_int(rule_details.get("limitScore")) or 0
        base_tun = utils.check_int(rule_details.get("baseTun")) or 1
        if limit_score not in (0, 200, 400):
            limit_score = 0
        if base_tun not in (1, 3, 5):
            base_tun = 1
        return dict({
            "limitScore": limit_score,
            "baseTun": base_tun,
        })

    @staticmethod
    def __make_da_tong_zi_rules(rule_details):
        total_seat = utils.check_int(rule_details.get("totalSeat")) or 3
        card_count = utils.check_int(rule_details.get("cardCount")) or 3
        total_score = utils.check_int(rule_details.get("totalScore")) or 600
        over_bonus = utils.check_int(rule_details.get("overBonus")) or 0
        random_dealer = utils.check_int(rule_details.get("randomDealer")) or 0
        show_card = utils.check_int(rule_details.get('showCard')) or 0
        must_denny = utils.check_int(rule_details.get('mustDenny')) or 0
        tail_3_with_card = utils.check_int(rule_details.get('tail3WithCard')) or 0

        if must_denny not in (0, 1):
            must_denny = 1

        # 当前只有三副牌 三人模式
        if total_seat not in (2, 3):
            total_seat = 3

        if card_count not in (3, 4,):
            card_count = 3

        if total_score not in (600, 1000):
            total_score = 600

        if over_bonus not in (0, 100, 200, 300, 500):
            over_bonus = 0

        if show_card not in (0, 1):
            show_card = 0

        return dict({
            "totalSeat": total_seat,
            "tail3WithCard": tail_3_with_card,
            "totalScore": total_score,
            "cardCount": card_count,
            "overBonus": over_bonus,
            "randomDealer": random_dealer,
            "showCard": show_card,
            "mustDenny": must_denny,
        })

    @staticmethod
    def __make_you_xian_peng_hu_rules(rule_details):
        limit_score = utils.check_int(rule_details.get("limitScore")) or 0
        zhong_zhuang = utils.check_int(rule_details.get("zhongZhuang")) or 0
        base_tun = utils.check_int(rule_details.get("baseTun")) or 1
        if limit_score not in (0, 20, 40, 60, 100, 120, 150):
            limit_score = 0
        if zhong_zhuang not in (0, 1):
            zhong_zhuang = 0
        if base_tun not in (1, 3, 5):
            base_tun = 1
        return dict({
            "limitScore": limit_score,
            "zhongZhuang": zhong_zhuang,
            "baseTun": base_tun,
        })

    @staticmethod
    def __make_niu_niu_rules(rule_details):
        player_count = utils.check_int(rule_details.get("playerCount")) or 2
        if player_count not in (2, 3, 4, 5, 6, 7, 8, 9, 10):
            player_count = 2
        zhuang_type = utils.check_int(rule_details.get("zhuangType")) or 1
        # 1 固定庄，2 牛牛庄，3 顺序庄，4 明牌庄
        if zhuang_type not in (1, 2, 3, 4, 5):
            zhuang_type = 1
        score = utils.check_int(rule_details.get("score")) or 1
        if score not in (1, 2, 3, 4, 5):
            score = 1
        max_qiang = utils.check_int(rule_details.get("maxQiang")) or 4
        if max_qiang not in (1, 2, 3, 4):
            max_qiang = 1
        tui_zhu = utils.check_int(rule_details.get("tuiZhu")) or 0
        if tui_zhu not in (0, 5, 10, 15, 20):
            tui_zhu = 0
        detail_type = utils.check_int(rule_details.get("detailType")) or 1
        if detail_type not in (1, 2):
            detail_type = 1
        joker = utils.check_int(rule_details.get("joker")) or 0
        if joker not in (0, 1):
            joker = 0
        # 0 默认牛牛 1 冰城牛牛
        niu_type = utils.check_int(rule_details.get("niuType")) or 0
        if niu_type not in (0, 1, 2):
            niu_type = 0
        return dict({
            "playerCount": player_count,
            "zhuangType": zhuang_type,
            "specType": utils.check_list(rule_details.get("specType")) or [-1],
            "score": score,
            "tuiZhu": tui_zhu,
            "maxQiang": max_qiang,
            "joker": joker,
            "detailType": detail_type,
            "niuType": niu_type,
            "fanBeiType": utils.check_int(rule_details.get("fanBeiType")) or 1,
            "prohibitFanCard": utils.check_int(rule_details.get("prohibitFanCard")) or 0,
            "prohibitEnter": utils.check_int(rule_details.get("prohibitEnter")) or 0,
        })

    @staticmethod
    def __make_zhu_po_jiu_rules(rule_details):
        player_count = utils.check_int(rule_details.get("playerCount")) or 2
        if player_count not in (2, 3, 4):
            player_count = 2
        zhuang_type = utils.check_int(rule_details.get("zhuangType")) or 1
        if zhuang_type not in (1, 2):
            zhuang_type = 1
        score = utils.check_int(rule_details.get("score")) or 1
        if score not in (1, 5, 10):
            score = 1
        return dict({
            "playerCount": player_count,
            "zhuangType": zhuang_type,
            "score": score
        })

    @staticmethod
    def __make_xt_ma_jiang_rules(rule_details):
        bird_count = utils.check_int(rule_details.get("birdCount")) or 0
        if bird_count not in (0, 2, 4, 6):
            bird_count = 0

        after_gang_cards_count = utils.check_int(rule_details.get("afterGangCardsCount")) or 0
        if after_gang_cards_count not in (0, 1, 2, 4):
            after_gang_cards_count = 0

        zhuang_type = utils.check_int(rule_details.get("zhuangType")) or 0
        if zhuang_type not in (0, 1):
            zhuang_type = 0

        bird_score_type = utils.check_int(rule_details.get("birdScoreType")) or 0
        if bird_score_type not in (0, 1):
            bird_score_type = 0

        lock_cards_type = utils.check_int(rule_details.get("lockCardsType")) or 0
        if lock_cards_type not in (0, 1):
            lock_cards_type = 0

        total_seat = utils.check_int(rule_details.get("totalSeat")) or 0
        if total_seat not in (2, 3, 4):
            total_seat = 4

        return dict({
            "limitScore": utils.check_int(rule_details.get("limitScore")) or 0,  # 单局得分上限
            "birdCount": bird_count,  # 抓几鸟
            "beginHuList": utils.check_list(rule_details.get("beginHuList")) or [],  # 单局得分上限
            "haiDiType": utils.check_int(rule_details.get("haiDiType")) or 0,  # 单局得分上限
            "afterGangCardsCount": after_gang_cards_count,  # 单局得分上限
            "zhuangType": zhuang_type,  # 单局得分上限
            "birdScoreType": bird_score_type,
            "lockCardsType": lock_cards_type,
            "totalSeat": total_seat
        })

    @staticmethod
    def __make_510k_rules(rule_details):
        total_seat = utils.check_int(rule_details.get("totalSeat")) or 0
        if total_seat not in (3, 4):
            total_seat = 3

        total_score = utils.check_int(rule_details.get("totalScore")) or 0
        if total_score not in (200, 400, 600):
            total_score = 200

        return dict({
            "totalScore": total_score,
            "totalSeat": total_seat
        })

    @staticmethod
    def __make_shuang_kou_rules(rule_details):
        total_seat = utils.check_int(rule_details.get("totalSeat")) or 4

        bian_pai = utils.check_int(rule_details.get("bianPai")) or 0

        return dict({
            "totalSeat": total_seat,
            "bianPai": bian_pai,
            "contribution": utils.check_int(rule_details.get("contribution")) or 0
        })

    @staticmethod
    def __make_fang_pao_fa_rules(rule_details):
        limit_score = utils.check_int(rule_details.get("limitScore")) or 0
        base_tun = utils.check_int(rule_details.get("baseTun")) or 1
        total_seat = utils.check_int(rule_details.get("totalSeat")) or 0
        qu_pai = utils.check_int(rule_details.get("quPai")) or 0
        lian_zhuang = utils.check_int(rule_details.get("lianZhuang")) or 0
        fan_bei = utils.check_int(rule_details.get("fanBei")) or 0
        tian_di_hu = utils.check_int(rule_details.get("tianDiHu")) or 1
        chong_cao = utils.check_int(rule_details.get("chongCao")) or 0
        qi_hu = utils.check_int(rule_details.get("qiHu")) or 10
        piao_hu = utils.check_int(rule_details.get("piaoHu")) or 0
        da_niao = utils.check_int(rule_details.get("daNiao")) or 0
        #carryCardIn
        carryCardIn = utils.check_int(rule_details.get("carryCardIn")) or 0
        if total_seat not in (3, 2, 4):
            total_seat = 3
        if limit_score not in (0, 20, 40, 60, 100, 120, 150, 200):
            limit_score = 0
        if base_tun not in (1, 3, 5):
            base_tun = 1
        if qu_pai not in(0, 1, 2):
            qu_pai = 0
        if lian_zhuang not in(0, 1):
            lian_zhuang = 0
        if fan_bei not in(0, 1):
            fan_bei = 0
        if tian_di_hu not in(1, 2, 3):
            tian_di_hu = 1
        if chong_cao not in(0, 1):
            chong_cao = 0
        if qi_hu not in(6, 10, 15):
            qi_hu = 10
        #if da_niao != 0:
        #    da_niao = 1
        if piao_hu != 0:
            piao_hu = 1
        return dict({
            "totalSeat": total_seat,
            "limitScore": limit_score,
            "baseTun": base_tun,
            "lianZhuang": lian_zhuang, #连庄 0 不连庄 1 连庄
            "fanBei": fan_bei, #翻倍 0 不翻倍 1 翻倍
            "tianDiHu": tian_di_hu, #天地胡 1 十胡 2 翻倍 3 切牌
            "quPai": qu_pai, #去牌 0 不去牌 1 去十张 2 去二十张
            "chongCao": chong_cao, #冲槽 0/1
            "piaoHu":piao_hu,
            "qiHu":qi_hu,
            "daNiao":da_niao,
            "carryCardIn":carryCardIn,
        })

    @staticmethod
    def __make_shi_san_dao_rules(rule_details):
        player_count = utils.check_int(rule_details.get("playerCount")) or 2
        if player_count not in (2, 3, 4):
            player_count = 4
        zhuang_type = utils.check_int(rule_details.get("zhuangType")) or 1
        # 1 随机庄，2 无庄，3 顺序庄
        if zhuang_type not in (1, 2, 3, 4, 5):
            zhuang_type = 2

        round_type = utils.check_int(rule_details.get("roundType"))
        # 积分类型 0-长跑 1-打捆
        if round_type not in (0, 1):
            round_type = 0

        bundle_score = utils.check_int(rule_details.get("bundleScore"))
        # 积分类型 0-长跑 1-打捆
        if round_type == 1:
            if bundle_score not in (50, 100, 200):
                bundle_score = 50

        special_type = utils.check_int(rule_details.get("specialType"))
        # 特殊牌型 开关 0-关闭 1-打开
        if special_type not in (0, 1):
            special_type = 0

        return dict({
            "playerCount": player_count,
            "zhuangType": zhuang_type,
            "bundleScore": bundle_score,
            "roundType": round_type,
            "specialType": special_type,
            "maPai": utils.check_int(rule_details.get("maPai")) or 0
        })

    @staticmethod
    def __make_zha_jin_hua_rules(rule_details):
        player_count = utils.check_int(rule_details.get("playerCount")) or 2
        if player_count not in (2, 3, 4):
            player_count = 4

        return dict({
            "playerCount": player_count,
            "A23IsBig": 1,
            "BaoziLose234":1,
            "BiMenTurns":0,
            "MaxTurns":0,
            "CompareDouble":1,
            "BaoZiScore":5,
            "ShunJinScore":5
        })

    @staticmethod
    def __make_an_hua_pao_hu_zi_rules(rule_details):
        player_count = utils.check_int(rule_details.get("playerCount")) or 2
        if player_count not in (2, 3, 4):
            player_count = 4
        sanxiyitun = utils.check_int(rule_details.get("sanxiyitun")) or 1
        _3twk = utils.check_int(rule_details.get("3twk")) or 0
        jiayitun = utils.check_int(rule_details.get("jiayitun")) or 0
        fanbei = utils.check_int(rule_details.get("fanbei")) or 0
        difen = utils.check_int(rule_details.get("difen")) or 0
        return dict({
            "totalSeat": player_count,
            "sanxiyitun": sanxiyitun,
            "3twk":_3twk,
            "jiayitun":jiayitun,
            "fanbei":fanbei,
            "difen":difen
        })
    @staticmethod
    def make_rule_details(game_type: int, rule_details):
        if game_type == const.SERVICE_ZZMJ:
            return CreateRoomHandler.__make_ma_jiang_rules(rule_details)
        elif game_type == const.SERVICE_TIAN_ZHA:
            return CreateRoomHandler.__make_tianzha_rules(rule_details)
        elif game_type == const.SERVICE_HUAI_HUA_QUAN_MING_TANG:
            return CreateRoomHandler.__make_huai_hua_quan_ming_tang_rules(rule_details)
        elif game_type == const.SERVICE_BPH:
            return CreateRoomHandler.__make_bo_pi_rules(rule_details)
        elif game_type == const.SERVICE_HZMJ:
            return CreateRoomHandler.__make_hz_ma_jiang_rules(rule_details)
        elif game_type == const.SERVICE_PDK:
            return CreateRoomHandler.__make_pao_de_kuai_rules(rule_details)
        elif game_type == const.SERVICE_CSMJ:
            return CreateRoomHandler.__make_cs_ma_jiang_rules(rule_details)
        elif game_type == const.SERVICE_XTMJ:
            return CreateRoomHandler.__make_xt_ma_jiang_rules(rule_details)
        elif game_type == const.SERVICE_HENG_YANG_MO_MO:
            return CreateRoomHandler.__make_heng_yang_mo_mo_rules(rule_details)
        elif game_type in (const.SERVICE_NIUNIU, const.SERVICE_BCNN):
            return CreateRoomHandler.__make_niu_niu_rules(rule_details)
        elif game_type == const.SERVICE_ZHU_PO_JIU:
            return CreateRoomHandler.__make_zhu_po_jiu_rules(rule_details)
        elif game_type == const.SERVICE_YXPH:
            return CreateRoomHandler.__make_you_xian_peng_hu_rules(rule_details)
        elif game_type == const.SERVICE_510K:
            return CreateRoomHandler.__make_510k_rules(rule_details)
        elif game_type == const.SERVICE_DTZ:
            return CreateRoomHandler.__make_da_tong_zi_rules(rule_details)
        elif game_type == const.SERVICE_XTPH:
            return CreateRoomHandler.__make_xt_pao_hu_rules(rule_details)
        elif game_type == const.SERVICE_SDH:
            return CreateRoomHandler.__make_san_da_ha_rules(rule_details)
        elif game_type == const.SERVICE_CDPH:
            return CreateRoomHandler.__make_pao_hu_rules(rule_details)
        elif game_type == const.SERVICE_HAN_SHOU_PAO_HU:
            return CreateRoomHandler.__make_han_shou_pao_hu_rules(rule_details)
        elif game_type == const.SERVICE_EBG:
            return CreateRoomHandler.__make_er_ba_gang_rules(rule_details)
        elif game_type == const.SERVICE_SHUANG_KOU:
            return CreateRoomHandler.__make_shuang_kou_rules(rule_details)
        elif game_type == const.SERVICE_SHI_SAN_DAO:
            return CreateRoomHandler.__make_shi_san_dao_rules(rule_details)
        elif game_type == const.SERVICE_YZCHZ:
            return CreateRoomHandler.__make_yzchz_rules(rule_details)
        elif game_type == const.SERVICE_CZPHZ:
            return CreateRoomHandler.__make_czphz_rules(rule_details)
        elif game_type == const.SERVICE_FENG_HUANG_HUA_SHUI:
            return CreateRoomHandler.__make_feng_huang_hua_shui_rules(rule_details)
        elif game_type == const.SERVICE_FENG_HUANG_HONG_ZHONG:
            return CreateRoomHandler.__make_feng_huang_hong_zhong_rules(rule_details)
        elif game_type == const.SERVICE_ZLMZ:
            return CreateRoomHandler.__make_zhuo_lao_ma_zi_rules(rule_details)
        elif game_type == const.SERVICE_TUI_DAO_HU:
            return CreateRoomHandler.__make_tui_dao_hu_rules(rule_details)
        elif game_type == const.SERVICE_FANG_PAO_FA:
            return CreateRoomHandler.__make_fang_pao_fa_rules(rule_details)
        elif game_type == const.SERVICE_ZJH:
            return CreateRoomHandler.__make_zha_jin_hua_rules(rule_details)
        elif game_type == const.SERVICE_AHPF:
            return CreateRoomHandler.__make_an_hua_pao_hu_zi_rules(rule_details)

    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode(self.get_string('params'))
        if not params or not params.get('gameType') or not params.get('totalRound'):
            return self.write_json(error.DATA_BROKEN)

        game_type = utils.check_int(params.get("gameType")) or 0
        total_round = utils.check_int(params.get("totalRound")) or 0
        is_agent = utils.check_int(params.get("isAgent")) or 0
        rule_type = utils.check_int(params.get("ruleType")) or 1
        club_id = int(params.get('clubID', -1))

        if total_round not in (4, 6, 10, 20, 12, 30, 18, 8, 16, 24, 200, 400, 600, 1000):
            return self.write_json(error.DATA_BROKEN)

        if not self.share_db():
            return self.write_json(error.SYSTEM_ERR)

        if club_id == -1 and is_agent == 0:
            info = tables_model.get_by_owner_not_agent(self.share_db(), self.uid)
            if info:
                return self.write_json(error.OK, {"gameType": info['game_type'], 'roomID': int(info.get('tid')),
                                                  "isAgent": info['is_agent']})


        rule_details = params.get("ruleDetails")
        rules = self.make_rule_details(game_type, rule_details)
        if rule_type not in (1, 2, 3, 4, 5, 6) or type(rule_details) is not dict:
            return self.write_json(error.DATA_BROKEN)
        if game_type == const.SERVICE_TUI_DAO_HU:
            postion_x = (utils.check_int(rule_details.get("postionX")) or 181)
            postion_y = (utils.check_int(rule_details.get("postionY")) or 91)
            print("===", postion_x, "====", postion_y, "===", utils.check_int(rule_details.get("fangZuoBiDistance", 0)))
            if (postion_x == 181 or postion_y == 91) and utils.check_int(rule_details.get("fangZuoBiDistance", 0)) != 0:
                return self.write_json(error.POSTION_UNKNOWN)
        if club_id != -1:
            is_agent = 1
            if not club_model.get_club_by_owner_and_club_id(self.share_db(), self.uid, club_id):
                return self.write_json(error.DATA_BROKEN)

        if club_id == -1 and is_agent == 1 \
                and tables_model.get_dai_kai_count_by_owner(self.share_db(), self.uid).get('room_count', 0) >= 5:
            return self.write_json(error.CREATE_ROOM_LIMIT)

        if is_agent == 0:
            info = tables_model.get_by_owner_not_agent(self.share_db(), self.uid)
            if info:
                return self.write_json(error.OK, {
                    'roomID': int(info.get('tid')), 'isAgent': is_agent})

        consume_type = int(params.get('consumeType', const.PAY_TYPE_CREATOR))
        if consume_type not in (const.PAY_TYPE_CREATOR, const.PAY_TYPE_AA, const.PAY_TYPE_WINNER):
            consume_type = const.PAY_TYPE_CREATOR

        tid = base_redis.spop_table_id() or utils.get_random_num(6)
        user = player_model.get_by_uid(self.share_db(), self.uid)
        if not user:
            return self.write_json(error.DATA_BROKEN)

        if game_type in const.CALC_DIAMOND_WITH_PLAYER_NUM:
            diamonds = self.__calc_diamonds_with_player_count(total_round, game_type, rule_details.get("totalSeat"))
        else:
            diamonds = self.__calc_diamonds(total_round, game_type)

        if diamonds == -1:
            return self.write_json(error.DATA_BROKEN)

        if user.get('diamond', 0) + user.get('yuan_bao') < diamonds:
            return self.write_json(error.DIAMONDS_NOT_ENOUGH)

        idle_table_diamond = tables_model.get_total_idle_diamonds_by_uid(self.share_db(), user['uid'])
        if user.get('diamond', 0) + user.get('yuan_bao') < diamonds + idle_table_diamond:
            return self.write_json(error.DIAMONDS_CLUB_NOT_ENOUGH)

        room_sid = game_room_model.get_best_server_sid(self.share_db(), redis_conn(), game_type)
        if not room_sid:
            return self.write_json(error.DATA_BROKEN)
        try:
            count = tables_model.insert(self.share_db(), room_sid, game_type, int(tid), self.uid, is_agent, total_round,
                                        diamonds, rule_type, club_id, rules, consume_type=consume_type)
            pass
        except Exception as data:
            logging.error(f"insert default table error: {self.uid} {data}")
            count = 0

        if count <= 0:
            return

        if club_id != -1:
            user_list = club_model.query_all_data_by_club_id(self.share_db(), club_id)
            uid_list = [user["uid"] for user in user_list]
            self.broad_cast_user(uid_list, {
                "type": const.CLUB_CREATE_ROOM,
                "data": {'roomID': int(tid), "gameType": game_type, "ruleDetails": rules, "isAgent": is_agent}})

        return self.write_json(error.OK, {'roomID': int(tid), "gameType": game_type,
                                          "ruleDetails": rules, "isAgent": is_agent})


class QueryRoomHandler(BaseHandler):
    def prepare(self):
        if not self.check_fixed_params(True):
            return self.write_json(error.DATA_BROKEN)
        if not self.check_sign():
            return self.write_json(error.SIGN_FAIL)

    def get(self):
        return self._request()

    def post(self):
        return self._request()

    def _request(self):
        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode(self.get_string('params'))
        if not params or not params.get('roomID'):
            return self.write_json(error.DATA_BROKEN)

        tid = int(params.get('roomID'))
        if tid <= 0:
            return self.write_json(error.DATA_BROKEN)

        if not self.share_db():
            return self.write_json(error.SYSTEM_ERR)

        info = tables_model.get_by_owner(self.share_db(), self.uid)
        if info:  # 如果自己已经创建了房间，直接返回此间
            return self.__response_by_table_info(info)

        info = tables_model.get(self.share_db(), tid)
        if not info:
            return self.write_json(error.ROOM_NOT_EXIST)

        return self.__response_by_table_info(info)

    def __response_by_table_info(self, info):
        result = {"gameType": info.game_type, 'roomID': int(info.get('tid'))}
        return self.write_json(error.OK, result)
