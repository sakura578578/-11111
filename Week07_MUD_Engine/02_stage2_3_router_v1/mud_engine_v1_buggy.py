"""mud_engine_v1_buggy.py — 课程靶场：中央指令路由的三处典型缺陷

缺陷 1（输入清洗缺失）：main() 直接把原始 input() 交给分流层，
        输入 " /Go East " 时所有等值/前缀判断全部落空，移动指令被当成未知指令。
缺陷 2（切分方式脆弱）：用 split(" ", 1)[1] 按单个空格切，
        输入 "/go   west" 会切出带前导空白的 "  west"，方向永远匹配不上出口。
缺陷 3（越界 + 无 in 守卫）：只输入 "/go" 时切出的列表长度为 1，强读索引 [1]
        抛 IndexError；方向不存在时 room["exits"][direction] 抛 KeyError，崩溃退出。

五类边界用例在本靶场上的实测结论：
    1 首尾空白与大小写 " /Go East "  -> 落到 else，打印「未知指令。」
    2 动词与方向多空格 "/go west(前置多空格)" -> 切出 "  west"，KeyError 误判为无此路
    3 缺失方向参数     "/go"         -> 第 49 行 IndexError: list index out of range
    4 非法方向越界     "/go up"      -> KeyError: 'up'（合规版应为石墙阻拦提示）
    5 空回车与乱码     ""、"/fly"    -> 空回车同样落 else；未知指令提示无归一化
运行：python mud_engine_v1_buggy.py
五类边界用例复现：python ../04_stage4_boundary_review/boundary_tests.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "01_stage1_world_model"))
from world_data import world, player


def describe(room):
    print(f"【{room['name']}】{room['description']}")
    for direction, target in room["exits"].items():
        print(f"  出口：[{direction}] -> {world[target]['name']}")


def show_status():
    print(f"  生命 {player['health']}/{player['max_health']}"
          f"  铜钱 {player['gold']}  声望 {player['reputation']}")
    print(f"  背包：{'、'.join(player['inventory'])}")


def dispatch_command_v1(command):
    """缺陷版分流层：三层防护一处都没有。"""
    room = world[player["location"]]

    if command == "/look":
        describe(room)
    elif command == "/status":
        show_status()
    elif command.startswith("/go"):
        # 案发点：Happy Path Bias —— 生成时默认 "/go" 之后必然跟着空格与方向。
        direction = command.split(" ", 1)[1]
        target = room["exits"][direction]
        player["location"] = target
        new_room = world[player["location"]]
        print(f"  你抵达了【{new_room['name']}】。")
    else:
        print("  未知指令。")


def main():
    while True:
        room = world[player["location"]]
        try:
            raw = input(f"[{room['name']}] > ")
        except EOFError:
            break
        dispatch_command_v1(raw)          # 缺陷 1：raw 未 strip().lower()


if __name__ == "__main__":
    main()
