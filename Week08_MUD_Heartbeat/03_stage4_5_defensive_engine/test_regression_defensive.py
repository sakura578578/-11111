"""test_regression_defensive.py — 第 8 周任务五三项回归测试（起真进程喂 stdin，同时检查 stderr 无 Traceback）

默认被测 mud_engine_defensive.py；负向对照（同一套断言跑阶段三靶场）：
    MUD_LOOP_ENGINE=../02_stage3_chaos_targets/mud_chaos_buggy.py python test_regression_defensive.py
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

results = []


def run(script):
    proc = subprocess.run([sys.executable, str(ENGINE)], input=script, capture_output=True,
                          text=True, encoding="utf-8", errors="replace", timeout=6)
    return proc.stdout, proc.stderr, proc.returncode


def check(label, ok, detail):
    results.append((label, ok, detail))
    print(f"  [{'x' if ok else ' '}] {label}\n        {detail}")


print(f"被测引擎：{ENGINE.name}\n")

# —— 回归 i：输入 /go east 正常抵达【春来茶馆】——
out, err, code = run("/go east\n/quit\n")
check("i  /go east 正常抵达【春来茶馆】",
      "你抵达了【春来茶馆】" in out and code == 0 and "Traceback" not in err,
      f"抵达行存在 = {'你抵达了【春来茶馆】' in out}，returncode = {code}，stderr 无 Traceback = {'Traceback' not in err}")

# —— 回归 ii：在茶馆输入 /buy_tea，铜钱从 50 正确扣减为 35 ——
out, err, code = run("/go east\n/buy_tea\n/quit\n")
ledger = re.search(r"铜钱 (\d+) -> (\d+)", out)
check("ii 茶馆 /buy_tea：50 文正确扣成 35 文（缺陷写法会变 65）",
      bool(ledger) and (int(ledger.group(1)), int(ledger.group(2))) == (50, 35) and code == 0,
      f"实测账目 = {ledger.groups() if ledger else '未打印扣款行'}（期望 ('50', '35')），returncode = {code}")

# —— 回归 iii：广场 /go north 指向未定义的 market_unbuilt -> 提示未开放，不崩溃、位置不变 ——
out, err, code = run("/go north\n/look\n/quit\n")
check("iii /go north 撞未开放区域：出系统提示 + 不崩 + 位置保持",
      "尚未开放，请留步" in out and code == 0 and "Traceback" not in err
      and out.count("【扬州中心广场】") >= 2,
      f"提示行存在 = {'尚未开放，请留步' in out}，returncode = {code}，stderr 无 Traceback = {'Traceback' not in err}，"
      f"被拦后 /look 仍在广场 = {out.count('【扬州中心广场】') >= 2}")

# —— 附加：钱不够时的限制性分支（不得扣成负数、不得白给茶）——
out, err, code = run("/buy_tea\n/buy_tea\n/buy_tea\n/buy_tea\n/quit\n")
final = re.findall(r"铜钱 \d+ -> (\d+)", out)
check("边界 连续买 4 碗：第 4 次钱不够被拦，铜钱不为负",
      final == ["35", "20", "5"] and "只剩 5 文" in out and code == 0,
      f"成功扣款序列 = {final}（期望 35/20/5，第 4 次拦下），returncode = {code}")

# —— 附加：启动自检只知情不阻断（故意未开放 != 事故）——
out, err, code = run("/quit\n")
check("启动自检输出未定义区域清单，但游戏仍能开局并正常 /quit",
      "[自检]" in out and "market_unbuilt" in out and code == 0 and "少侠抱拳离去" in out,
      f"自检行存在 = {'[自检]' in out}，returncode = {code}")

failed = [label for label, ok, _ in results if not ok]
print()
if failed:
    print(f"回归未通过：{len(failed)}/{len(results)} 项 -> " + "；".join(failed))
    sys.exit(1)
print(f"三项回归 + 边界/启动自检全部通过 [x]：{len(results)}/{len(results)} 项，目标文件 {ENGINE.name}")
