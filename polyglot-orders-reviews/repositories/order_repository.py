import csv
from collections import defaultdict

class OrderRepository:
    def __init__(self, file_path):
        self.file_path = file_path

    def get_top_products(self, limit=10):
        product_stats = defaultdict(lambda: {
            "product_id": "",
            "product_name": "",
            "total_quantity": 0,
            "total_revenue": 0,
            "order_count": 0
        })

        with open(self.file_path, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)

            for row in reader:
                product_id = row["product_id"]
                quantity = int(row["quantity"])
                price = int(row["price"])

                product_stats[product_id]["product_id"] = product_id
                product_stats[product_id]["product_name"] = row["product_name"]
                product_stats[product_id]["total_quantity"] += quantity
                product_stats[product_id]["total_revenue"] += quantity * price
                product_stats[product_id]["order_count"] += 1

        products = list(product_stats.values())

        products.sort(
            key=lambda item: item["total_quantity"],
            reverse=True
        )

        return products[:limit]