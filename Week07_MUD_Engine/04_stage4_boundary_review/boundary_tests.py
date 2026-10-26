"""boundary_tests.py — Stage 4/5 边界审查：5 类非常规输入测试与报错定位

对同一组用例分别喂给三个引擎（各自独立子进程，状态互不污染）：
    靶场 mud_engine_v1_buggy.py  —— 预期崩溃，用于取证
    合规 mud_engine_v1.py        —— 预期零异常
    加固 mud_engine_robust.py    —— 预期零异常（Stage 5 防御性重构版）
捕获真实 Traceback 并按「异常类型 / 案发行号 / 报错原因」三步归档。

运行：python boundary_tests.py
"""

import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
ENGINES = [
    ("靶场", ROOT / "02_stage2_3_router_v1" / "mud_engine_v1_buggy.py"),
    ("合规", ROOT / "02_stage2_3_router_v1" / "mud_engine_v1.py"),
    ("加固", ROOT / "03_stage4_5_robust_engine" / "mud_engine_robust.py"),
]
MUST_NOT_CRASH = {"合规", "加固"}

CASES = [
    ("1 首尾空白与大小写", " /Go East ", "期望归一化后成功移动至春来茶馆"),
    ("2 动词与方向多空格", "/go   west", "split(' ', 1) 会切出带前导空格的方向"),
    ("3 缺失方向参数", "/go", "仅动词无参数，考察索引越界"),
    ("4 非法方向越界", "/go up", "方向不存在，考察 in 守卫"),
    ("5a 空回车", "", "清洗后为空串，考察空输入守卫"),
    ("5b 乱码/非指令", "/fly", "非法规格指令，考察兜底分支"),
]

EXC_RE = re.compile(r"^(\w*(?:Error|Exception)):\s*(.*)$", re.M)
PROMPT_RE = re.compile(r"^\[[^\]]{1,12}\] >\s*")
NOISE = ("可用指令：",)


def drive(script, lines):
    proc = subprocess.run([sys.executable, str(script)],
                          input="\n".join(lines) + "\n", capture_output=True,
                          text=True, encoding="utf-8", cwd=str(script.parent))
    return proc.returncode, (proc.stdout or "").strip(), (proc.stderr or "").strip()


def brief(text, limit=64):
    """去掉提示符前缀与横幅，只留引擎对本条输入的响应。"""
    kept = []
    for line in text.splitlines():
        line = line.strip()
        while PROMPT_RE.match(line):          # 空回车会连着打印两个提示符，逐个剥掉
            line = PROMPT_RE.sub("", line).strip()
        if not line or any(line.startswith(n) for n in NOISE):
            continue
        kept.append(line)
    return " ⏎ ".join(kept[:3])[:limit] if kept else "（无响应）"


def describe_run(rc, out, err):
    exc = EXC_RE.search(err)
    if exc:
        frames = re.findall(r'File "([^"]+)", line (\d+), in (\w+)', err)
        fname, lineno, func = frames[-1] if frames else ("?", "?", "?")
        verdict = f"{exc.group(1)}: {exc.group(2)}"
        detail = (f"    异常类型：{exc.group(1)}\n"
                  f"    案发行号：{Path(fname).name}:{lineno}（函数 {func}）\n"
                  f"    崩溃前输出：{brief(out)}")
        return verdict, detail
    if rc != 0:
        return f"非零退出 rc={rc}", f"    {brief(err)}"
    return "正常返回", f"    {brief(out)}"


print("=" * 78)
print("Stage 4/5 边界审查：缺陷靶场 vs 合规引擎 vs 加固引擎")
print("=" * 78)

crash_count = {label: 0 for label, _ in ENGINES}
for name, case, note in CASES:
    print(f"\n用例 {name}：输入 {repr(case)}   （{note}）")
    for label, script in ENGINES:
        rc, out, err = drive(script, [case, "/look"])
        verdict, detail = describe_run(rc, out, err)
        print(f"  [{label}] {verdict}")
        print(detail)
        if "Traceback" in err:
            crash_count[label] += 1

print("\n" + "=" * 78)
print("审查结论")
print("=" * 78)
for label, _ in ENGINES:
    total = len(CASES)
    if label in MUST_NOT_CRASH:
        ok = crash_count[label] == 0
        print(f"  [{'x' if ok else ' '}] {label}引擎：{total} 组边界用例异常 {crash_count[label]} 次"
              f"{'，全部平稳提示' if ok else '，未达验收'}")
    else:
        print(f"  [i] 靶场引擎：{total} 组用例崩溃 {crash_count[label]} 次（预期缺陷现场，用于取证）")
if any(crash_count[l] for l in MUST_NOT_CRASH):
    raise SystemExit(1)
print("  => 指令路由 = strip().lower() + split() 切参数 + len(parts) 检查 + 字典查表")
