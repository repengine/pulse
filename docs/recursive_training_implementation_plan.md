# Recursive AI Training Capabilities Implementation Plan

This document outlines the implementation plan for enhancing Pulse's recursive AI training capabilities, organized into a phased approach with specific code deliverables for each component.

## Overview

The implementation will build upon Pulse's existing symbolic-capital foresight simulator architecture by adding specialized components that enable recursive learning, automated rule generation, and advanced model management. The new capabilities will integrate with existing systems including Iris data ingestion, forecast outputs, and retrodiction engines.

## Implementation Schedule

### Phase 1: Data Management Components (4 weeks)
- RecursiveDataIngestionManager
- RecursiveDataStore
- RecursiveFeatureProcessor

### Phase 2: Training Orchestration Components (6 weeks)
- RecursiveTrainingOrchestrator
- Enhanced Airflow DAGs
- Model Registry Extensions

### Phase 3: Rule Generation Components (5 weeks)
- RecursiveRuleGenerator
- RecursiveRuleEvaluator
- RuleRepository

### Phase 4: Metrics Components (5 weeks)
- RecursiveTrainingMetrics
- MetricsStore
- EnhancedRetrodictionCurriculum

### Phase 5: Error Handling Components (4 weeks)
- RecursiveTrainingErrorHandler
- RecursiveTrainingMonitor
- RecursiveTrainingRecovery

## Detailed Component Implementations

## Phase 1: Data Management Components

### RecursiveDataIngestionManager

**Purpose:** Manages data ingestion from diverse sources (Iris, Forecast outputs, Retrodiction results) into a centralized data store, handling schema validation and source-specific adaptations.

**Core Classes/Functions:**
```python
class RecursiveDataIngestionManager:
    def __init__(self, config: Dict, data_store: RecursiveDataStore):
        self.config = config
        self.data_store = data_store
        self.ingestion_plugins = {}
        self._load_plugins()
        
    def _load_plugins(self):
        """Load ingestion plugins based on configuration"""
        for plugin_name, plugin_config in self.config["plugins"].items():
            plugin_class = import_class(plugin_config["class"])
            self.ingestion_plugins[plugin_name] = plugin_class(**plugin_config["params"])
    
    def ingest_data(self, source_name: str, **kwargs) -> str:
        """Ingest data from specified source with optional parameters"""
        if source_name not in self.ingestion_plugins:
            raise ValueError(f"Unknown source: {source_name}")
        
        data = self.ingestion_plugins[source_name].extract(**kwargs)
        validated_data = self._validate_schema(data, source_name)
        data_id = self.data_store.store(validated_data, source=source_name, **kwargs)
        return data_id
    
    def _validate_schema(self, data, source_name: str):
        """Validate data against schema for the source"""
        schema = self.config["schemas"].get(source_name)
        if not schema:
            return data  # No schema validation
        
        # Implement schema validation logic
        return validated_data

    def register_callback(self, event_type: str, callback_fn: Callable):
        """Register callback for specific ingestion events"""
        # Implementation
```

**Interfaces with Pulse components:**
- `iris.ingestion_api`: Sources live market/social/political data
- `forecast_output.pfpa_logger`: Captures forecast outputs
- `trust_system.retrodiction_engine`: Sources retrodiction results

**Dependencies:**
- Core Python libraries: typing, logging, importlib
- Schema validation: pydantic
- Async processing: asyncio

**Sample code snippet (Iris Data Plugin):**
```python
class IrisDataPlugin:
    def __init__(self, api_config: Dict):
        self.api_url = api_config["api_url"]
        self.api_key = api_config["api_key"]
        self.client = IrisClient(self.api_url, self.api_key)
        
    async def extract(self, start_time: str, end_time: str, variables: List[str]) -> Dict:
        """Extract data from Iris API within time range for specified variables"""
        raw_data = await self.client.get_data(start_time, end_time, variables)
        
        # Transform raw API response into standardized format
        transformed_data = {
            "source": "iris",
            "timestamp": datetime.now().isoformat(),
            "data": self._transform_data(raw_data),
            "metadata": {
                "variables": variables,
                "time_range": {"start": start_time, "end": end_time}
            }
        }
        
        return transformed_data
        
    def _transform_data(self, raw_data: Dict) -> Dict:
        """Transform raw Iris data into standardized format"""
        # Implementation
```

### RecursiveDataStore

**Purpose:** Provides a unified storage layer for raw data from various sources with versioning and lineage tracking.

**Core Classes/Functions:**
```python
class RecursiveDataStore:
    def __init__(self, storage_path: str, config: Dict):
        self.storage_path = storage_path
        self.config = config
        self.storage_backend = self._initialize_storage()
        
    def _initialize_storage(self):
        """Initialize storage backend based on configuration"""
        backend_type = self.config.get("backend", "file")
        if backend_type == "file":
            return FileStorageBackend(self.storage_path)
        elif backend_type == "s3":
            return S3StorageBackend(self.config["s3_config"])
        # Add more backends as needed
        
    def store(self, data: Dict, source: str, **metadata) -> str:
        """Store data with source and metadata, return data ID"""
        data_id = self._generate_id()
        
        # Add metadata and lineage information
        enriched_data = {
            "id": data_id,
            "source": source,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata,
            "data": data,
        }
        
        self.storage_backend.save(data_id, enriched_data)
        return data_id
        
    def retrieve(self, data_id: str) -> Dict:
        """Retrieve data by ID"""
        return self.storage_backend.load(data_id)
    
    def query(self, filters: Dict) -> List[Dict]:
        """Query data using filters"""
        return self.storage_backend.query(filters)
        
    def _generate_id(self) -> str:
        """Generate unique ID for data entry"""
        return str(uuid.uuid4())
```

**Interfaces with Pulse components:**
- Core storage systems
- `core.path_registry` for storage paths

**Dependencies:**
- Data serialization: pickle, json
- Cloud storage: boto3 (for S3)
- Database: sqlalchemy (for metadata indexing)

**Sample code snippet (Storage Backend):**
```python
class FileStorageBackend:
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True, parents=True)
        self.index_path = self.base_path / "index.json"
        self.index = self._load_index()
        
    def _load_index(self) -> Dict:
        """Load or initialize index file"""
        if self.index_path.exists():
            with open(self.index_path, 'r') as f:
                return json.load(f)
        return {}
        
    def _save_index(self):
        """Save index to disk"""
        with open(self.index_path, 'w') as f:
            json.dump(self.index, f)
            
    def save(self, data_id: str, data: Dict):
        """Save data to file system"""
        # Save actual data
        data_path = self.base_path / f"{data_id}.pkl"
        with open(data_path, 'wb') as f:
            pickle.dump(data, f)
            
        # Update index with metadata for searching
        self.index[data_id] = {
            "source": data["source"],
            "timestamp": data["timestamp"],
            "metadata": data["metadata"],
            "path": str(data_path)
        }
        self._save_index()
        
    def load(self, data_id: str) -> Dict:
        """Load data by ID"""
        if data_id not in self.index:
            raise KeyError(f"Data ID {data_id} not found")
            
        data_path = Path(self.index[data_id]["path"])
        with open(data_path, 'rb') as f:
            return pickle.load(f)
            
    def query(self, filters: Dict) -> List[Dict]:
        """Query data using filters"""
        results = []
        for data_id, metadata in self.index.items():
            if all(metadata.get(k) == v for k, v in filters.items()):
                results.append(self.load(data_id))
        return results
```

### RecursiveFeatureProcessor

**Purpose:** Transforms raw data into ML-ready features, handling normalization, blending live/retrodiction data, and computing derived signals.

**Core Classes/Functions:**
```python
class RecursiveFeatureProcessor:
    def __init__(self, config: Dict, data_store: RecursiveDataStore):
        self.config = config
        self.data_store = data_store
        self.pipelines = self._initialize_pipelines()
        self.feature_store = FeatureStore(config["feature_store"])
        
    def _initialize_pipelines(self) -> Dict[str, Pipeline]:
        """Initialize processing pipelines for different data sources"""
        pipelines = {}
        for source, pipeline_config in self.config["pipelines"].items():
            pipelines[source] = self._build_pipeline(pipeline_config)
        return pipelines
        
    def _build_pipeline(self, pipeline_config: Dict) -> Pipeline:
        """Build processing pipeline from configuration"""
        # Implementation
        
    def process_data(self, data_ids: List[str], feature_set_name: str) -> str:
        """Process raw data into features and store in feature store"""
        data_list = [self.data_store.retrieve(data_id) for data_id in data_ids]
        
        # Group data by source
        grouped_data = defaultdict(list)
        for data in data_list:
            grouped_data[data["source"]].append(data)
            
        # Process each source with appropriate pipeline
        processed_data = {}
        for source, data_group in grouped_data.items():
            pipeline = self.pipelines.get(source)
            if pipeline:
                processed_data[source] = pipeline.transform(data_group)
            
        # Blend data from different sources
        blended_features = self._blend_features(processed_data)
        
        # Store in feature store
        feature_id = self.feature_store.store(
            blended_features, 
            name=feature_set_name,
            source_data_ids=data_ids
        )
        
        return feature_id
        
    def _blend_features(self, processed_data: Dict) -> Dict:
        """Blend features from different sources"""
        # Implementation
```

**Interfaces with Pulse components:**
- Feature representation in `forecast_engine`

**Dependencies:**
- Data processing: numpy, pandas
- Feature engineering: scikit-learn
- Vector operations: scipy

**Sample code snippet (Feature Pipeline):**
```python
class FeatureEngineeringPipeline:
    def __init__(self, steps: List[Dict]):
        self.steps = []
        for step in steps:
            self.steps.append(self._create_step(step))
    
    def _create_step(self, step_config: Dict):
        """Create processing step from configuration"""
        step_type = step_config["type"]
        
        if step_type == "normalize":
            return NormalizeStep(**step_config["params"])
        elif step_type == "fillna":
            return FillNAStep(**step_config["params"])
        elif step_type == "calculate_indicators":
            return CalculateIndicatorsStep(**step_config["params"])
        # Add more steps as needed
        
    def transform(self, data: List[Dict]) -> Dict:
        """Apply all steps in the pipeline to the data"""
        result = {"data": pd.DataFrame([d["data"] for d in data])}
        
        for step in self.steps:
            result = step.process(result)
            
        return result["data"]

class NormalizeStep:
    def __init__(self, method="z-score", columns=None):
        self.method = method
        self.columns = columns
        
    def process(self, data: Dict) -> Dict:
        """Normalize specified columns using the chosen method"""
        df = data["data"]
        columns = self.columns or df.columns
        
        if self.method == "z-score":
            for col in columns:
                if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
                    mean = df[col].mean()
                    std = df[col].std()
                    if std > 0:
                        df[col] = (df[col] - mean) / std
                        
        elif self.method == "min-max":
            for col in columns:
                if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
                    min_val = df[col].min()
                    max_val = df[col].max()
                    if max_val > min_val:
                        df[col] = (df[col] - min_val) / (max_val - min_val)
                        
        data["data"] = df
        return data
```

## Phase 2: Training Orchestration Components

### RecursiveTrainingOrchestrator

**Purpose:** Schedules and manages training experiments and fine-tuning jobs based on data drift, performance metrics, and defined schedules.

**Core Classes/Functions:**
```python
class RecursiveTrainingOrchestrator:
    def __init__(self, config: Dict, feature_store, model_registry):
        self.config = config
        self.feature_store = feature_store
        self.model_registry = model_registry
        self.scheduled_jobs = []
        self.metrics_client = MetricsClient(config["metrics"])
        
    def schedule_training_job(self, model_type: str, feature_set_id: str, 
                             training_params: Dict, schedule: Optional[str] = None) -> str:
        """Schedule a training job with optional time-based schedule"""
        job_id = str(uuid.uuid4())
        
        job_config = {
            "id": job_id,
            "model_type": model_type,
            "feature_set_id": feature_set_id,
            "training_params": training_params,
            "schedule": schedule,
            "status": "scheduled",
            "created_at": datetime.now().isoformat()
        }
        
        self.scheduled_jobs.append(job_config)
        
        # If schedule is None, trigger immediately
        if schedule is None:
            self._trigger_job(job_id)
            
        return job_id
        
    def _trigger_job(self, job_id: str):
        """Trigger a training job by ID"""
        job = next((j for j in self.scheduled_jobs if j["id"] == job_id), None)
        if not job:
            raise ValueError(f"Job {job_id} not found")
            
        job["status"] = "triggered"
        
        # Create DAG run for this job
        from airflow.api.client.local_client import Client
        client = Client(None, None)
        
        run_id = f"train_{job_id}"
        dag_id = f"train_{job['model_type']}"
        conf = {
            "job_id": job_id,
            "feature_set_id": job["feature_set_id"],
            "training_params": job["training_params"]
        }
        
        client.trigger_dag(dag_id=dag_id, run_id=run_id, conf=conf)
        
    def check_data_drift(self, model_id: str, new_data_id: str) -> bool:
        """Check if new data has drifted from training data of model"""
        model_info = self.model_registry.get_model(model_id)
        training_data_id = model_info["training_data_id"]
        
        training_data = self.feature_store.retrieve(training_data_id)
        new_data = self.feature_store.retrieve(new_data_id)
        
        # Implement drift detection logic
        drift_detected = self._detect_drift(training_data, new_data)
        
        if drift_detected:
            # Log drift event
            self.metrics_client.log_event("data_drift_detected", {
                "model_id": model_id,
                "training_data_id": training_data_id,
                "new_data_id": new_data_id,
                "timestamp": datetime.now().isoformat()
            })
            
        return drift_detected
        
    def _detect_drift(self, training_data, new_data) -> bool:
        """Detect statistical drift between datasets"""
        # Implementation
```

**Interfaces with Pulse components:**
- `learning.retrodiction_curriculum` for scenario selection
- `core.pulse_config` for configuration

**Dependencies:**
- Experiment tracking: mlflow
- Workflow automation: apache-airflow
- Drift detection: scipy, alibi-detect
- Cloud integration: boto3, google-cloud-storage (optional)

**Sample code snippet (Drift Detection):**
```python
def detect_statistical_drift(reference_data: pd.DataFrame, 
                           current_data: pd.DataFrame,
                           threshold: float = 0.05) -> Dict[str, bool]:
    """
    Detect statistical drift between reference and current data
    using Kolmogorov-Smirnov test for continuous features
    and Chi-squared test for categorical features.
    
    Returns a dict with feature names and drift detection results.
    """
    from scipy import stats
    
    drift_results = {}
    
    # Ensure we're comparing the same features
    common_features = set(reference_data.columns) & set(current_data.columns)
    
    for feature in common_features:
        ref_values = reference_data[feature].dropna().values
        cur_values = current_data[feature].dropna().values
        
        # Skip if not enough data
        if len(ref_values) < 10 or len(cur_values) < 10:
            drift_results[feature] = False
            continue
            
        # Check if numerical or categorical
        if pd.api.types.is_numeric_dtype(reference_data[feature]):
            # Kolmogorov-Smirnov test for numerical features
            ks_stat, p_value = stats.ks_2samp(ref_values, cur_values)
            drift_detected = p_value < threshold
        else:
            # Convert to categorical codes
            ref_cat = pd.Categorical(ref_values).codes
            cur_cat = pd.Categorical(cur_values).codes
            
            # Create contingency table
            contingency = pd.crosstab(ref_cat, cur_cat)
            
            # Chi-squared test for categorical features
            chi2, p_value, dof, expected = stats.chi2_contingency(contingency)
            drift_detected = p_value < threshold
            
        drift_results[feature] = drift_detected
        
    return drift_results
```

### Enhanced Airflow DAGs

**Purpose:** Implements workflow definitions for data processing, training, evaluation, and deployment pipelines.

**Core Classes/Functions:**
```python
# airflow_dags/recursive_training_dag.py
from datetime import datetime, timedelta
from airflow.sdk import DAG
from airflow.operators.python import PythonOperator
from airflow.sensors.external_task import ExternalTaskSensor
from airflow.models import Variable

from pulse.recursive_training.tasks import (
    prepare_training_data,
    train_model,
    evaluate_model,
    register_model,
    update_metrics
)

default_args = {
    'owner': 'pulse',
    'depends_on_past': False,
    'start_date': datetime(2025, 1, 1),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'recursive_training_pipeline',
    default_args=default_args,
    description='End-to-end recursive training pipeline',
    schedule=timedelta(days=1),
    catchup=False,
    max_active_runs=1
)

# Define tasks
prepare_data_task = PythonOperator(
    task_id='prepare_training_data',
    python_callable=prepare_training_data,
    op_kwargs={
        'data_store_config': Variable.get('data_store_config', deserialize_json=True),
        'feature_processor_config': Variable.get('feature_processor_config', deserialize_json=True),
    },
    dag=dag
)

train_model_task = PythonOperator(
    task_id='train_model',
    python_callable=train_model,
    op_kwargs={
        'model_type': '{{ dag_run.conf["model_type"] }}',
        'training_params': '{{ dag_run.conf["training_params"] }}',
    },
    dag=dag
)

evaluate_model_task = PythonOperator(
    task_id='evaluate_model',
    python_callable=evaluate_model,
    op_kwargs={
        'metrics_config': Variable.get('metrics_config', deserialize_json=True),
    },
    dag=dag
)

register_model_task = PythonOperator(
    task_id='register_model',
    python_callable=register_model,
    op_kwargs={
        'model_registry_config': Variable.get('model_registry_config', deserialize_json=True),
    },
    dag=dag
)

update_metrics_task = PythonOperator(
    task_id='update_metrics',
    python_callable=update_metrics,
    dag=dag
)

# Define task dependencies
prepare_data_task >> train_model_task >> evaluate_model_task >> register_model_task >> update_metrics_task
```

**Interfaces with Pulse components:**
- `dags` directory structure
- Execution environment

**Dependencies:**
- Workflow automation: apache-airflow
- Scheduling: python-dateutil, croniter
- Monitoring: prometheus-client (optional)

**Sample code snippet (Training Task):**
```python
# recursive_training/tasks.py
import os
import json
import logging
import tempfile
from typing import Dict, Any
import mlflow
import torch
from torch.utils.data import DataLoader, TensorDataset

from pulse.recursive_training.models import create_model

logger = logging.getLogger(__name__)

def train_model(model_type: str, training_params: Dict[str, Any], **context) -> Dict[str, Any]:
    """
    Train model based on provided parameters and track with MLflow
    """
    logger.info(f"Training model of type {model_type} with params: {training_params}")
    
    ti = context['ti']
    
    # Get training data from previous task
    data_dict = ti.xcom_pull(task_ids='prepare_training_data')
    
    if not data_dict:
        raise ValueError("No training data available")
        
    # Prepare PyTorch datasets
    features = torch.tensor(data_dict['features'], dtype=torch.float32)
    targets = torch.tensor(data_dict['targets'], dtype=torch.float32)
    
    dataset = TensorDataset(features, targets)
    train_size = int(0.8 * len(dataset))
    test_size = len(dataset) - train_size
    
    train_dataset, test_dataset = torch.utils.data.random_split(
        dataset, [train_size, test_size]
    )
    
    train_loader = DataLoader(
        train_dataset, 
        batch_size=training_params.get('batch_size', 32),
        shuffle=True
    )
    
    test_loader = DataLoader(
        test_dataset,
        batch_size=training_params.get('batch_size', 32)
    )
    
    # Create model
    input_size = features.shape[1]
    output_size = targets.shape[1]
    
    model = create_model(
        model_type=model_type,
        input_size=input_size,
        output_size=output_size,
        hidden_sizes=training_params.get('hidden_sizes', [64, 32]),
        dropout=training_params.get('dropout', 0.2)
    )
    
    # Define loss function and optimizer
    criterion = torch.nn.MSELoss()
    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=training_params.get('learning_rate', 0.001),
        weight_decay=training_params.get('weight_decay', 1e-5)
    )
    
    # Track with MLflow
    mlflow.set_tracking_uri(os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:5000"))
    mlflow.set_experiment(f"pulse-{model_type}")
    
    with mlflow.start_run() as run:
        # Log parameters
        mlflow.log_params(training_params)
        mlflow.log_param("input_size", input_size)
        mlflow.log_param("output_size", output_size)
        
        # Train model
        num_epochs = training_params.get('num_epochs', 50)
        for epoch in range(num_epochs):
            model.train()
            train_loss = 0.0
            
            for batch_features, batch_targets in train_loader:
                optimizer.zero_grad()
                outputs = model(batch_features)
                loss = criterion(outputs, batch_targets)
                loss.backward()
                optimizer.step()
                
                train_loss += loss.item()
                
            # Calculate validation loss
            model.eval()
            val_loss = 0.0
            with torch.no_grad():
                for batch_features, batch_targets in test_loader:
                    outputs = model(batch_features)
                    val_loss += criterion(outputs, batch_targets).item()
                    
            train_loss /= len(train_loader)
            val_loss /= len(test_loader)
            
            # Log metrics
            mlflow.log_metrics({
                "train_loss": train_loss,
                "val_loss": val_loss
            }, step=epoch)
            
            logger.info(f"Epoch {epoch+1}/{num_epochs}, Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}")
            
        # Save model artifacts
        with tempfile.TemporaryDirectory() as tmpdir:
            model_path = os.path.join(tmpdir, "model.pt")
            torch.save(model.state_dict(), model_path)
            
            mlflow.log_artifact(model_path)
            
            # Save model configuration for reproducibility
            config_path = os.path.join(tmpdir, "model_config.json")
            with open(config_path, 'w') as f:
                json.dump({
                    "model_type": model_type,
                    "input_size": input_size,
                    "output_size": output_size,
                    "hidden_sizes": training_params.get('hidden_sizes', [64, 32]),
                    "dropout": training_params.get('dropout', 0.2)
                }, f)
                
            mlflow.log_artifact(config_path)
            
        # Register the trained model
        model_info = mlflow.register_model(
            f"runs:/{run.info.run_id}/model",
            name=f"{model_type}-model"
        )
        
    return {
        "run_id": run.info.run_id,
        "model_uri": f"runs:/{run.info.run_id}/model",
        "registered_model_name": model_info.name,
        "registered_model_version": model_info.version
    }
```

### Model Registry Extensions

**Purpose:** Extends MLflow model registry for Pulse-specific needs including model versioning, metadata tracking, and deployment management.

**Core Classes/Functions:**
```python
class PulseModelRegistry:
    def __init__(self, config: Dict):
        self.config = config
        self.mlflow_uri = config.get("mlflow_uri", "http://localhost:5000")
        self.mlflow_client = MlflowClient(tracking_uri=self.mlflow_uri)
        
    def register_model(self, model_uri: str, name: str, 
                      tags: Dict[str, str] = None) -> Dict:
        """Register model in MLflow and extend with Pulse-specific metadata"""
        # Register in MLflow
        model_details = mlflow.register_model(model_uri, name)
        
        # Add custom tags
        if tags:
            for key, value in tags.items():
                self.mlflow_client.set_model_version_tag(
                    name=name,
                    version=model_details.version,
                    key=key,
                    value=value
                )
                
        # Register in Pulse's extended registry
        model_info = {
            "name": name,
            "version": model_details.version,
            "mlflow_uri": model_uri,
            "registered_at": datetime.now().isoformat(),
            "status": "registered",
            "tags": tags or {},
        }
        
        # Store extended info
        self._store_model_info(model_info)
        
        return model_info
        
    def transition_model(self, name: str, version: int, 
                        stage: str, reason: str = None) -> Dict:
        """Transition model to a new stage (staging, production, archived)"""
        # Update in MLflow
        self.mlflow_client.transition_model_version_stage(
            name=name,
            version=version,
            stage=stage
        )
        
        # Update in Pulse registry
        model_info = self._get_model_info(name, version)
        model_info["status"] = stage
        model_info["transition_history"] = model_info.get("transition_history", [])
        model_info["transition_history"].append({
            "from": model_info.get("status", "registered"),
            "to": stage,
            "timestamp": datetime.now().isoformat(),
            "reason": reason
        })
        
        self._store_model_info(model_info)
        
        return model_info
        
    def get_model_lineage(self, name: str, version: int) -> Dict:
        """Get full lineage info for model including ancestors and descendants"""
        # Implementation
        
    def _get_model_info(self, name: str, version: int) -> Dict:
        """Get model info from extended registry"""
        # Implementation
        
    def _store_model_info(self, model_info: Dict):
        """Store model info in extended registry"""
        # Implementation
```

**Interfaces with Pulse components:**
- `forecast_engine.model_storage`
- `learning` module for model metrics

**Dependencies:**
- Model registry: mlflow
- Data serialization: pickle, json
- Storage: sqlalchemy (for database storage)

**Sample code snippet (Model Lineage):**
```python
def get_model_lineage(self, name: str, version: int) -> Dict:
    """
    Get full lineage info for model including ancestors and descendants.
    Tracks model evolution through retraining, fine-tuning, and iteration.
    """
    model_info = self._get_model_info(name, version)
    
    if not model_info:
        raise ValueError(f"Model {name} version {version} not found")
    
    # Get ancestor models
    ancestors = []
    parent_id = model_info.get("parent_model_id")
    
    while parent_id:
        parent_parts = parent_id.split(":")
        parent_name = parent_parts[0]
        parent_version = int(parent_parts[1])
        
        parent_info = self._get_model_info(parent_name, parent_version)
        if not parent_info:
            break
            
        ancestors.insert(0, {
            "name": parent_name,
            "version": parent_version,
            "registered_at": parent_info.get("registered_at"),
            "status": parent_info.get("status")
        })
        
        parent_id = parent_info.get("parent_model_id")
    
    # Get descendant models
    descendants = []
    model_id = f"{name}:{version}"
    
    # Query for models that have this model as parent
    child_models = self._query_models_by_parent(model_id)
    
    for child in child_models:
        child_info = {
            "name": child["name"],
            "version": child["version"],
            "registered_at": child.get("registered_at"),
            "status": child.get("status")
        }
        
        descendants.append(child_info)
        
        # Recursively get children of this child
        grandchildren = self.get_model_lineage(child["name"], child["version"])["descendants"]
        
        for grandchild in grandchildren:
            descendants.append(grandchild)
    
    return {
        "model": {
            "name": name,
            "version": version,
            "registered_at": model_info.get("registered_at"),
            "status": model_info.get("status")
        },
        "ancestors": ancestors,
        "descendants": descendants
    }
```

## Phase 3: Rule Generation Components

### RecursiveRuleGenerator

**Purpose:** Creates new rules based on patterns observed in data and model performance. Uses GPT and symbolic revision planning to propose rule changes.

**Core Classes/Functions:**
```python
class RecursiveRuleGenerator:
    def __init__(self, config: Dict, model_registry, metrics_store):
        self.config = config
        self.model_registry = model_registry
        self.metrics_store = metrics_store
        self.gpt_client = GPTClient(config["gpt"])
        self.symbolic_planner = SymbolicRevisionPlanner(config["symbolic"])
        
    async def generate_rules(self, model_id: str, 
                           performance_metrics: Dict) -> List[Dict]:
        """Generate new rules based on model performance"""
        # Get model details
        model_info = self.model_registry.get_model_by_id(model_id)
        
        # Analyze performance metrics
        performance_analysis = self._analyze_performance(performance_metrics)
        
        # Generate rules using different methods
        gpt_rules = await self._generate_rules_gpt(model_info, performance_analysis)
        symbolic_rules = self._generate_rules_symbolic(model_info, performance_analysis)
        
        # Combine and deduplicate rules
        combined_rules = self._combine_rules(gpt_rules, symbolic_rules)
        
        return combined_rules
        
    async def _generate_rules_gpt(self, model_info: Dict, 
                               performance_analysis: Dict) -> List[Dict]:
        """Generate rules using GPT"""
        # Prepare prompt with model info and performance analysis
        prompt = self._create_gpt_prompt(model_info, performance_analysis)
        
        # Call GPT API
        response = await self.gpt_client.complete(
            prompt=prompt,
            max_tokens=1000,
            temperature=0.7
        )
        
        # Parse rules from response
        rules = self._parse_rules_from_gpt(response)
        
        return rules
        
    def _generate_rules_symbolic(self, model_info: Dict,
                              performance_analysis: Dict) -> List[Dict]:
        """Generate rules using symbolic revision planning"""
        # Implementation
        
    def _analyze_performance(self, performance_metrics: Dict) -> Dict:
        """Analyze performance metrics to identify areas for improvement"""
        # Implementation
        
    def _create_gpt_prompt(self, model_info: Dict, 
                         performance_analysis: Dict) -> str:
        """Create prompt for GPT rule generation"""
        # Implementation
        
    def _parse_rules_from_gpt(self, response: str) -> List[Dict]:
        """Parse rules from GPT response"""
        # Implementation
        
    def _combine_rules(self, gpt_rules: List[Dict], 
                     symbolic_rules: List[Dict]) -> List[Dict]:
        """Combine and deduplicate rules from different sources"""
        # Implementation
```

**Interfaces with Pulse components:**
- `symbolic_system.pulse_symbolic_revision_planner`
- `GPT.function_router`

**Dependencies:**
- LLM integration: openai
- Symbolic systems: sympy, networkx
- Asynchronous calls: asyncio, aiohttp

**Sample code snippet (GPT Prompt Creation):**
```python
def _create_gpt_prompt(self, model_info: Dict, performance_analysis: Dict) -> str:
    """
    Create a prompt for GPT to generate rules based on model info and performance analysis
    """
    model_type = model_info.get("model_type", "unknown")
    model_metrics = performance_analysis.get("metrics", {})
    
    error_patterns = performance_analysis.get("error_patterns", [])
    error_pattern_text = "\n".join([
        f"- Pattern: {pattern['description']}, Impact: {pattern['impact']}" 
        for pattern in error_patterns
    ])
    
    prompt = f"""
    As an expert in forecasting systems and rule generation for the Pulse platform, 
    analyze the performance of a {model_type} model and suggest new rules to improve its performance.
    
    Model Information:
    - Type: {model_type}
    - Version: {model_info.get('version', 'unknown')}
    - Training data range: {model_info.get('training_period', 'unknown')}
    
    Performance Metrics:
    - Overall RMSE: {model_metrics.get('rmse', 'N/A')}
    - MAE: {model_metrics.get('mae', 'N/A')}
    - Trust Score: {model_metrics.get('trust_score', 'N/A')}
    - Symbolic Alignment: {model_metrics.get('symbolic_alignment', 'N/A')}
    
    Identified Error Patterns:
    {error_pattern_text}
    
    Based on the above information, suggest 3-5 specific rules that could improve model performance.
    For each rule, provide:
    1. A clear name/identifier
    2. The rule definition in a symbolic format
    3. Expected impact on model performance
    4. Confidence level in the rule's effectiveness (low/medium/high)
    
    Format each rule as follows:
    
    RULE: [name]
    DEFINITION: [symbolic definition]
    IMPACT: [expected impact]
    CONFIDENCE: [low/medium/high]
    EXPLANATION: [brief explanation of how this rule addresses observed issues]
    
    Rules should focus on addressing the identified error patterns and improving overall performance.
    """
    
    return prompt
    
def _parse_rules_from_gpt(self, response: str) -> List[Dict]:
    """
    Parse rules from GPT response into structured format
    """
    rules = []
    
    # Split response by rule sections
    rule_sections = response.split("RULE: ")
    
    # Skip first section if it doesn't contain a rule
    for section in rule_sections[1:]:
        rule = {}
        
        # Parse rule name
        rule_name_match = re.search(r'^(.+?)(\n|$)', section)
        if rule_name_match:
            rule["name"] = rule_name_match.group(1).strip()
        
        # Parse definition
        definition_match = re.search(r'DEFINITION:(.*?)(?=IMPACT:|$)', section, re.DOTALL)
        if definition_match:
            rule["definition"] = definition_match.group(1).strip()
        
        # Parse impact
        impact_match = re.search(r'IMPACT:(.*?)(?=CONFIDENCE:|$)', section, re.DOTALL)
        if impact_match:
            rule["impact"] = impact_match.group(1).strip()
        
        # Parse confidence
        confidence_match = re.search(r'CONFIDENCE:(.*?)(?=EXPLANATION:|$)', section, re.DOTALL)
        if confidence_match:
            rule["confidence"] = confidence_match.group(1).strip().lower()
        
        # Parse explanation
        explanation_match = re.search(r'EXPLANATION:(.*?)(?=RULE:|$)', section, re.DOTALL)
        if explanation_match:
            rule["explanation"] = explanation_match.group(1).strip()
        
        # Add metadata
        rule["source"] = "gpt"
        rule["generated_at"] = datetime.now().isoformat()
        
        rules.append(rule)
    
    return rules
```

### RecursiveRuleEvaluator

**Purpose:** Tests proposed rules through simulation and retrodiction to assess their impact and effectiveness before adoption.

**Core Classes/Functions:**
```python
class RecursiveRuleEvaluator:
    def __init__(self, config: Dict, rule_repository, simulator):
        self.config = config
        self.rule_repository = rule_repository
        self.simulator = simulator
        self.retrodiction_engine = RetrodictionEngine(config["retrodiction"])
        
    def evaluate_rule(self, rule_id: str, 
                     evaluation_config: Dict = None) -> Dict:
        """Evaluate a single rule using simulation and retrodiction"""
        # Get rule from repository
        rule = self.rule_repository.get_rule(rule_id)
        
        # Define evaluation configuration
        if evaluation_config is None:
            evaluation_config = self.config["default_evaluation"]
            
        # Set up baseline simulation (without the rule)
        baseline_results = self._run_simulation(
            rules=[],
            simulation_config=evaluation_config["simulation"]
        )
        
        # Run simulation with the new rule
        rule_results = self._run_simulation(
            rules=[rule],
            simulation_config=evaluation_config["simulation"]
        )
        
        # Calculate performance metrics
        metrics = self._calculate_metrics(baseline_results, rule_results)
        
        # Determine overall impact
        impact_assessment = self._assess_impact(metrics, rule)
        
        # Store evaluation results
        evaluation_id = self._store_evaluation(rule_id, metrics, impact_assessment)
        
        return {
            "evaluation_id": evaluation_id,
            "rule_id": rule_id,
            "metrics": metrics,
            "impact": impact_assessment,
            "timestamp": datetime.now().isoformat()
        }
        
    def batch_evaluate(self, rule_ids: List[str], 
                      evaluation_config: Dict = None) -> Dict:
        """Evaluate multiple rules in batch"""
        # Implementation
        
    def comparative_evaluate(self, rule_ids: List[str],
                           evaluation_config: Dict = None) -> Dict:
        """Evaluate multiple rules comparatively to find the best combination"""
        # Implementation
        
    def _run_simulation(self, rules: List[Dict], 
                      simulation_config: Dict) -> Dict:
        """Run simulation with specified rules and configuration"""
        # Implementation
        
    def _calculate_metrics(self, baseline_results: Dict, 
                         rule_results: Dict) -> Dict:
        """Calculate performance metrics by comparing baseline and rule results"""
        # Implementation
        
    def _assess_impact(self, metrics: Dict, rule: Dict) -> Dict:
        """Assess overall impact of the rule based on metrics"""
        # Implementation
        
    def _store_evaluation(self, rule_id: str, metrics: Dict,
                        impact_assessment: Dict) -> str:
        """Store evaluation results and return evaluation ID"""
        # Implementation
```

**Interfaces with Pulse components:**
- `simulation_engine.simulator_core`
- `trust_system.retrodiction_engine`

**Dependencies:**
- Simulation: numpy, pandas
- Statistical analysis: scipy
- Metrics calculation: scikit-learn

**Sample code snippet (Performance Metrics):**
```python
def _calculate_metrics(self, baseline_results: Dict, rule_results: Dict) -> Dict:
    """
    Calculate detailed performance metrics by comparing baseline and rule simulation results
    """
    import numpy as np
    from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
    
    metrics = {}
    
    # Get forecast values
    baseline_forecasts = baseline_results.get("forecasts", [])
    rule_forecasts = rule_results.get("forecasts", [])
    
    # Get actual values
    actual_values = baseline_results.get("actual_values", [])
    
    # Calculate error metrics if we have actual values
    if actual_values and len(actual_values) > 0:
        # Convert to numpy arrays
        baseline_array = np.array([f["value"] for f in baseline_forecasts])
        rule_array = np.array([f["value"] for f in rule_forecasts])
        actual_array = np.array(actual_values)
        
        # Basic error metrics
        metrics["baseline_rmse"] = float(np.sqrt(mean_squared_error(actual_array, baseline_array)))
        metrics["rule_rmse"] = float(np.sqrt(mean_squared_error(actual_array, rule_array)))
        
        metrics["baseline_mae"] = float(mean_absolute_error(actual_array, baseline_array))
        metrics["rule_mae"] = float(mean_absolute_error(actual_array, rule_array))
        
        metrics["baseline_r2"] = float(r2_score(actual_array, baseline_array))
        metrics["rule_r2"] = float(r2_score(actual_array, rule_array))
        
        # Calculate improvement percentages
        metrics["rmse_improvement"] = float(
            (metrics["baseline_rmse"] - metrics["rule_rmse"]) / metrics["baseline_rmse"] * 100
            if metrics["baseline_rmse"] > 0 else 0
        )
        
        metrics["mae_improvement"] = float(
            (metrics["baseline_mae"] - metrics["rule_mae"]) / metrics["baseline_mae"] * 100
            if metrics["baseline_mae"] > 0 else 0
        )
        
        # Calculate confidence intervals using bootstrap
        metrics["confidence_intervals"] = self._calculate_confidence_intervals(
            actual_array, baseline_array, rule_array
        )
    
    # Trust system metrics
    baseline_trust = baseline_results.get("trust_scores", {})
    rule_trust = rule_results.get("trust_scores", {})
    
    if baseline_trust and rule_trust:
        metrics["baseline_trust_score"] = float(baseline_trust.get("overall", 0))
        metrics["rule_trust_score"] = float(rule_trust.get("overall", 0))
        
        metrics["trust_improvement"] = float(
            (metrics["rule_trust_score"] - metrics["baseline_trust_score"])
            if "baseline_trust_score" in metrics and "rule_trust_score" in metrics
            else 0
        )
    
    # Symbolic system metrics
    baseline_symbolic = baseline_results.get("symbolic_metrics", {})
    rule_symbolic = rule_results.get("symbolic_metrics", {})
    
    if baseline_symbolic and rule_symbolic:
        metrics["baseline_symbolic_alignment"] = float(baseline_symbolic.get("alignment_score", 0))
        metrics["rule_symbolic_alignment"] = float(rule_symbolic.get("alignment_score", 0))
        
        metrics["symbolic_improvement"] = float(
            (metrics["rule_symbolic_alignment"] - metrics["baseline_symbolic_alignment"])
            if "baseline_symbolic_alignment" in metrics and "rule_symbolic_alignment" in metrics
            else 0
        )
    
    return metrics
```

### RuleRepository

**Purpose:** Stores, versions, and manages access to rules. Provides interfaces for rule retrieval and updates.

**Core Classes/Functions:**
```python
class RuleRepository:
    def __init__(self, config: Dict):
        self.config = config
        self.storage_path = config.get("storage_path", "rules")
        self.db_uri = config.get("db_uri", "sqlite:///rules.db")
        self.engine = create_engine(self.db_uri)
        
        # Ensure storage directory exists
        os.makedirs(self.storage_path, exist_ok=True)
        
        # Initialize database
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        
    def add_rule(self, rule: Dict) -> str:
        """Add a new rule to the repository"""
        # Generate unique ID if not provided
        rule_id = rule.get("id", str(uuid.uuid4()))
        rule["id"] = rule_id
        
        # Add metadata
        if "created_at" not in rule:
            rule["created_at"] = datetime.now().isoformat()
            
        if "version" not in rule:
            rule["version"] = 1
            
        if "status" not in rule:
            rule["status"] = "draft"
        
        # Save to database
        with self.Session() as session:
            rule_record = RuleRecord(
                id=rule_id,
                name=rule.get("name", ""),
                description=rule.get("description", ""),
                source=rule.get("source", ""),
                version=rule["version"],
                status=rule["status"],
                created_at=rule["created_at"],
                rule_data=json.dumps(rule)
            )
            
            session.add(rule_record)
            session.commit()
            
        # Save to file system (for versioning)
        rule_path = os.path.join(self.storage_path, f"{rule_id}_v{rule['version']}.json")
        with open(rule_path, 'w') as f:
            json.dump(rule, f, indent=2)
            
        return rule_id
        
    def get_rule(self, rule_id: str, version: int = None) -> Dict:
        """Get a rule by ID and optional version"""
        with self.Session() as session:
            query = session.query(RuleRecord).filter(RuleRecord.id == rule_id)
            
            if version is not None:
                query = query.filter(RuleRecord.version == version)
            else:
                query = query.order_by(RuleRecord.version.desc())
                
            rule_record = query.first()
            
            if not rule_record:
                raise ValueError(f"Rule {rule_id} not found")
                
            return json.loads(rule_record.rule_data)
            
    def update_rule(self, rule_id: str, updates: Dict) -> Dict:
        """Update an existing rule, creating a new version"""
        # Get current rule
        current_rule = self.get_rule(rule_id)
        
        # Create new version
        new_version = current_rule["version"] + 1
        
        # Apply updates
        updated_rule = {**current_rule, **updates}
        updated_rule["version"] = new_version
        updated_rule["updated_at"] = datetime.now().isoformat()
        
        # Add version history
        if "version_history" not in updated_rule:
            updated_rule["version_history"] = []
            
        updated_rule["version_history"].append({
            "version": current_rule["version"],
            "timestamp": current_rule.get("updated_at", current_rule["created_at"]),
            "changes": list(updates.keys())
        })
        
        # Save new version
        with self.Session() as session:
            rule_record = RuleRecord(
                id=rule_id,
                name=updated_rule.get("name", ""),
                description=updated_rule.get("description", ""),
                source=updated_rule.get("source", ""),
                version=new_version,
                status=updated_rule["status"],
                created_at=current_rule["created_at"],
                rule_data=json.dumps(updated_rule)
            )
            
            session.add(rule_record)
            session.commit()
            
        # Save to file system
        rule_path = os.path.join(self.storage_path, f"{rule_id}_v{new_version}.json")
        with open(rule_path, 'w') as f:
            json.dump(updated_rule, f, indent=2)
            
        return updated_rule
        
    def search_rules(self, filters: Dict = None, 
                   sort_by: str = "created_at", 
                   sort_order: str = "desc",
                   limit: int = 100,
                   offset: int = 0) -> List[Dict]:
        """Search rules with filters and sorting"""
        # Implementation
        
    def delete_rule(self, rule_id: str) -> bool:
        """Mark a rule as deleted"""
        # Implementation
```

**Interfaces with Pulse components:**
- `symbolic_system.symbolic_utils`
- Rule storage system

**Dependencies:**
- Database: sqlalchemy
- Version control: gitpython (optional)
- Query building: sqlalchemy-filters

**Sample code snippet (Search Rules):**
```python
def search_rules(self, filters: Dict = None, 
               sort_by: str = "created_at",
               sort_order: str = "desc",
               limit: int = 100,
               offset: int = 0) -> List[Dict]:
    """
    Search rules with filters, sorting, and pagination
    
    Args:
        filters: Dict of field-value pairs to filter by
        sort_by: Field to sort by
        sort_order: 'asc' or 'desc'
        limit: Maximum number of results
        offset: Offset for pagination
        
    Returns:
        List of rule dictionaries matching criteria
    """
    with self.Session() as session:
        query = session.query(RuleRecord)
        
        # Apply filters
        if filters:
            for field, value in filters.items():
                if field == "name":
                    query = query.filter(RuleRecord.name.like(f"%{value}%"))
                elif field == "description":
                    query = query.filter(RuleRecord.description.like(f"%{value}%"))
                elif field == "status":
                    query = query.filter(RuleRecord.status == value)
                elif field == "source":
                    query = query.filter(RuleRecord.source == value)
                elif field == "created_after":
                    query = query.filter(RuleRecord.created_at >= value)
                elif field == "created_before":
                    query = query.filter(RuleRecord.created_at <= value)
                # Add more filters as needed
                    
        # Handle latest version only flag
        if filters and filters.get("latest_version_only", False):
            # This is a complex query in SQL that requires a subquery
            # to get the maximum version for each rule ID
            subquery = (
                session.query(
                    RuleRecord.id,
                    func.max(RuleRecord.version).label("max_version")
                )
                .group_by(RuleRecord.id)
                .subquery()
            )
            
            query = query.join(
                subquery,
                and_(
                    RuleRecord.id == subquery.c.id,
                    RuleRecord.version == subquery.c.max_version
                )
            )
                
        # Apply sorting
        if sort_by == "name":
            query = query.order_by(
                asc(RuleRecord.name) if sort_order == "asc" else desc(RuleRecord.name)
            )
        elif sort_by == "created_at":
            query = query.order_by(
                asc(RuleRecord.created_at) if sort_order == "asc" else desc(RuleRecord.created_at)
            )
        elif sort_by == "version":
            query = query.order_by(
                asc(RuleRecord.version) if sort_order == "asc" else desc(RuleRecord.version)
            )
        # Add more sort options as needed
            
        # Apply pagination
        query = query.limit(limit).offset(offset)
        
        # Execute query
        rule_records = query.all()
        
        # Convert to dictionaries
        rules = [json.loads(record.rule_data) for record in rule_records]
        
        return rules
```

## Phase 4: Metrics Components

### RecursiveTrainingMetrics

**Purpose:** Calculates, tracks, and reports performance metrics for models and rules. Implements metrics like retrodiction error, symbolic alignment score, and trust delta.

**Core Classes/Functions:**
```python
class RecursiveTrainingMetrics:
    def __init__(self, config: Dict, metrics_store):
        self.config = config
        self.metrics_store = metrics_store
        
    def calculate_model_metrics(self, model_id: str, 
                              test_data: Dict,
                              predictions: Dict) -> Dict:
        """Calculate comprehensive metrics for model predictions"""
        # Get actual values and predictions
        actual_values = test_data.get("actual_values", [])
        predicted_values = predictions.get("values", [])
        
        if len(actual_values) != len(predicted_values):
            raise ValueError(
                f"Length mismatch: {len(actual_values)} actual vs {len(predicted_values)} predicted"
            )
            
        # Calculate basic error metrics
        basic_metrics = self._calculate_basic_metrics(actual_values, predicted_values)
        
        # Calculate advanced metrics based on configuration
        advanced_metrics = {}
        
        if self.config.get("calculate_symbolic_alignment", True):
            advanced_metrics["symbolic_alignment"] = self._calculate_symbolic_alignment(
                model_id, test_data, predictions
            )
            
        if self.config.get("calculate_trust_delta", True):
            advanced_metrics["trust_delta"] = self._calculate_trust_delta(
                model_id, test_data, predictions
            )
            
        # Combine metrics
        all_metrics = {**basic_metrics, **advanced_metrics}
        
        # Store metrics
        metric_id = self.metrics_store.store_metrics(
            model_id=model_id,
            metrics=all_metrics,
            context={
                "test_data_id": test_data.get("id"),
                "prediction_id": predictions.get("id"),
                "timestamp": datetime.now().isoformat()
            }
        )
        
        return {
            "metric_id": metric_id,
            "model_id": model_id,
            "metrics": all_metrics,
            "timestamp": datetime.now().isoformat()
        }
        
    def calculate_rule_metrics(self, rule_id: str,
                             baseline_results: Dict,
                             rule_results: Dict) -> Dict:
        """Calculate metrics for rule evaluation"""
        # Implementation
        
    def _calculate_basic_metrics(self, actual_values: List[float],
                               predicted_values: List[float]) -> Dict:
        """Calculate basic error metrics (RMSE, MAE, etc.)"""
        # Implementation
        
    def _calculate_symbolic_alignment(self, model_id: str, 
                                   test_data: Dict,
                                   predictions: Dict) -> Dict:
        """Calculate symbolic alignment score for predictions"""
        # Implementation
        
    def _calculate_trust_delta(self, model_id: str,
                             test_data: Dict,
                             predictions: Dict) -> Dict:
        """Calculate trust delta metrics"""
        # Implementation
```

**Interfaces with Pulse components:**
- `symbolic_system.symbolic_trace_scorer`
- `trust_system.trust_scoring_service`

**Dependencies:**
- Metrics calculation: scikit-learn, scipy
- Time series analysis: statsmodels
- Visualization: matplotlib (for reports)

**Sample code snippet (Basic Metrics):**
```python
def _calculate_basic_metrics(self, actual_values: List[float],
                          predicted_values: List[float]) -> Dict:
    """
    Calculate basic error metrics for regression predictions
    
    Args:
        actual_values: List of actual target values
        predicted_values: List of model predictions
        
    Returns:
        Dictionary of calculated metrics
    """
    import numpy as np
    from sklearn.metrics import (
        mean_squared_error, mean_absolute_error, 
        r2_score, mean_absolute_percentage_error
    )
    
    # Convert to numpy arrays
    y_true = np.array(actual_values)
    y_pred = np.array(predicted_values)
    
    # Calculate basic metrics
    metrics = {
        "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "r2": float(r2_score(y_true, y_pred)),
    }
    
    # Calculate MAPE safely (avoiding division by zero)
    try:
        metrics["mape"] = float(mean_absolute_percentage_error(y_true, y_pred))
    except:
        # Handle cases with zeros in actual values
        non_zero_indices = y_true != 0
        if np.any(non_zero_indices):
            safe_y_true = y_true[non_zero_indices]
            safe_y_pred = y_pred[non_zero_indices]
            metrics["mape"] = float(mean_absolute_percentage_error(safe_y_true, safe_y_pred))
        else:
            metrics["mape"] = float('nan')
    
    # Calculate additional metrics
    # Mean Bias Error
    metrics["mbe"] = float(np.mean(y_pred - y_true))
    
    # Calculate percentile-based metrics
    metrics["median_ae"] = float(np.median(np.abs(y_pred - y_true)))
    metrics["p90_ae"] = float(np.percentile(np.abs(y_pred - y_true), 90))
    
    # Theil's U2 (forecast accuracy)
    # U2 = sqrt(sum((y_pred - y_true)^2) / sum(y_true^2))
    # Values < 1 indicate model is better than naive forecast
    with np.errstate(divide='ignore', invalid='ignore'):
        if np.sum(y_true**2) > 0:
            metrics["theils_u2"] = float(
                np.sqrt(np.sum((y_pred - y_true)**2) / np.sum(y_true**2))
            )
        else:
            metrics["theils_u2"] = float('nan')
    
    return metrics
```

### MetricsStore

**Purpose:** Persists metrics for long-term analysis, comparison, and reporting. Provides query capabilities for metric-based decision making.

**Core Classes/Functions:**
```python
class MetricsStore:
    def __init__(self, config: Dict):
        self.config = config
        self.db_uri = config.get("db_uri", "sqlite:///metrics.db")
        self.engine = create_engine(self.db_uri)
        
        # Initialize database
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        
    def store_metrics(self, model_id: str, metrics: Dict, 
                    context: Dict = None) -> str:
        """Store metrics for a model with optional context"""
        metric_id = str(uuid.uuid4())
        
        timestamp = context.get("timestamp", datetime.now().isoformat()) if context else datetime.now().isoformat()
        
        # Create record in database
        with self.Session() as session:
            metric_record = MetricRecord(
                id=metric_id,
                model_id=model_id,
                timestamp=timestamp,
                metrics_data=json.dumps(metrics),
                context_data=json.dumps(context) if context else None
            )
            
            session.add(metric_record)
            session.commit()
            
        return metric_id
        
    def get_metrics(self, metric_id: str) -> Dict:
        """Get metrics by ID"""
        with self.Session() as session:
            metric_record = session.query(MetricRecord).filter(
                MetricRecord.id == metric_id
            ).first()
            
            if not metric_record:
                raise ValueError(f"Metric {metric_id} not found")
                
            return {
                "id": metric_record.id,
                "model_id": metric_record.model_id,
                "timestamp": metric_record.timestamp,
                "metrics": json.loads(metric_record.metrics_data),
                "context": json.loads(metric_record.context_data) if metric_record.context_data else None
            }
            
    def get_model_metrics_history(self, model_id: str, 
                               metric_names: List[str] = None,
                               start_time: str = None,
                               end_time: str = None,
                               limit: int = 100) -> List[Dict]:
        """Get historical metrics for a model"""
        # Implementation
        
    def get_metric_summary(self, model_ids: List[str],
                         metric_names: List[str],
                         aggregation: str = "mean") -> Dict:
        """Get summary statistics for metrics across models"""
        # Implementation
        
    def compare_metrics(self, base_model_id: str, 
                      comparison_model_ids: List[str],
                      metric_names: List[str]) -> Dict:
        """Compare metrics between base model and other models"""
        # Implementation
```

**Interfaces with Pulse components:**
- `visualization` module for metric dashboards
- `core.path_registry` for storage locations

**Dependencies:**
- Database: sqlalchemy
- Query building: sqlalchemy-filters
- Visualization: matplotlib, seaborn

**Sample code snippet (Model Comparison):**
```python
def compare_metrics(self, base_model_id: str, 
                  comparison_model_ids: List[str],
                  metric_names: List[str]) -> Dict:
    """
    Compare metrics between a base model and a list of comparison models
    
    Args:
        base_model_id: ID of the base model to compare against
        comparison_model_ids: List of model IDs to compare
        metric_names: List of metric names to include in comparison
        
    Returns:
        Dictionary with comparison results
    """
    # Get latest metrics for base model
    base_metrics = self.get_model_metrics_history(
        model_id=base_model_id,
        metric_names=metric_names,
        limit=1
    )
    
    if not base_metrics:
        raise ValueError(f"No metrics found for base model {base_model_id}")
        
    base_metrics = base_metrics[0]["metrics"]
    
    # Get latest metrics for comparison models
    comparison_results = {}
    
    for model_id in comparison_model_ids:
        model_metrics = self.get_model_metrics_history(
            model_id=model_id,
            metric_names=metric_names,
            limit=1
        )
        
        if not model_metrics:
            continue
            
        model_metrics = model_metrics[0]["metrics"]
        
        # Calculate differences
        diffs = {}
        
        for metric_name in metric_names:
            if metric_name in base_metrics and metric_name in model_metrics:
                base_value = base_metrics[metric_name]
                comp_value = model_metrics[metric_name]
                
                # Skip if values are not numeric
                if not (isinstance(base_value, (int, float)) and 
                        isinstance(comp_value, (int, float))):
                    continue
                    
                # Calculate absolute and relative differences
                abs_diff = comp_value - base_value
                
                # Calculate relative diff safely
                if base_value != 0:
                    rel_diff = (comp_value - base_value) / abs(base_value) * 100
                else:
                    rel_diff = float('inf') if comp_value > 0 else (
                        float('-inf') if comp_value < 0 else 0
                    )
                    
                # Determine if the difference is an improvement
                # For most metrics, lower is better (errors)
                is_improvement = abs_diff < 0
                
                # Exception for metrics where higher is better
                if metric_name in ["r2", "symbolic_alignment", "trust_score"]:
                    is_improvement = abs_diff > 0
                    
                diffs[metric_name] = {
                    "base_value": base_value,
                    "comparison_value": comp_value,
                    "absolute_diff": abs_diff,
                    "relative_diff_percent": rel_diff,
                    "is_improvement": is_improvement
                }
                
        comparison_results[model_id] = {
            "metrics": model_metrics,
            "differences": diffs,
            "overall_improvement": self._calculate_overall_improvement(diffs)
        }
        
    return {
        "base_model": {
            "id": base_model_id,
            "metrics": base_metrics
        },
        "comparisons": comparison_results
    }
```

### EnhancedRetrodictionCurriculum

**Purpose:** Designs optimal learning sequences for models based on historical performance and current objectives. Prioritizes scenarios to maximize learning efficiency.

**Core Classes/Functions:**
```python
class EnhancedRetrodictionCurriculum:
    def __init__(self, config: Dict, metrics_store, feature_store):
        self.config = config
        self.metrics_store = metrics_store
        self.feature_store = feature_store
        self.learning_rate_scheduler = LearningRateScheduler(config["learning_rate"])
        
    def generate_curriculum(self, model_id: str, 
                           objectives: Dict,
                           available_scenarios: List[Dict]) -> Dict:
        """Generate an optimal learning curriculum for a model"""
        # Get model's historical performance
        model_history = self.metrics_store.get_model_metrics_history(
            model_id=model_id,
            limit=100
        )
        
        # Analyze model's strengths and weaknesses
        model_analysis = self._analyze_model_performance(model_history)
        
        # Score available scenarios based on learning potential
        scenario_scores = self._score_scenarios(
            model_analysis=model_analysis,
            objectives=objectives,
            scenarios=available_scenarios
        )
        
        # Select optimal scenario sequence
        selected_scenarios = self._select_optimal_sequence(
            scenario_scores=scenario_scores,
            max_scenarios=self.config.get("max_scenarios_per_curriculum", 10)
        )
        
        # Configure learning parameters for each scenario
        configured_scenarios = self._configure_learning_params(
            model_id=model_id,
            scenarios=selected_scenarios,
            model_analysis=model_analysis
        )
        
        # Create curriculum
        curriculum_id = str(uuid.uuid4())
        
        curriculum = {
            "id": curriculum_id,
            "model_id": model_id,
            "created_at": datetime.now().isoformat(),
            "objectives": objectives,
            "scenarios": configured_scenarios,
            "metadata": {
                "model_analysis": model_analysis,
                "scenario_selection_criteria": self._get_selection_criteria(objectives)
            }
        }
        
        # Store curriculum
        self._store_curriculum(curriculum)
        
        return curriculum
        
    def _analyze_model_performance(self, model_history: List[Dict]) -> Dict:
        """Analyze model's historical performance to identify strengths/weaknesses"""
        # Implementation
        
    def _score_scenarios(self, model_analysis: Dict,
                       objectives: Dict,
                       scenarios: List[Dict]) -> List[Dict]:
        """Score scenarios based on learning potential for the model"""
        # Implementation
        
    def _select_optimal_sequence(self, scenario_scores: List[Dict],
                               max_scenarios: int) -> List[Dict]:
        """Select optimal sequence of scenarios for learning curriculum"""
        # Implementation
        
    def _configure_learning_params(self, model_id: str,
                                scenarios: List[Dict],
                                model_analysis: Dict) -> List[Dict]:
        """Configure learning parameters for each scenario"""
        # Implementation
        
    def _store_curriculum(self, curriculum: Dict):
        """Store curriculum for later use"""
        # Implementation
```

**Interfaces with Pulse components:**
- `learning.retrodiction_curriculum`
- `learning.compute_retrodiction_error`

**Dependencies:**
- Machine learning: scikit-learn
- Optimization: scipy.optimize
- Deep learning: pytorch (optional)

**Sample code snippet (Scenario Scoring):**
```python
def _score_scenarios(self, model_analysis: Dict,
                   objectives: Dict,
                   scenarios: List[Dict]) -> List[Dict]:
    """
    Score scenarios based on learning potential for the model
    
    Args:
        model_analysis: Analysis of model's historical performance
        objectives: Learning objectives and priorities
        scenarios: List of available training scenarios
        
    Returns:
        List of scenarios with learning potential scores
    """
    scored_scenarios = []
    
    # Set score weights based on objectives
    # Default weights if not specified
    default_weights = {
        "error_reduction": 0.4,
        "coverage_expansion": 0.3,
        "edge_case_exposure": 0.2,
        "novelty": 0.1
    }
    
    # Override with user-specified weights
    weights = objectives.get("weights", default_weights)
    
    # Normalize weights to sum to 1
    weight_sum = sum(weights.values())
    norm_weights = {k: v / weight_sum for k, v in weights.items()}
    
    # Get model weaknesses
    weak_feature_ranges = model_analysis.get("weak_feature_ranges", {})
    weak_patterns = model_analysis.get("weak_patterns", [])
    covered_cases = model_analysis.get("covered_cases", [])
    
    for scenario in scenarios:
        # Calculate individual scores for different criteria
        scores = {}
        
        # 1. Error reduction potential (how well scenario addresses weak areas)
        error_score = self._calculate_error_reduction_score(
            scenario=scenario,
            weak_ranges=weak_feature_ranges,
            weak_patterns=weak_patterns
        )
        scores["error_reduction"] = error_score
        
        # 2. Coverage expansion (how much new territory this covers)
        coverage_score = self._calculate_coverage_score(
            scenario=scenario,
            covered_cases=covered_cases
        )
        scores["coverage_expansion"] = coverage_score
        
        # 3. Edge case exposure (whether scenario includes edge cases)
        edge_score = self._calculate_edge_case_score(scenario)
        scores["edge_case_exposure"] = edge_score
        
        # 4. Novelty (how different this scenario is from previously seen ones)
        novelty_score = self._calculate_novelty_score(
            scenario=scenario,
            model_history=model_analysis.get("training_history", [])
        )
        scores["novelty"] = novelty_score
        
        # Compute weighted sum for overall score
        overall_score = sum(
            score * norm_weights.get(criterion, 0)
            for criterion, score in scores.items()
        )
        
        # Add scores to scenario
        scored_scenario = {
            **scenario,
            "learning_potential": {
                "overall_score": overall_score,
                "component_scores": scores
            }
        }
        
        scored_scenarios.append(scored_scenario)
    
    # Sort by overall score (descending)
    sorted_scenarios = sorted(
        scored_scenarios,
        key=lambda x: x["learning_potential"]["overall_score"],
        reverse=True
    )
    
    return sorted_scenarios
```

## Phase 5: Error Handling Components

### RecursiveTrainingErrorHandler

**Purpose:** Detects, logs, and responds to errors during training. Implements fallback strategies for different failure scenarios.

**Core Classes/Functions:**
```python
class RecursiveTrainingErrorHandler:
    def __init__(self, config: Dict):
        self.config = config
        self.error_log = ErrorLog(config["error_log"])
        self.notification_service = NotificationService(config["notifications"])
        self.fallback_strategies = self._load_fallback_strategies()
        
    def _load_fallback_strategies(self) -> Dict:
        """Load error handling strategies from configuration"""
        strategies = {}
        
        for error_type, strategy_config in self.config["strategies"].items():
            strategy_class = import_class(strategy_config["class"])
            strategies[error_type] = strategy_class(**strategy_config["params"])
            
        return strategies
        
    def handle_error(self, error: Exception, context: Dict) -> Dict:
        """Handle an error that occurred during training"""
        # Determine error type
        error_type = self._classify_error(error)
        
        # Log error
        error_id = self.error_log.log_error(
            error_type=error_type,
            error_message=str(error),
            traceback=traceback.format_exc(),
            context=context
        )
        
        # Determine severity
        severity = self._determine_severity(error_type, context)
        
        # Choose and apply appropriate strategy
        strategy = self._get_strategy(error_type)
        result = strategy.handle(error, context) if strategy else None
        
        # Send notifications for high severity errors
        if severity >= self.config.get("notification_threshold", 3):
            self.notification_service.send_notification(
                title=f"Training Error: {error_type}",
                message=f"Error in {context.get('operation', 'unknown operation')}: {str(error)}",
                severity=severity,
                error_id=error_id
            )
            
        return {
            "error_id": error_id,
            "error_type": error_type,
            "severity": severity,
            "handled": strategy is not None,
            "resolution": result,
            "timestamp": datetime.now().isoformat()
        }
        
    def _classify_error(self, error: Exception) -> str:
        """Classify error into one of the predefined types"""
        # Implementation
        
    def _determine_severity(self, error_type: str, context: Dict) -> int:
        """Determine error severity (1-5 scale)"""
        # Implementation
        
    def _get_strategy(self, error_type: str):
        """Get appropriate strategy for error type"""
        # Implementation
```

**Interfaces with Pulse components:**
- `core.pulse_prompt_logger` for error logging

**Dependencies:**
- Error tracking: sentry-sdk (optional)
- Notification: slack-sdk, sendgrid
- Process management: psutil

**Sample code snippet (Error Classification):**
```python
def _classify_error(self, error: Exception) -> str:
    """
    Classify error into one of the predefined types
    
    Classification hierarchy:
    - data.invalid_input
    - data.schema_mismatch
    - data.missing_features
    - model.initialization_failed
    - model.training_diverged
    - model.gpu_out_of_memory
    - storage.permission_denied
    - storage.not_found
    - network.connection_failed
    - network.timeout
    - system.resource_exhausted
    - unknown
    """
    error_class = error.__class__.__name__
    error_message = str(error).lower()
    
    # Data errors
    if any(term in error_message for term in ["invalid input", "invalid data", "malformed"]):
        return "data.invalid_input"
    
    if any(term in error_message for term in ["schema", "field", "column", "type mismatch"]):
        return "data.schema_mismatch"
    
    if any(term in error_message for term in ["missing feature", "required field", "not found in input"]):
        return "data.missing_features"
    
    # Model errors
    if isinstance(error, (ValueError, TypeError)) and "model" in error_message:
        if "initialize" in error_message or "instantiate" in error_message:
            return "model.initialization_failed"
    
    if "nan" in error_message or "inf" in error_message or "diverge" in error_message:
        return "model.training_diverged"
    
    if any(term in error_message for term in ["cuda out of memory", "gpu memory", "cuda error"]):
        return "model.gpu_out_of_memory"
    
    # Storage errors
    if isinstance(error, (PermissionError, IOError)):
        return "storage.permission_denied"
    
    if isinstance(error, FileNotFoundError) or "not found" in error_message:
        return "storage.not_found"
    
    # Network errors
    if any(term in error_message for term in ["connection", "network", "unreachable"]):
        return "network.connection_failed"
    
    if "timeout" in error_message:
        return "network.timeout"
    
    # System errors
    if any(term in error_message for term in ["memory", "disk space", "resource"]):
        return "system.resource_exhausted"
    
    # Default to unknown
    return "unknown"
```

### RecursiveTrainingMonitor

**Purpose:** Monitors training processes in real-time, detecting anomalies and providing insights into model evolution.

**Core Classes/Functions:**
```python
class RecursiveTrainingMonitor:
    def __init__(self, config: Dict):
        self.config = config
        self.notification_threshold = config.get("notification_threshold", 0.3)
        self.metrics_client = MetricsClient(config.get("metrics", {}))
        self.anomaly_detectors = self._initialize_anomaly_detectors()
        
    def _initialize_anomaly_detectors(self) -> Dict:
        """Initialize anomaly detectors for different metrics"""
        detectors = {}
        
        for metric, detector_config in self.config.get("anomaly_detectors", {}).items():
            detector_class = import_class(detector_config["class"])
            detectors[metric] = detector_class(**detector_config.get("params", {}))
            
        return detectors
        
    def monitor_training(self, training_id: str, metrics: Dict) -> Dict:
        """Monitor training metrics and detect anomalies"""
        # Get baseline metrics for comparison
        baseline_metrics = self._get_baseline_metrics(training_id)
        
        # Check for anomalies in each metric
        anomalies = {}
        
        for metric_name, metric_value in metrics.items():
            if metric_name in self.anomaly_detectors:
                detector = self.anomaly_detectors[metric_name]
                is_anomaly, anomaly_score, details = detector.detect(
                    value=metric_value,
                    history=baseline_metrics.get(metric_name, [])
                )
                
                if is_anomaly:
                    anomalies[metric_name] = {
                        "value": metric_value,
                        "score": anomaly_score,
                        "details": details
                    }
        
        # Calculate overall anomaly score
        overall_score = self._calculate_overall_anomaly_score(anomalies)
        
        # Log monitoring results
        monitoring_result = {
            "training_id": training_id,
            "timestamp": datetime.now().isoformat(),
            "metrics": metrics,
            "anomalies": anomalies,
            "overall_anomaly_score": overall_score,
            "requires_attention": overall_score >= self.notification_threshold
        }
        
        self.metrics_client.log_monitoring_result(monitoring_result)
        
        # Send notification if needed
        if monitoring_result["requires_attention"]:
            self._send_notification(training_id, monitoring_result)
            
        return monitoring_result
        
    def _get_baseline_metrics(self, training_id: str) -> Dict:
        """Get baseline metrics for the training job"""
        # Implementation
        
    def _calculate_overall_anomaly_score(self, anomalies: Dict) -> float:
        """Calculate overall anomaly score from individual metric anomalies"""
        # Implementation
        
    def _send_notification(self, training_id: str, monitoring_result: Dict):
        """Send notification about anomalous training"""
        # Implementation
```

**Interfaces with Pulse components:**
- `core.pulse_prompt_logger` for logging
- `visualization` module for monitoring dashboards

**Dependencies:**
- Monitoring: prometheus-client
- Anomaly detection: scikit-learn, alibi-detect
- Notification: slack-sdk

**Sample code snippet (Anomaly Detection):**
```python
class StatisticalAnomalyDetector:
    """
    Detects anomalies in metrics using statistical methods (Z-score, IQR)
    """
    def __init__(self, method="z-score", threshold=3.0, window_size=10):
        self.method = method
        self.threshold = threshold
        self.window_size = window_size
        
    def detect(self, value: float, history: List[float]) -> Tuple[bool, float, Dict]:
        """
        Detect if a value is anomalous compared to historical values
        
        Args:
            value: Current metric value
            history: Historical values for the metric
            
        Returns:
            Tuple of (is_anomaly, anomaly_score, details)
        """
        if len(history) < 2:
            return False, 0.0, {"reason": "Not enough history for detection"}
            
        # Use recent history for comparison
        recent_history = history[-self.window_size:] if len(history) > self.window_size else history
        
        if self.method == "z-score":
            # Z-score method
            mean = np.mean(recent_history)
            std = np.std(recent_history)
            
            if std == 0:
                return False, 0.0, {"reason": "Zero standard deviation in history"}
                
            z_score = abs((value - mean) / std)
            is_anomaly = z_score > self.threshold
            
            return is_anomaly, z_score / self.threshold, {
                "mean": mean,
                "std": std,
                "z_score": z_score,
                "threshold": self.threshold
            }
            
        elif self.method == "iqr":
            # IQR method
            q1 = np.percentile(recent_history, 25)
            q3 = np.percentile(recent_history, 75)
            iqr = q3 - q1
            
            lower_bound = q1 - self.threshold * iqr
            upper_bound = q3 + self.threshold * iqr
            
            is_anomaly = value < lower_bound or value > upper_bound
            
            # Calculate how far outside the bounds
            if is_anomaly:
                if value < lower_bound:
                    distance = (lower_bound - value) / iqr
                else:
                    distance = (value - upper_bound) / iqr
            else:
                distance = 0.0
                
            return is_anomaly, distance, {
                "q1": q1,
                "q3": q3,
                "iqr": iqr,
                "lower_bound": lower_bound,
                "upper_bound": upper_bound
            }
            
        else:
            raise ValueError(f"Unknown anomaly detection method: {self.method}")
```

### RecursiveTrainingRecovery

**Purpose:** Recovers from training failures, implementing strategies to resume interrupted training, restore models from checkpoints, and adapt to errors.

**Core Classes/Functions:**
```python
class RecursiveTrainingRecovery:
    def __init__(self, config: Dict):
        self.config = config
        self.checkpoint_manager = CheckpointManager(config["checkpoints"])
        self.recovery_strategies = self._load_recovery_strategies()
        
    def _load_recovery_strategies(self) -> Dict:
        """Load recovery strategies from configuration"""
        strategies = {}
        
        for error_type, strategy_config in self.config["strategies"].items():
            strategy_class = import_class(strategy_config["class"])
            strategies[error_type] = strategy_class(**strategy_config.get("params", {}))
            
        return strategies
        
    def recover_training(self, training_id: str, error_info: Dict) -> Dict:
        """Attempt to recover a failed training job"""
        # Get training metadata
        training_meta = self._get_training_metadata(training_id)
        
        # Get appropriate recovery strategy
        error_type = error_info.get("error_type", "unknown")
        strategy = self._get_recovery_strategy(error_type)
        
        if not strategy:
            return {
                "training_id": training_id,
                "status": "recovery_failed",
                "reason": f"No recovery strategy available for error type: {error_type}",
                "timestamp": datetime.now().isoformat()
            }
            
        # Find latest checkpoint
        checkpoint = self.checkpoint_manager.get_latest_checkpoint(training_id)
        
        # Apply recovery strategy
        recovery_result = strategy.recover(
            training_meta=training_meta,
            error_info=error_info,
            checkpoint=checkpoint
        )
        
        # Log recovery attempt
        self._log_recovery_attempt(
            training_id=training_id,
            error_info=error_info,
            recovery_result=recovery_result
        )
        
        return {
            "training_id": training_id,
            "status": recovery_result.get("status", "unknown"),
            "new_training_id": recovery_result.get("new_training_id"),
            "strategy_used": strategy.__class__.__name__,
            "timestamp": datetime.now().isoformat()
        }
        
    def _get_training_metadata(self, training_id: str) -> Dict:
        """Get metadata for a training job"""
        # Implementation
        
    def _get_recovery_strategy(self, error_type: str):
        """Get appropriate recovery strategy for error type"""
        # Implementation
        
    def _log_recovery_attempt(self, training_id: str, 
                            error_info: Dict,
                            recovery_result: Dict):
        """Log recovery attempt for auditing and analysis"""
        # Implementation
```

**Interfaces with Pulse components:**
- Training job management system
- Model storage system

**Dependencies:**
- Model serialization: torch.save, pickle
- Process management: psutil
- Workflow management: airflow client (optional)

**Sample code snippet (Checkpoint Management):**
```python
class CheckpointManager:
    """
    Manages model checkpoints for resuming interrupted training
    """
    def __init__(self, config: Dict):
        self.config = config
        self.checkpoint_dir = Path(config.get("checkpoint_dir", "checkpoints"))
        self.max_checkpoints = config.get("max_checkpoints_per_training", 3)
        
        # Ensure checkpoint directory exists
        self.checkpoint_dir.mkdir(exist_ok=True, parents=True)
        
    def save_checkpoint(self, training_id: str, model_state: Dict, 
                       optimizer_state: Dict, epoch: int, 
                       metrics: Dict) -> str:
        """
        Save a model checkpoint
        
        Args:
            training_id: ID of the training job
            model_state: Model state dict
            optimizer_state: Optimizer state dict
            epoch: Current epoch number
            metrics: Current metrics
            
        Returns:
            Checkpoint ID
        """
        checkpoint_id = f"{training_id}_{epoch}_{int(time.time())}"
        
        # Create checkpoint directory for this training job
        training_checkpoint_dir = self.checkpoint_dir / training_id
        training_checkpoint_dir.mkdir(exist_ok=True)
        
        # Build checkpoint data
        checkpoint_data = {
            "id": checkpoint_id,
            "training_id": training_id,
            "epoch": epoch,
            "model_state": model_state,
            "optimizer_state": optimizer_state,
            "metrics": metrics,
            "timestamp": datetime.now().isoformat()
        }
        
        # Save checkpoint
        checkpoint_path = training_checkpoint_dir / f"{checkpoint_id}.pt"
        with open(checkpoint_path, 'wb') as f:
            torch.save(checkpoint_data, f)
            
        # Prune old checkpoints if needed
        self._prune_old_checkpoints(training_id)
        
        return checkpoint_id
        
    def get_latest_checkpoint(self, training_id: str) -> Optional[Dict]:
        """
        Get the latest checkpoint for a training job
        
        Args:
            training_id: ID of the training job
            
        Returns:
            Checkpoint data or None if no checkpoints exist
        """
        training_checkpoint_dir = self.checkpoint_dir / training_id
        
        if not training_checkpoint_dir.exists():
            return None
            
        checkpoint_files = list(training_checkpoint_dir.glob("*.pt"))
        
        if not checkpoint_files:
            return None
            
        # Sort by modification time (latest first)
        checkpoint_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        # Load the latest checkpoint
        with open(checkpoint_files[0], 'rb') as f:
            checkpoint_data = torch.load(f)
            
        return checkpoint_data
        
    def _prune_old_checkpoints(self, training_id: str):
        """
        Remove old checkpoints to save disk space
        
        Args:
            training_id: ID of the training job
        """
        training_checkpoint_dir = self.checkpoint_dir / training_id
        
        if not training_checkpoint_dir.exists():
            return
            
        checkpoint_files = list(training_checkpoint_dir.glob("*.pt"))
        
        if len(checkpoint_files) <= self.max_checkpoints:
            return
            
        # Sort by modification time (oldest first)
        checkpoint_files.sort(key=lambda x: x.stat().st_mtime)
        
        # Remove the oldest checkpoints
        for file in checkpoint_files[:-self.max_checkpoints]:
            file.unlink()
```

## Technical Challenges and Mitigations

1. **Data Consistency and Schema Evolution**
   - **Challenge**: Ensuring consistent data schemas across ingestion sources
   - **Mitigation**: Implement strict schema validation with versioning, migration tooling, and adaptive converters

2. **Training Stability and Reproducibility**
   - **Challenge**: Maintaining stable training across environments and hardware
   - **Mitigation**: Use deterministic training modes, containerized environments, fixed random seeds, and comprehensive checkpointing

3. **Resource Utilization and Scaling**
   - **Challenge**: Efficiently managing computational resources for large-scale training
   - **Mitigation**: Implement dynamic resource allocation, training job queuing, and multi-GPU/distributed training capabilities

4. **Rule Validation and Conflict Resolution**
   - **Challenge**: Ensuring generated rules don't conflict or cause regressions
   - **Mitigation**: Implement comprehensive rule validation testing, staged deployment, and automatic conflict detection

5. **Integration with Existing Components**
   - **Challenge**: Seamless integration with Pulse's existing modules
   - **Mitigation**: Design clear interfaces, implement adapter patterns, and provide comprehensive integration tests

## Implementation Enhancements

Based on verification against Pulse's architecture standards, the following enhancements will be incorporated throughout implementation:

1. **Version Management**
   - Add explicit version attributes to all component classes following Pulse's versioning standard
   - Example implementation in base classes:
   ```python
   class RecursiveComponentBase:
       VERSION = "0.1.0"  # Following semver pattern used in Pulse
       
       @classmethod
       def get_version(cls) -> str:
           return cls.VERSION
   ```

2. **Testing Framework**
   - Implement comprehensive test suites for each component
   - Follow Pulse's existing test patterns in the `tests/` directory
   - Test specifications:
     - Unit tests for all individual component functions
     - Integration tests between components
     - Regression tests for critical features
     - Performance benchmarks for high-throughput operations

3. **Configuration Integration**
   - Leverage `core.pulse_config` consistently for configuration
   - Example implementation:
   ```python
   from pulse.core.pulse_config import PulseConfig
   
   class RecursiveTrainingOrchestrator:
       def __init__(self, config_path: Optional[str] = None):
           self.config = PulseConfig.load_config(
               config_path or "configs/recursive_training.yaml"
           )
           # Initialize components with config
   ```

4. **Logging Standardization**
   - Use Pulse's logging infrastructure with consistent severity levels
   - Example implementation:
   ```python
   from pulse.core.pulse_prompt_logger import get_logger
   
   class RecursiveRuleGenerator:
       def __init__(self, config: Dict):
           self.logger = get_logger(
               logger_name="recursive_rule_generator",
               log_level=config.get("log_level", "INFO")
           )
   ```

5. **Documentation Standards**
   - Add documentation generation directives compatible with Pulse's documentation system
   - Include Sphinx-compatible docstrings
   - Generate API documentation as part of the build process

6. **Security Considerations**
   - Implement authentication for model registry access
   - Add authorization checks for training operations
   - Secure storage of sensitive configuration data
   - Sanitize user inputs in API endpoints
   - Audit logging for security-sensitive operations

These enhancements will be incorporated throughout all implementation phases to ensure full alignment with Pulse's architecture standards and best practices.
## Implementation Schedule Summary

1. **Phase 1: Data Management (4 weeks)**
   - Week 1-2: RecursiveDataIngestionManager & RecursiveDataStore
   - Week 3-4: RecursiveFeatureProcessor & Integration Testing

2. **Phase 2: Training Orchestration (6 weeks)**
   - Week 1-2: RecursiveTrainingOrchestrator
   - Week 3-4: Enhanced Airflow DAGs
   - Week 5-6: Model Registry Extensions & Integration Testing

3. **Phase 3: Rule Generation (5 weeks)**
   - Week 1-2: RecursiveRuleGenerator
   - Week 3-4: RecursiveRuleEvaluator & RuleRepository
   - Week 5: Integration Testing & Documentation

4. **Phase 4: Metrics Components (5 weeks)**
   - Week 1-2: RecursiveTrainingMetrics & MetricsStore
   - Week 3-4: EnhancedRetrodictionCurriculum
   - Week 5: Integration Testing & Documentation

5. **Phase 5: Error Handling (4 weeks)**
   - Week 1-2: RecursiveTrainingErrorHandler & RecursiveTrainingMonitor
   - Week 3-4: RecursiveTrainingRecovery & System Testing

Total Implementation Timeline: 24 weeks (6 months)