# Week08 MUD 心跳 · Stage 1 while True 主循环

实验者：龙勤涛（7904126014）　就绪状态：任务一至六 + 进阶一（`MAX_TURNS` 回合上限 + `test_chaos_suite.py` 7 步自动化回归）全部完成并通过验收（2026-11-02）；任务六为过程复盘·三道实验思考题报告

## 目录

| 文件 | 作用 |
| --- | --- |
| `01_stage1_while_loop/mud_loop_buggy.py` | 课程靶场（自建）：初始化与开场白被整块误缩进进 `while True`，复现"位置重置 + 重复打印" |
| `01_stage1_while_loop/mud_loop_v1.py` | ROCA 生成的持续交互主循环：循环外初始化 + 按需打印 + `/quit` 安全退出 |
| `01_stage1_while_loop/mud_loop_v2.py` | 任务二增量版：三处 `for` 遍历地面物品 / 出口字典 / `enumerate` 行囊，新增 `/bag` |
| `01_stage1_while_loop/check_while_loop.py` | 任务一验收自动化校验：起真进程喂 stdin，5 项断言，支持负向对照 |
| `01_stage1_while_loop/check_for_loops.py` | 任务二验收自动化校验：5 项断言（含空容器边界）；期望值从被测引擎的 `world` 现算，故 v2 与任务五终稿（3 出口广场）共用同一套断言 |
| `02_stage3_chaos_targets/mud_chaos_buggy.py` | 任务三靶场（自建）：缺陷 A 数据层 `KeyError: 'market'`（崩溃点实测 line 64）+ 缺陷 B `/buy_tea` 扣款符号写反 |
| `02_stage3_chaos_targets/mud_chaos_buggy_debug.py` | 同一缺陷 B，在扣款语句前后插 `[DEBUG]` 打印，把"预期 35 vs 实测 65"量化出来 |
| `annotated_prompts.md` | 阶段三记录表：Traceback 从下往上三步定位 + `[DEBUG]` 变量偏差取证 + 三类缺陷取证手段对照；**末尾为任务六「第 8 周实践报告」三道实验思考题 + 提示词与取证台账** |
| `03_stage4_5_defensive_engine/mre_keyerror.py` | 任务四最小复现案例（实测 11 行）：剥掉主循环/`/bag`/`/buy_tea`，只留两次连续取键，稳定抛 `KeyError: 'market'` |
| `03_stage4_5_defensive_engine/mre_keyerror_fix_a.py` | 方案 A：仅修正字典错误键值（`market` -> `chaguan`），代码零改动 |
| `03_stage4_5_defensive_engine/mre_keyerror_fix_b.py` | 方案 B：防御式编程，故意保留坏数据 + `if target_id not in world` 边界检查 |
| `03_stage4_5_defensive_engine/audit_world_exits.py` | 启动期地图完整性自检：`for` 双层遍历出口，报出"房间/方向/悬空代号"三元组 |
| `03_stage4_5_defensive_engine/mud_engine_defensive.py` | **任务五终稿**：方案 B 边界检查 + `/buy_tea` 扣款修复合入完整主程序，含北向未开放测试出口 |
| `03_stage4_5_defensive_engine/test_regression_defensive.py` | 任务五三项回归测试（+钱不够/启动自检 2 项），可切换被测引擎做负向对照 |
| `03_stage4_5_defensive_engine/test_chaos_suite.py` | 进阶一自动化套件：7 步多轮指令序列按序匹配 + `MAX_TURNS` 循环保护实测（含未加固对照组），输出 PASS 通过率 |

## 运行

```bash
python mud_loop_buggy.py      # 缺陷复现：/go east 到茶馆后下一轮被打回广场；/look 当轮场景打两遍
python mud_loop_v1.py         # 交互式游玩：/look  /go <方向>  /quit
python mud_loop_v2.py         # 交互式游玩：/look  /bag  /go <方向>  /quit（自动列地面物品与出口）
python check_while_loop.py    # 任务一正向验收：5/5 全部通过 [x]，exit 0
python check_for_loops.py     # 任务二正向验收：5/5 全部通过 [x]，exit 0

MUD_LOOP_ENGINE=mud_loop_buggy.py python check_while_loop.py   # 负向对照：3/5 不通过，exit 1
MUD_LOOP_ENGINE=mud_loop_v1.py python check_for_loops.py       # 负向对照：5/5 不通过，exit 1
MUD_LOOP_ENGINE=mud_loop_v2.py python check_while_loop.py      # 兼容性回归：任务一套件对 v2 仍 5/5 通过

# 任务三：两类典型缺陷复现（02_stage3_chaos_targets/）
printf '/go east\n/quit\n'   | python mud_chaos_buggy.py        # 缺陷 A：KeyError 'market'，红色 Traceback，exit 1
printf '/buy_tea\n/quit\n'   | python mud_chaos_buggy.py        # 缺陷 B：不报错，50 文变 65 文，exit 0
printf '/buy_tea\n/quit\n'   | python mud_chaos_buggy_debug.py  # 缺陷 B 取证：[DEBUG] 实测 65 vs 预期 35，偏差 +30

# 任务四：MRE 与两种修复方案（03_stage4_5_defensive_engine/）
python mre_keyerror.py         # 11 行最小复现：KeyError 'market'，与原程序同类异常，exit 1
python mre_keyerror_fix_a.py   # 方案 A 数据修正后：抵达：春来茶馆，exit 0
python mre_keyerror_fix_b.py   # 方案 B 坏数据仍在：提示黑巷 + 退回原处，exit 0（不崩）
python audit_world_exits.py    # 启动自检：坏图 1 处悬空 -> 拒绝开局；好图 0 处 -> 放行
python mud_engine_defensive.py # 任务五终稿：/look /bag /buy_tea /go /quit（含未开放北向出口）
python test_regression_defensive.py            # 三项回归 + 2 项边界：5/5 通过，exit 0

# 同一套回归断言切换被测引擎即成负向对照
MUD_LOOP_ENGINE=../02_stage3_chaos_targets/mud_chaos_buggy.py python test_regression_defensive.py   # 5/5 不通过，exit 1
MUD_LOOP_ENGINE=../03_stage4_5_defensive_engine/mud_engine_defensive.py python check_while_loop.py   # 任务一套件对终稿 5/5
MUD_LOOP_ENGINE=../03_stage4_5_defensive_engine/mud_engine_defensive.py python check_for_loops.py    # 任务二套件对终稿 5/5

# 进阶一：MAX_TURNS 循环保护 + 7 步自动化回归
python test_chaos_suite.py       # 7 步交互 + 循环保护：PASS 11/11（100%），exit 0
MUD_MAX_TURNS=3 python mud_engine_defensive.py    # 走满 3 回合自动收束（打印系统提示）
MUD_LOOP_ENGINE=../02_stage3_chaos_targets/mud_chaos_buggy.py python test_chaos_suite.py   # 负向对照：3/11（27%），exit 1
```

Windows 控制台中文乱码先 `set PYTHONIOENCODING=utf-8`。

## 两处反常现象与人工审查结论

| 现象 | 成因（缺陷写法） | 修复 |
| --- | --- | --- |
| 已走到春来茶馆，下一轮 `/look` 却回到扬州中心广场 | `player_location = "guangchang"` 被缩进进循环体，每轮开头重新执行 | 位置状态 `player` 字典与 `world` 一并提到 `while True` 上方，循环内只读写 `player["location"]` |
| `/look` 一次输出两遍场景描述 | 循环顶部无条件 `print(current_room)`，与下方 `/look` 分支叠加 | 开场白移到循环外只打印一次；循环内仅在 `/look` 或 `/go` 移动成功时按需打印 |

关键概念对照（状态为何会"丢"）：

| 写法 | 每轮循环发生什么 | 结果 |
| --- | --- | --- |
| 赋值语句在循环**内** | 初始化被反复执行，上一轮 `/go` 写入的值当场被覆盖 | 状态重置，玩家永远走不出广场 |
| 赋值语句在循环**外** | 只执行一次，循环内是"读—改—写"同一对象 | 状态跨轮累积，位置/血量等才可持久 |
| 打印语句在循环**内**且无条件 | 每轮先打一遍，指令分支再打一遍 | 重复输出；应改为"响应指令才打印" |

## 任务一 ROCA 提示词（生成 `mud_loop_v1.py` 原文）

```
【Role · 角色设定】Python 程序开发助手。
【Objective · 核心目标】将单回合 MUD 脚本修改为支持多轮持续交互的主循环脚本 mud_loop_v1.py。
【Constraint · 边界约束】
1. 循环外初始化：world 与位置 player 字典（含初始 "guangchang"）必须定义在 while True 循环外部上方，严禁缩进至循环内；
2. 初始打印与按需响应：在进入 while True 前仅打印一次初始房间开场白；循环内仅在输入 /look 或 /go 移动成功时打印房间描述；
3. 安全退出分支（防死循环）：当玩家输入 /quit 时，打印告别语并立即执行 break 终止循环。
【Acceptance · 验收清单】
- [ ] 输入 /go east 抵达春来茶馆后，下一轮输入 /look 是否仍留在茶馆（无位置重置）；
- [ ] 输入 /look 是否只打印一遍场景；输入 /quit 能否正常退出。
```

## 任务二 ROCA 增量提示词（生成 `mud_loop_v2.py` 原文）

```
【Role · 角色设定】Python 程序开发助手。
【Objective · 核心目标】在 mud_loop_v1.py 基础上增量扩展 mud_loop_v2.py，运用 for 循环遍历打印房间地面物品、可用出口与玩家行囊。
【Constraint · 兼容性与遍历约束】
1. 兼容性约束 (Non-Breaking)：保持现有 while True 主循环结构、循环外状态初始化、/go 长度检查与 /quit 退出机制不变；
2. 遍历地面物品与出口：在房间信息打印处，用 for item in room["items"] 打印地面物品；
   用 for d, tid in room["exits"].items() 遍历出口字典并查出 world[tid]["name"] 打印中文导航提示；
3. 带编号遍历行囊 (/bag)：新增 /bag 分支，用 for idx, item in enumerate(player["inventory"], 1) 打印带序号背包清单。
【Acceptance · 验收清单】
- [ ] 输入 /look 或移动后，能否自动列出当前房间所有物品与出口中文名；
- [ ] 输入 /bag 能否从 [1] 开始带编号打印行囊物品。
```

## 三种 for 遍历写法（`mud_loop_v2.py` 三处对照）

| 写法 | 容器类型 | 代码 | 取到什么 |
| --- | --- | --- | --- |
| ① 遍历列表元素 | `list` | `for item in room["items"]:` | 每轮直接拿到元素本身，无需下标 |
| ② 遍历字典键值对 | `dict` | `for d, tid in room["exits"].items():` | 同时拿到键（方向）与值（目标房间键），再 `world[tid]["name"]` 查中文名 |
| ③ 带序号枚举 | `enumerate` | `for idx, item in enumerate(player["inventory"], 1):` | 序号从 **1** 起（默认 0），打印 `[1] 金创药` |

## 追问记录

**i. 为什么遍历房间出口和背包物品时用 `for` 而不是 `while`？**

因为这两处的**遍历次数由容器自身决定，不是由外部事件决定**。写成 `while` 就得自己供养"下标三件套"（起点 / 终止条件 / 推进语句），三件套里任何一件写错都是一次真实故障，我逐条实测过：

| `while` 版要手工维护的东西 | 写错的方式 | 实测因果 |
| --- | --- | --- |
| 推进语句 `i += 1` | 漏写，或被误缩进进 `if` 分支 | **死循环**：3 s 未结束被强杀；早前同型脚本输出冲到 5 GB 才被截断 |
| 终止条件 `i < len(keys)` | 写成 `i <= len(keys)` | 末元素后多走一步：`IndexError: list index out of range`，returncode 1 |
| 起点 `i = 0` | 放进"逐条消费"的外层循环里 | 每轮从头再遍历一遍，同一批物品反复打印（`mud_loop_buggy.py` 的重复打印正是这一族） |
| 出口字典没有下标 | 只能先 `keys = list(room["exits"])` 再按下标取键 | 多绕一层，`d -> tid -> world[tid]` 的配对极易写反 |

`for` 走的是迭代器协议：一行 `for d, tid in room["exits"].items():` 同时完成"取值 + 解包 + 推进 + 收尾"，三件套不再由我负责，空容器也天然零次进入（`check_for_loops.py` 验收项 5 实测：`items`、`inventory` 清空后 `for` 一行不打、不报错）。

顺带把"守卫不能删"也实测了：把 v2 的 `/go` 分支去掉 `len(parts) < 2` 与 `parts[1] in room["exits"]` 两道检查后，裸 `/go` 直接 `IndexError: list index out of range`，`/go up` 直接 `KeyError: 'up'`，returncode 1。

所以 `while True:` 只留在它真正合适的位置——**读 `input()`，循环次数由玩家的 `/quit` 决定**：终止靠外部事件而非靠数数，这正是 `while` 的主场。

**ii. 多轮增量提问时，如果不写"兼容性约束"，AI 容易出现什么问题？**

| 没有 Non-Breaking 约束时的典型回归 | 表现 | 本仓库的取证方式 |
| --- | --- | --- |
| 整段重写而非增量：把 `world` / `player` 重新挪进循环 | 任务一刚修好的"位置重置"复活 | `MUD_LOOP_ENGINE=<新文件> python check_while_loop.py` 会立刻从 5/5 掉到 FAIL |
| 顺手"优化"掉守卫：删掉 `len(parts) < 2` 或 `in room["exits"]` | 裸 `/go` 触发 `IndexError`，`/go up` 触发 `KeyError` | 喂 `/dance`、`/go`、`/go north` 应只提示不崩 |
| 丢掉 `/quit` 分支或把 `break` 换成 `exit()` | 无法告别退出，管道输入提前 EOF | 任务一验收项 3（exit 0 + 告别语） |
| 把按需打印改成循环顶部无条件打印 | `/look` 又开始重复刷屏 | 任务一验收项 2（场景行计数） |
| 改了函数/字段名（`describe` -> `print_room`、`exits` -> `dirs`） | 已通过的旧校验与后续模块 import 全部断裂 | 校验脚本与被测文件名解耦（`MUD_LOOP_ENGINE`），改名即失败可见 |
| 只演示新功能、旧功能不验证 | 看起来"任务二完成"，实际破坏任务一 | 同一套断言对 v1/v2 各跑一遍：v2 兼容通过，v1 对新断言 5/5 FAIL |

结论：增量提示词里的兼容性约束等价于一份**回归测试约定**。人类评审记不住"哪些不许动"，但我保留了 `check_while_loop.py` 这套断言，`MUD_LOOP_ENGINE=mud_loop_v2.py` 一跑就能证明约束被守住了（实测 5/5 通过，exit 0）。

## 任务三：两类典型缺陷（结论摘要，完整取证见 `annotated_prompts.md`）

| 缺陷 | 现象 | 从输出里读到的第一手信息 | 定位手段 |
| --- | --- | --- | --- |
| A 显性运行期异常 | 输入 `/go east` 后程序直接终止 | `KeyError: 'market'` @ `line 64, in <module>`，语句 `new_room = world[target_id]` | **从下往上**读 Traceback：① 异常类型 ② 报错行与栈帧 ③ 顺变量追上游数据（第 22 行 `exits` 配了未定义的房间代号） |
| B 静默逻辑错误 | 控制台毫无报错，`exit 0` | 文案里的"当前铜钱 65 文"是**唯一线索** | 在可疑语句前后插 `print()`，**先把预期值算出来存住**再并排打印：实测 65 vs 预期 35，偏差恒 `+30 = 2×price` → 指向 `+=` 应为 `-=` |

两条经验：`in` 守卫只护得住"方向键不存在"，护不住"出口指向的房间里没有"（数据层缺陷需启动时做地图完整性自检）；只打印一个变量值仍要靠心算判对错，把 `expected` 和 `偏差` 一起打出来，缺陷方向当场可读。

## 任务四：最小复现案例（MRE）与两套修复方案（完整分析见 `annotated_prompts.md` 阶段四记录表）

68 行的靶场剪到 11 行：删掉欢迎词、`while True` 交互、`/look` `/bag` `/buy_tea` 与无关房间，**只保留两次连续取键**——`world[player_location]["exits"][direction]` 成功、`world[target_id]` 失败，这条分界线就是定位信息，合并成一行就查不出崩在哪一步。

| 方案 | 改动 | 实测 | 残留风险 |
| --- | --- | --- | --- |
| A 仅修数据 | `"east": "market"` -> `"chaguan"`，代码零改动 | `抵达：春来茶馆`，`exit 0` | 下次再配错（新增房间、改名只改一处）仍在运行时炸 |
| B 边界检查 | 故意保留坏数据，取键前 `if target_id not in world` | `向 [east] 前行通向一处未开市的黑巷（内部代号 market），你退回了原处。`，`exit 0`；喂好数据时 `抵达：春来茶馆`（防御层不吞正常路径） | 防御分支静默返回会让配置错隐身，需配自检/日志 |
| 附：启动自检 | `audit_world_exits.py` 双层 `for` 遍历出口 | 坏图 `悬空出口 1 处 -> 拒绝开局 [('guangchang', 'east', 'market')]`；好图 `0 处 -> 放行` | —— |

选型结论：A 治"这一次的数据笔误"，立刻做；B 治"这类配置错误永远不该崩"，交付版必须留；自检负责在开局前把缺陷**指名道姓**——三者是不同层次，不是三选一。

## 任务五：方案 B 合入终稿 + 三项回归

领航员决策：**采纳方案 B**，同时把 `/buy_tea` 的算术缺陷一并修掉，产出 `mud_engine_defensive.py`（广场东向恢复 `chaguan`，保留北向测试出口 `market_unbuilt` 且故意不定义，作为常驻回归用例）。

```
> /go east      你抵达了【春来茶馆】！                （回归 i）
> /buy_tea      你付了 15 文，铜钱 50 -> 35，行囊多了一碗碧螺春。   （回归 ii）
> /go west      你抵达了【扬州中心广场】！
> /go north     [系统提示] 前方的【market_unbuilt】区域尚未开放，请留步！   （回归 iii，不崩、位置不变）
> /look         【扬州中心广场】…                    （仍在广场，状态未被破坏）
```

| 回归项 | 断言 | 终稿 | 阶段三靶场（负向对照） |
| --- | --- | --- | --- |
| i `/go east` 抵达茶馆 | 抵达行 + `exit 0` + stderr 无 Traceback | 通过 | FAIL：`KeyError: 'market'`，`exit 1` |
| ii 茶馆 `/buy_tea` | 账目正则 `铜钱 50 -> 35` | 通过 | FAIL：无扣款行（写成 `+=` 会变 65），`exit 1` |
| iii `/go north` 未开放 | 提示行 + `exit 0` + 被拦后 `/look` 仍在广场 | 通过 | FAIL：无未开放提示（该图北向本就通茶馆） |
| 边界 连买 4 碗 | 扣款序列 35/20/5，第 4 次"只剩 5 文"被拦、不为负 | 通过 | FAIL |
| 启动自检 | `[自检]` 列出 `market_unbuilt` 但**不阻断开局** | 通过 | FAIL |

`test_regression_defensive.py` 合计 5/5 通过（exit 0），同一套断言指向 `mud_chaos_buggy.py` 时 5/5 FAIL（exit 1）。任务一/二两套旧套件也各自对终稿复跑 5/5（`check_for_loops.py` 已改为从被测引擎现算期望值，否则终稿广场多出的第 3 条出口会被误判成回归失败）。

完整排障流程（五个任务串起来）：**读报错定位行号 →（阶段三）** 提取 MRE 剥离无关模块 →（阶段四）分析根因、对比 A/B 方案 → 添加边界检查 →（阶段五）运行回归测试验证 —— 收尾判据不是"看起来修好了"，而是**同一套断言在缺陷版上必须红、在终稿上必须绿**。

## 进阶一：`MAX_TURNS` 回合上限与 `test_chaos_suite.py` 自动化回归

### 循环安全保护：第二道保险

`/quit` 触发的 `break` 只防得住"玩家正常离开"；防不住"程序自己绕进不出来"（守卫漏写、`input` 被喂空、逻辑分支永不命中 `/quit`）。所以主循环再加一层与玩家无关的上限：

```python
turn_count = 0
finished_by_quit = False
while turn_count < MAX_TURNS:              # 保险二：最大回合数上限，防异常死循环
    turn_count += 1
    command = input(f"\n[第 {turn_count} 回合] 少侠请下令 > ").strip().lower()
    ...
    if command == "/quit":
        finished_by_quit = True
        break                              # 保险一：人工退出
if not finished_by_quit and turn_count >= MAX_TURNS:
    print(f"\n  [系统提示] 已走满 {MAX_TURNS} 回合上限，为防异常死循环，本次江湖行到此收束。后会有期！")
```

| 保险 | 由谁触发 | 防的是什么 | 实测 |
| --- | --- | --- | --- |
| `/quit` + `break` | 玩家意愿 | 正常收尾，不让程序挂在输入上 | 步骤 7 命中"江湖再见"，`exit 0` |
| `while turn_count < MAX_TURNS` | 与玩家无关的硬上界 | 逻辑缺陷导致的无限循环、自动化脚本喂入未知指令洪流 | 上限压到 3、喂 5 条 `/look`：只消费 3 条（场景行 1 开场 + 3 = 4），第 4 回合未出现，收束提示打印，`exit 0` |
| `EOFError: break` | 管道/重定向输入耗尽 | 自动化跑测时的 `EOFError` 崩溃 | 各套件喂完指令后均 `exit 0` |

`MAX_TURNS` 默认 100，可用环境变量 `MUD_MAX_TURNS` 压低——**不是为了改行为，是为了让"到点收束"这件事能在 1 秒内被断言**（上限 100 就得喂 101 条指令才能测到）。加了这层之后，任务一/二/五的三套旧套件对终稿仍各自 5/5 通过（Non-Breaking 再次成立）。

### `test_chaos_suite.py`：7 步指令序列自动化回归

ROCA 提示词（原文）：

```
请编写自动化测试脚本 test_chaos_suite.py，使用 7 条测试指令序列，用 for 循环依次向 mud_engine_defensive.py 传入
["/look", "/bag", "/go north (测试未开放房间提示)", "/go east", "/buy_tea (验证 50->35 文)", "/go west", "/quit"]，
自动校验每一步返回文本是否符合预期并统计 PASS 通过率。
```

实现上有一条关键取舍：7 条指令喂进**同一次进程会话**，再用游标 `out.find(expected, cursor)` 顺序匹配。这样断言的不只是"文本出现过"，而是"第 N 步的文本出现在第 N-1 步之后"——位置状态与账目迁移都跑不掉。

| # | 指令 | 期望文本 | 校验的能力 |
| --- | --- | --- | --- |
| 1 | `/look` | `【扬州中心广场】` | 场景描述与 for 遍历 |
| 2 | `/bag` | `[1] 金创药` | `enumerate(..., 1)` 从 1 起编号 |
| 3 | `/go north` | `尚未开放，请留步` | 方案 B 边界检查吞掉未定义房间，不抛 `KeyError` |
| 4 | `/go east` | `你抵达了【春来茶馆】` | 合法出口照常放行（防御层不挡正路） |
| 5 | `/buy_tea` | `铜钱 50 -> 35` | 扣款方向（缺陷写法此处是 65） |
| 6 | `/go west` | `你抵达了【扬州中心广场】` | 多轮状态可回迁，位置未被重置 |
| 7 | `/quit` | `江湖再见` | 人工退出分支 |

实测结果：7 步全绿 + `无 Traceback 且 exit 0` + `回合编号第 1..7 回合齐全` + `上限收束保护` + `未加固对照组(v2)确实走满 5 回合` = **PASS 11/11（100%）**，`exit 0`；同一套件指向阶段三靶场时 **3/11（27%）**，`exit 1`。

对照组那条不是装饰：把 `MUD_MAX_TURNS=3` 同样喂给没有上限的 `mud_loop_v2.py`，它确实消费掉 5 条 `/look`（场景行 6）且无收束提示——证明"到点收束"是真行为，不是断言恒真。
