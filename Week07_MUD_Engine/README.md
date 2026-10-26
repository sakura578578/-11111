# Week07 MUD 引擎 · Stage 1 世界模型与角色档案

实验者：龙勤涛（7904126014）　就绪状态：Stage 1-5 + 进阶一/二 + 任务六三反思报告 全部提交（2026-10-26）

## 目录

| 文件 | 作用 |
| --- | --- |
| `01_stage1_world_model/world_data_buggy.py` | 课程靶场：故意用 str 存 health/gold，复现 `"80"+"20" -> "8020"` |
| `01_stage1_world_model/world_data_fixed.py` | 人工审查修复版：去除双引号，恢复原生 int |
| `01_stage1_world_model/world_data.py` | ROCA 生成的静态数据模块：world 四房间拓扑 + player 角色字典 |
| `01_stage1_world_model/check_world_data.py` | 验收清单自动化校验（含双向闭环与类型检查） |
| `02_stage2_3_router_v1/mud_engine_v1_buggy.py` | 课程靶场：未清洗输入 / split 越界 / 缺 in 守卫三处缺陷 |
| `02_stage2_3_router_v1/mud_engine_v1.py` | 中央指令路由：清洗层 → 分流层 → 查表层 |
| `02_stage2_3_router_v1/check_router.py` | Stage 2 验收 18 项自动化校验（含第 4 房间「只改字典」5 项） |
| `02_stage2_3_router_v1/rules_buggy.py` | 课程靶场：/heal 条件顺序颠倒、阈值写死 100、服药不封顶 |
| `02_stage2_3_router_v1/check_rules.py` | Stage 3 验收 24 项自动化校验（/heal、/help_scholar） |
| `02_stage2_3_router_v1/CODE_REVIEW.md` | 查表 vs elif、`in` 守卫、多条件先后顺序的评审答复 |
| `03_stage4_5_robust_engine/mud_engine_robust.py` | Stage 5 防御性重构版：清洗/切分/长度/键成员四道守卫 |
| `03_stage4_5_robust_engine/test_boundary_audit.py` | 自动化边界回归审计：5 类 9 用例，进程内直调，0.1 ms |
| `04_stage4_boundary_review/boundary_tests.py` | 5 类非常规输入 × (靶场/合规/加固) 三引擎取证台 |
| `annotated_prompts.md` | ROCA 提示词批注 + 边界对比记录表 + Traceback 三步定位 + 回归矩阵 + **第 7 周实践报告·人机协同三反思** |

## 运行

```bash
python world_data_buggy.py      # 缺陷复现：health = 8020 <class 'str'>
python world_data_fixed.py      # 修复后：health = 100 int
python check_world_data.py      # 验收：全部验收项通过 [x]，exit 0

python mud_engine_v1_buggy.py   # 缺陷复现：未知指令 / IndexError / KeyError
python rules_buggy.py           # 缺陷复现：ValueError / 服药后 100/80 突破上限
python mud_engine_v1.py         # 交互式游玩：/look /status /go /heal /help_scholar /help /quit
python check_router.py          # Stage 2 验收：全部通过 [x]，exit 0
python check_rules.py           # Stage 3 验收：全部通过 [x]，exit 0

python mud_engine_robust.py     # 加固版引擎（四道守卫）
python test_boundary_audit.py   # 自动化边界回归：5 类 9 用例全 PASS，0.1 ms，exit 0
python boundary_tests.py        # Stage 4/5 边界审查：三引擎对照，合规/加固异常 0

# 回归矩阵：同一套断言切换被测引擎
MUD_ENGINE=mud_engine_robust python check_router.py
MUD_ENGINE=mud_engine_robust python check_rules.py
```

Windows 控制台若中文输出乱码，先 `set PYTHONIOENCODING=utf-8`。

## 地图连通关系（4 房间，进阶二扩建）

```
              白鹿洞书院(shuyuan)
                      | south->广场
江南武馆(wuguan) ←west— 扬州中心广场(guangchang) —east→ 春来茶馆(chaguan)
   武馆 --east--> 广场        广场 --north--> 书院
```
