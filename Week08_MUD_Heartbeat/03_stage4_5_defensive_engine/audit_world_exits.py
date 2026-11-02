"""audit_world_exits.py — 启动期地图完整性自检（承接阶段三结论：in 守卫拦不住数据层缺陷）

用法：把 world 字典交给 audit(world)，它返回悬空出口列表；非空即拒绝开局。
    python audit_world_exits.py        # 自检演示：坏图 1 处悬空 / 好图 0 处
"""


def audit(world):
    """遍历每个房间的 exits 值，检查目标房间代号是否已在 world 中定义。"""
    dangling = []
    for room_id, room in world.items():
        for direction, target_id in room["exits"].items():
            if target_id not in world:
                dangling.append((room_id, direction, target_id))
    return dangling


if __name__ == "__main__":
    broken = {
        "guangchang": {"name": "扬州广场", "exits": {"east": "market", "west": "wuguan"}},
        "wuguan": {"name": "江南武馆", "exits": {"east": "guangchang"}},
    }
    fixed = {
        "guangchang": {"name": "扬州广场", "exits": {"east": "chaguan", "west": "wuguan"}},
        "chaguan": {"name": "春来茶馆", "exits": {"west": "guangchang"}},
        "wuguan": {"name": "江南武馆", "exits": {"east": "guangchang"}},
    }
    for label, world in (("坏图（market 未定义）", broken), ("好图（三房间连通）", fixed)):
        problems = audit(world)
        verdict = "拒绝开局" if problems else "放行"
        print(f"[自检] {label}: 悬空出口 {len(problems)} 处 -> {verdict}  {problems}")
