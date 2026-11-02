"""check_while_loop.py — 第 8 周任务一验收清单自动化校验（行为级，起真进程喂 stdin）

默认被测 mud_loop_v1.py；切换靶场做负向对照：
    MUD_LOOP_ENGINE=mud_loop_buggy.py python check_while_loop.py
"""

import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = Path(os.environ.get("MUD_LOOP_ENGINE", "mud_loop_v1.py"))
if not ENGINE.is_absolute():
    ENGINE = HERE / ENGINE

# 场景描述行的特征：【房间名】紧跟一段描述文字；抵达行 "你抵达了【春来茶馆】。" 不算。
SCENE_RE = re.compile(r"【(扬州中心广场|春来茶馆|江南武馆)】[^\n【]{4,}")
results = []


def scene_count(out, room=None):
    return [m.group(0) for m in SCENE_RE.finditer(out) if room is None or m.group(1) == room]


def run(script):
    """把脚本化指令喂给引擎，返回 (stdout, returncode)。6 秒超时视为死循环。"""
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


print(f"被测引擎：{ENGINE.name}\n")

# —— 验收项 1：输入 /go east 抵达春来茶馆后，下一轮输入 /look 是否仍留在茶馆（无位置重置）——
out, code = run("/go east\n/look\n/quit\n")
arrival = out.index("你抵达了【春来茶馆】") if "你抵达了【春来茶馆】" in out else -1
after = out[arrival:] if arrival >= 0 else ""
after_scenes = scene_count(after)
check(
    "抵达茶馆后 /look 仍留在茶馆（位置不被重置）",
    arrival >= 0 and after_scenes and all("春来茶馆" in s for s in after_scenes),
    f"抵达之后的场景行：{after_scenes}",
)

# —— 验收项 2：输入 /look 只打印一遍场景（开场白 1 次 + /look 1 次 = 2 次）——
out, code = run("/look\n/quit\n")
scenes = scene_count(out)
check(
    "/look 只打印一遍场景",
    len(scenes) == 2,
    f"场景行计数 = {len(scenes)}（期望 2：循环外开场 1 + /look 响应 1）",
)

# —— 验收项 2b：/go 移动成功当轮只打印新房间一次 ——
out, code = run("/go east\n/quit\n")
tea = scene_count(out, "春来茶馆")
check(
    "/go east 成功当轮只打印新房间描述一次",
    len(tea) == 1,
    f"春来茶馆场景行计数 = {len(tea)}（期望 1）",
)

# —— 验收项 2c：未输入任何指令直接 /quit，开场白只在循环外打印一次 ——
out, code = run("/quit\n")
scenes = scene_count(out)
check(
    "开场白只打印一次（已移出循环体）",
    len(scenes) == 1,
    f"场景行计数 = {len(scenes)}（期望 1）",
)

# —— 验收项 3：输入 /quit 能否正常退出（不死循环，exit 0，有告别语）——
out, code = run("/look\n/quit\n")
check(
    "/quit 正常退出：进程结束 + 告别语 + exit 0",
    code == 0 and "江湖再见" in out,
    f"returncode = {code}，告别语出现 = {'江湖再见' in out}",
)

failed = [label for label, ok, _ in results if not ok]
print()
if failed:
    print(f"验收未通过：{len(failed)}/{len(results)} 项 -> " + "；".join(failed))
    sys.exit(1)
print(f"验收清单全部通过 [x]：{len(results)}/{len(results)} 项，目标文件 {ENGINE.name}")
