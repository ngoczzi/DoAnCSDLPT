import json
from pathlib import Path

from repositories.order_repository import OrderRepository
from repositories.distributed_review_store import DistributedReviewStore
from mediation_layer import MediationLayer


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"


def build_mediation_layer():
    order_repository = OrderRepository(DATA_DIR / "orders.csv")

    review_store = DistributedReviewStore(
        nodes_dir=DATA_DIR / "nodes",
        simulated_latency=0.01
    )

    return MediationLayer(order_repository, review_store), review_store


def simulate_node_down():
    print("\n[Failure Test] Review node down")

    node_file = DATA_DIR / "nodes" / "review_node_1.json"
    backup_file = DATA_DIR / "nodes" / "review_node_1.json.bak"

    node_file.rename(backup_file)

    try:
        mediation_layer, review_store = build_mediation_layer()
        result = mediation_layer.query_batch_kv(top_n=10, review_limit=5)

        print("System did not crash.")
        print(f"Returned products: {len(result)}")
        print(f"Failed node reads: {review_store.metrics['failed_node_reads']}")

    finally:
        backup_file.rename(node_file)


def simulate_corrupted_json():
    print("\n[Failure Test] Corrupted JSON node")

    node_file = DATA_DIR / "nodes" / "review_node_2.json"

    original_content = node_file.read_text(encoding="utf-8")

    try:
        node_file.write_text("{ corrupted json file ", encoding="utf-8")

        mediation_layer, review_store = build_mediation_layer()
        result = mediation_layer.query_batch_kv(top_n=10, review_limit=5)

        print("System handled corrupted JSON.")
        print(f"Returned products: {len(result)}")
        print(f"Failed node reads: {review_store.metrics['failed_node_reads']}")

    finally:
        node_file.write_text(original_content, encoding="utf-8")


def simulate_duplicate_review_conflict():
    print("\n[Failure Test] Duplicate review_id conflict")

    node_file = DATA_DIR / "nodes" / "review_node_3.json"

    original_content = node_file.read_text(encoding="utf-8")
    node_data = json.loads(original_content)

    try:
        selected_product_id = None

        for product_id, reviews in node_data.items():
            if reviews:
                selected_product_id = product_id
                old_review = reviews[0]
                break

        if selected_product_id is None:
            print("No review found for duplicate test.")
            return

        duplicated_review = dict(old_review)
        duplicated_review["rating"] = 1
        duplicated_review["comment"] = "Conflict version - newer review wins"
        duplicated_review["review_date"] = "2026-01-01 00:00:00"

        node_data[selected_product_id].append(duplicated_review)

        node_file.write_text(
            json.dumps(node_data, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

        review_store = DistributedReviewStore(DATA_DIR / "nodes")
        reviews = review_store.get_reviews_by_product(
            selected_product_id,
            limit=5
        )

        print(f"Test product_id: {selected_product_id}")
        print("Latest review after conflict resolution:")
        print(reviews[0])

    finally:
        node_file.write_text(original_content, encoding="utf-8")


if __name__ == "__main__":
    simulate_node_down()
    simulate_corrupted_json()
    simulate_duplicate_review_conflict()