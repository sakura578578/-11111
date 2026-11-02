"""mud_loop_v1.py — 第 8 周任务一：持续交互主循环（ROCA 生成，缺陷已修复）

生成提示词（ROCA）见 ../README.md。

修复对照：
  问题 1 位置重置 -> player 字典与 world 一同定义在 while True 外部上方，循环内只读写 player["location"]。
  问题 2 重复打印 -> 初始开场白只在进入循环前打印一次；循环内仅在 /look 或 /go 移动成功时打印描述。
  约束 3 安全退出 -> /quit 打印告别语后立即 break，杜绝死循环。

运行：python mud_loop_v1.py
脚本化验收：printf '/go east\\n/look\\n/quit\\n' | python mud_loop_v1.py
"""

# ——————————————————————— 循环外初始化（严禁缩进进循环）———————————————————————
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

player = {"name": "少侠郭靖", "location": "guangchang"}

BANNER = "可用指令：/look  /go <方向>  /quit"


def describe(room):
    print(f"【{room['name']}】{room['description']}")


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
        elif command.startswith("/go"):
            parts = command.split()
            room = world[player["location"]]
            if len(parts) < 2:
                print("  要向哪里去？用法：/go <方向>")
            elif parts[1] in room["exits"]:
                player["location"] = room["exits"][parts[1]]
                new_room = world[player["location"]]
                print(f"  你抵达了【{new_room['name']}】。")
                describe(new_room)                   # 移动成功才打印
            else:
                print(f"  无法向 [{parts[1]}] 前行。")
        elif command:
            print(f"  未知指令 [{command}]。{BANNER}")


if __name__ == "__main__":
    main()
