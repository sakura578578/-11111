"""mre_keyerror_fix_b.py — 方案 B：防御式编程，取键前先做存在性检查

故意保留错误数据 "east": "market"，用来证明防御层生效：程序不崩、给玩家可读反馈、进程正常收尾。
"""

world = {
    "guangchang": {"name": "扬州广场", "exits": {"east": "market"}},
    "chaguan": {"name": "春来茶馆", "exits": {"west": "guangchang"}},
}
player_location = "guangchang"
direction = "east"

target_id = world[player_location]["exits"][direction]
if target_id not in world:                       # 边界检查：出口指向的房间是否已定义
    print(f"  向 [{direction}] 前行通向一处未开市的黑巷（内部代号 {target_id}），你退回了原处。")
else:
    player_location = target_id                  # 校验通过才落状态，避免写进不存在的房间
    new_room = world[player_location]
    print(f"抵达：{new_room['name']}")

print(f"  当前仍在：{world[player_location]['name']}    进程正常结束，无异常抛出。")
