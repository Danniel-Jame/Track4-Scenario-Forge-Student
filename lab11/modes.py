"""Part D: name the failure. TODO 8."""
from __future__ import annotations

from avsim import core


def label_mode(R: core.Rollout, k: int, event: dict, contact_type) -> str:
    """TODO 8. Name the kind of failure behind one ego failure event (a collision, or a crosswalk block). Return one of:

      'crosswalk_block' - the other party is the crossing pedestrian P1: the ego stopped with its body on the
                        crosswalk in P1's way (event["kind"] == "block"), or hit P1
      'rear_ended' - something ran into the ego from behind (use contact_type(R, k, event) == 'rear')
      'bus_bypass' - the ego hit C2 while C2 was squeezing past the stopped bus: at contact C2 is at x < 112 m
                     and slower than 6 m/s
      'cut_in'     - the ego hit C2 in any other situation
      'other'      - anything else
    Check in that order. Positions and speeds at contact: R.F[k, event["f"], core.IX["C2"]] (x is column 0, v is 4).
    """
    kind = event.get("kind")
    actor_a = event.get("a")
    actor_b = event.get("b")
    frame = event.get("f", event.get("frame"))
    
    # 1. Kiểm tra 'crosswalk_block': bên còn lại là người đi bộ P1 (ego chặn đường hoặc va chạm với P1)[cite: 5]
    other_actor = actor_b if actor_a == "ego" else actor_a
    if other_actor == "P1" or kind == "block":
        return "crosswalk_block"
        
    # 2. Kiểm tra 'rear_ended': phương tiện khác tông vào đuôi xe ta[cite: 5]
    if contact_type(R, k, event) == "rear":
        return "rear_ended"
        
    # 3. Kiểm tra 'bus_bypass': xe ta va chạm với C2 khi C2 đang lách qua xe buýt đỗ (x < 112m và v < 6 m/s)[cite: 5]
    if other_actor == "C2":
        c2_data = R.F[k, frame, core.IX["C2"]]
        x_c2 = c2_data[0]
        v_c2 = c2_data[4]
        if x_c2 < 112.0 and v_c2 < 6.0:
            return "bus_bypass"
        else:
            return "cut_in"
            
    # 4. Các trường hợp còn lại khác[cite: 5]
    return "other"