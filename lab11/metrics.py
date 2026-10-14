"""Part A: read a rollout. TODO 1, 2 and 9 live here; the helpers below them are given."""
from __future__ import annotations

import numpy as np

from avsim import core

G = 9.81
HALF_EGO = core.CAR[0] / 2   # 2.3 m: half the ego's length


def ego_events(R: core.Rollout, k: int) -> list[dict]:
    """Failure events involving the ego in scenario k, earliest first (given).

    event["kind"] is "contact" (the boxes touched) or "block" (the ego's body stopped the pedestrian P1 on the
    crosswalk: pedestrians never walk into a car, so this is how a planner that stops too late fails them)."""
    return [e for e in R.events[k] if e["a"] == "ego" or e["b"] == "ego"]


def min_ttc(R: core.Rollout, cap: float = 10.0) -> np.ndarray:
    """TODO 1. (K,) smallest time-to-collision between the ego and whatever it is following, capped at `cap` s.

    - The ego's leader at frame f is R.EGO[k, f, 3] (an actor index, -1 = nothing ahead).
    - Gap is bumper to bumper along the ego's heading: lon - 2.3 - (leader length / 2), where
      lon = (x_leader - x_ego) * hx_ego + (z_leader - z_ego) * hz_ego (the leader's position seen from the ego) and
      2.3 is half the ego's length. Leader length: core.LEN[j] for actor j; use 0.3 m as the half-length of a
      pedestrian. Clip the gap at 0.
    - TTC = gap / (v_ego - v_leader), only while the ego is closing in by more than 0.1 m/s.
    - A scenario where the ego crashed (see ego_events) returns 0.
    Shapes: R.F is (K, NF, N, 7) with x, z, hx, hz, v, a, d; core.IX["ego"] is the ego's actor index.
    Vectorise over frames (a Python loop over 481 frames x K scenarios is too slow for Part C).
    """
    K, NF, N, _ = R.F.shape
    ego_idx = core.IX["ego"]
    
    # Lấy thông tin của ego qua các khung hình: (K, NF, 7)
    ego_data = R.F[:, :, ego_idx, :]
    x_ego = ego_data[..., 0]
    z_ego = ego_data[..., 1]
    hx_ego = ego_data[..., 2]
    hz_ego = ego_data[..., 3]
    v_ego = ego_data[..., 4]
    
    # Lấy chỉ số xe dẫn đầu (leader index) từ R.EGO: shape (K, NF)
    # R.EGO lưu thông tin leader tại cột index 3 hoặc qua R.EGO
    leader_indices = R.EGO[:, :, 3].astype(int)
    
    # Tạo mảng index theo batch và frame để tra cứu R.F vector hóa
    k_idx = np.arange(K)[:, None]
    f_idx = np.arange(NF)[None, :]
    
    # Nếu không có xe dẫn đầu (-1), gán tạm index 0 để tránh lỗi out of bounds (sau đó sẽ mask đi)
    valid_leader = leader_indices >= 0
    safe_leader_indices = np.where(valid_leader, leader_indices, 0)
    
    # Lấy dữ liệu của xe dẫn đầu: shape (K, NF, 7)
    leader_data = R.F[k_idx, f_idx, safe_leader_indices, :]
    x_lead = leader_data[..., 0]
    z_lead = leader_data[..., 1]
    v_lead = leader_data[..., 4]
    
    # Lấy chiều dài (length) của xe dẫn đầu từ core.LEN
    # Đối với người đi bộ hoặc xe khác, core.LEN có sẵn kích thước theo actor index
    leader_len = core.LEN[safe_leader_indices]
    
    # Tính tọa độ dọc (lon) của xe dẫn đầu nhìn từ ego
    lon = (x_lead - x_ego) * hx_ego + (z_lead - z_ego) * hz_ego
    
    # Tính khoảng cách bumper-to-bumper dọc theo hướng đi
    gap = np.maximum(lon - HALF_EGO - leader_len / 2.0, 0.0)
    
    # Chênh lệch vận tốc (v_ego - v_lead)
    dv = v_ego - v_lead
    
    # Điều kiện tính TTC: có xe dẫn đầu hợp lệ, đang thu hẹp khoảng cách > 0.1 m/s, và lon > 0
    ok = valid_leader & (lon > 0) & (dv > 0.1)
    
    # Tính TTC, nếu không thỏa mãn thì gán bằng inf (hoặc cap)
    ttc = np.where(ok, gap / np.maximum(dv, 1e-6), np.inf)
    
    # Lấy giá trị nhỏ nhất qua các khung hình cho từng kịch bản (K,) và giới hạn bởi cap
    min_ttc_arr = np.minimum(cap, ttc.min(axis=1))
    
    # Nếu kịch bản có va chạm/thất bại của ego (ego_events không rỗng), TTC = 0
    for k_val in range(K):
        if ego_events(R, k_val):
            min_ttc_arr[k_val] = 0.0
            
    return min_ttc_arr


def contact_type(R: core.Rollout, k: int, event: dict) -> str:
    """TODO 2. 'front' (the ego ran into it), 'rear' (it ran into the ego) or 'side', at the contact frame.

    Put the other actor in the ego's frame: lon = r . h, lat = -r_x h_z + r_z h_x with h = (hx, hz) of the ego.
    'front' if lon > 2.3 and |lat| < 1.6; 'rear' if lon < -2.3 and |lat| < 1.6; otherwise 'side'.
    """
    # Lấy chỉ số khung hình từ khóa 'f' hoặc 'frame'
    frame = event.get("f", event.get("frame"))
    ego_idx = core.IX["ego"]
    
    # Xác định đối tượng va chạm còn lại
    other_actor_name = event["b"] if event["a"] == "ego" else event["a"]
    other_idx = core.IX[other_actor_name]
    
    # Lấy trạng thái của ego và đối tượng tại khung hình va chạm
    ego_f = R.F[k, frame, ego_idx]
    other_f = R.F[k, frame, other_idx]
    
    x_ego, z_ego, hx_ego, hz_ego = ego_f[0], ego_f[1], ego_f[2], ego_f[3]
    x_other, z_other = other_f[0], other_f[1]
    
    # Vector khoảng cách giữa 2 xe
    rx = x_other - x_ego
    rz = z_other - z_ego
    
    # Chuyển sang tọa độ dọc (lon) và ngang (lat) trong hệ quy chiếu của ego
    lon = rx * hx_ego + rz * hz_ego
    lat = -rx * hz_ego + rz * hx_ego
    
    if lon > 2.3 and abs(lat) < 1.6:
        return "front"
    elif lon < -2.3 and abs(lat) < 1.6:
        return "rear"
    else:
        return "side"


def progress_metrics(R: core.Rollout) -> tuple[np.ndarray, np.ndarray]:
    """TODO 9. Two (K,) arrays: the distance the ego covers in the 24 s (sum of frame-to-frame steps, metres),
    and the number of frames where the ego brakes harder than 3 m/s^2 (acceleration column < -3)."""
    ego_idx = core.IX["ego"]
    ego_data = R.F[:, :, ego_idx, :]  # shape: (K, NF, 7)
    
    # Tọa độ x, z của ego qua các khung hình để tính quãng đường bước (step-by-step distance)
    x = ego_data[..., 0]
    z = ego_data[..., 1]
    
    # Khoảng cách giữa các khung hình liên tiếp: sqrt(dx^2 + dz^2)
    dx = np.diff(x, axis=1)
    dz = np.diff(z, axis=1)
    step_distances = np.sqrt(dx**2 + dz**2)
    
    # Tổng quãng đường trong suốt đoạn đường chạy (K,)
    total_distance = np.sum(step_distances, axis=1)
    
    # Cột gia tốc (acceleration) là index 5 trong 7 thuộc tính của trạng thái
    accel = ego_data[..., 5]
    
    # Đếm số khung hình mà gia tốc phanh lớn hơn 3 m/s^2 (tức gia tốc < -3)
    hard_braking_counts = np.sum(accel < -3.0, axis=1)
    
    return total_distance, hard_braking_counts


# ---------------------------------------------------------------- given helpers

def pair_min_ttc(R, follower, leader, cap=10.0, lat_max=2.2, leader_vmin=-1.0):
    """(K,) smallest TTC of `follower` running into `leader` while they share a corridor."""
    F = R.F
    a, b = F[:, :, core.IX[follower]], F[:, :, core.IX[leader]]
    rx, rz = b[..., 0] - a[..., 0], b[..., 1] - a[..., 1]
    lon = rx * a[..., 2] + rz * a[..., 3]
    lat = -rx * a[..., 3] + rz * a[..., 2]
    gap = np.maximum(lon - core.LEN[core.IX[follower]] / 2 - core.LEN[core.IX[leader]] / 2, 0.0)
    dv = a[..., 4] - b[..., 4]
    ok = (lon > 0) & (np.abs(lat) < lat_max) & (dv > 0.1) & (b[..., 4] >= leader_vmin)
    ttc = np.where(ok, gap / np.maximum(dv, 1e-6), np.inf)
    return np.minimum(cap, ttc.min(1))


def ped_room(R, cap=30.0):
    """(K,) smallest stopping room [m] left while the crossing pedestrian is in the ego's lane
    (distance to them minus the ego's braking distance at mu*g). Negative = could not have stopped."""
    e, p = R.F[:, :, core.IX["ego"]], R.F[:, :, core.IX["P1"]]
    mu = np.asarray(R.params["mu"])[:, None]
    inlane = np.abs(p[..., 1] - e[..., 1]) < 1.9
    ahead = p[..., 0] - e[..., 0] - HALF_EGO
    room = np.where(inlane & (ahead > -1.0), ahead - e[..., 4] ** 2 / (2 * mu * G), cap)
    return np.clip(room.min(1), -cap, cap)