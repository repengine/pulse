import numpy as np
from typing import List, Dict

def compress_mc_samples(
    mc_samples: List[Dict[str, np.ndarray]], 
    alpha: float = 0.9
) -> Dict[str, Dict[str, np.ndarray]]:
    """
    Compress Monte Carlo forecast samples into mean and prediction interval.

    Parameters:
        mc_samples: List of forecast dictionaries. Each dict maps field names
                    to 1D numpy arrays of equal length (time steps).
        alpha:       Coverage probability for the prediction interval (0 < alpha < 1).

    Returns:
        A dict mapping each field name to a dict with keys:
            'mean' : np.ndarray of shape (T,), the average across samples.
            'lower': np.ndarray of shape (T,), the lower percentile at (1-alpha)/2*100.
            'upper': np.ndarray of shape (T,), the upper percentile at (1+alpha)/2*100.
    """
    if not mc_samples:
        raise ValueError("mc_samples list is empty; cannot compress forecasts")

    result: Dict[str, Dict[str, np.ndarray]] = {}
    lower_pct = (1 - alpha) / 2 * 100
    upper_pct = (1 + alpha) / 2 * 100

    # Iterate over each field in the first sample
    for field, array in mc_samples[0].items():
        # Stack arrays along a new axis: shape (N_paths, T)
        data = np.stack([sample[field] for sample in mc_samples], axis=0)
        mean = np.mean(data, axis=0)
        lower = np.percentile(data, lower_pct, axis=0)
        upper = np.percentile(data, upper_pct, axis=0)
        result[field] = {"mean": mean, "lower": lower, "upper": upper}

    return result