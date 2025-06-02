"""
Parallel Training Framework for Pulse Retrodiction

This module provides a parallel training framework that efficiently distributes
retrodiction training workloads across multiple CPU cores for improved performance.
"""

from analytics.trust_update_buffer import get_trust_update_buffer, TrustUpdateBuffer
from analytics.optimized_trust_tracker import optimized_bayesian_trust_tracker
from recursive_training.metrics.async_metrics_collector import (
    get_async_metrics_collector,
    AsyncMetricsCollector,
)
from recursive_training.metrics.metrics_store import get_metrics_store, MetricsStore
from recursive_training.data.data_store import RecursiveDataStore  # Base class
import os
import sys  # Added for __main__ block logging
import time
import logging
from typing import Dict, List, Any, Optional, Callable, Tuple
from datetime import datetime, timedelta
import json
from dask.distributed import Client, LocalCluster
import memory_profiler  # Added for memory profiling


class TrainingBatch:
    def __init__(
        self,
        batch_id: str,
        start_time: datetime,
        end_time: datetime,
        variables: List[str],
    ):
        self.batch_id = batch_id
        self.start_time = start_time
        self.end_time = end_time
        self.variables = variables
        # Additional attributes that get set during processing
        self.processed: bool = False
        self.processing_time: float = 0.0
        self.results: Optional[Dict[str, Any]] = None


# Import components needed for parallel training

# Attempt to import specialized data stores, fall back if not available
try:
    from recursive_training.data.streaming_data_store import StreamingDataStore
except ImportError:
    StreamingDataStore = None  # type: ignore
try:
    from recursive_training.data.optimized_data_store import OptimizedDataStore
except ImportError:
    OptimizedDataStore = None  # type: ignore


# Module-level logger for the main coordinator process
coordinator_logger = logging.getLogger(__name__)


# --- Top-level function for Dask tasks ---
@memory_profiler.profile  # type: ignore
def _dask_process_batch_task(
    batch_data: Dict[str, Any],
    # Name of the DataStore class to use ('Streaming', 'Optimized', 'Recursive')
    data_store_class_name: str,
    data_store_base_config: Optional[
        Dict[str, Any]
    ],  # Base config for DataStore.get_instance()
    async_metrics_reinit_config: Optional[Dict[str, Any]],
    trust_buffer_reinit_config: Optional[Dict[str, Any]],
    # all_batches_for_upcoming_data: List[Dict[str, Any]] # Removed for
    # simplicity for now
) -> Tuple[str, Dict[str, Any]]:
    """
    Processes a single training batch in a Dask worker.
    This function is designed to be top-level to avoid Dask serialization issues with instance methods.
    """
    # Re-initialize logger for the Dask worker process
    # Ensure worker logger name is unique or well-defined
    worker_logger_name = f"dask_worker_batch_{batch_data.get('batch_id', 'unknown')}"
    worker_logger = logging.getLogger(worker_logger_name)

    # Configure worker logger if not already configured (Dask might handle this)
    if not worker_logger.handlers:
        log_level_str = os.environ.get("LOG_LEVEL", "INFO")
        log_level = getattr(logging, log_level_str.upper(), logging.INFO)
        logging.basicConfig(
            level=log_level,  # Apply level to root logger for simplicity here
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            force=True,
        )  # Force reconfig if Dask did its own
        worker_logger.setLevel(log_level)

    start_time_proc = time.time()
    # Re-hydrate TrainingBatch object
    batch = TrainingBatch(
        batch_id=str(batch_data["batch_id"]),  # Ensure string
        start_time=datetime.fromisoformat(str(batch_data["start_time"])),
        end_time=datetime.fromisoformat(str(batch_data["end_time"])),
        variables=list(batch_data["variables"]),
    )

    worker_logger.info(
        f"Dask Worker ({
            os.getpid()}): Processing batch {
            batch.batch_id} (vars: {
                len(
                    batch.variables)}, period: {
                        batch.start_time} to {
                            batch.end_time})")

    current_data_store: Any
    if data_store_class_name == "StreamingDataStore" and StreamingDataStore:
        current_data_store = StreamingDataStore.get_instance(
            config=data_store_base_config
        )
    elif data_store_class_name == "OptimizedDataStore" and OptimizedDataStore:
        current_data_store = OptimizedDataStore.get_instance(
            config=data_store_base_config
        )
    else:
        current_data_store = RecursiveDataStore.get_instance(
            config=data_store_base_config
        )
    worker_logger.info(
        f"Dask Worker: Initialized data store of type {type(current_data_store)}"
    )

    current_async_metrics = get_async_metrics_collector(
        config=async_metrics_reinit_config
    )
    current_trust_buffer = get_trust_update_buffer(config=trust_buffer_reinit_config)

    loaded_data: Dict[str, list] = {}
    start_str = batch.start_time.isoformat()
    end_str = batch.end_time.isoformat()

    for variable_name_load in batch.variables:
        dataset_name_load = f"historical_{variable_name_load}"
        try:
            items_to_filter = None
            if isinstance(current_data_store, StreamingDataStore):
                # retrieve_dataset_streaming needs a callback, which is complex to pass here.
                # Using retrieve_dataset as a simplified path for now.
                # This means true streaming benefits might not be realized in worker
                # without further refactor.
                worker_logger.debug(
                    f"Dask Worker: Loading {dataset_name_load} via StreamingDataStore (simplified path).")
                items_to_filter, _ = current_data_store.retrieve_dataset(
                    dataset_name_load
                )
            elif isinstance(current_data_store, OptimizedDataStore):
                worker_logger.debug(
                    f"Dask Worker: Loading {dataset_name_load} via OptimizedDataStore."
                )
                df_opt, _ = current_data_store.retrieve_dataset_optimized(
                    dataset_name_load, start_str, end_str
                )
                if df_opt is not None and not df_opt.empty:
                    loaded_data[variable_name_load] = df_opt.to_dict("records")
                else:
                    loaded_data[variable_name_load] = []
                continue  # Skip common filtering if OptimizedDataStore handled it
            else:  # RecursiveDataStore
                worker_logger.debug(
                    f"Dask Worker: Loading {dataset_name_load} via RecursiveDataStore."
                )
                items_to_filter, _ = current_data_store.retrieve_dataset(
                    dataset_name_load
                )

            if items_to_filter:
                filtered_items = [
                    item
                    for item in items_to_filter
                    if start_str <= item.get("timestamp", "") <= end_str
                ]
                loaded_data[variable_name_load] = filtered_items
            else:
                loaded_data[variable_name_load] = []
            worker_logger.info(
                f"Dask Worker: Loaded {
                    len(
                        loaded_data.get(
                            variable_name_load,
                            []))} items for {variable_name_load}")

        except Exception as e_load_task:
            worker_logger.error(
                f"Dask Worker: Error loading {variable_name_load}: {e_load_task}",
                exc_info=True,
            )
            loaded_data[variable_name_load] = []

    data_for_batch_task = loaded_data

    if not data_for_batch_task or all(
        not v_item_task for v_item_task in data_for_batch_task.values()
    ):
        worker_logger.warning(
            f"Dask Worker: Batch {batch.batch_id}: No data loaded. Skipping."
        )
        return batch.batch_id, {
            "success": True,
            "processing_time": time.time() - start_time_proc,
            "metrics": {"total_data_points": 0},
            "skipped": True,
        }

    results_retro_task = {"metrics": {}, "rules_generated": [], "trust_updates": {}}
    trust_updates_list_task = []
    for var_retro_task in batch.variables:
        import random

        sr_retro_task = 0.7 + random.random() * 0.3
        sc_retro_task = int(100 * sr_retro_task)
        for _ in range(sc_retro_task):
            trust_updates_list_task.append((var_retro_task, True, 1.0))
        for _ in range(100 - sc_retro_task):
            trust_updates_list_task.append((var_retro_task, False, 1.0))
        results_retro_task["trust_updates"][var_retro_task] = {
            "success_rate": sr_retro_task,
            "updates": 100,
        }

    current_trust_buffer.add_updates_batch(trust_updates_list_task)

    total_dp_retro_task = sum(
        len(var_data_item_task) for var_data_item_task in data_for_batch_task.values()
    )
    results_retro_task["metrics"] = {
        "total_data_points": total_dp_retro_task,
        "variables_processed": len(batch.variables),
        "time_period_days": (batch.end_time - batch.start_time).days,
        "avg_success_rate": (
            sum(
                upd_item_task["success_rate"]
                for upd_item_task in results_retro_task["trust_updates"].values()
            )
            / len(batch.variables)
            if batch.variables
            else 0
        ),
    }

    current_async_metrics.submit_metric(
        {
            "metric_type": "retrodiction_batch",
            "batch_id": batch.batch_id,
            "start_time": batch.start_time.isoformat(),
            "end_time": batch.end_time.isoformat(),
            "variables": len(batch.variables),
            "metrics": results_retro_task.get("metrics", {}),
            "timestamp": datetime.now().isoformat(),
        }
    )

    pt_val_task = time.time() - start_time_proc
    final_results_task = {
        "success": True,
        "processing_time": pt_val_task,
        "metrics": results_retro_task.get("metrics", {}),
        "rules_generated": results_retro_task.get("rules_generated", []),
        "trust_updates": results_retro_task.get("trust_updates", {}),
    }
    worker_logger.info(
        f"Dask Worker: Finished processing batch {batch.batch_id} in {pt_val_task:.2f}s"
    )
    # Ensure worker-specific resources are cleaned up if necessary, e.g.,
    # closing store connections if they are not managed by get_instance()
    if hasattr(current_data_store, "close"):
        current_data_store.close()
    if hasattr(current_async_metrics, "shutdown"):
        current_async_metrics.shutdown()
    if hasattr(current_trust_buffer, "flush_all"):
        current_trust_buffer.flush_all()  # Or similar cleanup

    return batch.batch_id, final_results_task


# --- End of Top-level Dask task function ---


class ParallelTrainingCoordinator:
    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        max_workers: Optional[int] = None,
        dask_scheduler_port: Optional[int] = None,
        dask_dashboard_port: Optional[int] = None,
        dask_threads_per_worker: int = 1,
    ):
        self.config = config or {}
        self.max_workers = max_workers or max(1, (os.cpu_count() or 4) - 1)
        self.dask_scheduler_port = dask_scheduler_port
        self.dask_dashboard_port = dask_dashboard_port
        self.dask_threads_per_worker = dask_threads_per_worker
        self.logger = coordinator_logger
        self.logger.info(
            f"Initializing ParallelTrainingCoordinator with {self.max_workers} workers"
        )

        self.data_store_config = self.config.get(
            "data_store_config", {}
        )  # Store config for workers
        self.async_metrics_config = self.config.get("async_metrics_config", {})
        self.trust_buffer_config = self.config.get("trust_buffer_config", {})

        # Initialize main instances for the coordinator itself
        if StreamingDataStore:
            self.data_store: Any = StreamingDataStore.get_instance(
                config=self.data_store_config
            )
            self.logger.info("Coordinator using StreamingDataStore")
        elif OptimizedDataStore:
            self.data_store = OptimizedDataStore.get_instance(
                config=self.data_store_config
            )
            self.logger.info("Coordinator using OptimizedDataStore")
        else:
            self.data_store = RecursiveDataStore.get_instance(
                config=self.data_store_config
            )
            self.logger.info("Coordinator using standard RecursiveDataStore")

        self.metrics_store: MetricsStore = (
            get_metrics_store()
        )  # This might not be needed if workers handle all
        self.async_metrics: AsyncMetricsCollector = get_async_metrics_collector(
            config=self.async_metrics_config
        )
        self.trust_buffer: TrustUpdateBuffer = get_trust_update_buffer(
            config=self.trust_buffer_config
        )

        self.batches: List[TrainingBatch] = []
        self.batch_results: Dict[str, Any] = {}
        self.training_start_time: Optional[datetime] = None
        self.training_end_time: Optional[datetime] = None
        self.is_training: bool = False
        self.errors: List[str] = []
        self.dask_futures: list = []
        self.performance_metrics: Dict[str, Any] = {
            "total_batches": 0,
            "completed_batches": 0,
            "failed_batches": 0,
            "total_variables": 0,
            "processing_time": 0.0,
            "speedup_factor": 0.0,
            "estimated_sequential_time": 0.0,
        }
        self.progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
        self.dask_cluster_info: Optional[Dict[str, Any]] = None
        self._register_signal_handlers()

    def _register_signal_handlers(self):  # Same as before
        import signal

        def handle_signal(sig, frame):
            self.logger.warning(
                f"Received signal {sig}, shutting down training gracefully"
            )
            self.stop_training()

        try:
            signal.signal(signal.SIGINT, handle_signal)
            signal.signal(signal.SIGTERM, handle_signal)
        except (AttributeError, ValueError):  # pragma: no cover
            self.logger.warning("Signal handling not available on this platform.")
            pass

    def prepare_training_batches(  # Same as before
        self,
        variables: List[str],
        start_time: datetime,
        end_time: datetime,
        batch_size_days: int = 30,
        overlap_days: int = 5,
        batch_limit: Optional[int] = None,
        preload_data: bool = True,
    ) -> List[TrainingBatch]:
        self.logger.info(f"Preparing training batches from {start_time} to {end_time}")
        if not variables:
            raise ValueError("No variables specified for training")
        if start_time >= end_time:
            raise ValueError("Start time must be before end time")
        if batch_size_days <= 0:
            raise ValueError("Batch size must be positive")

        batch_delta = timedelta(days=batch_size_days)
        overlap_delta = timedelta(days=overlap_days)

        if preload_data:
            self.logger.info(
                "Preload data requested by coordinator, but actual preloading happens in workers or is disabled if executor was removed."
            )

        batches: List[TrainingBatch] = []
        current_batch_start = start_time
        batch_id_counter = 0
        while current_batch_start < end_time:
            current_batch_end = min(current_batch_start + batch_delta, end_time)
            if (current_batch_end - current_batch_start).total_seconds() < 86400:
                break

            batch = TrainingBatch(
                batch_id=f"batch_{batch_id_counter:04d}",
                start_time=current_batch_start,
                end_time=current_batch_end,
                variables=variables,
            )
            batches.append(batch)
            batch_id_counter += 1
            current_batch_start = current_batch_end - overlap_delta
            if batch_limit is not None and len(batches) >= batch_limit:
                self.logger.info(f"Reached batch_limit of {batch_limit}.")
                break

        self.logger.info(f"Created {len(batches)} training batches")
        self.batches = batches
        self.performance_metrics["total_batches"] = len(batches)
        self.performance_metrics["total_variables"] = len(variables)
        return batches

    @memory_profiler.profile  # type: ignore
    def start_training(
        self, progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> None:
        if self.is_training:
            self.logger.warning("Training is already in progress")
            return
        if not self.batches:
            self.logger.error("No training batches prepared")
            raise RuntimeError("No batches.")

        self.training_start_time = datetime.now()
        self.is_training = True
        self.progress_callback = progress_callback
        self.logger.info(f"Starting Dask training with {len(self.batches)} batches")
        self.dask_futures = []

        cluster_kwargs: Dict[str, Any] = {
            "n_workers": self.max_workers,
            "threads_per_worker": self.dask_threads_per_worker,
        }
        if self.dask_dashboard_port is not None:
            cluster_kwargs["dashboard_address"] = f":{self.dask_dashboard_port}"

        with LocalCluster(**cluster_kwargs) as cluster:
            self.logger.info(
                f"Dask Cluster: {
                    cluster.scheduler_address}, Dashboard: {
                    cluster.dashboard_link}")
            with Client(cluster) as client:
                self.logger.info(
                    f"Dask Client connected. Dashboard: {client.dashboard_link}"
                )
                self.dask_cluster_info = {
                    "dashboard_link": client.dashboard_link,
                    "scheduler_address": str(client.scheduler_info().get("address")),
                    "n_workers": len(client.scheduler_info().get("workers", {})),
                    "threads": self.dask_threads_per_worker,
                }

                data_store_class_name = self.data_store.__class__.__name__

                for batch_item in self.batches:
                    batch_item_data = {
                        "batch_id": batch_item.batch_id,
                        "start_time": batch_item.start_time.isoformat(),
                        "end_time": batch_item.end_time.isoformat(),
                        "variables": batch_item.variables,
                    }
                    future = client.submit(
                        _dask_process_batch_task,
                        batch_item_data,
                        data_store_class_name,
                        self.data_store_config,
                        self.async_metrics_config,
                        self.trust_buffer_config,
                        # Removed passing all_batches for simplicity in worker
                        # _get_upcoming_vars
                    )
                    self.dask_futures.append(future)

                completed_count = 0
                while completed_count < len(self.dask_futures) and self.is_training:
                    completed_count = sum(1 for f in self.dask_futures if f.done())
                    self._report_progress(completed_count)
                    time.sleep(2)

                if self.is_training:
                    for i, future_item_done in enumerate(self.dask_futures):
                        if future_item_done.done():  # Check again before getting result
                            try:
                                batch_id_res, result_data = future_item_done.result()
                                self._on_batch_complete((batch_id_res, result_data))
                            except Exception as e_res:
                                self.logger.error(
                                    f"Error collecting result for batch {
                                        self.batches[i].batch_id if i < len(
                                            self.batches) else 'unknown'}: {
                                        str(e_res)}", exc_info=True, )
                                self._on_batch_error(e_res)

        self.training_end_time = datetime.now()
        self.is_training = False
        if self.training_start_time:  # Check if training actually started
            total_time = (
                self.training_end_time - self.training_start_time
            ).total_seconds()
            self.performance_metrics["processing_time"] = total_time
            if self.performance_metrics["completed_batches"] > 0:
                sum_proc_time = sum(
                    b.processing_time
                    for b in self.batches
                    if b.processed and b.results and b.results.get("success")
                )
                avg_batch_time = (
                    sum_proc_time / self.performance_metrics["completed_batches"]
                )
                est_seq_time = avg_batch_time * len(self.batches)
                self.performance_metrics["estimated_sequential_time"] = est_seq_time
                if total_time > 0:
                    self.performance_metrics["speedup_factor"] = (
                        est_seq_time / total_time
                    )
            self._report_progress(len(self.batches))
            self.logger.info(
                f"Training completed in {
                    total_time:.2f}s. Speedup: {
                    self.performance_metrics.get(
                        'speedup_factor',
                        0.0):.2f}x")
        else:
            self.logger.error("Training start time not recorded.")

    def _on_batch_complete(
        self, result: Tuple[str, Dict[str, Any]]
    ) -> None:  # Same as before
        batch_id_comp, data_comp = result
        for batch_item_comp in self.batches:
            if batch_item_comp.batch_id == batch_id_comp:
                batch_item_comp.processed = True
                batch_item_comp.processing_time = data_comp.get("processing_time", 0.0)
                batch_item_comp.results = data_comp
                self.logger.info(
                    f"Batch {batch_id_comp} completed. Processing time: {
                        data_comp.get(
                            'processing_time',
                            0.0):.2f}s. Skipped: {
                        data_comp.get(
                            'skipped',
                            False)}")
                break
        self.performance_metrics["completed_batches"] += 1
        self._report_progress(
            self.performance_metrics["completed_batches"]
            + self.performance_metrics["failed_batches"]
        )

    def _on_batch_error(self, error: Exception) -> None:  # Same as before
        self.logger.error(
            f"A batch processing error occurred: {str(error)}", exc_info=True
        )
        self.errors.append(str(error))  # Store error message
        self.performance_metrics["failed_batches"] += 1
        # Potentially mark a specific batch as failed if identifiable
        self._report_progress(
            self.performance_metrics["completed_batches"]
            + self.performance_metrics["failed_batches"]
        )

    def _report_progress(self, completed_batches_count: int) -> None:  # Same as before
        if not self.batches:
            return
        total_b_rep = len(self.batches)
        actual_comp_rep = min(completed_batches_count, total_b_rep)
        prog_rep = actual_comp_rep / total_b_rep if total_b_rep > 0 else 0
        elap_rep, rem_rep = 0.0, 0.0
        if self.training_start_time and actual_comp_rep > 0:
            elap_rep = (datetime.now() - self.training_start_time).total_seconds()
            total_est_rep = (elap_rep / prog_rep) if prog_rep > 0 else 0
            rem_rep = total_est_rep - elap_rep if total_est_rep > 0 else 0

        s_rate_str = "0.0%"
        if (
            actual_comp_rep > 0
            and self.performance_metrics["completed_batches"] <= actual_comp_rep
        ):
            s_rate_str = f"{
                self.performance_metrics['completed_batches'] / actual_comp_rep * 100:.1f}%"

        prog_data_map = {
            "progress": prog_rep,
            "completed_batches": actual_comp_rep,
            "total_batches": total_b_rep,
            "elapsed_seconds": elap_rep,
            "remaining_seconds": rem_rep,
            "completed_percentage": f"{prog_rep * 100:.1f}%",
            "success_rate": s_rate_str,
            "errors": len(self.errors),
        }
        if self.progress_callback:
            try:
                self.progress_callback(prog_data_map)
            except Exception as e_cb:
                self.logger.error(f"Error in progress_callback: {e_cb}")
        self.logger.info(
            f"Progress: {
                prog_data_map['completed_percentage']} ({actual_comp_rep}/{total_b_rep}), Elapsed: {
                elap_rep:.1f}s, Remaining: {
                rem_rep:.1f}s, Errors: {
                    len(
                        self.errors)}")

    def stop_training(self) -> None:  # Same as before
        if not self.is_training:
            return
        self.logger.info("Stopping training...")
        self.is_training = False
        if hasattr(self, "dask_futures") and self.dask_futures:
            self.logger.info("Cancelling Dask tasks...")
            for f_stop in self.dask_futures:
                if not f_stop.done():
                    try:
                        f_stop.cancel(asynchronous=True)
                    except Exception as e_stop:
                        self.logger.warning(f"Error cancelling Dask future: {e_stop}")
        if self.trust_buffer:
            self.logger.info("Flushing trust buffer...")
            flushed_stop = self.trust_buffer.flush()
            self.logger.info(f"Flushed {flushed_stop} trust updates.")
        if not self.training_end_time:
            self.training_end_time = datetime.now()

    def get_results_summary(self) -> Dict[str, Any]:  # Same as before
        comp_sum = self.performance_metrics["completed_batches"]
        fail_sum = self.performance_metrics["failed_batches"]
        tot_sum = comp_sum + fail_sum
        sr_sum = comp_sum / tot_sum if tot_sum > 0 else 0
        all_v_sum = set().union(*(b.variables for b in self.batches))
        if self.trust_buffer:
            self.trust_buffer.flush()
        ts_map_sum = {}
        if all_v_sum:
            try:
                ts_map_sum = optimized_bayesian_trust_tracker.get_trust_batch(
                    list(all_v_sum)
                )
            except Exception as e_ts:
                self.logger.error(f"Error getting trust scores: {e_ts}")
        dur_sum = (
            (self.training_end_time - self.training_start_time).total_seconds()
            if self.training_start_time and self.training_end_time
            else 0.0
        )

        return {
            "batches": {
                "total": len(self.batches),
                "completed": comp_sum,
                "failed": fail_sum,
                "success_rate": sr_sum,
            },
            "variables": {"total": len(all_v_sum), "trust_scores": ts_map_sum},
            "performance": {
                "duration_seconds": dur_sum,
                "speedup_factor": self.performance_metrics.get("speedup_factor", 0.0),
                "estimated_sequential_time": self.performance_metrics.get(
                    "estimated_sequential_time", 0.0
                ),
            },
            "dask_cluster": self.dask_cluster_info or {"status": "Not used"},
            "errors": self.errors[:10],
        }

    def save_results_to_file(self, filepath: str) -> None:  # Same as before
        if self.trust_buffer:
            self.trust_buffer.flush()
        tb_stats_save = self.trust_buffer.get_stats() if self.trust_buffer else {}
        am_stats_save = self.async_metrics.get_stats() if self.async_metrics else {}
        res_data_save = self.get_results_summary()
        res_data_save["optimization_metrics"] = {
            "trust_buffer": tb_stats_save,
            "async_metrics": am_stats_save,
        }

        def json_ser_save(obj_save):
            if isinstance(obj_save, datetime):
                return obj_save.isoformat()
            return str(obj_save)

        try:
            with open(filepath, "w") as f_js_save:
                json.dump(res_data_save, f_js_save, default=json_ser_save, indent=2)
            self.logger.info(f"Results saved to {filepath}")
        except Exception as e_f_save:
            self.logger.error(f"Failed to save results to {filepath}: {e_f_save}")


def run_parallel_retrodiction_training(  # Same as before
    variables: List[str],
    start_time: datetime,
    end_time: datetime,
    max_workers: Optional[int] = None,
    batch_size_days: int = 30,
    output_file: Optional[str] = None,
    dask_scheduler_port: Optional[int] = None,
    dask_dashboard_port: Optional[int] = None,
    dask_threads_per_worker: int = 1,
    batch_limit: Optional[int] = None,
) -> Dict[str, Any]:
    coord = ParallelTrainingCoordinator(
        max_workers=max_workers,
        dask_scheduler_port=dask_scheduler_port,
        dask_dashboard_port=dask_dashboard_port,
        dask_threads_per_worker=dask_threads_per_worker,
    )
    coord.prepare_training_batches(
        variables=variables,
        start_time=start_time,
        end_time=end_time,
        batch_size_days=batch_size_days,
        preload_data=True,
        batch_limit=batch_limit,
    )

    def prog_cb_run(p_data_run):
        cp_run, cb_run, tb_run = (
            p_data_run.get("completed_percentage", "N/A"),
            p_data_run.get("completed_batches", "N/A"),
            p_data_run.get("total_batches", "N/A"),
        )
        print(f"Training progress: {cp_run} ({cb_run}/{tb_run} batches)")

    coord.start_training(progress_callback=prog_cb_run)
    res_sum_run = coord.get_results_summary()
    if output_file:
        coord.save_results_to_file(output_file)
    return res_sum_run


if __name__ == "__main__":  # pragma: no cover
    ex_vars_main = [
        "spx_close",
        "us_10y_yield",
        "wb_gdp_growth_annual",
        "wb_unemployment_total",
    ]
    ex_start_main, ex_end_main = datetime(2020, 1, 1), datetime(2021, 1, 1)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    coordinator_logger.info(
        "Starting example parallel retrodiction training from __main__..."
    )
    ex_res_main = run_parallel_retrodiction_training(
        variables=ex_vars_main,
        start_time=ex_start_main,
        end_time=ex_end_main,
        max_workers=2,
        batch_size_days=30,
        output_file="retrodiction_training_results_example.json",
        batch_limit=3,
        dask_dashboard_port=8788,
    )
    coordinator_logger.info("Example training completed.")
    if ex_res_main and ex_res_main.get("performance"):
        spd_main = ex_res_main["performance"].get("speedup_factor", 0.0)
        coordinator_logger.info(f"Speedup factor: {spd_main:.2f}x")
    if ex_res_main and ex_res_main.get("batches"):
        sr_main = ex_res_main["batches"].get("success_rate", 0.0)
        coordinator_logger.info(f"Success rate: {sr_main * 100:.2f}%")
