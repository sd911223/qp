from models import table_name
from models.database import share_db


def get_lottery_configs():
    sql = "SELECT * FROM `{0}`".format(table_name.lottery)
    configs = share_db().query(sql)
    if not configs or len(configs) == 0:
        configs = [{'id': 1, 'round': 8, 'diamond': 1, 'count': 7740},
                   {'id': 2, 'round': 8, 'diamond': 2, 'count': 1140},
                   {'id': 3, 'round': 8, 'diamond': 8, 'count': 1018},
                   {'id': 4, 'round': 8, 'diamond': 18, 'count': 102},
                   {'id': 5, 'round': 16, 'diamond': 2, 'count': 7255},
                   {'id': 6, 'round': 16, 'diamond': 8, 'count': 2455},
                   {'id': 7, 'round': 16, 'diamond': 18, 'count': 281},
                   {'id': 8, 'round': 16, 'diamond': 88, 'count': 9}]
    return configs


def make_lottery(round_count):
    configs = get_lottery_configs()
    lotteries = []
    for lottery in configs:
        if lottery['round'] == round_count:
            for _ in range(1, lottery['count'] + 1):
                lotteries.append(lottery['diamond'])
    return lotteries
