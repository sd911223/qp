# coding:utf-8
from base import const
from base.init import start

if __name__ == '__main__':
    from games.pao_de_kuai.game import GameServer

    start(GameServer, const.SERVICE_PDK, __file__[0:-3])
