"""mud_chaos_buggy_debug.py — 第 8 周任务三：缺陷 B 的 print() 调试取证版

与 mud_chaos_buggy.py 唯一的区别：在 /buy_tea 扣款语句前后各插一行 [DEBUG] 打印，
把"控制台不报错但数值悄悄跑偏"的静默逻辑错误显式量化出来。缺陷本身原样保留。
缺陷 A 的原始 Traceback 请用 mud_chaos_buggy.py 采集（实测 line 64, in <module>）；
本文件因文档注释与插入打印的行数之差，实测缺陷 A 的崩溃行落在 line 63——行号以原版为准。

静默错误的取证办法：预期值先算好存进 expected，交易后再与实测值并排打印。

运行：python mud_chaos_buggy_debug.py
取证 B：printf '/buy_tea\n/quit\n' | python mud_chaos_buggy_debug.py
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
        expected = player["gold"] - price          # 先按"应付账"算出预期值
        print(f"  伙计报上价：碧螺春 {price} 文一碗。")
        print(f"[DEBUG] 交易前 player['gold'] = {player['gold']}，单价 price = {price}，预期交易后 = {expected}")
        player["gold"] += price                # ← 缺陷 B：扣款方向写反（应为 -=），类型正确故不报错
        print(f"[DEBUG] 交易后 player['gold'] = {player['gold']}，实测 {player['gold']} vs 预期 {expected}，偏差 {player['gold'] - expected:+d}")
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
