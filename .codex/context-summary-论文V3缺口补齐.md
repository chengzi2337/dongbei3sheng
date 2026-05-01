# 项目上下文摘要（论文V3缺口补齐）

生成时间：2026-05-01 17:50:00

## 1. 相似实现与材料分析

- **实现1**：`D:\dongbei3sheng\large_expo_staff_scheduling_solver.py`
  - 模式：基础求解链，直接实现问题一聚合 IP、问题二单日覆盖、问题三综合模式覆盖。
  - 可复用：`read_demand`、`build_shift_pairs`、`build_problem3_patterns`、`solve_problem1_one_group`、`solve_daily_problem2`、`solve_daily_problem3`。
  - 需注意：该脚本已经提供问题一“小规模聚合 IP”证据，因此论文 V3 中问题一主要求解口径应以它为主，而不是把列生成写成唯一主算法。

- **实现2**：`D:\dongbei3sheng\independent_advanced_staff_scheduling.py`
  - 模式：独立高级验证链，围绕列生成、最大流、ALNS 组织问题一到问题三的复核与可行性验证。
  - 可复用：问题一列生成复核结果、问题二 `3247 -> 406` 下界与最大流、问题三 `3198 -> 400` 下界与 ALNS 重构。
  - 需注意：问题一在这里更适合被表述为“复核与扩展框架”，而不是替代基础聚合 IP 的主求解链。

- **实现3**：`D:\dongbei3sheng\paper_mainline_visualizations.py`
  - 模式：根目录主线图脚本，当前已输出 `visualizations\mainline\fig01` 至 `fig10`。
  - 可复用：需求热力图、问题一下界闭合图、问题二三每日出勤图、问题三跨组班型结构图、最终人数对比图。
  - 需注意：它尚未与用户当前 V3 图表目录完全对齐，缺少最大流网络拓扑图、13 类模板与 370 模式示意图、需求扰动下原方案 UDR 对比图。

- **实现4**：`D:\dongbei3sheng\.codex\paper_sensitivity_analysis.py`
  - 模式：从原始附件重算需求扰动、随机缺勤、工作天数、跨组休息间隔等鲁棒性指标。
  - 可复用：`paper-sensitivity-results.json` 中的 `UDR`、总缺口、最大单元缺口、缺口时段数量，以及 `S1/S2/S3` 场景关键值。
  - 需注意：结果已经存在，但尚未被根目录主线图脚本和 V3 图表规划完整吸收。

- **材料5**：`D:\dongbei3sheng\q1_video_discrepancy_audit.md`
  - 模式：问题一 `411.375 -> 415 -> 417` 口径纠偏与逐组结果审计。
  - 可复用：逐组 LP 松弛、向上取整下界、整数最优人数表。
  - 需注意：这是论文中“415 不是可执行人数”的直接证据来源。

## 2. 项目约定

- **命名约定**：Python 使用 `snake_case`，图文件使用 `fig编号_主题.png`，论文辅助文档使用 `.codex\paper-*`、`.codex\context-summary-*`、`.codex\verification-*` 命名。
- **文件组织**：求解脚本与图表脚本在项目根目录；论文底稿、上下文摘要、验证脚本和验证报告位于项目本地 `.codex\`。
- **代码风格**：沿用现有 `matplotlib + seaborn + 过程式函数` 风格，中文注释只说明设计意图和约束来源。
- **文稿风格**：优先使用“模型定义 -> 结果证据 -> 风险边界”的学术论文表达，不写口语化说明。

## 3. 可复用组件清单

- `D:\dongbei3sheng\advanced_summary.json`：问题二、三的高级验证摘要。
- `D:\dongbei3sheng\independent_advanced_summary.json`：独立高级验证摘要，含 `417/406/400`、`3247/3198`、问题三覆盖指标。
- `D:\dongbei3sheng\.codex\paper-sensitivity-results.json`：需求扰动与随机缺勤场景数据。
- `D:\dongbei3sheng\高级排班优化结果.xlsx`：问题三覆盖明细和工人排班表。
- `D:\dongbei3sheng\q1_417_feasible_schedule.csv`：问题一逐人工排班表。

## 4. V3 缺口判断

- **已实现**：
  - 问题一聚合 IP、问题二最大流下界验证、问题三 370 模式与 ALNS 可行构造。
  - `S1/S2/S3` 场景的数值重算与缺口指标。
  - 问题一下界审计与逐人工可行排班导出。

- **未完整同步到 V3 证据层**：
  - 主线图目录仍是旧 10 图版本，尚未完整映射到当前 V3 的 11 图结构。
  - `.codex\paper-advanced-model-mainline.md` 仍以问题一“列生成主算法”叙事为主，未明确“聚合 IP 主求解、列生成复核”的口径。
  - 待命池建议尚未完全更新为“15–20 人初始管理方案，需结合历史缺勤率或分位数仿真校准”的保守表述。
  - 主线验证脚本仍按旧版关键短语校验，未覆盖新图表和新边界表述。

## 5. 测试与验证策略

- 代码层：运行主线图脚本，确认 V3 图表输出存在。
- 文稿层：运行主线验证脚本，核对 `417/406/400`、`3247/3198`、`370`、`S1/S2/S3` 数值和关键表述。
- 结果层：对照 `q1_video_discrepancy_audit.md`、`independent_advanced_summary.json`、`paper-sensitivity-results.json` 核验表格与图题。

## 6. 关键风险点

- **图号漂移风险**：旧版主线图脚本与用户 V3 图表目录不一致，若不统一会导致论文正文与仓库产物错位。
- **口径漂移风险**：问题一若继续突出“列生成主求解”，会与用户最新明确修正相冲突。
- **语言强度风险**：待命池若写成“95% 风险保障”会超出现有仿真证据。
- **验证覆盖风险**：若只更新文稿不更新验证脚本，仓库后续仍可能回退到旧表述而不被发现。
