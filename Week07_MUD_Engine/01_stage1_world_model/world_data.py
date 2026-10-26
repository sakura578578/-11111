"""world_data.py — Stage 1 静态数据模块（ROCA 生成）

只定义数据，不含游戏逻辑，供后续 MUD 引擎模块 import。
类型安全约束：health / max_health / gold / reputation 必须为原生 int。
"""

# ——————————————————————— 世界地图：三连通房间 ———————————————————————
world = {
    "guangchang": {
        "name": "扬州中心广场",
        "description": "青石铺地，人来人往，告示栏上贴着武林帖。向东可去茶馆，向西可去武馆，北面通往白鹿洞书院。",
        "exits": {"east": "chaguan", "west": "wuguan", "north": "shuyuan"},
    },
    "shuyuan": {
        "name": "白鹿洞书院",
        "description": "翠竹掩映着古朴的藏书阁，案头摆放着先贤手稿。向南可返回中心广场。",
        "exits": {"south": "guangchang"},
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

# ——————————————————————— 角色档案 ———————————————————————
player = {
    "name": "少侠郭靖",
    "location": "guangchang",
    "health": 80,
    "max_health": 100,
    "gold": 50,
    "reputation": 10,
    "inventory": ["金创药", "粗布行囊"],
    "scholar_saved": False,
}

if __name__ == "__main__":
    for room_id, room in world.items():
        print(f"[{room_id}] {room['name']} -> {room['exits']}")
    print("player =", player)
