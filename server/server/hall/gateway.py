# coding:utf-8
import random
import datetime
from twisted.internet import reactor
from twisted.internet.protocol import Factory

from base import commands_system, const, error, commands_auth
from models import database, servers_model
from protocol import protocol_utils
from utils import utils
from base.base_server import BaseServer
from protocol.session_client import SessionClient
from hall.auth import AuthService
from hall.system import SystemService
from utils.twisted_tools import LoopingCall
from utils.twisted_tools import DelayCall

class Gateway(BaseServer):
    def __init__(self):
        BaseServer.__init__(self)
        self.__port = 0  # 网关所对外服务的端口
        self.__tmp_sessions = []  # 临时会话
        self.__sessions = dict({})  # 会话
        self.__bind_list = []
        self.__services = {}  # 服务的处理类
        self.__delay_android = DelayCall(10, self.__push_client_android)
        self.__key = "onlinenum"  # 在线人数
        self.__room_id = 1
        self.__android = dict() # 存放机器人

    def __push_client_android(self):
        from models import tables_model
        key = 'union_player_online'
        key1 = 'androidtids'

        def union_android():
            data = database.share_redis_game().hgetall(key)
            data = [int(x) for x in data.values()]
            data = set(data)
            for u in data:
                android = tables_model.get_android_settings(u)
                if not android:
                    continue
                if android['state'] == 1:
                    continue
                lsa = tables_model.android(u, android['minnum'], android['maxnum'],
                                           android['start'], android['end'])
                lsa = tables_model.one_by_one_to_step(android['start'], android['end'],
                                                      lsa, u)
                if not lsa:
                    self.__android[u] = []
                    continue
                if len(lsa) == 0:
                    self.__android[u] = []
                    continue
                #lsa = tables_model.close_random_to_android_list(lsa,u)
                # 获取状态
                statuslst = database.share_redis_game().hget(key1,u)
                if not statuslst:
                    continue
                """获取桌子状态"""
                statuslst = utils.json_decode(str(statuslst,encoding='utf8'))
                """获取联盟在线玩家"""
                online = database.share_redis_game().hgetall('union_player_online')
                online = [{'k':int(str(x[1],encoding='utf8')), 'v':int(str(x[0],encoding='utf8')) }
                          for x in online.items()]
                online = [x.get('v') for x in online if x.get('k') == u]
                ongameuid = tables_model.get_online_uids()
                for uidgame in ongameuid:
                    if uidgame in online:
                        online.remove(uidgame)
                """获取联盟在线玩家"""
                self.__android[u] = lsa
                """新增桌子"""
                for onlineuid in online:
                    session = self.__get_session_by_uid(onlineuid)
                    if not session:
                        continue
                    datatwo = dict(data = lsa,type=10)
                    session.send(protocol_utils.pack_client_message(0, 301, datatwo))

        # 内部调用
        try:
            union_android()
        except Exception as e:
            n_time = datetime.datetime.now()
            print(n_time)
            print('机器人调用出现异常')
            print(e)
        # 重新开始计算延迟调用
        delay_second = random.randint(70, 90)
        self.__delay_android = DelayCall(delay_second, self.__push_client_android)

    def on_signal_stop(self):  # 收到结束的信号
        return self.__close_server()

    def __close_server(self):
        for s in self.__bind_list:
            s.close()
        self.logger.info("start close gate server %d ", self.server_id)
        servers_model.update_status(self.server_id, 0)  # 已关闭
        self._stop_listen_channel()
        self.logger.info("stop listen channel %d ", self.server_id)
        database.share_db().close()
        database.share_db_logs().close()
        database.share_redis_game().connection_pool.disconnect()

    def __save_session(self, session: SessionClient):
        if not session or not session.uid or not session.verified:
            return
        self.__sessions[session.uid] = session
        #更新在线人数
        attachnum = random.randint(5,20)
        database.share_redis_game().hset(self.__key,self.__room_id,len(self.__sessions) + attachnum)

    def __save_tmp_session(self, session: SessionClient):
        try:
            #self.__tmp_sessions.index(session)
            if self.__tmp_sessions.count(session) == 0:
                self.__tmp_sessions.append(session)
        except ValueError:
            self.__tmp_sessions.append(session)

    def __del_session(self, session: SessionClient):
        if not session:
            return

        try:
            uid = session.uid
            if id(self.__sessions[session.uid]) == id(session):
                del self.__sessions[session.uid]
            attachnum = random.randint(5,20)
            database.share_redis_game().hset(self.__key,self.__room_id,len(self.__sessions) + attachnum)
            #key = "union_player_online"
            #database.share_redis_game().hdel(key,uid)
        except KeyError:
            pass

        self.__del_tmp_session(session)
        session.close()

    def __del_tmp_session(self, session: SessionClient):
        if not session:
            return
        try:
            self.__tmp_sessions.remove(session)
        except ValueError:
            pass

    def __get_session_by_uid(self, uid) -> SessionClient:
        obj = self.__sessions.get(uid)
        if isinstance(obj, SessionClient):
            return obj

    def setup(self, server_id, service_type, service_name, server_info):
        BaseServer.setup(self, server_id, service_type, service_name, server_info)
        port = int(server_info.get('port'))
        self.__port = port
        self.set_service(AuthService())
        self.set_service(SystemService())

    def set_listen_port(self, port):
        self.__port = port

    def set_service(self, service):
        assert service and service.service_type
        self.__services[service.service_type] = service

    def on_player_connection_made(self, session):  # 玩家连接建立时被调用的
        self.__save_tmp_session(session)

    def on_player_connection_lost(self, session):  # 玩家掉线时被调用
        if session and session.uid > 0:
            if self.__sessions.get(session.uid) and id(self.__sessions.get(session.uid)) == id(session):
                data = {"online": 0}
                cmd = commands_system.PLAYER_SOCKET_CHANGE
                self.publish_to_channel_from_service(const.SERVICE_SYSTEM, 0, cmd, session.uid, data)
                self.__del_session(session)
        print('服务器清理session:' + str(session.uid))


    def on_session_auth_success(self, session):
        self.__del_tmp_session(session)
        self.__save_session(session)

    def on_line_received(self, session, line):  # 收到玩家数据
        if not line or len(line) < 2:
            return
        ret = utils.json_decode(line)
        if not ret or not ret.get('cmd'):
            session.close()
            return self.logger.info('receive data error: ' + utils.bytes_to_str(line))
        self.distribute(session, ret.get('cmd'), ret.get('msg'))

    def distribute(self, session, cmd, msg):
        service_type, cmd = protocol_utils.unpack_command(cmd)
        service = self.__services.get(service_type)
        if not service:
            return self.__check_run_client_commands(session, service_type, cmd, msg)
        service.service(session, cmd, msg)

    def __check_run_client_commands(self, session, service_type, cmd, msg):
        if cmd == commands_auth.ENTER_ROOM and service_type == const.SERVICE_AUTH:
            room_id = int(msg.get("roomID", 0))
            if not room_id:
                return session.send(protocol_utils.pack_client_message(service_type, cmd, {"code": error.DATA_BROKEN}))
            from models import tables_model
            room_info = tables_model.get(room_id)
            if not room_info:
                return session.send(protocol_utils.pack_client_message(service_type, cmd, {
                    "code": error.TABLE_NOT_EXIST
                }))
            client = {"uid": session.uid, "verified": session.verified, "ip": session.ip}
            msg["_client"] = client

        return self.publish_to_channel(service_type, cmd, session.uid, msg)

    def distribute_to_system_push(self, service_type, cmd, msg, uids):
        service = self.__services.get(service_type)
        if not service:
            return

        if type(uids) == int:
            uids = [uids]

        service.service_broad(service_type, cmd, msg, uids)

    def publish_to_channel_from_service(self, from_service, to_service, cmd, uid, message):
        self.logger.info("gate publish to channel: %d", cmd)
        body = protocol_utils.pack_to_player_body(cmd, uid, message)
        return self._s2s_raw_send(0, from_service, 0, to_service, 1, body)

    def publish_to_channel(self, service, cmd, uid, message):
        self.logger.info("gate publish to channel: %d", cmd)
        body = protocol_utils.pack_to_player_body(cmd, uid, message)
        return self._s2s_send(0, service, 1, body)

    def __on_receive_message(self, from_sid, from_service, to_sid, to_service, body):
        cmd, uid, msg = protocol_utils.unpack_to_player_body(body)
        self.logger.debug("handle receive message: %s %s %s %s %s %s %s",
                          from_sid, from_service, to_sid, to_service, cmd, uid, msg)
        if not cmd:
            return

        if from_service == const.SERVICE_SYSTEM and cmd == commands_system.PUSH_MESSAGE:
            return self.distribute_to_system_push(from_service, cmd, msg, uid)

        session = self.__get_session_by_uid(uid)
        if session:
            session.send(protocol_utils.pack_client_message(from_service, cmd, msg))
        elif uid == 2:
            union_id = msg['union_id']
            uid = msg['uid']
            selfuid = msg['selfuid']
            type = msg['type']
            session = self.__get_session_by_uid(selfuid)
            from utils.twisted_tools import DelayCall
            if session:
                DelayCall(1,self.push_msg_energy,union_id,uid,session,selfuid,type)
        elif uid == 3:
            union_id = msg['union_id']
            uid = msg['uid']
            selfuid = msg['selfuid']
            type = msg['type']
            session = self.__get_session_by_uid(selfuid)
            from utils.twisted_tools import DelayCall
            if session:
                DelayCall(1,self.push_msg_energybyuid,union_id,uid,session,selfuid,type)
        elif uid == 5: # 进入联盟获取所有的桌子
            union_id = msg['union_id']
            uid = msg.get('uid')
            selfuid = msg['selfuid']
            type = msg['type']
            session = self.__get_session_by_uid(selfuid)
            from utils.twisted_tools import DelayCall
            if session:
                DelayCall(0,self.push_union_alltables,union_id,uid,session,selfuid,type)
        elif uid == 6:# 有人在桌子上面打牌，通知联盟大厅桌子更新状态
            union_id = msg['union_id']
            uid = msg['uid']
            selfuid = msg['selfuid']
            type = msg['type']
            tid = msg['tid']
            subfloor = msg['subfloor']
            deltids = msg.get('deltids') or []
            new_tid = msg.get('new_tid') or 0
            from utils.twisted_tools import DelayCall
            if tid == -9:
                DelayCall(0,self.push_union_deltids, deltids, union_id)
            else:
                DelayCall(0,self.push_union_tables_change,union_id,uid,session,selfuid,type,tid,subfloor,new_tid)
        elif uid == 9:
            union_id = msg['union_id']
            type = msg['type']
            tid = msg['tid']
            subfloor = msg['subfloor']
            round_index = msg['round_index']
            from utils.twisted_tools import DelayCall
            DelayCall(0,self.push_union_table_round_change,union_id,type,tid,subfloor,round_index)

    def push_union_table_round_change(self,union_id,type,tid,subfloor,round_index):
        """桌子局数变化"""
        from models import tables_model
        tables = tables_model.get_table_by_union(union_id,subfloor)
        key = "union_player_online"
        online = database.share_redis_game().hgetall('union_player_online')
        online = [{'k':int(str(x[1],encoding='utf8')), 'v':int(str(x[0],encoding='utf8')) }
                  for x in online.items()]
        online = [x.get('v') for x in online if x.get('k') == union_id]

        ongameuid = tables_model.get_online_uids()
        for uidgame in ongameuid:
            if uidgame in online:
                online.remove(uidgame)
        data_round = [x for x in tables if x['tid'] == tid]
        if len(data_round) == 0:
            return
        data_round[0]['roundIndex'] = round_index
        for uid_onlie in online:
            sessionuid = self.__get_session_by_uid(uid_onlie)
            if not sessionuid:
                database.share_redis_game().hdel(key,uid_onlie)
                continue
            data = dict(data = data_round,type=9)
            sessionuid.send(protocol_utils.pack_client_message(0, 301, data))

    def push_union_deltids(self, deltids,union_id):
        from models import tables_model
        online = database.share_redis_game().hgetall('union_player_online')
        online = [{'k':int(str(x[1],encoding='utf8')), 'v':int(str(x[0],encoding='utf8')) }
                  for x in online.items()]
        online = [x.get('v') for x in online if x.get('k') == union_id]
        ongameuid = tables_model.get_online_uids()
        key = "union_player_online"
        for uidgame in ongameuid:
            if uidgame in online:
                online.remove(uidgame)
        for uid_onlie in online:
            sessionuid = self.__get_session_by_uid(uid_onlie)
            if not sessionuid:
                database.share_redis_game().hdel(key,uid_onlie)
                continue
            for td in deltids:
                sessionuid.send(protocol_utils.pack_client_message(0, 301, {'tid':td,'type':8}))

    def push_union_tables_change(self, union_id, uid, session, selfuid, type,tid,subfloor, new_tid):
        """联盟成员广播桌子变动"""
        from models import tables_model
        tables = tables_model.get_table_by_union(union_id,subfloor)
        key = "union_player_online"
        online = database.share_redis_game().hgetall('union_player_online')
        online = [{'k':int(str(x[1],encoding='utf8')), 'v':int(str(x[0],encoding='utf8')) }
             for x in online.items()]
        online = [x.get('v') for x in online if x.get('k') == union_id]
        changetable = [x for x in tables if x.get('tid') == tid]
        addtable = [x for x in tables if x.get('tid') == int(new_tid)]
        deltable = [x['tid'] for x in tables]
        isdel = int(tid) not in deltable or tid == -9
        ongameuid = tables_model.get_online_uids()
        for uidgame in ongameuid:
            if uidgame in online:
                online.remove(uidgame)
        for uid_onlie in online:
            sessionuid = self.__get_session_by_uid(uid_onlie)
            if not sessionuid:
                database.share_redis_game().hdel(key,uid_onlie)
                continue
            if isdel:
                sessionuid.send(protocol_utils.pack_client_message(0, 301, {'tid':tid,'type':8}))
            if len(changetable) > 0:
                data = dict(data = changetable,type=7)
                sessionuid.send(protocol_utils.pack_client_message(0, 301, data))
            if len(addtable) > 0:
                data1 = dict(data = addtable,type=6)
                sessionuid.send(protocol_utils.pack_client_message(0, 301, data1))



    def push_union_alltables(self, union_id, uid, session, selfuid, type):
        """获取联盟里面所有的桌子"""
        from models import tables_model
        tables = tables_model.get_table_by_union(union_id,0)
        android = tables_model.get_android_settings(union_id)
        if android:
            print('after %d ' % len(android))
        if android and len(android) > 3:
            if android['state'] == 0 and union_id in self.__android and \
               len(self.__android[union_id]) > 0:
                tables.extend(self.__android[union_id])

        data = dict(data = tables,type=type)
        session.send(protocol_utils.pack_client_message(0, 301, data))


    def push_msg_energybyuid(self,union_id,uid,session,selfuid,type):
        from models import union_model
        data = union_model.getenergybyuid(union_id,uid,selfuid)
        if not data or len(data) == 0:
            session.send(protocol_utils.pack_client_message(0, 301, {'energy':0,'uid':uid,'type':-type}))
        else:
            data = data[0]
            data['type'] = type
            session.send(protocol_utils.pack_client_message(0, 301, data))


    def push_msg_energy(self,union_id,uid,session,selfuid,type):
        """服务器推送总能量给指定的玩家"""
        from models import union_model
        energy = union_model.getallenergy(union_id,uid)
        num = 0
        if energy:
            if len(energy) > 0:
                num = energy[0]['energy']
                if session:
                    session.send(protocol_utils.pack_client_message(0, 301, {'energy':num,'uid':uid,'type':type}))



    def __clean_timeout_sessions(self):
        self.logger.info("clean timeout sessions begin %d %d", len(self.__tmp_sessions), len(self.__sessions))
        curr_time = utils.timestamp()
        tmp_del_list = []
        for ts in self.__tmp_sessions:
            if not ts:
                continue
            if curr_time - ts.last_data_time < 5 * 60:
                continue
            tmp_del_list.append(ts)
        for ts in tmp_del_list:
            self.__del_tmp_session(ts)
            ts.close()
        tmp_del_list.clear()
        del_list = []
        for uid, session in list(self.__sessions.items()):
            if not session:
                continue
            if curr_time - session.last_data_time < 10 * 60:
                continue
            del_list.append(session)
        for ds in del_list:
            print('清理超时会话:%d' % ds.uid)
            self.__del_session(ds)
            ds.close()
        del_list.clear()
        self.logger.info("clean timeout sessions end %d %d", len(self.__tmp_sessions), len(self.__sessions))

    def send_uids_message(self, uids, service_type, cmd, msg):
        from collections import Iterable
        if not isinstance(uids,Iterable):
            return
        for uid in uids:
            self.__send_message_by_uid(uid, service_type, cmd, msg)

    def send_global_message(self, service_type, cmd, msg):
        for s in self.__sessions.values():
            self.__send_message_by_session(s, service_type, cmd, msg)

    def __send_message_by_uid(self, uid, service_type, cmd, msg):
        session = self.__get_session_by_uid(uid)
        if session:
            session.send(protocol_utils.pack_client_message(service_type, cmd, msg))

    @staticmethod
    def __send_message_by_session(session, service_type, cmd, msg):
        if session:
            session.send(protocol_utils.pack_client_message(service_type, cmd, msg))

    def start_service(self):  # 启动游戏服务
        self._start_listen_channel(self.__on_receive_message)
        player_agent = Factory()
        player_agent.protocol = SessionClient
        reactor.listenTCP(self.__port, player_agent)
        self.logger.info('Starting listening on port %d', self.__port)
        LoopingCall(5 * 60, self.__clean_timeout_sessions)
        servers_model.update_status(self.server_id, 1)
        reactor.addSystemEventTrigger('before', 'shutdown', self.on_signal_stop)
        reactor.run()

    @staticmethod
    def share_server():
        return Gateway()
