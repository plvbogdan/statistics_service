from typing import List, Dict, Optional


def calculate_statistics(values: List[float]) -> Dict[str, Optional[float]]:
    if not values:
        return {
            "min": None,
            "max": None,
            "count": 0,
            "sum": 0,
            "median": None
        }
    
    sorted_values = sorted(values)
    n = len(sorted_values)

    if n % 2 == 0:
        median = (sorted_values[n//2 - 1] + sorted_values[n//2]) / 2
    else:
        median = sorted_values[n//2]
    
    return {
        "min": min(values),
        "max": max(values),
        "count": n,
        "sum": sum(values),
        "median": median
    }


def calculate_metrics(
    x_values: List[float],
    y_values: List[float],
    z_values: List[float]
) -> Dict[str, Dict]:
    return {
        "x": calculate_statistics(x_values),
        "y": calculate_statistics(y_values),
        "z": calculate_statistics(z_values)
    }


def empty_statistics() -> Dict[str, Dict]:
    empty = {
        "min": None,
        "max": None,
        "count": 0,
        "sum": 0,
        "median": None
    }
    return {
        "x": empty.copy(),
        "y": empty.copy(),
        "z": empty.copy()
    }