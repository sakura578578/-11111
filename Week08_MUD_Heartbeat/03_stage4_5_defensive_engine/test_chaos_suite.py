"""test_chaos_suite.py — 进阶挑战一：7 步多轮交互自动化回归套件 + MAX_TURNS 循环保护实测

ROCA 提示词：请编写自动化测试脚本 test_chaos_suite.py，使用 7 条测试指令序列，
用 for 循环依次向 mud_engine_defensive.py 传入
["/look", "/bag", "/go north(测试未开放房间提示)", "/go east", "/buy_tea(验证 50->35 文)", "/go west", "/quit"]，
自动校验每一步返回文本是否符合预期并统计 PASS 通过率。

设计要点：7 条指令在**同一次进程会话**里按序喂入（真·多轮状态迁移），再用游标顺序匹配期望文本——
既校验"内容对不对"，也校验"顺序对不对"（第 5 步的账目必须出现在第 4 步抵达茶馆之后）。

默认被测 mud_engine_defensive.py；负向对照：
    MUD_LOOP_ENGINE=../02_stage3_chaos_targets/mud_chaos_buggy.py python test_chaos_suite.py
"""

import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = Path(os.environ.get("MUD_LOOP_ENGINE", "mud_engine_defensive.py"))
if not ENGINE.is_absolute():
    ENGINE = HERE / ENGINE
V2 = HERE.parent / "01_stage1_while_loop" / "mud_loop_v2.py"   # 未加回合上限保护的对照组

# 7 步指令 -> 该步应有的返回文本
STEPS = [
    ("/look", "【扬州中心广场】", "开场场景可查"),
    ("/bag", "[1] 金创药", "行囊从 [1] 起编号"),
    ("/go north", "尚未开放，请留步", "未定义房间走方案 B 提示，不抛 KeyError"),
    ("/go east", "你抵达了【春来茶馆】", "边界检查放行合法出口"),
    ("/buy_tea", "铜钱 50 -> 35", "扣款方向正确（缺陷写法会变 65）"),
    ("/go west", "你抵达了【扬州中心广场】", "多轮位置状态可回迁"),
    ("/quit", "江湖再见", "人工退出分支 break 生效"),
]


def run(engine, lines, env_extra=None):
    env = {**os.environ, **(env_extra or {})}
    proc = subprocess.run([sys.executable, str(engine)], input="".join(line + "\n" for line in lines),
                          capture_output=True, text=True, encoding="utf-8", errors="replace",
                          timeout=8, env=env)
    return proc.stdout, proc.stderr, proc.returncode


def check(label, ok, detail):
    print(f"  [{'x' if ok else ' '}] {label}\n        {detail}")
    return ok


print(f"被测引擎：{ENGINE.name}\n")
results = []

# ————— 一、7 步指令序列：单次会话按序喂入，游标顺序匹配 —————
out, err, code = run(ENGINE, [cmd for cmd, _, _ in STEPS])
cursor = 0
for index, (cmd, expected, why) in enumerate(STEPS, 1):
    pos = out.find(expected, cursor)
    ok = pos >= 0
    results.append(ok)
    check(f"步骤 {index} {cmd:<10} 预期文本 {expected!r}", ok,
          (f"命中于输出第 {pos} 字符（顺序正确），用途：{why}" if ok
           else f"游标 {cursor} 之后未找到 {expected!r}，用途：{why}")
          + ("" if ok else f"\n        实际该段输出：{out[cursor:cursor + 160]!r}"))

clean_exit = code == 0 and "Traceback" not in err
results.append(clean_exit)
check("全流程 无 Traceback 且 exit 0", clean_exit, f"returncode = {code}，stderr 含 Traceback = {'Traceback' in err}")

turns_ok = all(f"[第 {i} 回合] 少侠请下令" in out for i in range(1, len(STEPS) + 1))
results.append(turns_ok)
check("回合编号逐轮递增可见（第 1..7 回合）", turns_ok,
      f"7 个回合提示全部出现 = {turns_ok}")

# ————— 二、MAX_TURNS 循环安全保护：上限压到 3，却喂 5 条指令 —————
SCENE_RE = re.compile(r"【(扬州中心广场|春来茶馆|江南武馆)】[^\n【]{4,}")


def scenes(text):
    """场景描述行计数：不写死行首，因为回合提示符会与响应同处一行。"""
    return SCENE_RE.findall(text)


FIVE_LOOKS = ["/look"] * 5
out, err, code = run(ENGINE, FIVE_LOOKS, {"MUD_MAX_TURNS": "3"})
cap_hit = ("已走满 3 回合上限" in out and "[第 4 回合]" not in out and code == 0
           and len(scenes(out)) == 1 + 3)          # 开场 1 次 + 仅前 3 条指令被消费
results.append(cap_hit)
check("保护一 走满上限自动收束（上限 3，喂 5 条 /look）", cap_hit,
      f"场景行数 = {len(scenes(out))}（期望 4 = 开场 1 + 前 3 回合），第 4 回合出现 = {'[第 4 回合]' in out}（应 False），"
      f"收束提示 = {'已走满 3 回合上限' in out}，returncode = {code}")

# 负向对照：未加保护的 v2 忽略 MUD_MAX_TURNS，5 条指令全部被消费且无收束提示——否则该断言是恒真
out2, err2, code2 = run(V2, FIVE_LOOKS, {"MUD_MAX_TURNS": "3"})
no_cap = len(scenes(out2)) == 1 + 5 and "已走满" not in out2
control_ok = no_cap and code2 == 0
results.append(control_ok)
check(f"保护一 负向对照成立（未加固的 {V2.name} 走满 5 回合、无收束提示）", control_ok,
      f"v2 场景行数 = {len(scenes(out2))}（无上限时应为 6 = 开场 1 + 5 条全消费），收束提示 = {'已走满' in out2}")

passed = sum(results)
total = len(results)
print(f"\nPASS 通过率 = {passed}/{total}（{passed * 100 // total}%）")
if passed != total:
    print(f"套件未通过：{total - passed} 项失败，目标文件 {ENGINE.name}")
    sys.exit(1)
print(f"7 步交互 + 循环保护自动化回归全部通过 [x]，目标文件 mud_engine_defensive.py")
