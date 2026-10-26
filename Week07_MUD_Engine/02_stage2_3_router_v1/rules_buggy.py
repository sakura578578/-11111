"""rules_buggy.py — 课程靶场：/heal 条件顺序与封顶缺陷，用于人工审查

缺陷 A（顺序颠倒）：先判满血、后服药，却没先校验药是否在行囊 ->
        无药时 list.remove 抛 ValueError，或"无药空加血"凭空回满。
缺陷 B（硬编码上限）：满血阈值与封顶值写成字面量 100，而非 player["max_health"]；
        一旦角色 max_health 不等于 100（如受伤体质被压到 80），满血判定形同虚设。
缺陷 C（无封顶）：health += 20 不取 min，气血可突破上限无限堆叠。

运行：python rules_buggy.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "01_stage1_world_model"))
from world_data import player


def heal_buggy_order():
    """缺陷 A：限制条件没排在动作前面。"""
    player["inventory"] = ["粗布行囊"]          # 金创药已用尽
    player["health"] = 40
    player["inventory"].remove("金创药")         # 未先判存在 -> ValueError
    player["health"] += 20
    return player["health"]


def heal_buggy_no_cap():
    """缺陷 B + C：阈值/封顶写死 100，且 += 20 不封顶。

    角色「受伤体质」max_health 被压到 80，字面量 100 的满血判定彻底失真：
    明明已满血仍被判为可服药，气血一路突破上限。
    """
    player["max_health"] = 80
    player["inventory"] = ["金创药", "金创药", "金创药"]
    player["health"] = 80
    log = []
    for _ in range(3):
        if player["health"] >= 100:              # 应为 max_health：80 已满血却放行
            log.append("满血拒服")
            continue
        player["inventory"].remove("金创药")
        player["health"] = player["health"] + 20  # 应为 min(max_health, ...)
        log.append(f"服药后 {player['health']}/{player['max_health']}")
    return "  ->  ".join(log)


if __name__ == "__main__":
    print("— 缺陷 A：服药前未校验道具存在性 —")
    try:
        heal_buggy_order()
    except ValueError as exc:
        print(f"  ValueError: {exc}")
    print()
    print("— 缺陷 B/C：硬编码 100 + 无封顶 —")
    print("  " + heal_buggy_no_cap())
