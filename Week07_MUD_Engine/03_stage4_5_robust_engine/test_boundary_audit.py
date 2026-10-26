"""test_boundary_audit.py — 自动化边界回归审计（5 类 9 用例，进程内直调路由函数）

对照手工敲键：改一次路由分支就要在终端重敲 9 条，耗时且易漏测。
本脚本把输入与预期关键词固化为用例表，直接 import mud_engine_robust.dispatch()，
用 try...except 兜住任何未预见异常，统计通过率。

运行：python test_boundary_audit.py     （9 项，进程内耗时 <0.1 秒）
"""

import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "01_stage1_world_model"))

import mud_engine_robust as engine
from world_data import player, world

# (类别, 输入, 起始地点, 必含关键词组, 预期落点)
CASES = [
    ("1 首尾空白与大小写", " /Go East ", "guangchang", ("你抵达了", "春来茶馆"), "chaguan"),
    ("1 首尾空白与大小写", "/GO EAST", "guangchang", ("你抵达了", "春来茶馆"), "chaguan"),
    ("2 动词与方向多空格", "/go   west", "guangchang", ("你抵达了", "江南武馆"), "wuguan"),
    ("2 动词与方向多空格", "/go    east   ", "guangchang", ("你抵达了", "春来茶馆"), "chaguan"),
    ("3 缺失方向参数", "/go", "guangchang", ("指明方向",), "guangchang"),
    ("4 非法方向越界", "/go up", "guangchang", ("无法向 [up] 前行",), "guangchang"),
    ("4 非法方向越界", "/go north", "shuyuan", ("石墙受阻",), "shuyuan"),
    ("5 空回车与乱码", "", "chaguan", ("查看指令",), "chaguan"),
    ("5 空回车与乱码", "/fly", "chaguan", ("未知指令",), "chaguan"),
]


def setup(location):
    player["location"] = location
    player["health"] = 80
    player["gold"] = 50
    player["scholar_saved"] = False
    player["inventory"] = ["金创药", "粗布行囊"]


def audit(category, raw, start, keywords, expect_room):
    setup(start)
    before = world[start]["name"]
    try:
        output = engine.dispatch(raw)
    except Exception as exc:                       # 任何逃逸异常都算审计失败
        return False, f"{type(exc).__name__}: {exc}", "", True
    text = output if isinstance(output, str) else str(output)
    missing = [k for k in keywords if k not in text]
    if missing:
        return False, f"缺少关键词 {missing}", text, False
    if player["location"] != expect_room:
        return False, f"落点应为 {expect_room}，实际 {player['location']}", text, False
    return True, f"含 {list(keywords)}，落点 {before}->{world[expect_room]['name']}", text, False


print("=" * 74)
print("边界审计自动化回归：mud_engine_robust.dispatch()")
print("=" * 74)

started = time.perf_counter()
passed = 0
caught = 0
last_category = None
for idx, case in enumerate(CASES, start=1):
    category, raw = case[0], case[1]
    if category != last_category:
        print(f"\n— 类别 {category} —")
        last_category = category
    ok, reason, text, was_exc = audit(*case)
    passed += ok
    caught += was_exc
    print(f"  [{idx}] {'PASS' if ok else 'FAIL'}  输入 {repr(raw)}")
    print(f"        {reason}")
    if not ok:
        print(f"        实得输出：{text[:60]}")

elapsed = time.perf_counter() - started
total = len(CASES)
rate = passed / total * 100
print("\n" + "-" * 74)
print(f"  用例总数：{total}    PASS：{passed}    FAIL：{total - passed}")
print(f"  通过率：{rate:.1f}%    耗时：{elapsed * 1000:.1f} ms（进程内直调，零子进程开销）")
print(f"  被 try 兜住的异常：{caught}（>0 说明路由层守卫失守，只是没让进程崩）")
print("  指令路由 = strip().lower() + split() + len() 检查 + 字典查表")
print("-" * 74)
if passed != total or caught:
    print("  [ ] 未通过：存在崩溃或语义偏差用例")
    raise SystemExit(1)
print("  [x] 全部 PASS，零异常崩溃")
