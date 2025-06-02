"""
Airflow DAG to schedule Pulse historical retrodiction runs.
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
from engine.historical_retrodiction_runner import run_retrodiction_tests

default_args = {
    "owner": "pulse",
    "depends_on_past": False,
    "start_date": datetime(2020, 1, 1),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    "historical_retrodiction",
    default_args=default_args,
    schedule_interval="@daily`",
    catchup=False,
) as dag:

    def task_retrodict(**kwargs):
        params = kwargs.get("params", {})
        dates = params.get("start_dates", ["2020-01-01"])
        days = params.get("days", 30)
        workers = params.get("parallel", 4)
        run_retrodiction_tests(dates, days=days, max_workers=workers)

    retrodict = PythonOperator(
        task_id="run_retrodiction", python_callable=task_retrodict, provide_context=True
    )

    retrodict
