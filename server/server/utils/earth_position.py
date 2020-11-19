from math import radians, cos, sin, asin, sqrt

X_NA = 181  # 未知经度, 经度最大值只有180, 181表示未知
Y_NA = 91  # 未知纬度, 纬度最大值只有90, 91表示未知
DISTANCE_UNKNOWN = -1  # 未知距离


def calc_earth_distance(lon1, lat1, lon2, lat2):
    """
    计算两个给定的坐标之间的物理距离
    两组经纬度中, 有任意一个值不正确, 则直接返回 -1 为未知距离
    :param lon1: 经度1 
    :param lat1: 纬度1
    :param lon2: 经度2
    :param lat2: 纬度2
    :return: number 米
    """
    if lon1 is None or lat1 is None or lon2 is None or lat2 is None:
        return DISTANCE_UNKNOWN
    if lon1 == X_NA or lon2 == X_NA:
        return DISTANCE_UNKNOWN
    if lat1 == Y_NA or lat2 == Y_NA:
        return DISTANCE_UNKNOWN
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])  # 将十进制度数转化为弧度
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2  # haversine公式
    c = 2 * asin(sqrt(a))
    r = 6371.393  # 地球平均半径，单位为公里
    return int(c * r * 1000)
