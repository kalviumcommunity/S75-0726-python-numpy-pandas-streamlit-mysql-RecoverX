import numpy as np
from typing import Tuple, List, Optional


def calculate_basic_stats(arr: np.ndarray) -> dict:
    """
    Calculate basic statistical metrics from a NumPy array.
    
    Args:
        arr (np.ndarray): Input numeric array
        
    Returns:
        dict: Dictionary containing mean, median, std, min, max, count
    """
    arr = arr[~np.isnan(arr)]  # Remove NaN values
    return {
        "mean": float(np.mean(arr)),
        "median": float(np.median(arr)),
        "std": float(np.std(arr)),
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
        "count": int(len(arr))
    }


def detect_outliers(arr: np.ndarray, method: str = "iqr", threshold: float = 1.5) -> Tuple[np.ndarray, np.ndarray]:
    """
    Detect outliers in a numeric array using either IQR or Z-score method.
    
    Args:
        arr (np.ndarray): Input numeric array
        method (str): "iqr" (default) or "zscore"
        threshold (float): Threshold for outlier detection
        
    Returns:
        Tuple[np.ndarray, np.ndarray]: (array without outliers, array of outlier values)
    """
    arr = arr[~np.isnan(arr)]
    
    if method == "iqr":
        q1 = np.percentile(arr, 25)
        q3 = np.percentile(arr, 75)
        iqr = q3 - q1
        lower_bound = q1 - threshold * iqr
        upper_bound = q3 + threshold * iqr
        mask = (arr >= lower_bound) & (arr <= upper_bound)
    elif method == "zscore":
        z_scores = np.abs((arr - np.mean(arr)) / np.std(arr))
        mask = z_scores < threshold
    else:
        raise ValueError("Method must be either 'iqr' or 'zscore'")
    
    return arr[mask], arr[~mask]


def normalize_data(arr: np.ndarray, method: str = "minmax") -> np.ndarray:
    """
    Normalize a numeric array using specified method.
    
    Args:
        arr (np.ndarray): Input numeric array
        method (str): "minmax" (default) or "zscore"
        
    Returns:
        np.ndarray: Normalized array
    """
    arr = arr[~np.isnan(arr)]
    
    if method == "minmax":
        min_val = np.min(arr)
        max_val = np.max(arr)
        normalized = (arr - min_val) / (max_val - min_val)
    elif method == "zscore":
        mean_val = np.mean(arr)
        std_val = np.std(arr)
        normalized = (arr - mean_val) / std_val
    else:
        raise ValueError("Method must be either 'minmax' or 'zscore'")
    
    return normalized


def calculate_percentiles(arr: np.ndarray, percentiles: Optional[List[float]] = None) -> dict:
    """
    Calculate specified percentiles from a numeric array.
    
    Args:
        arr (np.ndarray): Input numeric array
        percentiles (Optional[List[float]]): List of percentiles to calculate (default: [10,25,50,75,90])
        
    Returns:
        dict: Dictionary of percentile values
    """
    arr = arr[~np.isnan(arr)]
    
    if percentiles is None:
        percentiles = [10, 25, 50, 75, 90]
        
    return {f"p{p}": float(np.percentile(arr, p)) for p in percentiles}


def bin_data(arr: np.ndarray, bins: int = 10) -> Tuple[np.ndarray, np.ndarray]:
    """
    Bin numeric data into specified number of bins.
    
    Args:
        arr (np.ndarray): Input numeric array
        bins (int): Number of bins (default: 10)
        
    Returns:
        Tuple[np.ndarray, np.ndarray]: (counts per bin, bin edges)
    """
    arr = arr[~np.isnan(arr)]
    return np.histogram(arr, bins=bins)


def calculate_correlation(x: np.ndarray, y: np.ndarray) -> float:
    """
    Calculate Pearson correlation coefficient between two arrays.
    
    Args:
        x (np.ndarray): First numeric array
        y (np.ndarray): Second numeric array
        
    Returns:
        float: Pearson correlation coefficient
    """
    x = x[~np.isnan(x)]
    y = y[~np.isnan(y)]
    return float(np.corrcoef(x, y)[0, 1])
