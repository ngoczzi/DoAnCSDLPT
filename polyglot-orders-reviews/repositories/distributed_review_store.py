import json
import time
import hashlib
from pathlib import Path
from datetime import datetime
from collections import defaultdict


class DistributedReviewStore:
    def __init__(
        self,
        nodes_dir,
        node_count=None,
        replication_factor=2,
        simulated_latency=0.0
    ):
        self.nodes_dir = Path(nodes_dir)
        self.simulated_latency = simulated_latency
        self.metrics = {}

        metadata_file = self.nodes_dir / "cluster_metadata.json"

        if metadata_file.exists():
            with open(metadata_file, "r", encoding="utf-8") as file:
                metadata = json.load(file)

            self.node_count = metadata.get("node_count", node_count or 3)
            self.replication_factor = metadata.get(
                "replication_factor",
                replication_factor
            )
        else:
            self.node_count = node_count or 3
            self.replication_factor = replication_factor

        self.reset_metrics()

    def reset_metrics(self):
        self.metrics = {
            "logical_review_queries": 0,
            "node_file_reads": 0,
            "failed_node_reads": 0
        }

    def stable_hash(self, value):
        return int(hashlib.md5(value.encode("utf-8")).hexdigest(), 16)

    def get_primary_node_index(self, product_id):
        return self.stable_hash(product_id) % self.node_count

    def get_candidate_nodes(self, product_id):
        primary = self.get_primary_node_index(product_id)

        return [
            (primary + offset) % self.node_count
            for offset in range(self.replication_factor)
        ]

    def get_node_file(self, node_index):
        return self.nodes_dir / f"review_node_{node_index + 1}.json"

    def load_node(self, node_index):
        time.sleep(self.simulated_latency)

        node_file = self.get_node_file(node_index)
        self.metrics["node_file_reads"] += 1

        try:
            with open(node_file, "r", encoding="utf-8") as file:
                return json.load(file)

        except FileNotFoundError:
            self.metrics["failed_node_reads"] += 1
            return {}

        except json.JSONDecodeError:
            self.metrics["failed_node_reads"] += 1
            return {}

    def parse_date(self, date_string):
        try:
            return datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
        except Exception:
            return datetime.min

    def remove_duplicate_reviews(self, reviews):
        unique_reviews = {}

        for review in reviews:
            review_id = review.get("review_id")

            if not review_id:
                continue

            if review_id not in unique_reviews:
                unique_reviews[review_id] = review
            else:
                old_review = unique_reviews[review_id]

                old_date = self.parse_date(old_review.get("review_date", ""))
                new_date = self.parse_date(review.get("review_date", ""))

                # Last Write Wins
                if new_date > old_date:
                    unique_reviews[review_id] = review

        return list(unique_reviews.values())

    def latest_reviews(self, reviews, limit=5):
        clean_reviews = self.remove_duplicate_reviews(reviews)

        clean_reviews.sort(
            key=lambda item: self.parse_date(item.get("review_date", "")),
            reverse=True
        )

        return clean_reviews[:limit]

    def get_reviews_by_product(self, product_id, limit=5):
        """
        N+1 query dùng hàm này nhiều lần.
        Mỗi product_id là một logical review query.
        """
        self.metrics["logical_review_queries"] += 1

        for node_index in self.get_candidate_nodes(product_id):
            node_data = self.load_node(node_index)
            reviews = node_data.get(product_id)

            if reviews:
                return self.latest_reviews(reviews, limit=limit)

        return []

    def batch_get_reviews(self, product_ids, limit=5):
        """
        Batch KV Query.
        Một logical query cho nhiều product_id.
        Tránh N+1 Query Problem.
        """
        self.metrics["logical_review_queries"] += 1

        result = {}
        node_cache = {}

        for product_id in product_ids:
            result[product_id] = []

            for node_index in self.get_candidate_nodes(product_id):
                if node_index not in node_cache:
                    node_cache[node_index] = self.load_node(node_index)

                reviews = node_cache[node_index].get(product_id)

                if reviews:
                    result[product_id] = self.latest_reviews(
                        reviews,
                        limit=limit
                    )
                    break

        return result

    def fetch_all_reviews_by_product(self, limit=5):
        """
        Fetch All Reviews.
        Đọc toàn bộ các node, sau đó gom theo product_id.
        Do có replication nên cần deduplicate.
        """
        self.metrics["logical_review_queries"] += 1

        grouped_reviews = defaultdict(list)

        for node_index in range(self.node_count):
            node_data = self.load_node(node_index)

            for product_id, reviews in node_data.items():
                grouped_reviews[product_id].extend(reviews)

        result = {}

        for product_id, reviews in grouped_reviews.items():
            result[product_id] = self.latest_reviews(reviews, limit=limit)

        return result