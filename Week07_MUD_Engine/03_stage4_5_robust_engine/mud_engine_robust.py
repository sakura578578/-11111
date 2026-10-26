"""mud_engine_robust.py — Stage 5 防御性重构版中央指令路由

相对 mud_engine_v1.py 的四道守卫：
    [守卫 1] 清洗后空输入直接回引导，不进入任何分支
    [守卫 2] 无参 split() 自动合并连续空格、丢掉首尾空白
    [守卫 3] 读取 parts[1] 前先判 len(parts) < 2，杜绝 IndexError
    [守卫 4] 字典键成员守卫 in room["exits"]，杜绝 KeyError
路由按 command.split() 的首个 token 精确比对，/help 与 /help_scholar
不再存在前缀吞噬问题。

指令路由要点：去首尾空格转小写 + split() 切参数 + 检查列表长度 + 字典查表。

运行：python mud_engine_robust.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "01_stage1_world_model"))
from world_data import world, player

DIRECTION_CN = {"north": "北", "south": "南", "east": "东", "west": "西", "up": "上", "down": "下"}

BANNER = "可用指令：/look  /status  /go <方向>  /heal  /help_scholar  /help  /quit"


def describe(room):
    lines = [f"【{room['name']}】{room['description']}"]
    if room["exits"]:
        for direction, target in room["exits"].items():
            cn = DIRECTION_CN.get(direction, direction)
            lines.append(f"  出口：向{cn} [{direction}] -> {world[target]['name']}")
    else:
        lines.append("  这里四面皆墙，无路可走。")
    return "\n".join(lines)


def show_status():
    return (f"  姓名：{player['name']}    生命：{player['health']}/{player['max_health']}\n"
            f"  铜钱：{player['gold']}    声望：{player['reputation']}\n"
            f"  背包：{'、'.join(player['inventory']) if player['inventory'] else '空如洗'}")


def heal():
    if "金创药" not in player["inventory"]:
        return "  你的行囊中已经没有【金创药】了！"
    if player["health"] >= player["max_health"]:
        return "  你当前气血充沛，无需服用金创药。"
    player["inventory"].remove("金创药")
    player["health"] = min(player["max_health"], player["health"] + 20)
    return (f"  你敷上【金创药】，气血恢复至 "
            f"{player['health']}/{player['max_health']}！")


def help_scholar():
    if player["location"] != "chaguan":
        return "  四下并无落魄书生——这份机缘只在【春来茶馆】才会撞见。"
    if player["scholar_saved"]:
        return "  书生已中举赴京，你的恩情他早已记下，不必再破费。"
    if player["gold"] < 10:
        return f"  你盘缠只剩 {player['gold']} 文，不够周济书生（需 10 文）。"
    player["gold"] -= 10
    player["reputation"] += 15
    player["scholar_saved"] = True
    return (f"  你掏出 10 文铜钱替书生付了茶钱。"
            f"铜钱 -10 -> {player['gold']}，江湖声望 +15 -> {player['reputation']}！")


def move(direction, room):
    if direction in room["exits"]:                      # [守卫 4]
        player["location"] = room["exits"][direction]
        new_room = world[player["location"]]
        return f"  你抵达了【{new_room['name']}】。\n{describe(new_room)}"
    blocked = "、".join(f"[{d}]" for d in room["exits"]) or "无"
    return f"  无法向 [{direction}] 前行！前面似有石墙受阻。此路唯有：{blocked}"


def dispatch(raw):
    """返回一串要给玩家看的话；返回 None 表示退出主循环。"""
    command = raw.strip().lower()                       # [守卫 1] 清洗层
    if not command:
        return "  （四下无言）输入 /look 看看四周，或 /help 查看指令。"

    parts = command.split()                             # [守卫 2] 切分层
    verb = parts[0]
    room = world[player["location"]]

    if verb == "/look":
        return describe(room)
    elif verb == "/status":
        return show_status()
    elif verb == "/heal":
        return heal()
    elif verb == "/help_scholar":
        return help_scholar()
    elif verb == "/help":
        return f"  {BANNER}"
    elif verb == "/quit":
        print("  少侠抱拳离去，江湖再见。")
        return None
    elif verb == "/go":
        if len(parts) < 2:                              # [守卫 3] 长度守卫
            return "  少侠欲往何方？请在 /go 后指明方向（例如：/go east）！"
        return move(parts[1], room)
    return f"  未知指令 [{verb}]。{BANNER}"


def main():
    print(BANNER)
    while True:
        room = world[player["location"]]
        try:
            raw = input(f"[{room['name']}] > ")
        except EOFError:
            break
        result = dispatch(raw)
        if result is None:
            break
        print(result)


if __name__ == "__main__":
    main()
