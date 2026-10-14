"""Part E: choose a policy honestly. TODO 10."""
from __future__ import annotations


def choose_policy(table: list[dict], baseline_progress: float, max_loss: float = 0.05):
    """TODO 10. table rows: dict(policy=..., fail_hi=upper 95% bound of the failure rate on the TRAIN sample,
    progress=mean distance on the natural progress sample). Return the row with the lowest fail_hi among rows that
    keep at least (1 - max_loss) of the baseline's progress; break ties by higher progress. None if no row qualifies.

    Ranking by the UPPER bound, not the point estimate, stops you picking a policy that only looks safe
    because its few test crashes happened not to be drawn."""
    min_progress_threshold = (1.0 - max_loss) * baseline_progress
    
    qualified_rows = []
    for row in table:
        progress = row.get("progress", 0.0)
        if progress >= min_progress_threshold:
            qualified_rows.append(row)
            
    if not qualified_rows:
        return None
        
    # Sắp xếp các hàng đủ điều kiện:
    # 1. Ưu tiên fail_hi thấp nhất (tăng dần)
    # 2. Nếu fail_hi bằng nhau, ưu tiên progress cao nhất (giảm dần)
    best_row = min(qualified_rows, key=lambda r: (r.get("fail_hi", float("inf")), -r.get("progress", 0.0)))
    
    return best_row