from utils import utils
from models import player_model
import ujson as json
from urllib.parse import quote

BASE_URL = 'http://ytxy.jingangdp.com/'
REG_URL = BASE_URL + "UserInfosService.asmx/login?data="


def register(db, openid):
    player = player_model.get_by_openid(db, openid)
    if not player:
        return

    nick_name = player['nick_name']
    uid = player['uid']
    # union_id = player['unionid']
    avatar = player['avatar']
    invite_uid = player['invite_uid_2']

    if invite_uid == 0:
        params = {"UserName": nick_name, "UserId": uid, "WeixinOpenId": openid, "Imgpath": avatar}
    else:
        params = {"UserName": nick_name, "UserId": uid, "WeixinOpenId": openid, "Imgpath": avatar,
                  "FatherId": invite_uid}

    def suc_func(data):
        utils.log(str(data), 'outer-reg.txt')

    def fail_func():
        utils.log(f'FAIL : {uid}', 'outer-reg.txt')

    url = REG_URL + quote(json.dumps(params))
    utils.log(url, 'url.txt')
    utils.http_get(url, suc_func, fail_func)
