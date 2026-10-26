# 缺陷修复版：去除 health / gold 及增量两侧的双引号，恢复原生 int
# 修复前 player["health"] = "80" + "20" -> "8020"（字符串首尾拼接）
# 修复后 player["health"] = 80 + 20    -> 100（整数加法，但已超出 max_health）

player = {
    "name": "少侠郭靖",
    "health": 80,   # 修复：int
    "gold": 50,     # 修复：int
    "inventory": ["金创药", "粗布行囊"],
}

player["health"] = player["health"] + 20   # 100
player["gold"] = player["gold"] + 10       # 60

if __name__ == "__main__":
    print("health =", player["health"], type(player["health"]).__name__)
    print("gold   =", player["gold"], type(player["gold"]).__name__)
    assert isinstance(player["health"], int) and isinstance(player["gold"], int)
    print("类型校验通过：health / gold 均为 int")
