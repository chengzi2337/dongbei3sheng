# 项目上下文摘要（算法论文优化）

生成时间：2026-04-30 19:26:29 +08:00

## 1. 任务目标

本轮任务评估当前大型展销会临时工招聘与排班优化算法是否还有优化空间，并检索相关学术论文，判断如何降低“照讲解视频复刻”的雷同风险，同时增强论文故事线叙事。

## 2. 本地相似实现与材料分析

- **实现1**：`D:\dongbei3sheng\advanced_staff_scheduling_methods.py`
  - 模式：高级主实现，包含列生成、最大流、ALNS、指标计算和结果导出。
  - 关键位置：`Dinic`、`build_workday_flow`、`Q3Alns`、`solve_q1_master_lp`、`price_q1_columns`、`solve_q1_integer_master`、`solve_problem2_network_flow`、`solve_problem3_alns`。
  - 需注意：ALNS 当前从可行初始解出发，收敛日志显示第 1 次迭代已达到最终最优分数。

- **实现2**：`D:\dongbei3sheng\independent_advanced_staff_scheduling.py`
  - 模式：完全独立高级求解链，从 `附件1.xlsx` 读取原始数据并自行完成三问建模、求解、导出和验证。
  - 可复用：独立性证据、结果工作簿、JSON 摘要、ALNS 收敛日志。
  - 需注意：这是降低视频雷同风险的主要证据，因为它不依赖原始简单模型或旧结果。

- **实现3**：`D:\dongbei3sheng\large_expo_staff_scheduling_solver.py`
  - 模式：基础 MILP 求解器，提供需求读取、合法班型构造、单日覆盖 MILP、问题三模式枚举等基础能力。
  - 可复用：`read_demand`、`build_shift_pairs`、`solve_daily_problem2`、`solve_daily_problem3`、`build_problem3_patterns`。
  - 需注意：高级脚本复用了其中部分接口，论文可将其抽象为“合法模式生成与单日覆盖求解层”。

- **材料4**：`D:\dongbei3sheng\q1_video_discrepancy_audit.md`
  - 模式：第一问视频结果冲突审计。
  - 关键结论：视频中的 415 是 LP 松弛下界取整口径，不是可执行排班人数；当前模型构造了 417 人可执行整数排班，覆盖缺口为 0，每人工日为 8-8。
  - 叙事价值：可作为“本文不是复刻视频，而是纠正下界与可行解口径”的证据。

- **材料5**：`D:\dongbei3sheng\.codex\paper-advanced-model-mainline.md`
  - 模式：高级模型论文主线材料。
  - 关键主线：问题一列生成，问题二理论下界加最大流，问题三理论下界加最大流加 ALNS。
  - 需注意：已有材料已明确 ALNS 不承担全局最优证明。

## 3. 当前算法主线

- **问题一**：固定小组服务，将单个员工 10 天内工作 8 天、休息 2 天、每天选合法 8 小时班型的完整轨迹定义为列；使用 RMP 线性松弛、定价子问题和整数主问题恢复，得到 417 人。
- **问题二**：跨日可换组但日内单组服务；先求每日最少出勤人次，再由 `max(max m_d, ceil(sum m_d / 8))` 推理论下界，并用最大流完成个人工作日映射，得到 406 人且达到下界。
- **问题三**：日内最多双组服务；枚举单组 8 小时和双组 4+4 小时异构模式，求每日最少出勤人次，推导 400 人下界，再用最大流和 ALNS 构造 400 人可行排班。

## 4. 关键结果证据

- `advanced_summary.json`：问题一 417 人、问题二 406 人、问题三 400 人；问题二理论下界 406，问题三理论下界 400。
- `q3_alns_convergence.csv`：最优分数从第 1 次迭代开始保持 `7918.4047`，覆盖缺口为 0，最优冗余为 `7918`。
- `.codex\paper-sensitivity-results.json`：已有需求上浮、工作天数、跨组休息间隔三类敏感性结果。
- `.codex\independent-verification-report.md`：独立脚本编译、运行、验证通过；源码独立性检查通过。

## 5. 学术论文来源表

- Ernst 等，2004，*Staff scheduling and rostering: A review of applications, methods and models*：人员排班应用、方法和模型综述。来源：https://ideas.repec.org/a/eee/ejores/v153y2004i1p3-27.html
- Van den Bergh 等，2013，*Personnel scheduling: A literature review*：人员排班分类综述，DOI `10.1016/j.ejor.2012.11.029`。来源：https://ideas.repec.org/a/eee/ejores/v226y2013i3p367-385.html
- De Bruecker 等，2015，*Workforce planning incorporating skills: State of the art*：技能约束与真实管理含义综述。来源：https://ideas.repec.org/a/eee/ejores/v243y2015i1p1-16.html
- Dantzig 与 Wolfe，1960，*Decomposition Principle for Linear Programs*：Dantzig-Wolfe 分解与列生成理论基础。来源：https://econpapers.repec.org/RePEc:inm:oropre:v:8:y:1960:i:1:p:101-111
- Sarin 与 Aggarwal，2001，*Modeling and algorithmic development of a staff scheduling problem*：员工排班中的集合划分/列生成程序。来源：https://www.sciencedirect.com/science/article/abs/pii/S037722179900421X
- Gérard、Clautiaux 与 Sadykov，2016，*Column generation based approaches for a tour scheduling problem with a multi-skill heterogeneous workforce*：多活动、多技能员工 tour scheduling 的列生成方法。来源：https://www.sciencedirect.com/science/article/abs/pii/S0377221716000813

- Segal，1974，*The Operator-Scheduling Problem: A Network-Flow Approach*：电话接线员排班中的网络流方法。来源：https://ideas.repec.org/a/inm/oropre/v22y1974i4p808-823.html
- Brucker 与 Qu，2014，*Network flow models for intraday personnel scheduling problems*：日内人员任务分配的网络流模型。来源：https://ideas.repec.org/a/spr/annopr/v218y2014i1p107-11410.1007-s10479-012-1234-y.html
- Di Gaspero 等，2007，*The minimum shift design problem*：最小班次设计、网络流类比、贪心加局部搜索。来源：https://ideas.repec.org/a/spr/annopr/v155y2007i1p79-10510.1007-s10479-007-0221-1.html
- Lin 与 Ying，2014，*Minimizing shifts for personnel task scheduling problems: A three-phase algorithm*：人员任务排班最小班次数三阶段算法。来源：https://ideas.repec.org/a/eee/ejores/v237y2014i1p323-334.html
- Røpke 与 Pisinger，2006，*An Adaptive Large Neighborhood Search Heuristic for the Pickup and Delivery Problem with Time Windows*：ALNS 的 destroy/repair、自适应权重和接受机制。来源：https://backend.orbit.dtu.dk/ws/portalfiles/portal/3154899/An+adaptive+large+neighborhood+search+heuristic+for+the+pickup+and+delivery+problem+with+time+windows_TechRep_ropke_pisinger.pdf
- Gutjahr、Parragh 与 Tricoire，2023，*Adaptive large neighborhood search for a personnel task scheduling problem with task selection and parallel task assignments*：ALNS 在人员任务排班中的应用。来源：https://arxiv.org/abs/2302.04494

## 6. 优化空间判断

- **短期不建议推翻现有算法**：当前 417、406、400 的结果有独立脚本、下界证明、可行性验证和敏感性实验支撑。
- **问题一可加强**：当前列生成定价以候选启发式生成新列，论文中应避免把这一过程直接表述为完整 branch-and-price；若要进一步提升学术性，可补充完整动态规划定价或分支定价口径。
- **问题三可加强**：ALNS 当前没有改善初始最大流解的最优分数，因此论文中应将其定位为异构任务匹配和鲁棒性重构；若要成为真正优化贡献，应加入冗余平方、最大冗余、跨组切换公平性、个体连续工作负荷等目标。
- **叙事可加强**：把三问统一为“流动约束逐步放宽下的分层人员调度框架”，用“下界定标、可行构造、本地验证”贯穿全文。

## 7. 上下文充分性检查

- 能说出至少 3 个相关实现或材料路径：是，见第 2 节。
- 理解实现模式：是，列生成、MILP、最大流、ALNS、敏感性分析已定位。
- 知道可复用组件：是，`read_demand`、`build_shift_pairs`、`solve_daily_problem2`、`solve_daily_problem3`、`build_workday_flow`、`Q3Alns`。
- 理解测试方式：是，当前仓库以本地验证脚本和结果文件一致性为主。
- 确认没有重复造轮子：是，本轮不新增算法代码，只提出优化和论文重构建议。
- 理解依赖和集成点：是，唯一业务输入为 `附件1.xlsx`，主要依赖为 `numpy`、`pandas`、`scipy`、`openpyxl`。
