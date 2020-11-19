from models import table_name
from models import database


def _rewrite_config(params, data, platform, channel_id):
    assert type(params) is dict
    for item in data:
        if not item:
            continue
        if item.get("platform") != platform:
            continue
        if item.get("channel_id") != channel_id:
            continue
        if not item.get('name'):
            continue
        params[item.get('name')] = database.resume_int(item.get('value'))


def _format_channel_configs(data, platform, channel_id):
    if not data:
        return {}
    result = {}
    _rewrite_config(result, data, 0, 0)
    _rewrite_config(result, data, platform, 0)
    _rewrite_config(result, data, platform, channel_id)
    return result


def get_by_key(platform, channel_id, key):
    key = database.escape(key)
    platform = int(platform)
    channel_id = int(channel_id)
    sql = "SELECT * FROM `{0}` WHERE `name`='{1}' AND " \
          "((platform=0 AND channel_id=0) OR (platform={2} AND channel_id=0) OR (platform={3} AND channel_id={4}))"
    sql = sql.format(table_name.channel_configs, key, platform, platform, channel_id)
    result = _format_channel_configs(database.share_db().query(sql), platform, channel_id)
    data = result.get(key)
    return database.resume_bool(data)
