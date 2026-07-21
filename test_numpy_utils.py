import numpy as np
from src.numpy_utils import (
    calculate_basic_stats,
    detect_outliers,
    normalize_data,
    calculate_percentiles,
    bin_data,
    calculate_correlation
)


def test_numpy_utils():
    # Test data
    test_data = np.array([10, 20, 30, 40, 50, 150, 60, 70, 80, 90, 100, -50])
    
    print("Testing calculate_basic_stats...")
    stats = calculate_basic_stats(test_data)
    print(stats)
    print("-" * 50)
    
    print("Testing detect_outliers (IQR)...")
    cleaned, outliers = detect_outliers(test_data)
    print(f"Cleaned data: {cleaned}")
    print(f"Outliers: {outliers}")
    print("-" * 50)
    
    print("Testing normalize_data (minmax)...")
    normalized = normalize_data(cleaned)
    print(normalized)
    print("-" * 50)
    
    print("Testing calculate_percentiles...")
    percentiles = calculate_percentiles(cleaned)
    print(percentiles)
    print("-" * 50)
    
    print("Testing bin_data...")
    counts, edges = bin_data(cleaned, bins=5)
    print(f"Counts: {counts}")
    print(f"Edges: {edges}")
    print("-" * 50)
    
    print("Testing calculate_correlation...")
    x = np.array([1, 2, 3, 4, 5])
    y = np.array([2, 4, 6, 8, 10])
    corr = calculate_correlation(x, y)
    print(f"Correlation: {corr}")
    print("-" * 50)
    
    print("All NumPy utility functions tested successfully!")


if __name__ == "__main__":
    test_numpy_utils()
