import time
import tracemalloc

def benchmark_function(strategy_name, function, review_store):
    tracemalloc.start()

    start_time = time.perf_counter()

    result = function()

    end_time = time.perf_counter()

    current_memory, peak_memory = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    execution_time_ms = (end_time - start_time) * 1000
    peak_memory_mb = peak_memory / 1024 / 1024

    return {
        "strategy": strategy_name,
        "execution_time_ms": execution_time_ms,
        "peak_memory_mb": peak_memory_mb,
        "logical_review_queries": review_store.metrics["logical_review_queries"],
        "node_file_reads": review_store.metrics["node_file_reads"],
        "failed_node_reads": review_store.metrics["failed_node_reads"],
        "result": result
    }