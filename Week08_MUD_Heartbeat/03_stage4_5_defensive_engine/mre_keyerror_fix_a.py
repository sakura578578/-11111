"""mre_keyerror_fix_a.py — 方案 A：仅修正字典错误键值（market -> chaguan），代码结构一字未动"""

world = {
    "guangchang": {"name": "扬州广场", "exits": {"east": "chaguan"}},
    "chaguan": {"name": "春来茶馆", "exits": {"west": "guangchang"}},
}
player_location = "guangchang"
direction = "east"
target_id = world[player_location]["exits"][direction]
new_room = world[target_id]          # 数据改对后此处不再抛异常
print(f"抵达：{new_room['name']}")
