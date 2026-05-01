# 高级模型论文可视化图表索引

生成时间：2026-04-30

本图表包服务于数学建模 B 题“大型展销会临时工招聘与排班优化问题”的高级模型论文主线。所有图表均由 `generate_academic_visualizations.py` 从独立高级模型产物生成，不引用原始简单模型结果作为输入。

## 1. 图表总体设计原则

- **论文审美**：采用浅底色、克制配色、清晰网格、统一字体和可解释注释，避免宣传海报式装饰。
- **主线一致**：图表围绕“固定小组服务 → 跨日换组 → 日内双组服务”的约束递进展开。
- **证据优先**：优先展示理论下界、可行解、覆盖缺口、工作天数、列生成过程、ALNS收敛和敏感性响应。
- **可复现性**：每张图均有 PNG 与 SVG 两种格式。PNG 适合直接插入 Word，SVG 适合后续排版编辑。

## 2. 图表清单

### 图1 独立高级模型求解链路与论文证据闭环

- PNG：`D:\dongbei3sheng\.codex\academic_visualizations\fig01_model_framework.png`
- SVG：`D:\dongbei3sheng\.codex\academic_visualizations\fig01_model_framework.svg`
- 适用章节：模型总体设计、论文方法概述。
- 数据来源：`independent_advanced_summary.json`、`paper-advanced-model-mainline.md`。
- 论文图题建议：**图1 独立高级模型求解链路与可复现验证闭环**。
- 解读要点：该图用于从宏观上说明三问不是三个割裂模型，而是同一调度问题在流动约束逐步放宽下的递进式优化链路。
- 正文插入句：本文首先将原始附件重构为时空需求张量，再分别构建列生成、理论下界加最大流、异构任务匹配加 ALNS 的分层模型，最终通过本地验证脚本形成可复现证据闭环。

### 图2 三问招聘人数与下界/恢复证据对比

- PNG：`D:\dongbei3sheng\.codex\academic_visualizations\fig02_optimality_evidence.png`
- SVG：`D:\dongbei3sheng\.codex\academic_visualizations\fig02_optimality_evidence.svg`
- 适用章节：结果总览、最优性分析。
- 数据来源：`independent_advanced_summary.json`。
- 论文图题建议：**图2 三类流动约束下的招聘人数与下界/恢复证据对比**。
- 解读要点：问题一展示 LP 取整下界 415 与整数恢复 417 的差异；问题二得到 406 人且等于理论下界；问题三得到 400 人且等于理论下界。
- 正文插入句：随着人员流动规则放宽，招聘人数由 417 人下降至 406 人和 400 人；其中问题二和问题三由“理论下界等于可行构造”支撑最优性，问题一则展示列生成整数恢复相对 LP 取整下界的修正幅度。

### 图3 问题一列生成规模与整数恢复结果

- PNG：`D:\dongbei3sheng\.codex\academic_visualizations\fig03_q1_column_generation.png`
- SVG：`D:\dongbei3sheng\.codex\academic_visualizations\fig03_q1_column_generation.svg`
- 适用章节：问题一模型与算法结果。
- 数据来源：`independent_advanced_summary.json` 的 `q1_column_generation`。
- 论文图题建议：**图3 固定小组服务场景下的列生成规模与整数主问题恢复结果**。
- 解读要点：图中左侧说明各小组精确人数与列生成整数人数一致；右侧说明不同小组列池规模和新增列数差异。
- 正文插入句：列生成过程在各小组中动态扩展列池，最终整数主问题恢复得到 417 人方案，且所有人工松弛均为 0。

### 图4 问题二与问题三每日出勤结构对比

- PNG：`D:\dongbei3sheng\.codex\academic_visualizations\fig04_daily_attendance.png`
- SVG：`D:\dongbei3sheng\.codex\academic_visualizations\fig04_daily_attendance.svg`
- 适用章节：问题二和问题三的下界构造、最大流映射。
- 数据来源：`independent_advanced_summary.json` 的 `q2_day_minima`、`q2_daily_counts`、`q3_day_minima`、`q3_daily_counts_alns`。
- 论文图题建议：**图4 理论下界驱动下的每日出勤结构对比**。
- 解读要点：问题二总最少出勤为 3247，406 人对应 3248 个工作日；问题三总最少出勤为 3198，400 人对应 3200 个工作日。
- 正文插入句：每日最少出勤曲线给出了不可突破的需求边界，而最大流映射将其转化为满足每人工作 8 天的个体工作日安排。

### 图5 问题三覆盖冗余热力图

- PNG：`D:\dongbei3sheng\.codex\academic_visualizations\fig05_q3_coverage_heatmap.png`
- SVG：`D:\dongbei3sheng\.codex\academic_visualizations\fig05_q3_coverage_heatmap.svg`
- 适用章节：问题三可行性验证、覆盖结构分析。
- 数据来源：`independent_高级排班优化结果.xlsx` 的 `Q3_ALNS_Coverage` 工作表。
- 论文图题建议：**图5 日内双组服务方案的覆盖冗余热力分布**。
- 解读要点：热力图展示按“小组-日期”聚合后的覆盖冗余；覆盖缺口总和为 0，图中颜色深浅用于说明可行方案的剩余覆盖分布。
- 正文插入句：在所有时空需求点均无缺口的前提下，覆盖冗余主要集中于部分高峰日期和小组，说明可行构造满足约束但仍存在可进一步均衡的覆盖余量。

### 图6 问题三员工工作日矩阵示例

- PNG：`D:\dongbei3sheng\.codex\academic_visualizations\fig06_worker_schedule_matrix.png`
- SVG：`D:\dongbei3sheng\.codex\academic_visualizations\fig06_worker_schedule_matrix.svg`
- 适用章节：问题三排班表展示、附录。
- 数据来源：`independent_高级排班优化结果.xlsx` 的 `Q3_ALNS_WorkerSchedule` 工作表。
- 论文图题建议：**图6 问题三个体工作日安排矩阵示例**。
- 解读要点：图中展示前 80 名员工的工作/休息状态，每行均呈现 8 个工作日和 2 个休息日的结构。
- 正文插入句：个体排班矩阵可直观说明最大流映射和 ALNS 重构后的排班满足逐人工工作天数约束。

### 图7 问题三 ALNS 收敛轨迹与算子权重

- PNG：`D:\dongbei3sheng\.codex\academic_visualizations\fig07_alns_convergence.png`
- SVG：`D:\dongbei3sheng\.codex\academic_visualizations\fig07_alns_convergence.svg`
- 适用章节：问题三算法过程、元启发式搜索说明。
- 数据来源：`independent_q3_alns_convergence.csv`、`independent_advanced_summary.json` 的 `q3_operator_weights`。
- 论文图题建议：**图7 ALNS 相对最优差值轨迹与自适应算子权重分布**。
- 解读要点：左图不再直接绘制绝对评分，而是绘制当前解相对历史最优的差值；这能更清楚地说明初始最大流方案已接近最优且后续搜索主要承担异构任务重构。右图展示不同破坏和修复算子的相对贡献。
- 正文插入句：ALNS 在本文中不承担全局最优证明，而是承担异构任务匹配和轨迹重构职责；相对差值轨迹显示当前解在极小波动内围绕最优解搜索。

### 图8 三问关键参数敏感性分析

- PNG：`D:\dongbei3sheng\.codex\academic_visualizations\fig08_sensitivity_analysis.png`
- SVG：`D:\dongbei3sheng\.codex\academic_visualizations\fig08_sensitivity_analysis.svg`
- 适用章节：敏感性分析、模型稳健性讨论。
- 数据来源：`paper-sensitivity-results.json`。
- 论文图题建议：**图8 需求规模、工作天数与休息间隔约束的敏感性分析**。
- 解读要点：需求上浮会同步推高三问人数；工作天数越多，理论下界越低；休息间隔从 2 小时收紧到 3 小时时，问题三人数下界由 400 升至 401。
- 正文插入句：敏感性结果表明模型对需求规模变化具有单调响应，并揭示日内跨组休息间隔是影响问题三排班弹性的关键参数。

### 图9 流动规则放宽带来的边际人力节约

- PNG：`D:\dongbei3sheng\.codex\academic_visualizations\fig09_improvement_gradient.png`
- SVG：`D:\dongbei3sheng\.codex\academic_visualizations\fig09_improvement_gradient.svg`
- 适用章节：结果讨论、管理启示。
- 数据来源：`independent_advanced_summary.json`。
- 论文图题建议：**图9 约束逐步放宽下的边际人力节约效应**。
- 解读要点：从问题一到问题二减少 11 人，从问题二到问题三再减少 6 人，总计减少 17 人。
- 正文插入句：该结果说明，在满足题目约束的前提下，适度提高人员跨日和日内流动性能够显著降低招聘规模。

## 3. 推荐插入顺序

1. 模型方法部分插入图1。
2. 结果总览部分插入图2。
3. 问题一小节插入图3。
4. 问题二和问题三下界构造部分插入图4。
5. 问题三结果分析部分插入图5和图7。
6. 附录或排班展示部分插入图6。
7. 敏感性分析部分插入图8。
8. 结论或管理启示部分插入图9。

## 4. 复现命令

在项目根目录执行：

```powershell
python D:\dongbei3sheng\.codex\academic_visualizations\generate_academic_visualizations.py
```

脚本将重新生成全部 PNG、SVG 和 `figures-manifest.json`。
