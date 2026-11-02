"""mud_loop_v2.py — 第 8 周任务二：for 循环遍历地面物品 / 可用出口 / 玩家行囊（ROCA 增量生成）

在 mud_loop_v1.py 上增量扩展，三处 for 循环：
  ① for item in room["items"]                      遍历列表元素（地面物品）
  ② for d, tid in room["exits"].items()            遍历字典键值对（出口方向 -> 目标房间中文名）
  ③ for idx, item in enumerate(player["inventory"], 1)  带序号枚举列表（/bag 行囊清单）

兼容性约束（Non-Breaking）：while True 主循环结构、循环外状态初始化、/go 长度检查、/quit 退出机制均未改动，
可用 MUD_LOOP_ENGINE=mud_loop_v2.py python check_while_loop.py 回归验证。

运行：python mud_loop_v2.py
脚本化验收：printf '/look\\n/bag\\n/go east\\n/quit\\n' | python mud_loop_v2.py
"""

# ——————————————————————— 循环外初始化（严禁缩进进循环）———————————————————————
world = {
    "guangchang": {
        "name": "扬州中心广场",
        "description": "青石铺地，人来人往，告示栏上贴着武林帖。向东可去茶馆，向西可去武馆。",
        "exits": {"east": "chaguan", "west": "wuguan"},
        "items": ["武林帖", "半块碎银"],
    },
    "chaguan": {
        "name": "春来茶馆",
        "description": "说书人醒木一拍，茶客们正议论少侠事迹。向西可返回中心广场。",
        "exits": {"west": "guangchang"},
        "items": ["粗瓷茶碗", "书生折扇"],
    },
    "wuguan": {
        "name": "江南武馆",
        "description": "沙地上桩眼密布，教头正盯着你的根基。向东可返回中心广场。",
        "exits": {"east": "guangchang"},
        "items": ["绑腿沙袋"],
    },
}

DIRECTION_CN = {"north": "北", "south": "南", "east": "东", "west": "西", "up": "上", "down": "下"}

player = {"name": "少侠郭靖", "location": "guangchang", "inventory": ["金创药", "粗布行囊", "三十贯铜钱"]}

BANNER = "可用指令：/look  /bag  /go <方向>  /quit"


def describe(room):
    print(f"【{room['name']}】{room['description']}")

    # ① 遍历列表元素：地面物品
    for item in room["items"]:
        print(f"   [地面物品] 你发现地上有：【{item}】")

    # ② 遍历字典键值对：可用出口方向 -> 目标房间中文名
    for d, tid in room["exits"].items():
        cn = DIRECTION_CN.get(d, d)
        print(f"   [此地出口] 向{cn} [{d}] -> 通往【{world[tid]['name']}】")


def show_bag():
    """③ 带序号枚举列表：start=1，行囊清单从 [1] 开始编号。"""
    if not player["inventory"]:
        print("  行囊空空如也。")
        return
    for idx, item in enumerate(player["inventory"], 1):
        print(f"  [{idx}] {item}")


def main():
    # ———— 进入循环前只打印一次的开场白 ————
    print(BANNER)
    describe(world[player["location"]])

    while True:
        try:
            command = input("> ").strip().lower()
        except EOFError:
            break

        # ———— 多路分流：仅在收到对应指令时才按需打印 ————
        if command == "/quit":                       # 安全退出分支（防死循环）
            print("少侠抱拳离去，江湖再见。")
            break
        elif command == "/look":
            describe(world[player["location"]])      # 读当前位置，不做任何重置
        elif command == "/bag":
            show_bag()
        elif command.startswith("/go"):
            parts = command.split()
            room = world[player["location"]]
            if len(parts) < 2:                       # /go 长度检查保持不变
                print("  要向哪里去？用法：/go <方向>")
            elif parts[1] in room["exits"]:
                player["location"] = room["exits"][parts[1]]
                print(f"  你抵达了【{world[player['location']]['name']}】。")
                describe(world[player["location"]])  # 移动成功才打印
            else:
                print(f"  无法向 [{parts[1]}] 前行。")
        elif command:
            print(f"  未知指令 [{command}]。{BANNER}")


if __name__ == "__main__":
    main()
