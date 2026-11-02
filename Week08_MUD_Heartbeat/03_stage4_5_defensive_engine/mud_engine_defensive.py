"""mud_engine_defensive.py — 第 8 周任务五终稿：方案 B（边界检查）+ 买茶算术修复 合入主程序

领航员指令落地清单：
  1. 寻路边界检查：广场东向出口恢复为 "chaguan"，另保留一个北向未开放测试出口 "north": "market_unbuilt"；
     /go 分支在访问 world[target_id] 之前先做 if target_id in world，未开放则打印系统提示并保持原位置不变。
  2. 买茶算术修复：/buy_tea 的扣款由缺陷写法（gold += price，等价于 gold - (-tea_price)）修正为 gold -= tea_price，
     并把"铜钱是否足够"作为限制性条件前置校验。
  3. 循环安全保护：主循环除人工 /quit 触发 break 外，另设 MAX_TURNS 最大回合数上限（默认 100，可用环境变量
     MUD_MAX_TURNS 压低以便自动化实测），到点主动收束并打印系统提示，防异常死循环无限运行。
  4. 兼容性：while 主循环、循环外状态初始化、/go 长度检查、/quit 退出机制沿用 v1/v2；
     地面物品/出口/行囊的三处 for 遍历沿用 v2。可用 MUD_LOOP_ENGINE 跑 check_while_loop.py 回归。

运行：python mud_engine_defensive.py
脚本化回归：printf '/go east\\n/buy_tea\\n/go west\\n/go north\\n/quit\\n' | python mud_engine_defensive.py
回合上限实测：MUD_MAX_TURNS=3 python mud_engine_defensive.py   # 喂 5 条指令，只走 3 回合后自动收束
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_world_exits import audit            # 复用阶段四的地图完整性自检

# ——————————————————————— 循环外初始化（严禁缩进进循环）———————————————————————
world = {
    "guangchang": {
        "name": "扬州中心广场",
        "description": "青石铺地，人来人往。向东是春来茶馆，向西可去武馆，北面那片工地挂着「此处无市」的木牌。",
        "exits": {"east": "chaguan", "west": "wuguan", "north": "market_unbuilt"},
        "items": ["武林帖", "半块碎银"],
    },
    "chaguan": {
        "name": "春来茶馆",
        "description": "说书人醒木一拍，茶客们正议论少侠事迹。伙计正端着碧螺春招手。向西可返回中心广场。",
        "exits": {"west": "guangchang"},
        "items": ["粗瓷茶碗", "书生折扇"],
    },
    "wuguan": {
        "name": "江南武馆",
        "description": "沙地上桩眼密布，教头正盯着你的根基。向东可返回中心广场。",
        "exits": {"east": "guangchang"},
        "items": ["绑腿沙袋"],
    },
}   # 注意：market_unbuilt 故意不定义，作为方案 B 的常驻测试用例

DIRECTION_CN = {"north": "北", "south": "南", "east": "东", "west": "西", "up": "上", "down": "下"}
TEA_PRICE = 15
# 最大回合上限：人工 /quit 之外的第二道防死循环保险；压低它只为在测试里实测"到点收束"。
MAX_TURNS = int(os.environ.get("MUD_MAX_TURNS", "100"))

player = {
    "name": "少侠郭靖",
    "location": "guangchang",
    "gold": 50,
    "inventory": ["金创药", "粗布行囊", "三十贯铜钱"],
}

BANNER = "可用指令：/look  /bag  /buy_tea  /go <方向>  /quit"


def describe(room):
    print(f"【{room['name']}】{room['description']}")
    for item in room["items"]:                                     # ① 遍历列表元素
        print(f"   [地面物品] 你发现地上有：【{item}】")
    for d, tid in room["exits"].items():                           # ② 遍历字典键值对
        cn = DIRECTION_CN.get(d, d)
        where = world[tid]["name"] if tid in world else "尚未开放的工地"
        print(f"   [此地出口] 向{cn} [{d}] -> 通往【{where}】")


def show_bag():
    for idx, item in enumerate(player["inventory"], 1):            # ③ 带序号枚举
        print(f"  [{idx}] {item}")


def buy_tea():
    """/buy_tea：限制性条件在前（钱不够 -> 才真正扣款），扣款方向为减法。"""
    if player["gold"] < TEA_PRICE:
        return f"一碗碧螺春 {TEA_PRICE} 文，你只剩 {player['gold']} 文，伙计不肯赊账。"
    before = player["gold"]
    player["gold"] -= TEA_PRICE                                    # 修复：缺陷写作 += price（等价 gold - (-price)）
    player["inventory"].append("碧螺春")
    return f"你付了 {TEA_PRICE} 文，铜钱 {before} -> {player['gold']}，行囊多了一碗碧螺春。"


def move(direction, room):
    """查表寻址 + 方案 B 边界检查：先确认目标房间已定义，再落状态。"""
    target_id = room["exits"][direction]
    if target_id in world:                                         # ← 边界检查，访问键之前
        player["location"] = target_id
        print(f"  你抵达了【{world[target_id]['name']}】！")
        describe(world[player["location"]])
    else:
        print(f"  [系统提示] 前方的【{target_id}】区域尚未开放，请留步！")
        # 保持原位置不变，主循环正常继续，避免触发 KeyError


def main():
    print(BANNER)
    dangling = audit(world)                                        # 启动期知情清单：故意未开放 != 事故
    if dangling:
        print(f"  [自检] 地图有 {len(dangling)} 处出口指向未定义区域（按未开放处理）：{dangling}")
    describe(world[player["location"]])

    turn_count = 0
    finished_by_quit = False
    while turn_count < MAX_TURNS:                                  # 保险二：最大回合数上限，防异常死循环
        turn_count += 1
        try:
            command = input(f"\n[第 {turn_count} 回合] 少侠请下令 > ").strip().lower()
        except EOFError:
            break

        if command == "/quit":
            print("少侠抱拳离去，江湖再见。")
            finished_by_quit = True
            break
        elif command == "/look":
            describe(world[player["location"]])
        elif command == "/bag":
            show_bag()
        elif command == "/buy_tea":
            print("  " + buy_tea())
        elif command.startswith("/go"):
            parts = command.split()
            room = world[player["location"]]
            if len(parts) < 2:
                print("  要向哪里去？用法：/go <方向>")
            elif parts[1] not in room["exits"]:
                print(f"  无法向 [{parts[1]}] 前行。")
            else:
                move(parts[1], room)
        elif command:
            print(f"  未知指令 [{command}]。{BANNER}")

    if not finished_by_quit and turn_count >= MAX_TURNS:
        print(f"\n  [系统提示] 已走满 {MAX_TURNS} 回合上限，为防异常死循环，本次江湖行到此收束。后会有期！")


if __name__ == "__main__":
    main()
