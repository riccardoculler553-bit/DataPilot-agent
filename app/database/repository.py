from app.database.connection import get_connection

class ProductRepository:
    """
    商品相关的数据访问。
    """
    def get_product_count(self):
        connection = get_connection()

        try:
            with connection.cursor() as cursor:
                cursor.execute("select count(*) as count from products")
                result = cursor.fetchall()

                return result[0]["count"]
        finally:
            connection.close()