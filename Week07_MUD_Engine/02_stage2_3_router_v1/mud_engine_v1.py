"""mud_engine_v1.py — Stage 2 中央指令路由（ROCA 生成，三层结构）

输入清洗层 -> 多路分流层 -> 查表寻址层
指令：/look  /status  /go <方向>  /help  /quit

运行：python mud_engine_v1.py
脚本化验收：printf ' /Go East \\n/go up\\n/quit\\n' | python mud_engine_v1.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "01_stage1_world_model"))
from world_data import world, player

DIRECTION_CN = {"north": "北", "south": "南", "east": "东", "west": "西", "up": "上", "down": "下"}

BANNER = "可用指令：/look  /status  /go <方向>  /heal  /help_scholar  /help  /quit"


def describe(room):
    print(f"【{room['name']}】{room['description']}")
    if room["exits"]:
        for direction, target in room["exits"].items():
            cn = DIRECTION_CN.get(direction, direction)
            print(f"  出口：向{cn} [{direction}] -> {world[target]['name']}")
    else:
        print("  这里四面皆墙，无路可走。")


def show_status():
    print(f"  姓名：{player['name']}    生命：{player['health']}/{player['max_health']}")
    print(f"  铜钱：{player['gold']}    声望：{player['reputation']}")
    print(f"  背包：{'、'.join(player['inventory']) if player['inventory'] else '空如洗'}")


def heal():
    """/heal 多分支规则：限制性条件在前（无药 -> 满血 -> 才真正服药）。"""
    if "金创药" not in player["inventory"]:
        return "你的行囊中已经没有【金创药】了！"
    if player["health"] >= player["max_health"]:
        return "你当前气血充沛，无需服用金创药。"
    player["inventory"].remove("金创药")
    player["health"] = min(player["max_health"], player["health"] + 20)
    return f"你掏出游方带回的【金创药】敷上，气血恢复至 {player['health']}/{player['max_health']}！"


def help_scholar():
    """/help_scholar 价值抉择：先校验地点与盘缠两道限制，再扣铜钱换声望。"""
    if player["location"] != "chaguan":
        return "四下并无落魄书生——这份机缘只在【春来茶馆】才会撞见。"
    if player["scholar_saved"]:
        return "书生已中举赴京，你的恩情他早已记下，不必再破费。"
    if player["gold"] < 10:
        return f"你盘缠只剩 {player['gold']} 文，不够周济书生（需 10 文）。"
    player["gold"] -= 10
    player["reputation"] += 15
    player["scholar_saved"] = True
    return (f"你掏出 10 文铜钱替书生付了茶钱，他拱手道谢。"
            f"铜钱 -10 -> {player['gold']}，江湖声望 +15 -> {player['reputation']}！")


def move(direction, room):
    """查表寻址层：if direction in room['exits'] 守卫，禁止硬编码房间名。"""
    if direction in room["exits"]:
        player["location"] = room["exits"][direction]      # 动态取键值，非 if/elif 硬编码
        new_room = world[player["location"]]
        print(f"  你抵达了【{new_room['name']}】。")
        describe(new_room)
    else:
        blocked = "、".join(f"[{d}]" for d in room["exits"]) or "无"
        print(f"  无法向 [{direction}] 前行！前面似有石墙受阻。此路唯有：{blocked}")


def handle(raw, room):
    # —— 输入清洗层：统一消除首尾空白与大小写差异 ——
    command = raw.strip().lower()
    if not command:
        return True

    # —— 多路分流层 ——
    if command == "/look":
        describe(room)
    elif command == "/status":
        show_status()
    elif command == "/heal":
        print("  " + heal())
    elif command == "/help_scholar":
        print("  " + help_scholar())
    elif command == "/help":
        print(BANNER)
    elif command == "/quit":
        print("  少侠抱拳离去，江湖再见。")
        return False
    elif command.startswith("/go"):
        parts = command.split()
        if len(parts) < 2:                 # 先补齐参数，再进查表层
            print("  要向哪里去？用法：/go <方向>，例如 /go east")
        else:
            move(parts[1], room)
    else:
        print(f"  未知指令 [{command}]。{BANNER}")
    return True


def main():
    print(BANNER)
    while True:
        room = world[player["location"]]
        try:
            raw = input(f"[{room['name']}] > ")
        except EOFError:
            break
        if not handle(raw, room):
            break


if __name__ == "__main__":
    main()
