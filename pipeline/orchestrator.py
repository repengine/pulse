"""
Orchestrator
------------
Schedules and runs the end-to-end AI training cycle:
  - Preprocessing
  - Training orchestration
  - Evaluation
  - Rule generation & pruning
"""

import schedule
import time
from pipeline.preprocessor import Preprocessor
from pipeline.model_manager import ModelManager
from pipeline.evaluator import Evaluator
from pipeline.rule_engine import RuleEngine


class Orchestrator:
    def __init__(
        self,
        raw_data_dir: str,
        feature_store_path: str,
        model_registry_uri: str,
    ) -> None:
        self.preprocessor = Preprocessor(raw_data_dir, feature_store_path)
        self.model_manager = ModelManager(model_registry_uri)
        self.evaluator = Evaluator()
        self.rule_engine = RuleEngine()

    def run_training_cycle(self) -> None:
        """
        Executes one full training cycle:
          1. Load and preprocess data
          2. Train or fine-tune models
          3. Evaluate new models
          4. Generate and prune rules
        """
        # 1. Preprocess
        self.preprocessor.load_raw()
        self.preprocessor.merge_data()
        self.preprocessor.normalize()
        self.preprocessor.compute_features()
        feature_path = self.preprocessor.save_features()

        # 2. Train / fine-tune
        model_info = self.model_manager.train(feature_path)

        # 3. Evaluate
        metrics = self.evaluator.evaluate(model_info, feature_path)
        self.model_manager.log_metrics(model_info, metrics)

        # 4. Rule generation & pruning
        self.rule_engine.generate_rules()
        self.rule_engine.evaluate_rules()
        self.rule_engine.prune_rules()

    def schedule_daily(self, time_str: str = "02:00") -> None:
        """
        Schedule the training cycle to run daily at the given time.
        """
        schedule.every().day.at(time_str).do(self.run_training_cycle)
        while True:
            schedule.run_pending()
            time.sleep(30)


if __name__ == "__main__":
    # Example usage
    orchestrator = Orchestrator(
        raw_data_dir="data/",
        feature_store_path="pipeline/features.parquet",
        model_registry_uri="mlflow://localhost:5000",
    )
    orchestrator.schedule_daily("02:00")
