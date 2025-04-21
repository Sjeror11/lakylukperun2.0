import statistics
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple

from ... import config
from ...utils.logger import log
from ...utils.exceptions import OptimizationServiceError, MemoryQueryError
from ...models.memory_entry import MemoryEntry, MemoryEntryType
from ..memory_service.storage import MemoryStorage

# --- Constants ---
OPTIMIZATION_SERVICE_SOURCE = "OptimizationService"
MIN_LATENCY_SAMPLES = 10 # Minimum number of data points needed for meaningful analysis

class FrequencyAnalyzer:
    """
    Analyzes historical system latencies (pipeline, execution) and market volatility
    to determine an optimal trading frequency.
    """

    def __init__(self, memory_storage: MemoryStorage):
        self.memory = memory_storage
        log.info("FrequencyAnalyzer initialized.")

    def _query_latency_metrics(self, metric_name: str, days_history: int) -> List[float]:
        """Queries specific latency metrics from memory storage."""
        latencies: List[float] = []
        time_start = datetime.now(timezone.utc) - timedelta(days=days_history)
        log.debug(f"Querying '{metric_name}' metrics from memory since {time_start}...")

        try:
            # Query memory for metric entries
            # Assuming latency is stored in payload['value'] or similar
            # Flags might be used to identify metrics, e.g., 'M'
            query_results = self.memory.query_memories(
                time_start=time_start,
                flags_include="M", # Assuming 'M' flag for Metric
                # Add content keyword search if metric name is in payload
                # content_keywords=[metric_name] # This would be slow without indexing
                max_results=10000 # Limit query size for performance
            )

            files_processed = 0
            for filename, _ in query_results:
                 try:
                      entry = self.memory.read_memory("cur", filename)
                      if entry.entry_type == MemoryEntryType.METRIC and entry.payload.get("name") == metric_name:
                           value = entry.payload.get("value")
                           if isinstance(value, (int, float)):
                                latencies.append(float(value))
                           else:
                                log.warning(f"Invalid value type for metric '{metric_name}' in {filename}: {type(value)}")
                      files_processed += 1
                 except Exception as e:
                      log.error(f"Error reading or processing metric memory file {filename}: {e}", exc_info=True)
                      continue # Skip corrupted entries

            log.info(f"Found {len(latencies)} valid '{metric_name}' metrics out of {files_processed} processed entries.")
            return latencies

        except MemoryQueryError as e:
            log.error(f"Failed to query memory for '{metric_name}' metrics: {e}", exc_info=True)
            raise OptimizationServiceError(f"Memory query failed for {metric_name}: {e}") from e
        except Exception as e:
            log.error(f"Unexpected error querying '{metric_name}' metrics: {e}", exc_info=True)
            raise OptimizationServiceError(f"Unexpected error querying {metric_name}: {e}") from e


    def calculate_optimal_frequency(
        self,
        days_history: int = config.OPTIMIZATION_MEMORY_QUERY_DAYS,
        min_frequency_sec: int = config.OPTIMIZATION_MIN_FREQUENCY,
        buffer_factor: float = config.OPTIMIZATION_FREQUENCY_BUFFER_FACTOR
        ) -> Optional[int]:
        """
        Calculates the optimal trading frequency based on historical latencies.

        Args:
            days_history: How many days of historical metrics to analyze.
            min_frequency_sec: The minimum allowed frequency in seconds.
            buffer_factor: A safety multiplier applied to the calculated latency sum.

        Returns:
            The calculated optimal frequency in seconds, or None if calculation fails.
        """
        log.info("Calculating optimal trading frequency...")

        try:
            # 1. Query Latencies from Memory
            # Assuming 'pipeline_latency_ms' and 'execution_latency_ms' are stored
            pipeline_latencies_ms = self._query_latency_metrics("pipeline_latency_ms", days_history)
            execution_latencies_ms = self._query_latency_metrics("execution_latency_ms", days_history)

            if len(pipeline_latencies_ms) < MIN_LATENCY_SAMPLES or len(execution_latencies_ms) < MIN_LATENCY_SAMPLES:
                log.warning(f"Insufficient latency data (Pipeline: {len(pipeline_latencies_ms)}, Execution: {len(execution_latencies_ms)}). Need at least {MIN_LATENCY_SAMPLES}. Cannot calculate optimal frequency.")
                return None

            # 2. Calculate Latency Statistics (e.g., median or 95th percentile)
            # Using median is often more robust to outliers than average
            median_pipeline_latency_ms = statistics.median(pipeline_latencies_ms)
            median_execution_latency_ms = statistics.median(execution_latencies_ms)
            log.debug(f"Median Pipeline Latency: {median_pipeline_latency_ms:.2f} ms")
            log.debug(f"Median Execution Latency: {median_execution_latency_ms:.2f} ms")

            # 3. Calculate Target Frequency
            total_latency_sec = (median_pipeline_latency_ms + median_execution_latency_ms) / 1000.0
            target_frequency_sec = total_latency_sec * buffer_factor
            log.debug(f"Total Median Latency: {total_latency_sec:.3f} s")
            log.debug(f"Target Frequency (Latency * Buffer Factor {buffer_factor}): {target_frequency_sec:.3f} s")

            # 4. Apply Minimum Frequency Constraint
            optimal_frequency_sec = max(min_frequency_sec, target_frequency_sec)
            # Round to nearest integer second
            optimal_frequency_sec = int(round(optimal_frequency_sec))

            log.info(f"Calculated Optimal Trading Frequency: {optimal_frequency_sec} seconds (Min Freq: {min_frequency_sec}s)")

            # 5. Save Analysis to Memory
            analysis_payload = {
                "calculation_timestamp": datetime.now(timezone.utc).isoformat(),
                "days_history_analyzed": days_history,
                "pipeline_latency_samples": len(pipeline_latencies_ms),
                "execution_latency_samples": len(execution_latencies_ms),
                "median_pipeline_latency_ms": median_pipeline_latency_ms,
                "median_execution_latency_ms": median_execution_latency_ms,
                "buffer_factor_used": buffer_factor,
                "min_frequency_constraint_sec": min_frequency_sec,
                "calculated_optimal_frequency_sec": optimal_frequency_sec,
                # TODO: Add volatility metric used if incorporated later
            }
            analysis_entry = MemoryEntry(
                entry_type=MemoryEntryType.OPTIMIZATION_RUN, # Or a specific FREQUENCY_ANALYSIS type
                source_service=OPTIMIZATION_SERVICE_SOURCE,
                payload=analysis_payload
            )
            try:
                self.memory.save_memory(analysis_entry)
            except MemoryServiceError as mem_err:
                 log.error(f"Failed to save frequency analysis memory entry: {mem_err}")


            return optimal_frequency_sec

        except OptimizationServiceError as e:
             # Errors querying memory are already logged
             log.error(f"Failed to calculate optimal frequency due to service error: {e}")
             return None
        except statistics.StatisticsError as e:
             log.error(f"Statistical error calculating frequency (likely insufficient data): {e}", exc_info=True)
             return None
        except Exception as e:
            log.critical(f"Unexpected critical error calculating optimal frequency: {e}", exc_info=True)
            # Save critical error memory entry?
            return None

# Example Usage (Requires MemoryStorage with relevant metric data)
# if __name__ == '__main__':
#     print("Testing FrequencyAnalyzer...")
#     # Requires MemoryStorage instance
#     # Need to populate 'cur' dir with dummy METRIC memory files for testing

#     # --- Setup Mocks/Dummies ---
#     from unittest.mock import MagicMock
#     mock_storage = MagicMock(spec=MemoryStorage)

#     # Mock query results
#     def mock_query(*args, **kwargs):
#         # Simulate finding metric files based on keywords (crude)
#         keywords = kwargs.get('content_keywords', [])
#         results = []
#         if keywords and "pipeline_latency_ms" in keywords[0]:
#             # Return dummy pipeline latencies (filename, parsed_info)
#             results = [ (f"pipe_{i}.dat", {}) for i in range(20) ]
#         elif keywords and "execution_latency_ms" in keywords[0]:
#             # Return dummy execution latencies
#             results = [ (f"exec_{i}.dat", {}) for i in range(20) ]
#         return results

#     # Mock read results
#     def mock_read(directory, filename):
#         entry_type = MemoryEntryType.METRIC
#         payload = {}
#         if filename.startswith("pipe_"):
#             payload = {"name": "pipeline_latency_ms", "value": 150 + int(filename.split('_')[1]) * 5} # Simulate values 150-245ms
#         elif filename.startswith("exec_"):
#             payload = {"name": "execution_latency_ms", "value": 50 + int(filename.split('_')[1]) * 2} # Simulate values 50-88ms
#         return MemoryEntry(entry_type=entry_type, source_service="Mock", payload=payload)

#     # Apply mocks (adjust based on actual query implementation)
#     # This assumes query_memories uses content_keywords which is slow.
#     # A better mock would simulate flag-based or index-based querying.
#     # For now, we'll mock _query_latency_metrics directly.

#     mock_analyzer_instance = FrequencyAnalyzer(mock_storage)
#     mock_analyzer_instance._query_latency_metrics = MagicMock()

#     def query_side_effect(metric_name, days_history):
#         if metric_name == "pipeline_latency_ms":
#             return [150.0 + i * 5 for i in range(20)] # 150-245ms
#         elif metric_name == "execution_latency_ms":
#             return [50.0 + i * 2 for i in range(20)] # 50-88ms
#         return []
#     mock_analyzer_instance._query_latency_metrics.side_effect = query_side_effect
#     mock_storage.save_memory.return_value = "mock_analysis_filename" # Mock saving analysis

#     # --- End Setup ---

#     try:
#         print("Calculating optimal frequency...")
#         optimal_freq = mock_analyzer_instance.calculate_optimal_frequency()

#         if optimal_freq is not None:
#             print(f"\nCalculated Optimal Frequency: {optimal_freq} seconds")
#             # Check if analysis was saved
#             mock_storage.save_memory.assert_called_once()
#             saved_payload = mock_storage.save_memory.call_args[0][0].payload
#             print("Analysis Payload Saved:")
#             print(json.dumps(saved_payload, indent=2))
#             assert saved_payload["calculated_optimal_frequency_sec"] == optimal_freq
#         else:
#             print("\nFailed to calculate optimal frequency.")

#     except Exception as e:
#         print(f"\nError during FrequencyAnalyzer test: {e}")
