"""Part B: physics check. TODO 3."""
from __future__ import annotations

import math

G = 9.81


def is_feasible(p: dict) -> bool:
    """TODO 3. False for scenarios no real road user could produce. Reject if ANY of:

    - the lane change needs more sideways grip than the road has: the cosine lane change of 3.5 m over
      p["cutDur"] seconds peaks at a_lat = (pi / cutDur)^2 * 3.5 / 2; reject if a_lat > mu * g;
    - the post-merge braking p["cutBrake"] exceeds mu * g;
    - the pedestrian runs: p["pedV"] > 2.5 m/s;
    - the cut-in speed p["cutV"] is not in (0, 22] m/s.
    mu is p["mu"]. A search that keeps infeasible scenarios reports failures that cannot happen.
    """
    mu = p.get("mu", 0.7) # Mặc định lấy theo tham số mu trong p
    
    # 1. Kiểm tra gia tốc ngang khi chuyển làn (a_lat) so với độ bám đường (mu * g)
    cut_dur = p.get("cutDur", 1.0)
    if cut_dur > 0:
        a_lat = (math.pi / cut_dur) ** 2 * 3.5 / 2.0
        if a_lat > mu * G:
            return False
    else:
        return False

    # 2. Kiểm tra lực phanh sau khi nhập làn (cutBrake) vượt quá giới hạn bám đường mu * g
    cut_brake = p.get("cutBrake", 0.0)
    if cut_brake > mu * G:
        return False

    # 3. Kiểm tra tốc độ người đi bộ (pedV) không được vượt quá 2.5 m/s (chạy bộ)
    ped_v = p.get("pedV", 0.0)
    if ped_v > 2.5:
        return False

    # 4. Kiểm tra tốc độ xe chuyển làn (cutV) phải nằm trong khoảng (0, 22] m/s
    cut_v = p.get("cutV", 0.0)
    if not (0.0 < cut_v <= 22.0):
        return False

    return True