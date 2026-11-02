"""mre_keyerror.py — 最小复现案例（MRE）：仅保留触发异常的核心语句，稳定复现 KeyError: 'market'"""

world = {
    "guangchang": {"name": "扬州广场", "exits": {"east": "market"}},
    "chaguan": {"name": "春来茶馆", "exits": {"west": "guangchang"}},
}
player_location = "guangchang"
direction = "east"
target_id = world[player_location]["exits"][direction]
new_room = world[target_id]          # 运行到这里稳定复现 KeyError: 'market'
print(f"抵达：{new_room['name']}")
