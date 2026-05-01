# 项目上下文摘要（六点算法增强）

生成时间：2026-04-30 20:35:00 +08:00

## 1. 任务目标

在保留现有独立高级求解链和核心结果口径的前提下，分任务完成六点保守算法增强：ALNS目标函数细化、ALNS算子消融、多随机种子稳定性、可选最小费用工作日流、问题一列生成定价候选扩展、敏感性分析整理。

## 2. 本地实现落点

- **主脚本**：`D:\dongbei3sheng\independent_advanced_staff_scheduling.py`
  - `AlnsConfig`：ALNS迭代、随机种子、退火参数和破坏规模配置。
  - `metrics_for_assignments`、`score_metrics`：问题三排班质量指标和评分函数。
  - `build_workday_flow`：把每日出勤人数映射到具体员工工作日的最大流构造。
  - `price_q1_columns`、`solve_q1_column_generation_group`：问题一列生成定价与列池扩展。
  - `solve_problem3_alns`：问题三理论下界、工作日映射、ALNS重构的主入口。
  - `parse_args`、`write_outputs`：命令行参数与结果工作簿、JSON、收敛日志输出。

- **敏感性脚本**：`D:\dongbei3sheng\.codex\paper_sensitivity_analysis.py`
  - 已从原始 `附件1.xlsx` 重新计算需求上浮、工作天数、跨组休息间隔三类场景。
  - 可复用其结果作为第六点增强的论文表格来源。

- **验证脚本**：`D:\dongbei3sheng\.codex\verify_independent_advanced_results.py`
  - 检查独立脚本不导入旧简单模型、不读取旧结果、不硬编码 417/406/400。
  - 检查问题一人工松弛、问题二/三理论下界、问题三覆盖缺口、工作簿工作表和逐人工工作天数。

## 3. 编程库文档依据

- 通过 Context7 查询 SciPy 文档，确认 `linprog` 用于线性规划松弛，`milp` 用于混合整数线性规划，`LinearConstraint`、`Bounds` 分别表达线性约束和变量边界。
- 本轮不引入新外部优化库，避免破坏现有依赖结构。

## 4. 六点增强映射

1. ALNS目标函数细化：落点为 `AlnsConfig`、`metrics_for_assignments`、`score_metrics`、`Q3Alns.run`。
2. 算子消融：新增 `.codex/run_algorithm_enhancements.py`，通过配置启用/禁用破坏和修复算子。
3. 多随机种子稳定性：新增增强脚本循环调用 `solve_problem3_alns`。
4. 最小费用流可选增强：在主脚本新增轻量 `build_workday_min_cost_flow`，默认不替代旧最大流，命令行可选启用。
5. 问题一定价候选扩展：扩展 `price_q1_columns` 的 `per_day_top` 和 `max_new_columns` 参数。
6. 敏感性分析整理：复用 `paper_sensitivity_analysis.py` 输出，新增论文表格 Markdown。

## 5. 项目约定

- Python 函数与变量使用 snake_case，类使用 PascalCase，常量使用大写。
- 文档、错误提示、注释使用简体中文。
- `.codex` 目录用于上下文摘要、验证脚本、分析结果和报告。
- 默认行为应尽量保持旧结果口径；增强项通过参数或派生脚本运行。

## 6. 风险与控制

- ALNS不能在论文中表述为全局最优证明；全局最优性仍来自理论下界与可行解相等。
- 最小费用流仅作为工作日映射结构优化，不改变人数下界。
- 算子消融和多种子稳定性使用轻量迭代，避免过度运行成本。
- 问题一列生成候选扩展应记录参数，不应虚构为完整分支定价。
