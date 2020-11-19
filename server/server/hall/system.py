# coding:utf-8

from base import const
from base import error
from base.commands_system import *
from models import configs_model
from models import servers_model
from base.base_service import BaseService


class SystemService(BaseService):

    def __init__(self):
        BaseService.__init__(self, const.SERVICE_SYSTEM)
        self._add_handlers({
            HEART_BEAT: self.__on_heart_beat,
            STOP_SERVER: self.__on_stop_server,
            PUSH_MESSAGE: self.__on_push_message,
            SOCKET_CHANGE: self.__on_socket_change
        })

    def __on_stop_server(self, session, data):
        if not session.ip or not data or not data.get('key'):
            return self.response_fail(session, STOP_SERVER, error.COMMAND_DENNY)
        ips = configs_model.get("ips")
        if not ips:
            return self.response_fail(session, STOP_SERVER, error.SYSTEM_ERROR)
        ips = ips.split(",")
        if session.ip not in ips:
            return self.response_fail(session, STOP_SERVER, error.COMMAND_DENNY)
        key = data.get('key')
        from hall.gateway import Gateway
        server = Gateway.share_server()
        server_info = servers_model.get(server.server_id)
        if key != server_info.get("key"):
            return self.response_fail(session, STOP_SERVER, error.TOKEN_ERROR)
        is_force = data.get('isForce', False)
        code = error.OK
        if is_force:
            if not server.stop_game_force():
                code = error.COMMAND_DENNY
        else:
            server.stop_game()
        params = {"server_id": server.server_id, "in_stop": server.in_stop}
        return self.response(session, STOP_SERVER, params, code)

    def __on_heart_beat(self, session, data):
        return self.response(session, HEART_BEAT, data)

    @staticmethod
    def __on_push_message(service_type, cmd, msg, uids):
        from hall.gateway import Gateway
        from collections import  Iterable
        server = Gateway.share_server()
        if uids == None:
            return
        if not uids and not isinstance(uids, list) and len(uids) == 0:
            return
        if uids and isinstance(uids,list)  and len(uids)>0:
            if uids[0] == -1:
                return server.send_global_message(service_type, cmd, msg)
        server.send_uids_message(uids, service_type, cmd, msg)

    def __on_socket_change(self, session, data):
        if session and session.uid:
            from hall.gateway import Gateway
            gate = Gateway.share_server()
            gate.publish_to_channel_from_service(const.SERVICE_SYSTEM, 0, SOCKET_CHANGE, session.uid, data)


system = SystemService()
