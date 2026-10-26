"""check_router.py — Stage 2 验收清单自动化校验

运行：python check_router.py
"""

import builtins
import importlib
import inspect
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


def run(lines):
    """在干净的 player 状态上跑一串指令，返回引擎的全部输出文本。
    v1 的 handle() 直接 print；robust 的 dispatch() 返回文本。"""
    engine.player["location"] = "guangchang"
    out = []
    real_print = builtins.print
    builtins.print = lambda *a, **k: out.append(" ".join(str(x) for x in a))
    try:
        if hasattr(engine, "handle"):
            for line in lines:
                if not engine.handle(line, world[engine.player["location"]]):
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
    print(f"  {label:<44} -> {cond}" + (f"   ({detail})" if detail and not cond else ""))
    if not cond:
        failures.append(f"{label} {detail}")


print("=" * 60)
print(f"Stage 2 验收清单（被测引擎 {MODULE}）")
print("=" * 60)

# 1) " /Go East " 归一化并成功移动
text = run([" /Go East "])
check('输入 " /Go East " 归一化识别为移动', "你抵达了" in text, text[:40])
check('  落点 = 春来茶馆(chaguan)', engine.player["location"] == "chaguan", engine.player["location"])

# 2) "/GO   EAST" 多空格 / 全大写同样归一
engine.player["location"] = "guangchang"
run(["  /GO   EAST  "])
check('输入 "  /GO   EAST  " 仍归一成功', engine.player["location"] == "chaguan", engine.player["location"])

# 3) 不存在方向被 in 守卫拦截，不崩溃且位置不变
engine.player["location"] = "guangchang"
text = run(["/go up"])
check('输入 /go up 被 in 守卫拦截（无 Traceback）', "无法向 [up] 前行" in text, text[:40])
check('  石墙受阻提示可见', "石墙" in text)
check('  非法移动后位置未被改写', engine.player["location"] == "guangchang", engine.player["location"])

# 4) 只有 "/go" 无方向：不得 IndexError
engine.player["location"] = "guangchang"
text = run(["/go"])
check('输入裸 /go 不触发 IndexError', any(k in text for k in ("用法", "要向哪里", "指明方向")), text[:40])

# 5) 查表寻址：移动分支内不得出现硬编码房间 id
move_src = inspect.getsource(engine.move)
check("  移动分支零硬编码房间 id", all(rid not in move_src for rid in world))

# 6) 双向闭环可走通：广场->茶馆->广场
engine.player["location"] = "guangchang"
run(["/go east", "/go west"])
check('广场 --east--> 茶馆 --west--> 广场 闭环', engine.player["location"] == "guangchang", engine.player["location"])

# 7) /look 与 /status 正常输出
engine.player["location"] = "wuguan"
text = run(["/look", "/status"])
check('/look 打印房间描述与出口', "江南武馆" in text and "出口" in text)
check('/status 打印生命/铜钱/声望/背包', all(k in text for k in ("生命", "铜钱", "声望", "背包")))

# 8) 端到端子进程冒烟（真实 stdin/stdout）
proc = subprocess.run([sys.executable, str(ENGINE_PATH)],
                      input=" /Go East \n/go up\n/quit\n", capture_output=True, text=True,
                      encoding="utf-8", cwd=str(ENGINE_PATH.parent))
check('子进程端到端跑通 exit 0', proc.returncode == 0, f"rc={proc.returncode} {proc.stderr[:80]}")
check('  子进程输出无 Traceback', "Traceback" not in proc.stdout + proc.stderr)

# 9) 第 4 房间「只改字典不改分支」：新房间必须纯靠查表抵达
engine.player["location"] = "guangchang"
text = run(["/look"])
check("广场 /look 自动列出 3 个出口（含北向）", text.count("出口：") == 3 and "[north]" in text, text[:40])
text = run(["/go north"])
check('输入 /go north 查表抵达【白鹿洞书院】', engine.player["location"] == "shuyuan", engine.player["location"])
check("  新房间描述随之自动生效", "白鹿洞书院" in text and "翠竹掩映" in text, text[:40])
engine.player["location"] = "shuyuan"
run(["/go north", "/go south"])
check("  书院北向仍受阻且 --south--> 广场闭环", engine.player["location"] == "guangchang", engine.player["location"])
engine_src = ENGINE_PATH.read_text(encoding="utf-8")
check("  路由源码零出现新房间 id（真·只改数据）", "shuyuan" not in engine_src and "白鹿洞" not in engine_src)

print("-" * 60)
if failures:
    print("未通过项：")
    for item in failures:
        print("  [ ]", item)
    raise SystemExit(1)
print("全部验收项通过 [x]")
