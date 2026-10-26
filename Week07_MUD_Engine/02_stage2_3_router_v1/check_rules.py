"""check_rules.py — Stage 3 多条件规则验收清单自动化校验

运行：python check_rules.py
"""

import builtins
import importlib
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROBUST = HERE.parent / "03_stage4_5_robust_engine"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROBUST))
sys.path.insert(0, str(HERE.parent / "01_stage1_world_model"))

MODULE = os.environ.get("MUD_ENGINE", "mud_engine_v1")
ENGINE_PATH = (ROBUST / "mud_engine_robust.py") if MODULE == "mud_engine_robust" else (HERE / f"{MODULE}.py")
engine = importlib.import_module(MODULE)
from world_data import world

failures = []
P = engine.player


def reset(health=80, max_health=100, gold=50, reputation=10, inventory=None,
          location="guangchang", scholar_saved=False):
    P.update(health=health, max_health=max_health, gold=gold, reputation=reputation,
             inventory=list(inventory if inventory is not None else ["金创药", "粗布行囊"]),
             location=location, scholar_saved=scholar_saved)


def run(lines):
    """v1 用 handle() 直接 print；robust 用 dispatch() 返回文本。两者统一取证。"""
    out = []
    real_print = builtins.print
    builtins.print = lambda *a, **k: out.append(" ".join(str(x) for x in a))
    try:
        if hasattr(engine, "handle"):
            for line in lines:
                if not engine.handle(line, world[P["location"]]):
                    break
        else:
            for line in lines:
                result = engine.dispatch(line)
                if result is None:
                    break
                out.append(result)
    finally:
        builtins.print = real_print
    return "\n".join(out)


def check(label, cond, detail=""):
    mark = "True" if cond else f"False   ({detail})"
    print(f"  {label:<46} -> {mark}")
    if not cond:
        failures.append(label)


print("=" * 66)
print(f"Stage 3 验收清单：多条件先后顺序与价值规则（被测引擎 {MODULE}）")
print("=" * 66)

# —— 1. /heal：限制条件前置拦截 ——
reset(health=80, inventory=["粗布行囊"])
text = run(["/heal"])
check("无药时 /heal 被前置分支拦截", "已经没有【金创药】" in text, text.strip()[:40])
check("  无药未发生『空加血』", P["health"] == 80, P["health"])

reset(health=100, max_health=100, inventory=["金创药"])
text = run(["/heal"])
check("满血时 /heal 被前置分支拦截", "无需服用" in text, text.strip()[:40])
check("  满血未白耗药材", P["inventory"].count("金创药") == 1, P["inventory"])

reset(health=100, max_health=100, inventory=["粗布行囊"])
run(["/heal"])
check("既无药又满血 -> 优先命中『无药』(特异性优先)", "已经没有【金创药】" in run(["/heal"]), "顺序颠倒")

# —— 2. /heal：正常服药与封顶 ——
reset(health=70, inventory=["金创药", "粗布行囊"])
text = run(["/heal"])
check("受伤 70 -> 服药后 90", P["health"] == 90 and "90/100" in text, f"{P['health']} {text.strip()[:30]}")
check("  药材被移除", "金创药" not in P["inventory"], P["inventory"])

reset(health=95, inventory=["金创药"] * 5)
run(["/heal", "/heal", "/heal", "/heal", "/heal"])
check("连续服药气血封顶在 max_health(100)", P["health"] == 100, P["health"])

reset(health=60, max_health=80, inventory=["金创药"] * 3)
run(["/heal", "/heal", "/heal"])
check("低上限角色(80)服药同样不突破上限", P["health"] == 80, P["health"])
reset(health=80, max_health=80, inventory=["金创药"])
check("  低上限角色满血能被识别", "无需服用" in run(["/heal"]), "硬编码 100 会失真")

# —— 3. /help_scholar：地点与盘缠双守卫 ——
reset(gold=50, location="wuguan")
text = run(["/help_scholar"])
check("非茶馆地点被拦截并给出提示", "春来茶馆" in text, text.strip()[:40])
check("  拦截后铜钱/声望未变动", (P["gold"], P["reputation"]) == (50, 10), (P["gold"], P["reputation"]))

reset(gold=5, location="chaguan")
text = run(["/help_scholar"])
check("铜钱不足(<10)被拦截并给出提示", "盘缠" in text, text.strip()[:40])
check("  拦截后数值未变动", (P["gold"], P["reputation"]) == (5, 10), (P["gold"], P["reputation"]))

reset(gold=50, reputation=10, location="chaguan")
text = run(["/help_scholar"])
check("茶馆且铜钱充足 -> 扣 10 文、+15 声望", (P["gold"], P["reputation"]) == (40, 25), (P["gold"], P["reputation"]))
check("  回报文案含数值", "40" in text and "25" in text, text.strip()[:40])

text = run(["/help_scholar"])
check("重复救助被 scholar_saved 拦截(防刷声望)", (P["gold"], P["reputation"]) == (40, 25), (P["gold"], P["reputation"]))

# —— 4. 路由顺序：/help_scholar 不得被 /help 分支截走 ——
reset(location="chaguan", gold=50)
text = run(["/help_scholar"])
check("/help_scholar 未被 /help 前缀吞掉", "可用指令" not in text, text.strip()[:40])
reset(location="chaguan", gold=50)
text = run(["/HELP_SCHOLAR"])
check("  大写 /HELP_SCHOLAR 仍归一化生效", "扣 10 文" in text or "铜钱 -10" in text, text.strip()[:40])

# —— 5. /status 能反映规则改动的数值 ——
reset(health=70, gold=50, inventory=["金创药", "粗布行囊"])
text = run(["/heal", "/status"])
check("/status 展示服药后的最新状态", "生命：90/100" in text and "铜钱：50" in text, text.strip()[:40])

# —— 6. 端到端子进程 ——
proc = subprocess.run([sys.executable, str(ENGINE_PATH)],
                      input="/heal\n/heal\n/help_scholar\n/go east\n/help_scholar\n/status\n/quit\n",
                      capture_output=True, text=True, encoding="utf-8", cwd=str(ENGINE_PATH.parent))
check("子进程端到端 exit 0", proc.returncode == 0, f"rc={proc.returncode} {proc.stderr[:100]}")
check("  输出无 Traceback", "Traceback" not in proc.stdout + proc.stderr, proc.stderr[:120])
check("  第二次 /heal 触发满血或无药拦截", ("无需服用" in proc.stdout) or ("已经没有" in proc.stdout))

print("-" * 66)
if failures:
    print("未通过项：")
    for item in failures:
        print("  [ ]", item)
    raise SystemExit(1)
print("全部验收项通过 [x]")
