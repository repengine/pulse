import pandas as pd
import os
from datetime import datetime, timedelta


def create_dummy_parquet_data(variable_name, start_date, end_date, output_dir):
    """
    Creates a dummy DataFrame and saves it as a Parquet file.
    """
    dates = [
        start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)
    ]
    values = [float(i) for i in range(len(dates))]  # Dummy values

    df = pd.DataFrame({"timestamp": dates, "value": values})

    filepath = os.path.join(output_dir, f"historical_{variable_name}.parquet")
    df.to_parquet(filepath, index=False)
    print(f"Created dummy data for {variable_name} at {filepath}")


if __name__ == "__main__":
    output_directory = "data/recursive_training/optimized"
    os.makedirs(output_directory, exist_ok=True)

    start_date = datetime(2022, 1, 1)
    end_date = datetime(2025, 1, 1)  # Extend to cover the training period

    create_dummy_parquet_data("spx_close", start_date, end_date, output_directory)
    create_dummy_parquet_data("us_10y_yield", start_date, end_date, output_directory)
