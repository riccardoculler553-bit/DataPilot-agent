from unittest import result

from app.database.repository import ProductRepository



def main():
    repository = ProductRepository()

    count = repository.get_product_count()

    print(f"商品数量：{count}")


if __name__ == "__main__":
    main()