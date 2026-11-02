"""mud_chaos_buggy.py — 第 8 周任务三课程靶场（自建）：两类典型缺陷共存一脚本

缺陷 A（显性运行期异常）：广场东向出口被写成不存在的 "east": "market"。
    输入 /go east -> 程序异常终止并抛红色 Traceback。
    题面引用的崩溃点：line 64, in <module>，语句 new_room = world[target_id]；
    为使实测 Traceback 与题面行号一致，本文件上方文档注释的行数请勿随意增删。

缺陷 B（静默逻辑错误）：/buy_tea 买 15 文碧螺春，控制台不报任何错，
    50 文付完账反而变成 65 文（扣款符号写反：+= 应为 -=）。
    静默错误的取证办法见同目录 mud_chaos_buggy_debug.py 的 [DEBUG] 调试打印。

运行：python mud_chaos_buggy.py
取证 A：printf '/go east\n/quit\n' | python mud_chaos_buggy.py
取证 B：printf '/buy_tea\n/quit\n' | python mud_chaos_buggy.py
静默错误取证：printf '/buy_tea\n/quit\n' | python mud_chaos_buggy_debug.py
"""

world = {
    "guangchang": {
        "name": "扬州中心广场",
        "description": "青石铺地，人来人往。向东是传闻新开的市集，向西可去武馆，北面通往春来茶馆。",
        "exits": {"east": "market", "west": "wuguan", "north": "chaguan"},   # ← 缺陷 A：market 这个房间代号从未定义
    },
    "chaguan": {
        "name": "春来茶馆",
        "description": "说书人醒木一拍，茶客们正议论少侠事迹。向南可返回中心广场。",
        "exits": {"south": "guangchang"},
    },
    "wuguan": {
        "name": "江南武馆",
        "description": "沙地上桩眼密布，教头正盯着你的根基。向东可返回中心广场。",
        "exits": {"east": "guangchang"},
    },
}

player = {"name": "少侠郭靖", "location": "guangchang", "gold": 50, "inventory": ["金创药", "粗布行囊"]}

print("可用指令：/look  /buy_tea  /go <方向>  /quit")
print("【扬州中心广场】青石铺地，人来人往。")

while True:
    command = input("> ").strip().lower()
    if command == "/quit":
        print("少侠抱拳离去，江湖再见。")
        break
    elif command == "/look":
        room = world[player["location"]]
        print(f"【{room['name']}】{room['description']}")
    elif command == "/buy_tea":
        price = 15
        print(f"  伙计报上价：碧螺春 {price} 文一碗。")
        player["gold"] += price                # ← 缺陷 B：扣款方向写反（应为 -=），类型正确故不报错
        player["inventory"].append("碧螺春")
        print(f"  购买成功，行囊多了一碗碧螺春，当前铜钱 {player['gold']} 文。")
    elif command.startswith("/go"):
        parts = command.split()
        room = world[player["location"]]
        if len(parts) < 2:
            print("  要向哪里去？用法：/go <方向>")
        elif parts[1] not in room["exits"]:
            print(f"  无法向 [{parts[1]}] 前行。")
        else:
            target_id = room["exits"][parts[1]]
            new_room = world[target_id]
            print(f"  你抵达了【{new_room['name']}】。")
            print(f"【{new_room['name']}】{new_room['description']}")
    else:
        print(f"  未知指令 [{command}]。")
