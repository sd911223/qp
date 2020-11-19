# coding:utf-8
from base import const
from base.init import start

if __name__ == '__main__':
    from games.niu_niu.game import GameServer

    start(GameServer, const.SERVICE_NIU_NIU, __file__[0:-3])
