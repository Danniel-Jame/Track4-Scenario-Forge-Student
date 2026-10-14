"""Part C/D: search for failures with the cross-entropy method. TODO 5; the sampling helpers are given."""
from __future__ import annotations

import math

import numpy as np

from avsim import space


def cem_update(Z, Bn, score, prev: dict, rho: float = 0.1, smooth: float = 0.7, min_std: float = 0.25,
               p_clip=(0.03, 0.97)) -> dict:
    """TODO 5. One cross-entropy step. Keep the elite = the top ceil(rho * n) rows by score (at least 2;
    higher score = more dangerous; on equal scores the earlier row wins, i.e. np.argsort(-score, kind="stable")),
    then return a new proposal dict:

      mean  = smooth * elite mean + (1 - smooth) * prev["mean"]           (per continuous coordinate)
      std   = max(min_std, smooth * elite std + (1 - smooth) * prev["std"])
      p_bin = clip(smooth * elite frequency + (1 - smooth) * prev["p_bin"], *p_clip)  (per binary coordinate)
      level = the lowest score inside the elite (how dangerous the elite already is)

    Why the floors: a std that collapses to 0 or a probability of exactly 0/1 makes importance weights explode."""
    n = len(score)
    # Xác định số lượng mẫu elite: top ceil(rho * n), tối thiểu là 2 (hoặc n nếu n nhỏ hơn 2)
    n_elite = max(2, math.ceil(rho * n))
    n_elite = min(n_elite, n)
    
    # Sắp xếp điểm số theo thứ tự giảm dần (điểm cao hơn = nguy hiểm hơn), 
    # với điểm bằng nhau thì hàng nào xuất hiện trước sẽ thắng (dùng kind="stable")[cite: 7]
    sorted_indices = np.argsort(-score, kind="stable")
    elite_indices = sorted_indices[:n_elite]
    
    # Lấy các mẫu elite tương ứng cho tọa độ liên tục (Z) và nhị phân (Bn)
    elite_Z = Z[elite_indices]
    elite_Bn = Bn[elite_indices]
    
    # Tính toán thống kê từ tập elite
    elite_mean = np.mean(elite_Z, axis=0)
    elite_std = np.std(elite_Z, axis=0, ddof=0)
    elite_freq = np.mean(elite_Bn, axis=0)
    
    # Cập nhật theo hệ số làm mượt `smooth` và giá trị cũ `prev`
    new_mean = smooth * elite_mean + (1.0 - smooth) * prev["mean"]
    
    raw_std = smooth * elite_std + (1.0 - smooth) * prev["std"]
    new_std = np.maximum(min_std, raw_std)
    
    raw_p_bin = smooth * elite_freq + (1.0 - smooth) * prev["p_bin"]
    new_p_bin = np.clip(raw_p_bin, p_clip[0], p_clip[1])
    
    # Mức độ nguy hiểm tối thiểu bên trong tập elite (điểm số thấp nhất trong nhóm elite)
    elite_scores = score[elite_indices]
    level = float(np.min(elite_scores))
    
    return dict(
        mean=new_mean,
        std=new_std,
        p_bin=new_p_bin,
        level=level
    )


# ---------------------------------------------------------------- given

def natural_proposal(nat: space.Natural) -> dict:
    return dict(mean=np.zeros(space.D), std=np.ones(space.D), p_bin=nat.p_bin.copy(), level=-math.inf)


def proposal_sample(prop, n, rng):
    Z = prop["mean"] + prop["std"] * rng.standard_normal((n, space.D))
    Bn = (rng.random((n, space.B)) < prop["p_bin"]).astype(int)
    return Z, Bn


def proposal_logpdf(prop, Z, Bn):
    lz = (-0.5 * np.sum(((Z - prop["mean"]) / prop["std"]) ** 2, 1) - np.sum(np.log(prop["std"]))
          - 0.5 * space.D * math.log(2 * math.pi))
    lb = np.sum(Bn * np.log(prop["p_bin"]) + (1 - Bn) * np.log1p(-prop["p_bin"]), 1)
    return lz + lb


def mixture_sample(prop, nat: space.Natural, n, rng, beta=0.2):
    """Draw n rows from the defensive mixture (1 - beta) * proposal + beta * natural."""
    Z, Bn = proposal_sample(prop, n, rng)
    m = rng.random(n) < beta
    Zn, Bnn = nat.sample(int(m.sum()), rng)
    Z[m], Bn[m] = Zn, Bnn
    return Z, Bn