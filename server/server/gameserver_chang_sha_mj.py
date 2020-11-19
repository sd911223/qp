# coding:utf-8
from base import const
from base.init import start

if __name__ == '__main__':
    from games.cs_ma_jiang.game import GameServer

    start(GameServer, const.SERVICE_CSMJ, __file__[0:-3])
