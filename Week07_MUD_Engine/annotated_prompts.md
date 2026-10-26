# annotated_prompts.md — 提示词对照记录与边界审查归档

实验者：龙勤涛（7904126014）　日期：2026-10-26　被测：`02_stage2_3_router_v1/`、`03_stage4_5_robust_engine/`

## 一、5 类非常规输入测试对比记录表

复现命令：`python boundary_tests.py`（6 组用例 × 3 个引擎，各自独立子进程，状态互不污染；合规与加固两版异常计数均为 0，exit 0）

| # | 边界用例 | 输入（`repr`） | 缺陷靶场 `mud_engine_v1_buggy.py` 实测 | 合规引擎 `mud_engine_v1.py` 实测 | 加固引擎 `mud_engine_robust.py` 实测 | 生效的防线 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 首尾空白 + 大小写 | `' /Go East '` | 打印「未知指令。」，移动指令**静默丢失**（无报错，最难发现） | `你抵达了【春来茶馆】。` | `你抵达了【春来茶馆】。` | 清洗层 `raw.strip().lower()` |
| 2 | 动词与方向多空格 | `'/go   west'` | `KeyError: '  west'`（`split(" ", 1)[1]` 切出带前导空格的方向） | `你抵达了【江南武馆】。` | `你抵达了【江南武馆】。` | `command.split()` 自动合并连续空格 |
| 3 | 缺失方向参数 | `'/go'` | **崩溃**：`IndexError: list index out of range` @ `:49`（`dispatch_command_v1`） | `要向哪里去？用法：/go <方向>，例如 /go east` | `少侠欲往何方？请在 /go 后指明方向（例如：/go east）！` | `len(parts) < 2` 前置长度守卫 |
| 4 | 非法方向越界 | `'/go up'` | **崩溃**：`KeyError: 'up'` @ `:50` | `无法向 [up] 前行！前面似有石墙受阻。此路唯有：[east]、[west]` | 同合规版（含可走方向列表） | `if direction in room["exits"]` 守卫 |
| 5a | 空回车 | `''` | 打印「未知指令。」（噪声提示，语义错） | 静默跳过，重新给房间描述，不改状态 | `（四下无言）输入 /look 看看四周，或 /help 查看指令。` | 空输入守卫改为**主动引导** |
| 5b | 乱码/越界指令 | `'/fly'` | 「未知指令。」无引导 | `未知指令 [/fly]。可用指令：…` | `未知指令 [/fly]。可用指令：…` | `else` 兜底 + BANNER 引导 |

**靶场缺陷 2 与缺陷 3 是同一条语句的两种崩法**：`split(" ", 1)` 既可能切出脏值（用例 2/4 → KeyError），也可能根本切不出第二个元素（用例 3 → IndexError）。修复不是补 `try/except`，而是换成对空白不敏感的 `split()` 再判长度。

## 二、Traceback 现场与三步定位

真实回溯栈（用例 3，`python mud_engine_v1_buggy.py` 输入 `/go`）：

```
Traceback (most recent call last):
  File "...mud_engine_v1_buggy.py", line 69, in <module>
    main()
  File "...mud_engine_v1_buggy.py", line 65, in main
    dispatch_command_v1(raw)          # 缺陷 1：raw 未 strip().lower()
  File "...mud_engine_v1_buggy.py", line 49, in dispatch_command_v1
    direction = command.split(" ", 1)[1]
                ~~~~~~~~~~~~~~~~~~~~~^^^
IndexError: list index out of range
```

| 步骤 | 读法 | 本例结论 |
| --- | --- | --- |
| i 异常类型 | 只看**最后一行**冒号左侧 | `IndexError` = 序列索引越界，不是逻辑写错而是取值越界 |
| ii 案发地点 | 从栈**由下往上**找自己写的那帧（跳过 stdlib） | `line 49, in dispatch_command_v1`，代码行 `direction = command.split(" ", 1)[1]` |
| iii 成因链 | 把该行拆开，问「谁是长度 1」 | `"/go".split(" ", 1)` → `['/go']`，长度为 1；强读 `[1]` 越界。根因是**默认了 "/go" 之后必有空格与方向** |

补充教训：栈里 `<module>` → `main` → `dispatch_command_v1` 三帧说明崩溃发生在被调用函数内部，而驱动它的是主循环里那句未清洗的 `dispatch_command_v1(raw)`；报错行号（49）指向的永远是**症状**（读到越界索引），**病因**在上游的分支条件（`startswith("/go")` 太宽，只验了前缀没验参数）。所以修 bug 要在报错行的**上一行逻辑**下手，而不是在 49 行包一层 `try/except`。

## 三、提示词对照：阳光路径偏见（Happy Path Bias）

| 维度 | A 版提示词（Stage 2 原始 ROCA） | B 版提示词（本轮补的边界约束） |
| --- | --- | --- |
| Constraint 措辞 | 「对 input() 读取的字符串调用 `.strip().lower()`」「用 `if direction in room["exits"]` 检查出口」 | 增补：**动词后可能没有参数、可能有连续多个空格、可能是空回车或非指令串**；要求「取参数前先判 `len(parts)`，切分一律用无参 `split()`」 |
| Acceptance 措辞 | 「`/Go East` 能否归一化移动」「`/go up` 能否被拦截」 | 增补：**列出 5 类边界输入为验收用例，要求合规引擎在全部用例下 `Traceback` 计数为 0**，并把「空回车不得报未知指令」写成硬条款 |
| 生成结果 | 代码只保证**正常输入**跑通：`split(" ", 1)[1]` + 直接索引，用例 3/4 直接崩溃；用例 1 因未清洗而静默失效 | 同一骨架补上清洗层、`len()` 校验、`in` 守卫后，6 组用例全部给出玩家可读反馈，0 异常 |
| 偏差表现 | 模型把「用户一定按规范输入」当作隐含前提写进代码，且**不报错的错**（用例 1 指令丢失）比崩溃更难发现 | 显式把「输入不可信」写进 Constraint，模型才会生成守卫分支 |

**可复用规则**：ROCA 的 Constraint 里凡是「解析用户输入」的目标，验收清单必须自带一组**畸形输入用例**（缺参、多空白、脏大小写、空行、非指令）；否则 AI 交付的是 happy path demo，不是引擎。

## 四、Stage 5 防御性重构：四道守卫与回归矩阵

加固版 `03_stage4_5_robust_engine/mud_engine_robust.py` 把移动分支拆成可核对的四步：

```python
command = raw.strip().lower()          # [守卫 1] 清洗层：空白与大小写
if not command:                        #          空输入不进任何分支，直接回引导
    return "  （四下无言）输入 /look 看看四周，或 /help 查看指令。"
parts = command.split()                # [守卫 2] 切分层：无参 split() 合并任意连续空格
verb = parts[0]
...
elif verb == "/go":
    if len(parts) < 2:                 # [守卫 3] 长度守卫：读 parts[1] 之前先验它存在
        return "  少侠欲往何方？请在 /go 后指明方向（例如：/go east）！"
    direction = parts[1]
    if direction in room["exits"]:     # [守卫 4] 键成员守卫：非法方向不再 KeyError
        player["location"] = room["exits"][direction]
```

一处顺带的结构升级：路由改为按 `parts[0]`（动词 token）精确比对，而不是 `startswith("/go")`。Stage 3 记录的 `/help` 吞噬 `/help_scholar` 的前缀陷阱因此从根上消失——动词之间不可能互为前缀，新增指令也不用再排顺序。

**回归矩阵**（校验脚本用 `MUD_ENGINE` 环境变量切换被测引擎，同一套断言跑两版）：

| 验收套件 | `mud_engine_v1` | `mud_engine_robust` |
| --- | --- | --- |
| `check_world_data.py`（Stage 1，7 项） | exit 0 全通过 | exit 0 全通过 |
| `check_router.py`（Stage 2，13 项） | exit 0 全通过 | exit 0 全通过 |
| `check_rules.py`（Stage 3，24 项） | exit 0 全通过 | exit 0 全通过 |
| `boundary_tests.py`（Stage 4/5，6 组用例） | 异常 0 | 异常 0 |

复现：

```bash
MUD_ENGINE=mud_engine_v1      python check_router.py && MUD_ENGINE=mud_engine_v1      python check_rules.py
MUD_ENGINE=mud_engine_robust  python check_router.py && MUD_ENGINE=mud_engine_robust  python check_rules.py
python ../04_stage4_boundary_review/boundary_tests.py
```

加固版与合规版的**唯一行为差异**是空回车：合规版静默跳过（只重画房间），加固版主动给出下一步指引。两者都不改状态、都不抛异常——这条差异是提示词里「直接返回引导提示」的明确要求，不是回归缺陷。

## 五、进阶：一次性人工测试 → 自动化回归测试

`03_stage4_5_robust_engine/test_boundary_audit.py` 把 5 类共 **9 条**用例固化为 `CASES` 元组表：`(类别, 输入, 起始地点, 必含关键词组, 预期落点)`，直接 `import mud_engine_robust` 调 `dispatch()`，不再起子进程。

| 设计点 | 做法 | 为什么 |
| --- | --- | --- |
| 进程内直调 | 不用 `subprocess`，9 条用例走同一解释器 | 耗时从「子进程冷启动 ×9」降到 **0.1 ms**，重构时可以随手反复跑 |
| 关键词断言 | `missing = [k for k in keywords if k not in text]` | 不锁死整段文案，改措辞不必改测试；又能证明确实走到了目标分支 |
| 落点断言 | 除文案外还比 `player["location"] == expect_room` | 防「嘴上说受阻、脚下却走了一步」——拦截类分支必须**状态不变** |
| 状态隔离 | 每条用例前 `setup()` 复位 location/health/gold/inventory | 用例顺序无关，避免前一格的移动污染后一格的判定 |
| 异常兜住 | `try...except Exception` 捕获后计入 FAIL 并打印异常类型 | 审计脚本自身绝不能因被测崩溃而中断，否则只看到半张表 |
| 兜住数单列 | 汇总里把「被 try 兜住的异常」与「语义 FAIL」分开计数 | 兜住 ≠ 通过；数字非 0 就说明守卫失守，只是进程没死 |

实测（`python test_boundary_audit.py`）：

```
用例总数：9    PASS：9    FAIL：0
通过率：100.0%    耗时：0.1 ms（进程内直调，零子进程开销）
被 try 兜住的异常：0
[x] 全部 PASS，零异常崩溃          exit 0
```

负向自检（把 `dispatch` 换成 Stage 4 的缺陷写法 `split(" ", 1)[1]` 再跑）证明这套断言真的有效，而不是恒真：

```
用例总数：9    PASS：0    FAIL：9
被 try 兜住的异常：3          [ ] 未通过：存在崩溃或语义偏差用例    exit 1
```

## 六、进阶二：扩建第 4 房间，验证「只改字典不改分支」

**唯一的改动是数据**（`01_stage1_world_model/world_data.py`）：广场补一条 `north` 出口 + 新增 `shuyuan` 房间定义。

```python
"guangchang": {
    "name": "扬州中心广场",
    "description": "青石铺地，人来人往，告示栏上贴着武林帖。向东可去茶馆，向西可去武馆，北面通往白鹿洞书院。",
    "exits": {"east": "chaguan", "west": "wuguan", "north": "shuyuan"},
},
"shuyuan": {
    "name": "白鹿洞书院",
    "description": "翠竹掩映着古朴的藏书阁，案头摆放着先贤手稿。向南可返回中心广场。",
    "exits": {"south": "guangchang"},
},
```

**零逻辑改动检验**（改数据前后对两个引擎取 sha256 比对）：

```
$ sha256sum -c engine_before.txt
02_stage2_3_router_v1/mud_engine_v1.py: OK
03_stage4_5_robust_engine/mud_engine_robust.py: OK
```

`dispatch_command_robust()` / `handle()` 的 if-elif-else 一行未动，`check_router.py` 另加了一条源码级断言：引擎源文件里**不出现** `shuyuan`、`白鹿洞` 字样——新房间确实只活在数据里。

**`/go north` 通行验证记录**（同一句输入分别喂给两个引擎）：

```
02_stage2_3_router_v1/mud_engine_v1.py              你抵达了【白鹿洞书院】
03_stage4_5_robust_engine/mud_engine_robust.py      你抵达了【白鹿洞书院】
```

`/look` 在广场自动列出 **3** 个出口（含「向北 [north] -> 白鹿洞书院」），无需改任何打印代码；`/go south` 从书院自动返回广场，Stage 1 的连通性校验把 `north/south` 加进 `REQUIRED_ROOMS` 后「双向出口闭环连通」仍为 True。

**回归与加分项**：

| 套件 | 结果 |
| --- | --- |
| `check_world_data.py`（4 房间拓扑 + 类型） | rc=0 全通过 |
| `check_router.py` × `mud_engine_v1` / `mud_engine_robust`（各 18 项，含新增 5 项新房间断言） | 双引擎 rc=0 全通过 |
| `check_rules.py` × 双引擎（24 项） | 双引擎 rc=0 全通过 |
| `test_boundary_audit.py`（**9 项自动化边界审计**） | 9/9 PASS，通过率 100%，耗时 0.1 ms，rc=0 |
| `boundary_tests.py`（6 组 × 3 引擎） | rc=0，加固/合规异常 0 次 |

审计用例 7 顺手改到了新房间上：`/go north` 在广场已合法，于是把「非法方向」这一类用例的起点移到书院（书院只开 `south`），既保住 9 项计数，又让新房间参与边界断言。

**一句话结论**：查表把「地图长什么样」变成数据，所以加房间=改 dict；反之 elif 硬编码要新增 N×方向 个分支，`sha256` 必然变化——这条哈希比对就是两种写法最直观的差别。

---

## 七、ROCA 提示词批注（逐条：AI 首轮产出 → 人工批注与追问）

| # | ROCA 提示词要点 | AI 首轮产出 | 人工批注 / 追问 | 结论 |
| --- | --- | --- | --- | --- |
| 1 | Stage 1：world 三连通 + player 七字段，Constraint 写明「数值必须原生 int，严禁误加双引号」 | 一次通过，双向出口闭环 | 追问「`type()` 怎么当场证给你看？」→ 补 `check_world_data.py` 用 `type(...) is int` 硬断言，并加**负向对照**（把 health 改回 str 必须 exit 1） | 类型约束只有配了反向用例才算被验证 |
| 2 | Stage 2：清洗层 + if-elif-else 分流 + `if direction in room["exits"]` | 结构合规，但用 `command.split(" ", 1)[1]` 取方向 | 追问「只敲 `/go` 回车会怎样」→ 靶场复现 `IndexError` @ line 49；再追问「`/go   west` 呢」→ `KeyError: '  west'` | AI 的 Constraint 只抄了「用 in 守卫」，**取参数那一步根本没进它的思考范围** |
| 3 | Stage 3：`/heal` 先验道具与满血；`/help_scholar` 验地点与盘缠 | 骨架正确，但封顶写成 `min(100, ...)` | 批注：100 是 `max_health` 的字面量复制，`max_health=80` 时满血判定失真（实测 `服药后 100/80`）；另自加 `scholar_saved` 闸门防「10 文换 15 声望」无限刷 | 阈值一律回指数据；兑换型规则必须自带次数约束 |
| 4 | Stage 4：5 类边界输入审计 | 我最初只跑了「能跑通」的输入 | 切换成测试视角后发现：用例 1（`" /Go East "`）**不报错、只丢指令**，比崩溃更危险 | 报错会逼人看，静默失效不会——边界表必须逐条读输出 |
| 5 | Stage 5：加固重构（空守卫 / `split()` / `len(parts)` / `in`） | 四道守卫齐备；改为按 `parts[0]` 动词路由 | 批注：这条路由改造**修掉了 Stage 3 记下的 `/help` 吞噬 `/help_scholar` 前缀陷阱**，属计划外收益，已回归验证 | 防御性重构的价值外溢到相邻模块 |
| 6 | 进阶一：自动化边界审计脚本 | 9 用例 + `try/except` + 通过率 | 追问「这表会不会恒真」→ 负向自检：把 `dispatch` 换回缺陷写法，9/9 FAIL、兜住异常 3、exit 1 | 断言有效性要靠「人为注入缺陷」来反证 |
| 7 | 进阶二：第 4 房间只改字典 | 数据加完即通 | 要求「证明路由一行没改」→ `sha256sum -c` 双 OK + 源码级断言（引擎里搜不到 `shuyuan`） | 解耦不能只靠嘴说，要留可复跑的凭证 |

# 第 7 周实验：逻辑世界建模与 MUD 分支审查实践报告

实验者：龙勤涛（7904126014）　班级：生物工程 261 班　日期：2026-10-26

## 1. 数据类型安全与「数据—逻辑分离」架构思考

【思考手记】：阶段一靶场把血量存成字符串 `"80"`，喝药后变成 `"8020"`，让我体会到人工审查数据类型的必要性。我复核的方式不是"看代码觉得对不对"，而是让程序自证：`print(type(player["health"]))` 打出 `<class 'str'>`，`"80" + "20"` 得 `"8020"`；去掉双引号后 `80 + 20 -> 100`。更关键的一步是**反向验证**——把 `health` 改回字符串再跑验收脚本，它必须报 3 条未通过并以 exit 1 退出，否则那个 `[x] 全部通过` 只是恒真的安慰剂。

同一类错误在 Stage 3 又以另一种面目出现：课程骨架里 `min(100, player["health"] + 20)`。这个 100 是 `max_health` 的字面量复制，和 `"80"` 一样属于"把数据降级成常量写进控制流"。实测把角色上限压到 80，满血判定 `health >= 100` 直接失真，出现 `服药后 100/80`——**血条突破上限**。类型安全与"取值来源安全"其实是同一件事：凡是能从数据模块读到的量，写死就是债。

字典查表让我在扩展第 4 房间时无需改动一行路由逻辑。这次我不是口头宣称，而是留了凭证：改数据前后对 `mud_engine_v1.py`、`mud_engine_robust.py` 做 `sha256sum -c`，两个文件都 `OK`；又在验收脚本里加了一条源码级断言——引擎源文件里搜不到 `shuyuan`、`白鹿洞` 字样。加完 `north` 出口，`/look` 自己就列出 3 个出口，`/go north` 自己就抵达白鹿洞书院。反过来看 elif 硬编码：每加一个房间要补 房间×方向 个分支，还要逐条判断"这间房能不能往北"。**数据可以新增、校验、序列化，控制流不动**——这才是"数据驱动"四个字的落点。代价也要记账：查表把错误从写代码时推迟到运行时（`KeyError`），所以它必须与 `in` 守卫、Stage 1 的连通性校验配套出现，否则优势立刻变成脆点。

## 2. 大模型「阳光路径偏见」与批判性边界审计思考

【思考手记】：初版代码在常规输入下完全正常，但单敲 `/go` 立即触发 `IndexError`。因为 AI 默认用户必然传入完整参数，唯有靠人类设计畸形边界测试才能暴露出这一隐患。回溯栈读法我总结成三步：只看最后一行的冒号左侧定性质（`IndexError` = 序列越界）；从栈底往上找属于自己写的那一帧（`line 49, in dispatch_command_v1`）；再问"谁是长度 1"——`"/go".split(" ", 1)` 得 `['/go']`，强读 `[1]` 必崩。更重要的是认识到：**49 行只是症状，病因在上游的 `startswith("/go")` 只验了前缀没验参数**。所以正确修法不是在 49 行包一层 `try/except`，而是换掉取参数的方式。

五个边界用例里最让我警惕的反而是**不报错的那一个**：`" /Go East "` 在缺陷版只打印「未知指令。」，程序活着、玩家却寸步难行。同类陷阱还有 `.get(direction)`——它让非法方向静默写入 `player["location"] = None`，崩溃点被推迟到下一轮 `world[...]`，异常点与错误点分离，最难定位。与之相对，`/go   west` 切出 `'  west'` 抛 `KeyError`、`/go` 抛 `IndexError`，这两个"崩给你看"的反而好修。

方法论上，我把这一周踩到的防线抽象成三层，每次改动都按这三层重跑：**清洗层**（`strip().lower()`，管住空白与大小写）、**切分层**（无参 `split()` + `len(parts) < 2`，管住参数个数与连续空格）、**查表层**（`in room["exits"]`，管住键是否存在）。三层各管一类输入缺陷，互不重叠，因此漏测可以定位到"哪一层没写"。最后一步是把一次性人工测试升级成自动化回归：`test_boundary_audit.py` 进程内直调路由函数，9 项 0.1 ms 跑完；并且对它做过负向自检——人为把 `dispatch` 换回缺陷写法，结果 9/9 FAIL、`被 try 兜住的异常：3`、exit 1。这证明断言表真能抓到回归，而不是恒真。**AI 负责生成，人负责设计能让 AI 出错的那张表**，这是本周我最大的收获。

## 3. 条件分支背后的价值判断与设计者责任

【思考手记】：AI 可以快速生成 if-elif-else 语法，但决定分支优先级、伦理取向与安全兜底防线的，始终是人类工程师。`/heal` 是最好的例子：三条分支语法上都等价可跑，**顺序却是一种裁决**。先判"无药"还是先判"满血"，决定的是玩家能否无药空加血——`rules_buggy.py` 实测把道具校验挪到后面就抛 `ValueError: list.remove(x): x not in list`，改成容错写法则变成"凭空回血"，道具经济当场失效。同理，动作内部先 `remove` 药、后 `+20` 血，是"先成本后收益"的价值排序；封顶值取 `max_health` 而非 100，是"规则要对所有角色一致生效"的责任。

`/help_scholar` 更直接地暴露了设计者的裁决权。课程只要求两道限制（地点、盘缠），但**10 文换 15 声望这个兑换比率本身没有任何依据**——它是我定的，AI 不会主动质疑一个由提示词给定的数值是否失衡。我另外加了一道 `scholar_saved` 一次性闸门，因为不加，茶馆就可以无限刷声望；可一旦加了，游戏就在说"善行不可重复套利"。这是一条**价值观写进代码**的决定，不是技术决定：它把"鼓励行善"改成了"善行有且只有一次"。这类取舍 AI 给不出答案，因为它不知道我们想要什么样的江湖，只有设计者能为这个后果签字。

责任还体现在对失败的处理方式上：非法方向我不写"错误"，而写「前面似有石墙受阻。此路唯有：[east]、[west]」，把拦截变成引导；空回车不报「未知指令」而是给下一步提示。同样是一行 `return`，措辞决定了一个新手是被劝退还是被扶一把。最后必须诚实记账：本次有**三处超出课程要求的改动由我（与 AI 协同）自行决定**——`scholar_saved` 闸门、robust 版改按动词 token 路由、验收脚本加 `MUD_ENGINE` 环境变量切换被测引擎。它们都留下了回归记录，但**属于设计者的主动选择而非题目要求**，理应被审阅者质疑。AI 能数秒生成分支，而"这条分支该不该存在、按什么顺序存在、失败了谁承担后果"，是人的判断，也应当由人来署名。
