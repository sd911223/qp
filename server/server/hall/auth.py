# coding:utf-8

from base import const
from base import error
from base.commands_auth import *
from models import onlines_model
from base.base_service import BaseService
from utils.logs import gate_logger
from models import tables_model
from utils.twisted_tools import DelayCall


class AuthService(BaseService):

    def __init__(self):
        BaseService.__init__(self, const.SERVICE_AUTH)
        self._add_handlers({
            LOGIN: self.__on_login,
            ENTER_ROOM: self.__on_enter_room,
            EXPRESS_ENTER_ROOM:self.__on_express_enter_room,
            GETONLINENUM:self.__getonlinenum
        })
    def __getonlinenum(self,session,data):
        return self.response(session, LOGIN, {"code": error.OK})
    def __on_login(self, session, data):
        """
        登录认证处理
        :param session: PlayerClient
        :param data: dict
        :return:
        """
        if session.verified:
            return self.response(session, LOGIN, {"code": error.OK})

        if data.get("gameId") != const.GAME_ID:
            return self.response_fail(session, LOGIN, error.DATA_BROKEN)

        if not data.get('uid') or not data.get('key') or not data.get('gameId'):
            return self.response_fail(session, LOGIN, error.DATA_BROKEN)

        online = onlines_model.get_by_token(data.get('key'))
        if not online or not online.get('uid') or int(online.get('uid')) != data.get('uid'):
            gate_logger.info(str(data))
            gate_logger.info(str(online))
            return self.response_fail(session, LOGIN, error.TOKEN_ERROR)

        session.set_verified(int(online.get('uid')), True)
        self.response(session, LOGIN, {"code": error.OK})
        from hall.gateway import Gateway
        return Gateway.share_server().on_session_auth_success(session)

    def __on_enter_room(self, session, data):
        from hall.gateway import Gateway
        gate = Gateway.share_server()
        room_id = int(data.get("roomID", 0))
        if not room_id:
            return self.response_fail(session, ENTER_ROOM, error.DATA_BROKEN)

        client = {"uid": session.uid, "verified": session.verified, "ip": session.ip}
        data["_client"] = client

        user = onlines_model.get_by_uid(session.uid)
        if user and user['tid'] != 0 and user['tid'] != room_id:
            room_info = tables_model.get(user['tid'])
            if room_info:
                if room_info['state'] == "1":
                    return self.response(session, ENTER_ROOM, {"roomID": user['tid']}, error.GAME_ALREADY_START)
                else:
                    gate.publish_to_channel(room_info['game_type'], 2, session.uid, {})
                    return DelayCall(1, self.__delay_enter_room, room_id, session, data)

        room_info = tables_model.get(room_id)
        if room_info:
            self.response(session, ENTER_ROOM, {"gameType": room_info['game_type']})
            #return gate.publish_to_channel(room_info.game_type, 1, session.uid, data)
            return gate.publish_to_channel(room_info['game_type'], 1, session.uid, data)

        return self.response_fail(session, ENTER_ROOM, error.TABLE_NOT_EXIST)





    def get_empter_table_by_redis(self,unionID,subFloor):
        from utils import utils
        room_from_db = tables_model.query_table_with_not_start_and_sub_floor2(subFloor,unionID)
        room_from_redis = tables_model.get_table_from_redis()
        room_id = 0
        redis_room_list = []
        for i_r in room_from_redis:
            tid_fr_redis = int(i_r)
            r_db = [x for x in room_from_db if x['tid'] == tid_fr_redis]
            if len(r_db) == 0:
                continue
            redis_room_list.append(tid_fr_redis)
            rulesstrbur = r_db[0]['rules']
            rulesstrbur = rulesstrbur.replace('\\"','\"',len(rulesstrbur))
            rules = utils.json_decode(rulesstrbur)
            playercount = 2
            if "playerCount" in rules:
                playercount =  rules['playerCount']
            elif "totalSeat" in rules:
                playercount = rules['totalSeat']
            tab_redis = utils.json_decode(room_from_redis[i_r])
            player_list = tab_redis['player_list']
            if len(player_list) < playercount and room_id == 0:
                room_id = tid_fr_redis
        if room_id == 0:
            for i_db in room_from_db:
                tid = i_db['tid']
                find_db = [x1 for x1 in redis_room_list if x1 == tid]
                if len(find_db) > 0:
                    continue
                room_id = tid
        if room_id == 0:
            from models import union_model,database
            uid = union_model.get_union_id(database.share_db(),unionID )
            #判断子玩法是否存在
            subfloorresult = union_model.get_sub_floor_by_floor1(database.share_db(), subFloor)
            tables_model.create_sub_floor_room(uid['uid'], 1, 0, subFloor,unionID)
            if not subfloorresult:
                return -1
            if len(subfloorresult) == 0:
                return -1
            return self.get_empter_table_by_redis(unionID,subFloor)
        return room_id
    def __on_express_enter_room(self, session, data):
        from hall.gateway import Gateway
        gate = Gateway.share_server()
        room_id = int(data.get("roomID", 0))
        unionID = int(data.get("unionID",0))
        subFloor = int(data.get("subFloor", 0))
        try:
            from models import union_model
            from models import union_model, database
            union_db = union_model.get_union_id(  database.share_db(),unionID )
            if not union_db:
                return self.response_fail(session, ENTER_ROOM, error.DATA_BROKEN)
            if len(union_db) == 0:
                return self.response_fail(session, ENTER_ROOM, error.DATA_BROKEN)
            subfloordb = union_model.get_union_sub_floor_config(database.share_db(), unionID, subFloor)
            if not subfloordb:
                return self.response_fail(session, ENTER_ROOM, -99)
            if len(subfloordb) == 0:
                return self.response_fail(session, ENTER_ROOM, -99)
            print('快速进入房间,',unionID,subFloor)
            room_id = self.get_empter_table_by_redis(unionID,subFloor)
        except RecursionError as ef:
            return self.response_fail(session, ENTER_ROOM, error.DATA_BROKEN)
        except Exception as ex:
            return self.response_fail(session, ENTER_ROOM, error.DATA_BROKEN)
        else:
            print(1)
        if room_id == -1:
            return self.response_fail(session, ENTER_ROOM, error.DATA_BROKEN)
        data['roomID'] = room_id
        if not room_id and not True:
            return self.response_fail(session, ENTER_ROOM, error.DATA_BROKEN)

        client = {"uid": session.uid, "verified": session.verified, "ip": session.ip}
        data["_client"] = client

        user = onlines_model.get_by_uid(session.uid)
        if user and user['tid'] != 0 and user['tid'] != room_id:
            room_info = tables_model.get(user['tid'])
            if room_info:
                if room_info['state'] == "1":
                    return self.response(session, ENTER_ROOM, {"roomID": user['tid']}, error.GAME_ALREADY_START)
                else:
                    gate.publish_to_channel(room_info['game_type'], 2, session.uid, {})
                    return DelayCall(1, self.__delay_enter_room, room_id, session, data)

        room_info = tables_model.get(room_id)
        if room_info:
            self.response(session, ENTER_ROOM, {"gameType": room_info['game_type']})
            return gate.publish_to_channel(room_info['game_type'], 253, session.uid, data)

        return self.response_fail(session, ENTER_ROOM, error.TABLE_NOT_EXIST)

    def __delay_enter_room(self, room_id, session, data):
        from hall.gateway import Gateway
        gate = Gateway.share_server()
        room_info = tables_model.get(room_id)
        if room_info:
            self.response(session, ENTER_ROOM, {"gameType": room_info['game_type']})
            return gate.publish_to_channel(room_info['game_type'], 1, session.uid, data)

        return self.response_fail(session, ENTER_ROOM, error.TABLE_NOT_EXIST)
