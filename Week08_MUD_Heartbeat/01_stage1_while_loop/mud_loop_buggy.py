"""mud_loop_buggy.py — 第 8 周任务一课程靶场（自建）

情景：把第 7 周的"单回合"脚本套上 while True 变成多轮交互时，整块初始化代码连同
开场白一起被误缩进到了循环体内，于是产生两处反常现象。

问题 1（位置重置）：位置初始化在循环内部，每轮开头把已走到茶馆的玩家置回扬州广场。
问题 2（重复打印）：每轮循环顶部无条件打印房间描述，与下方 /look 分支重复打印。

运行：python mud_loop_buggy.py
脚本化取证：printf '/go east\\n/look\\n/quit\\n' | python mud_loop_buggy.py
"""

world = {
    "guangchang": {
        "name": "扬州中心广场",
        "description": "青石铺地，人来人往，告示栏上贴着武林帖。向东可去茶馆，向西可去武馆。",
        "exits": {"east": "chaguan", "west": "wuguan"},
    },
    "chaguan": {
        "name": "春来茶馆",
        "description": "说书人醒木一拍，茶客们正议论少侠事迹。向西可返回中心广场。",
        "exits": {"west": "guangchang"},
    },
    "wuguan": {
        "name": "江南武馆",
        "description": "沙地上桩眼密布，教头正盯着你的根基。向东可返回中心广场。",
        "exits": {"east": "guangchang"},
    },
}

print("可用指令：/look  /go <方向>  /quit")

while True:
    # ———— 问题 1：位置初始化被误缩进到循环内部，每轮都被重新置回广场 ————
    player_location = "guangchang"

    # ———— 问题 2：循环顶部无条件打印房间描述，与下方 /look 分支重复 ————
    current_room = world[player_location]
    print(f"【{current_room['name']}】{current_room['description']}")

    command = input("> ").strip().lower()

    if command == "/quit":
        print("少侠抱拳离去，江湖再见。")
        break
    elif command == "/look":
        print(f"【{current_room['name']}】{current_room['description']}")
    elif command.startswith("/go"):
        parts = command.split()
        if len(parts) < 2:
            print("  要向哪里去？用法：/go <方向>")
        elif parts[1] in current_room["exits"]:
            player_location = current_room["exits"][parts[1]]
            print(f"  你抵达了【{world[player_location]['name']}】。")
        else:
            print(f"  无法向 [{parts[1]}] 前行。")
    else:
        print(f"  未知指令 [{command}]。")
