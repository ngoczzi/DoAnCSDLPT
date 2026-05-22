import csv
import json
import random
from pathlib import Path
from datetime import datetime, timedelta


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

NUM_PRODUCTS = 200
NUM_CUSTOMERS = 3000
NUM_ORDERS = 10000
NUM_REVIEWS = 50000

random.seed(42)

PRODUCT_NAMES = [
    "Wireless Mouse",
    "Mechanical Keyboard",
    "Bluetooth Speaker",
    "USB-C Cable",
    "Laptop Stand",
    "Gaming Headset",
    "Portable SSD",
    "Smart Watch",
    "Power Bank",
    "Webcam",
    "Monitor 24 inch",
    "Monitor 27 inch",
    "External HDD",
    "Wireless Charger",
    "Tablet Case",
    "Phone Case",
    "HDMI Cable",
    "Office Chair",
    "Desk Lamp",
    "Microphone"
]

COMMENTS = [
    "Good product",
    "Very useful",
    "Average quality",
    "Worth the price",
    "Not satisfied",
    "Fast delivery",
    "Excellent",
    "Could be better",
    "The product works well",
    "I will buy again",
    "Nice design",
    "Battery life is good",
    "Quality is acceptable",
    "The packaging was damaged",
    "Highly recommended"
]


def create_products():
    products = []

    for i in range(1, NUM_PRODUCTS + 1):
        base_name = random.choice(PRODUCT_NAMES)

        products.append({
            "product_id": f"P{i:03d}",
            "product_name": f"{base_name} {i:03d}",
            "price": random.randint(50, 500) * 1000
        })

    return products


def generate_orders_csv(products):
    file_path = DATA_DIR / "orders.csv"

    with open(file_path, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        writer.writerow([
            "order_id",
            "product_id",
            "product_name",
            "customer_id",
            "quantity",
            "price",
            "order_date"
        ])

        for i in range(1, NUM_ORDERS + 1):
            product = random.choice(products)

            order_date = datetime(2025, 1, 1) + timedelta(
                days=random.randint(0, 120)
            )

            writer.writerow([
                f"O{i:06d}",
                product["product_id"],
                product["product_name"],
                f"C{random.randint(1, NUM_CUSTOMERS):04d}",
                random.randint(1, 5),
                product["price"],
                order_date.strftime("%Y-%m-%d")
            ])

    print(f"Created {file_path}")


def generate_reviews_json(products):
    reviews = []

    for i in range(1, NUM_REVIEWS + 1):
        product = random.choice(products)

        review_date = datetime(2025, 1, 1) + timedelta(
            days=random.randint(0, 150),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59),
            seconds=random.randint(0, 59)
        )

        review = {
            "review_id": f"R{i:06d}",
            "product_id": product["product_id"],
            "user_id": f"C{random.randint(1, NUM_CUSTOMERS):04d}",
            "rating": random.randint(1, 5),
            "comment": random.choice(COMMENTS),
            "review_date": review_date.strftime("%Y-%m-%d %H:%M:%S")
        }

        # Một số field tùy chọn để thể hiện schema-less của NoSQL JSON
        if random.random() < 0.35:
            review["verified_purchase"] = random.choice([True, False])

        if random.random() < 0.25:
            review["device"] = random.choice(["mobile", "web", "tablet"])

        if random.random() < 0.10:
            review["images"] = [f"img_{random.randint(1, 1000)}.jpg"]

        reviews.append(review)

    file_path = DATA_DIR / "product_reviews.json"

    with open(file_path, mode="w", encoding="utf-8") as file:
        json.dump(reviews, file, indent=2, ensure_ascii=False)

    print(f"Created {file_path}")


def main():
    print("Generating dataset...")

    products = create_products()

    generate_orders_csv(products)
    generate_reviews_json(products)

    print("Dataset generated successfully.")
    print(f"Number of products: {NUM_PRODUCTS}")
    print(f"Number of orders: {NUM_ORDERS}")
    print(f"Number of reviews: {NUM_REVIEWS}")


if __name__ == "__main__":
    main()