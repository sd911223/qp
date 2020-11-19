# coding:utf-8

from configs import error

from .base_handler import BaseHandler
from models import player_model
from utils import utils
from configs import const

BIND_DIAMOND = 100


class BindHandler(BaseHandler):
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
        if not self.share_db():
            return self.write_json(error.SYSTEM_ERR)

        if not self.get_string('params'):
            return self.write_json(error.DATA_BROKEN)

        params = utils.json_decode(self.get_string('params'))
        if not params or not params.get('agentID'):
            return self.write_json(error.DATA_BROKEN)

        player = player_model.get_by_uid(self.share_db(), self.uid)
        if not player:
            return self.write_json(error.ACCESS_DENNY)
        if player['father_id'] != 0:
            return self.write_json(error.ALREADY_BIND_AGENT)

        agent_id = params.get('agentID')
        if int(agent_id) == int(self.uid):
            return self.write_json(error.NOT_AGENT)

        agent = player_model.get_by_uid(self.share_db(), agent_id)
        if not agent:
            return self.write_json(error.NOT_AGENT)
        if agent['custom_type'] == 0:
            return self.write_json(error.NOT_AGENT)

        count = player_model.bind_agent(self.share_db(), self.uid, agent['agent_id'], agent_id, agent['hierarchical'])
        if count == 0:
            return self.write_json(error.SYSTEM_ERR)

        player_model.add_diamonds_with_log(self.share_db(), self.share_db_logs(), self.uid, BIND_DIAMOND,
                                           agent_id, agent['nick_name'], const.REASON_BIND, player['diamond'])

        return self.write_json(error.OK)
