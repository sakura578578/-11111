# 课程靶场：故意保留类型缺陷，用于人工审查练习
# 缺陷点：health / gold 及增量数值被写成 str（带双引号），+ 变成字符串拼接

player = {
    "name": "少侠郭靖",
    "health": "80",   # 缺陷：误用 str 存储数值
    "gold": "50",     # 缺陷：误用 str 存储数值
    "inventory": ["金创药", "粗布行囊"],
}

player["health"] = player["health"] + "20"   # 实测输出 "8020"
player["gold"] = player["gold"] + "10"       # 实测输出 "5010"

if __name__ == "__main__":
    print("health =", player["health"], type(player["health"]))
    print("gold   =", player["gold"], type(player["gold"]))
