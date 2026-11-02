"""check_for_loops.py — 第 8 周任务二验收自动化校验（for 遍历三处写法）

期望值不再写死地图，而是从被测引擎的 world 字典现算，因此同一套断言可验 v2 与任务五终稿（广场多出 1 条未开放出口）。
默认被测 mud_loop_v2.py；切换负向对照：
    MUD_LOOP_ENGINE=mud_loop_v1.py python check_for_loops.py            # 无 items / 无 /bag -> FAIL
    MUD_LOOP_ENGINE=../03_stage4_5_defensive_engine/mud_engine_defensive.py python check_for_loops.py
"""

import contextlib
import io
import importlib.util
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = Path(os.environ.get("MUD_LOOP_ENGINE", "mud_loop_v2.py"))
if not ENGINE.is_absolute():
    ENGINE = HERE / ENGINE

ROOM_NAMES = ("扬州中心广场", "春来茶馆", "江南武馆")
results = []


def run(script):
    proc = subprocess.run(
        [sys.executable, str(ENGINE)],
        input=script,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=6,
    )
    return proc.stdout, proc.returncode


def check(label, ok, detail):
    results.append((label, ok, detail))
    print(f"  [{'x' if ok else ' '}] {label}\n        {detail}")


# —— 从被测引擎现算期望值；缺字段即判定"任务二功能缺失"，不让断言退化成恒真 ——
spec = importlib.util.spec_from_file_location("engine_under_test", ENGINE)
MOD = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(MOD)                               # 模块级应只有初始化
    load_error = None
except Exception as exc:                                        # 靶场是模块级交互脚本，import 即起循环
    load_error = f"{type(exc).__name__}: {exc}"


def fixture():
    gc = MOD.world["guangchang"]
    items = gc["items"]
    exits = gc["exits"]
    defined = {MOD.world[t]["name"] for t in exits.values() if t in MOD.world}
    return items, exits, defined


if load_error:
    GC_ITEMS = GC_EXITS = CHA_ITEMS = None
    GC_DEFINED_TARGETS = set()
    INVENTORY_LEN = 0
    missing = f"被测引擎无法作为数据源加载：{load_error}"
else:
    try:
        GC_ITEMS, GC_EXITS, GC_DEFINED_TARGETS = fixture()
        CHA_ITEMS = MOD.world["chaguan"]["items"]
        INVENTORY_LEN = len(MOD.player["inventory"])
        missing = None
    except (KeyError, AttributeError) as exc:
        GC_ITEMS = GC_EXITS = CHA_ITEMS = None
        GC_DEFINED_TARGETS = set()
        INVENTORY_LEN = 0
        missing = f"被测引擎缺字段：{exc!r}"

print(f"被测引擎：{ENGINE.name}" + (f"（{missing}）" if missing else "") + "\n")


def lines_with(out, tag):
    return [line for line in out.splitlines() if tag in line]


def targets_of(nav_lines):
    captured = [re.search(r"通往【(.+?)】", line).group(1) for line in nav_lines if "通往【" in line]
    return [name for name in captured if name in ROOM_NAMES]


# —— 验收项 1：/look 自动列出当前房间全部地面物品（① 遍历列表元素）——
out, code = run("/look\n/quit\n")
ground = lines_with(out, "[地面物品]")
expect_items = len(GC_ITEMS) * 2 if GC_ITEMS is not None else 0     # 循环外开场 1 次 + /look 响应 1 次
check(
    "/look 列出当前房间全部地面物品",
    bool(missing is None and len(ground) == expect_items and all("你发现地上有：【" in line for line in ground)),
    f"[地面物品] 行数 = {len(ground)}（期望 {expect_items}：开场与 /look 各 {len(GC_ITEMS) if GC_ITEMS else 0} 件）"
    + (f" —— {missing}" if missing else ""),
)

# —— 验收项 2：/look 遍历出口字典，打印目标房间中文名（② 遍历字典键值对）——
nav = lines_with(out, "[此地出口]")
expect_nav = len(GC_EXITS) * 2 if GC_EXITS is not None else 0
check(
    "/look 用 .items() 遍历出口并查出目标房间中文名",
    missing is None and len(nav) == expect_nav and set(targets_of(nav)) == GC_DEFINED_TARGETS,
    f"[此地出口] 行数 = {len(nav)}（期望 {expect_nav}：出口 {len(GC_EXITS) if GC_EXITS else 0} 条 ×2），"
    f"已定义目标中文名 = {sorted(set(targets_of(nav)))}（期望 {sorted(GC_DEFINED_TARGETS)}）",
)

# —— 验收项 3：/go 移动后自动列出新房间的物品与出口（不是旧房间残留）——
out, code = run("/go east\n/quit\n")
after = out[out.index("你抵达了【春来茶馆】"):] if "你抵达了【春来茶馆】" in out else ""
tea_ground = lines_with(after, "[地面物品]")
tea_nav = lines_with(after, "[此地出口]")
opening_leftover = [line for line in tea_ground if any(item in line for item in (GC_ITEMS or []))]
check(
    "移动后自动列出新房间（春来茶馆）的物品与出口，无旧房间残留",
    missing is None and len(tea_ground) == len(CHA_ITEMS or []) and not opening_leftover
    and targets_of(tea_nav) == ["扬州中心广场"],
    f"抵达后物品行 = {len(tea_ground)}（期望 {len(CHA_ITEMS or [])}）；旧房间残留 = {opening_leftover}；"
    f"抵达后出口目标 = {targets_of(tea_nav)}",
)

# —— 验收项 4：/bag 从 [1] 开始带编号打印行囊（③ enumerate(start=1)）——
out, code = run("/bag\n/quit\n")
nums = [int(m.group(1)) for line in out.splitlines() for m in [re.search(r"\[(\d+)\]\s+\S", line)] if m]
check(
    "/bag 行囊清单从 [1] 开始连续编号",
    missing is None and nums == list(range(1, INVENTORY_LEN + 1)) and INVENTORY_LEN > 0,
    f"编号序列 = {nums}（期望 1..{INVENTORY_LEN}，enumerate 起点为 1 非 0）"
    + (f" —— {missing}" if missing else ""),
)

# —— 验收项 5：空容器边界——地面物品为空 / 行囊为空时 for 不进入循环，程序不崩 ——
captured = io.StringIO()
try:
    with contextlib.redirect_stdout(captured):
        MOD.player["inventory"] = []                         # 掏空行囊
        MOD.show_bag()                                        # ③ 遍历空列表
        MOD.player["location"] = "chaguan"
        MOD.world["chaguan"]["items"] = []                    # 掏空地面物品
        MOD.describe(MOD.world["chaguan"])                    # ① 遍历空列表
    crashed = False
except Exception as exc:                                       # 缺 /bag、房间无 items 等
    crashed = True
    captured.write(f"EXC {type(exc).__name__}: {exc}")
body = captured.getvalue()
check(
    "空容器边界：items / inventory 为空时 for 零次进入，不报错",
    not crashed and "[1]" not in body and "[地面物品]" not in body and "【春来茶馆】" in body,
    f"空容器输出片段：{body.strip().splitlines()[:4]}",
)

failed = [label for label, ok, _ in results if not ok]
print()
if failed:
    print(f"验收未通过：{len(failed)}/{len(results)} 项 -> " + "；".join(failed))
    sys.exit(1)
print(f"验收清单全部通过 [x]：{len(results)}/{len(results)} 项，目标文件 {ENGINE.name}")
