"""check_world_data.py — Stage 1 验收清单自动化校验

运行：python check_world_data.py
"""

from world_data import world, player

REQUIRED_ROOMS = {
    "guangchang": ("west", "wuguan", "east", "chaguan", "north", "shuyuan"),
    "shuyuan": ("south", "guangchang"),
    "chaguan": ("west", "guangchang"),
    "wuguan": ("east", "guangchang"),
}

failures = []

# 1) 房间齐全 + 字段类型
for room_id in REQUIRED_ROOMS:
    if room_id not in world:
        failures.append(f"world 缺少地点 {room_id}")
        continue
    room = world[room_id]
    if not isinstance(room.get("name"), str):
        failures.append(f"{room_id}.name 不是 str")
    if not isinstance(room.get("description"), str):
        failures.append(f"{room_id}.description 不是 str")
    if not isinstance(room.get("exits"), dict):
        failures.append(f"{room_id}.exits 不是 dict")

# 2) 双向出口闭环连通
for room_id, required in REQUIRED_ROOMS.items():
    exits = world.get(room_id, {}).get("exits", {})
    for i in range(0, len(required), 2):
        direction, target = required[i], required[i + 1]
        if exits.get(direction) != target:
            failures.append(f"{room_id} 的 {direction} 未指向 {target}")
        back = world.get(target, {}).get("exits", {})
        if room_id not in back.values():
            failures.append(f"{target} 没有回指 {room_id} 的出口（单向死路）")

# 3) 所有出口目标必须是已定义地点
for room_id, room in world.items():
    for direction, target in room.get("exits", {}).items():
        if target not in world:
            failures.append(f"{room_id}.{direction} 指向未定义地点 {target}")

# 4) 角色字段类型安全（严禁 str 存数值）
for field in ("health", "max_health", "gold", "reputation"):
    value = player.get(field)
    if type(value) is not int:
        failures.append(f"player['{field}'] 应为 int，实际 {type(value).__name__} = {value!r}")

for field in ("name", "location"):
    if not isinstance(player.get(field), str):
        failures.append(f"player['{field}'] 应为 str")
if not isinstance(player.get("inventory"), list):
    failures.append("player['inventory'] 应为 list")
if player.get("location") not in world:
    failures.append("player['location'] 不在 world 中")

# 5) 数值运算验证：+20 必须做整数加法，不得出现 "8020"
if type(player["health"]) is int:
    if player["health"] + 20 != 100:
        failures.append(f"health + 20 = {player['health'] + 20}，期望 100")
else:
    failures.append("health 为 str，80+20 会拼成 '8020'")

health_ok = type(player["health"]) is int

print("=" * 46)
print("Stage 1 验收清单")
print("=" * 46)
print(f"  type(player['health']) is int      -> {type(player['health']) is int}")
print(f"  type(player['gold']) is int        -> {type(player['gold']) is int}")
print(f"  type(player['reputation']) is int  -> {type(player['reputation']) is int}")
print(f"  health(80) + 20 == 100             -> {health_ok and player['health'] + 20 == 100}")
print(f"  出口均指向已定义地点               -> {not any('未定义' in f for f in failures)}")
print(f"  双向出口闭环连通                   -> {not any('单向死路' in f or '未指向' in f or '缺少' in f for f in failures)}")
print("-" * 46)
if failures:
    print("未通过项：")
    for item in failures:
        print("  [ ]", item)
    raise SystemExit(1)
print("全部验收项通过 [x]")
