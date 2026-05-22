import json
import hashlib
import sys
from collections import defaultdict
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
NODES_DIR = DATA_DIR / "nodes"

REVIEWS_FILE = DATA_DIR / "product_reviews.json"


def stable_hash(value):
    return int(hashlib.md5(value.encode("utf-8")).hexdigest(), 16)


def build_review_kv_nodes(node_count=3, replication_factor=2):
    NODES_DIR.mkdir(exist_ok=True)

    for old_file in NODES_DIR.glob("review_node_*.json"):
        old_file.unlink()

    with open(REVIEWS_FILE, "r", encoding="utf-8") as file:
        reviews = json.load(file)

    node_maps = [defaultdict(list) for _ in range(node_count)]
    primary_distribution = {str(i + 1): set() for i in range(node_count)}

    invalid_records = 0

    for review in reviews:
        required_fields = ["review_id", "product_id", "rating", "review_date"]

        if not all(field in review for field in required_fields):
            invalid_records += 1
            continue

        product_id = review["product_id"]
        primary_index = stable_hash(product_id) % node_count

        primary_distribution[str(primary_index + 1)].add(product_id)

        # Replication factor = 2:
        # review được lưu ở primary node và 1 replica node kế tiếp
        for offset in range(replication_factor):
            node_index = (primary_index + offset) % node_count
            node_maps[node_index][product_id].append(review)

    for index, node_map in enumerate(node_maps, start=1):
        node_file = NODES_DIR / f"review_node_{index}.json"

        serializable_node = {
            product_id: node_map[product_id]
            for product_id in sorted(node_map.keys())
        }

        with open(node_file, "w", encoding="utf-8") as file:
            json.dump(serializable_node, file, indent=2, ensure_ascii=False)

        print(f"Created {node_file} with {len(serializable_node)} product keys")

    metadata = {
        "node_count": node_count,
        "replication_factor": replication_factor,
        "partition_strategy": "md5(product_id) % node_count",
        "primary_key_distribution": {
            node_id: len(keys)
            for node_id, keys in primary_distribution.items()
        },
        "invalid_records": invalid_records
    }

    metadata_file = NODES_DIR / "cluster_metadata.json"

    with open(metadata_file, "w", encoding="utf-8") as file:
        json.dump(metadata, file, indent=2, ensure_ascii=False)

    print(f"Created {metadata_file}")
    print("Review KV nodes generated successfully.")


if __name__ == "__main__":
    node_count = 3

    if len(sys.argv) >= 2:
        node_count = int(sys.argv[1])

    build_review_kv_nodes(node_count=node_count, replication_factor=2)