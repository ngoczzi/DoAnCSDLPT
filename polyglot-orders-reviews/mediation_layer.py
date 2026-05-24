class MediationLayer:
    def __init__(self, order_repository, review_store):
        self.order_repository = order_repository
        self.review_store = review_store

    def query_n_plus_1(self, top_n=10, review_limit=5):
        """
        Strategy 1:
        1 query Orders + N query Reviews.
        """
        self.review_store.reset_metrics()

        top_products = self.order_repository.get_top_products(limit=top_n)

        result = []

        for product in top_products:
            product_id = product["product_id"]

            latest_reviews = self.review_store.get_reviews_by_product(
                product_id,
                limit=review_limit
            )

            result.append({
                **product,
                "latest_reviews": latest_reviews
            })

        return result

    def query_fetch_all(self, top_n=10, review_limit=5):
        """
        Strategy 2:
        Fetch all reviews from all nodes, then filter.
        """
        self.review_store.reset_metrics()

        top_products = self.order_repository.get_top_products(limit=top_n)

        all_reviews_map = self.review_store.fetch_all_reviews_by_product(
            limit=review_limit
        )

        result = []

        for product in top_products:
            product_id = product["product_id"]

            result.append({
                **product,
                "latest_reviews": all_reviews_map.get(product_id, [])
            })

        return result

    def query_batch_kv(self, top_n=10, review_limit=5):
        """
        Strategy 3:
        Batch KV Query.
        Đây là chiến lược chính được đề xuất.
        """
        self.review_store.reset_metrics()

        top_products = self.order_repository.get_top_products(limit=top_n)

        product_ids = [
            product["product_id"]
            for product in top_products
        ]

        reviews_map = self.review_store.batch_get_reviews(
            product_ids,
            limit=review_limit
        )

        result = []

        for product in top_products:
            product_id = product["product_id"]

            result.append({
                **product,
                "latest_reviews": reviews_map.get(product_id, [])
            })

        return result