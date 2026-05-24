import json
from pathlib import Path

from repositories.order_repository import OrderRepository
from repositories.distributed_review_store import DistributedReviewStore
from mediation_layer import MediationLayer
from benchmark import benchmark_function


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


def print_sample_result(result):
    print("\nSample result:")
    print("-" * 80)

    for product in result[:3]:
        print(f"Product ID      : {product['product_id']}")
        print(f"Product Name    : {product['product_name']}")
        print(f"Total Quantity  : {product['total_quantity']}")
        print(f"Total Revenue   : {product['total_revenue']}")
        print(f"Order Count     : {product['order_count']}")
        print("Latest Reviews  :")

        for review in product["latest_reviews"]:
            print(
                f"  - {review.get('review_date')} | "
                f"Rating: {review.get('rating')} | "
                f"{review.get('comment')}"
            )

        print("-" * 80)


def main():
    order_repository = OrderRepository(DATA_DIR / "orders.csv")

    review_store = DistributedReviewStore(
        nodes_dir=DATA_DIR / "nodes",
        simulated_latency=0.02
    )

    mediation_layer = MediationLayer(
        order_repository=order_repository,
        review_store=review_store
    )

    benchmark_results = []

    benchmark_results.append(
        benchmark_function(
            "N+1 Query",
            lambda: mediation_layer.query_n_plus_1(top_n=10, review_limit=5),
            review_store
        )
    )

    benchmark_results.append(
        benchmark_function(
            "Fetch All Reviews",
            lambda: mediation_layer.query_fetch_all(top_n=10, review_limit=5),
            review_store
        )
    )

    benchmark_results.append(
        benchmark_function(
            "Batch KV Query",
            lambda: mediation_layer.query_batch_kv(top_n=10, review_limit=5),
            review_store
        )
    )

    print("\nBenchmark Results")
    print("=" * 100)

    for item in benchmark_results:
        print(
            f"{item['strategy']:<20} | "
            f"Time: {item['execution_time_ms']:.2f} ms | "
            f"Memory: {item['peak_memory_mb']:.2f} MB | "
            f"Logical Queries: {item['logical_review_queries']} | "
            f"Node Reads: {item['node_file_reads']} | "
            f"Failed Reads: {item['failed_node_reads']}"
        )

    summary = []

    for item in benchmark_results:
        summary.append({
            "strategy": item["strategy"],
            "execution_time_ms": item["execution_time_ms"],
            "peak_memory_mb": item["peak_memory_mb"],
            "logical_review_queries": item["logical_review_queries"],
            "node_file_reads": item["node_file_reads"],
            "failed_node_reads": item["failed_node_reads"]
        })

    with open(OUTPUT_DIR / "benchmark_result.json", "w", encoding="utf-8") as file:
        json.dump(summary, file, indent=2, ensure_ascii=False)

    with open(OUTPUT_DIR / "batch_query_result.json", "w", encoding="utf-8") as file:
        json.dump(
            benchmark_results[2]["result"],
            file,
            indent=2,
            ensure_ascii=False
        )

    print_sample_result(benchmark_results[2]["result"])

    print("\nSaved:")
    print("- output/benchmark_result.json")
    print("- output/batch_query_result.json")


if __name__ == "__main__":
    main()