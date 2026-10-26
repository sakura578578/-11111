# Stage 2 Code Review：查表寻址 vs elif 硬编码

实验者：龙勤涛（7904126014）　日期：2026-10-26

## 追问 i：为什么 `room["exits"][direction]` 比 `elif command == "/go east":` 更易维护？

| 维度 | elif 硬编码 | 字典查表 |
| --- | --- | --- |
| 新增房间 | 要新增 N 个 `elif`，逐条写「该房间能否向某方向走」，还要改引擎代码 | 只在 `world_data.py` 加一条 dict，引擎 **0 行改动** |
| 分支数量 | 房间数 × 方向数量，且每个房间可达集合不同，必须逐组合枚举 | 一行 `player["location"] = room["exits"][direction]` 覆盖全部房间 |
| 数据/逻辑耦合 | 地图拓扑散落在 if-elif 里，与 `world` 描述形成两处真相 | 拓扑只在 `world` 一处，`/look` 出口列表、移动判定、Stage 1 闭环校验读同一份数据 |
| 典型故障 | 改了数据忘了改 elif，出现「描述说能往东，代码不让走」的静默不一致 | 键写错会立刻 `KeyError`/校验失败，**错误暴露得更早** |
| 后续扩展 | 存档、传送、动态开门需重新生成代码 | 改 dict 即可，甚至可由 JSON 载入 |

一句话：elif 把「世界长什么样」硬编码进控制流，查表把它降级成**数据**——数据可以新增、校验、序列化，控制流不用动。

代价也要讲清楚：查表把错误从编译期推到运行期（见追问 ii），所以必须配 `in` 守卫 + Stage 1 的连通性校验脚本，否则优势变成脆点。

## 追问 ii：`if direction in room["exits"]:` 防止了什么运行期异常？

**直接防的是 `KeyError`。** 靶场实测（`mud_engine_v1_buggy.py` 去掉守卫后输入 `/go up`）：

```
target = room["exits"][direction]
KeyError: 'up'
```

它还连带防住两类二次故障：

1. **状态污染后的连锁崩溃**。若写成 `player["location"] = room["exits"].get(direction)`，缺失方向会返回 `None`，语句本身不报错，于是 `player["location"] = None`；下一轮 `world[player["location"]]` 才炸，且栈里看不出玩家是怎么走丢的——异常点与错误点分离，最难查。守卫让非法移动**根本不写状态**（`check_router.py` 第 3 项专测「非法移动后位置未被改写」）。
2. **越界取值 `IndexError`**。这是靶场缺陷 2：`command.split(" ", 1)[1]` 在玩家只输入 `/go` 时切出长度为 1 的列表 → `IndexError: list index out of range`。守卫思路同源：**先确认取值得到，再取**。

`in` 守卫 vs `.get()` 的取舍：`.get()` 返回 `None` 仍需再判一次，且容易漏判；`in` 让「合法」与「提示」共用同一份 `exits`，所以受阻提示能直接列出 `此路唯有：[west]`——顺手把报错变成了引导。

## 靶场三缺陷与修复对照

| 缺陷 | 现象（实测） | 修复 |
| --- | --- | --- |
| 1 未做 `.strip().lower()` | 输入 `" /Go East "` → 打印「未知指令。」，移动指令整体丢失 | 输入清洗层 `command = raw.strip().lower()` |
| 2 `split(" ", 1)[1]` 越界 | 输入 `/go` → `IndexError: list index out of range` | `parts = command.split()`，先判 `len(parts) < 2` |
| 3 无 `in` 守卫 | 输入 `/go up` → `KeyError: 'up'`，引擎崩溃退出 | `if direction in room["exits"]` |

---

# Stage 3 审查：多条件判断的先后顺序与价值规则

## 审查要点：`/heal` 的限制条件为什么必须排在动作前面

课程给的骨架里两条前置校验（道具存在性、满血上限）都在 `else` 之前，这是**特异性优先**：越具体的限制越先判。靶场 `rules_buggy.py` 实测三处失守的代价：

| 缺陷 | 写法 | 实测后果 |
| --- | --- | --- |
| A 未先校验道具 | 直接 `player["inventory"].remove("金创药")` | `ValueError: list.remove(x): x not in list`，引擎崩；若改用 `if...remove` 分开写而顺序颠倒，则**无药空加血**——凭空回血，道具经济失效 |
| B 阈值写死字面量 | `if player["health"] >= 100` | `max_health = 80` 的受伤体质满血时判定失真，实测 `服药后 100/80`——血条突破上限 |
| C 服药不封顶 | `player["health"] += 20` | 连服可无限堆叠，实测一路涨过 `max_health` |

修复后的正确顺序（已落进 `mud_engine_v1.py:heal()`）：

```python
if "金创药" not in player["inventory"]:   # 1 最特异：资源是否存在
    return "你的行囊中已经没有【金创药】了！"
if player["health"] >= player["max_health"]:  # 2 是否还有收益空间
    return "你当前气血充沛，无需服用金创药。"
player["inventory"].remove("金创药")      # 3 先扣成本，再加收益
player["health"] = min(player["max_health"], player["health"] + 20)  # 4 上限取自数据，非字面量
```

三条顺序原则：

1. **限制先于动作**：所有 `return` 的拦截分支写完，才允许出现修改状态的语句。任何一条前置校验失效，状态就是干净的——不必写回滚。
2. **成本先于收益**：先 `remove` 药、后 `+20` 血。反过来的话，中途若抛异常就变成「血加了药没扣」。
3. **阈值来自数据**：`max_health` 而非 `100`，与 Stage 1 的类型/取值约束同源——数字写死在控制流里，就等于放弃了让 `world_data.py` 单独演进的能力。

`check_rules.py` 用「既无药又满血」这条输入专门验了顺序：期望命中『无药』而非『满血』，命中错分支说明条件排序退化。

## `/help_scholar`：价值抉择的双守卫 + 路由前缀陷阱

限制条件同样是两道前置：地点必须 `chaguan`（剧情触发点），盘缠必须 `>= 10`（成本），二者拦截后 **`gold` / `reputation` 一律不变**（验收专测）。另加一道 `scholar_saved` 一次性闸门——否则茶馆里可反复 `/help_scholar` 以 10 文换 15 声望，把声望刷穿；「用铜钱换声望」这类兑换型规则，**必须自带次数约束**。

路由层的坑：`/help_scholar` 与 `/help` 共享前缀。若把原 `/help` 分支写成 `command.startswith("/help")`，救助指令会被帮助菜单静默吞掉——玩家看不到任何报错，只是「说了没用」。因此两条都用**精确 `==` 匹配**，并把 `/help_scholar` 排在 `/help` 之前；`check_rules.py` 第 4 组专门断言 `/help_scholar` 的输出里不含「可用指令」。
