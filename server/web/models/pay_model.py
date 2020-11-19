def get_item_by_id(conn, item_id):
    sql = f"SELECT * FROM `configdetailed` WHERE id='{item_id}' LIMIT 1"
    return conn.get(sql)


def insert_order(conn, uid, order_id, order_price, order_type, give_number, product_id, order_num):
    sql = f"INSERT INTO `Orders` SET Userinfoid={uid}," \
          f"Ordernum='{order_id}',Orderprice={order_price},Ordertype={order_type}," \
          f"Paystates=0,Ordertates=1,Ordernumber={order_num},Givenumber={give_number}," \
          f"Productid={product_id},Creationtime=now()"
    return conn.execute_rowcount(sql)
