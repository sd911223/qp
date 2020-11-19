# coding:utf-8

from configs import error
from .comm_handler import CommHandler
from models import tables_model

from models.base_redis import share_connect as redis_conn


class GetAgentRoomList(CommHandler):
    def _request(self):
        room_info_list = tables_model.get_tables_by_owner_not_club(self.share_db(), self.uid)
        table_data = []
        for room_info in room_info_list:
            table_cache_data = tables_model.get_table_info(redis_conn(), room_info["tid"]) or {"player_list": [],
                                                                                               "round_index": 1,
                                                                                               "table_status": 0}

            if not table_cache_data:
                continue
            table_cache_data.update(room_info)
            table_data.append(table_cache_data)

        return self.write_json(error.OK, table_data)
