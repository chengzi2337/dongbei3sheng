# Gemini 核心文件清单

本清单用于说明 `gemini_core_files_2026-05-01.zip` 中各文件的作用，方便外部模型快速理解项目结构。

## 1. 输入与原始数据

- `D:\dongbei3sheng\附件1.xlsx`
  - 原始需求数据源，包含 10 天、10 个小组、11 个小时槽的排班需求。

## 2. 核心求解脚本

- `D:\dongbei3sheng\independent_advanced_staff_scheduling.py`
  - 当前最完整、最独立的求解主链，覆盖三问的班型生成、覆盖优化、最大流工作日分解与问题三 ALNS 重构。
- `D:\dongbei3sheng\large_expo_staff_scheduling_solver.py`
  - 项目内基础求解模块，提供需求读取、班型构造和分问题求解函数。
- `D:\dongbei3sheng\.codex\paper_sensitivity_analysis.py`
  - 论文用灵敏度分析脚本，负责输出 `UDR`、总缺口、最大单元缺口、缺口时段数量及随机缺勤模拟结果。
- `D:\dongbei3sheng\paper_mainline_visualizations.py`
  - 论文主线可视化脚本，生成主叙事所需图表。

## 3. 结果摘要与关键证据

- `D:\dongbei3sheng\independent_advanced_summary.json`
  - 三问核心结果摘要，包含 `417/406/400`、问题二和问题三的每日最少出勤序列与 ALNS 指标。
- `D:\dongbei3sheng\q1_video_discrepancy_audit.md`
  - 问题一 `411.375 → 415 → 417` 的口径纠偏说明。
- `D:\dongbei3sheng\q1_video_discrepancy_audit.json`
  - 问题一审计的结构化结果。
- `D:\dongbei3sheng\q1_417_feasible_schedule.csv`
  - 问题一 417 人逐人工可行排班。
- `D:\dongbei3sheng\independent_q3_alns_convergence.csv`
  - 问题三 ALNS 收敛日志。
- `D:\dongbei3sheng\.codex\paper-sensitivity-results.json`
  - 论文最终使用的灵敏度分析结果。

## 4. 论文主线与说明材料

- `D:\dongbei3sheng\.codex\paper-advanced-model-mainline.md`
  - 当前最完整的论文主线材料。
- `D:\dongbei3sheng\.codex\paper-organization-draft.md`
  - 论文详细组织初稿。
- `D:\dongbei3sheng\.codex\sensitivity-paper-table.md`
  - 灵敏度分析论文表格。
- `D:\dongbei3sheng\.codex\verification-report.md`
  - 本地验证报告汇总。
- `D:\dongbei3sheng\.codex\context-summary-研究建议整合与鲁棒性重构.md`
  - 最近一轮关于鲁棒性重构的上下文摘要。
- `D:\dongbei3sheng\Large Expo Staff Scheduling Paper Draft.pdf`
  - 当前论文导出稿，可用于整体结构快速浏览。

## 5. 主线可视化结果

- `D:\dongbei3sheng\visualizations\mainline\`
  - 论文主线可视化输出目录，包含热力图、模型递进图、问题一瀑布图、问题二/三每日出勤图和最终人数对比图。

## 6. 适合 Gemini 的阅读顺序

建议按以下顺序阅读：

1. `paper-advanced-model-mainline.md`
2. `independent_advanced_summary.json`
3. `independent_advanced_staff_scheduling.py`
4. `paper-sensitivity-results.json`
5. `verification-report.md`
6. `visualizations/mainline/`
