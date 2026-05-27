import csv
import json
import sys
import time
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR))
sys.path.append(str(BASE_DIR / "scripts"))

from build_review_kv_nodes import build_review_kv_nodes
from repositories.order_repository import OrderRepository
from repositories.distributed_review_store import DistributedReviewStore
from mediation_layer import MediationLayer


DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


def run_scalability_test():
    rows = []

    for node_count in [2, 3, 4, 5]:
        print(f"Testing with {node_count} nodes...")

        build_review_kv_nodes(node_count=node_count, replication_factor=2)

        order_repository = OrderRepository(DATA_DIR / "orders.csv")
        review_store = DistributedReviewStore(
            nodes_dir=DATA_DIR / "nodes",
            simulated_latency=0.01
        )

        mediation_layer = MediationLayer(order_repository, review_store)

        start = time.perf_counter()
        mediation_layer.query_batch_kv(top_n=10, review_limit=5)
        end = time.perf_counter()

        metadata_file = DATA_DIR / "nodes" / "cluster_metadata.json"

        with open(metadata_file, "r", encoding="utf-8") as file:
            metadata = json.load(file)

        distribution = metadata["primary_key_distribution"]

        key_counts = list(distribution.values())

        rows.append({
            "node_count": node_count,
            "replication_factor": metadata["replication_factor"],
            "avg_primary_keys_per_node": sum(key_counts) / len(key_counts),
            "max_primary_keys_on_node": max(key_counts),
            "min_primary_keys_on_node": min(key_counts),
            "query_time_ms": (end - start) * 1000,
            "node_file_reads": review_store.metrics["node_file_reads"]
        })

    output_file = OUTPUT_DIR / "scalability_result.csv"

    with open(output_file, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"Saved {output_file}")


if __name__ == "__main__":
    run_scalability_test()