# 正文图表安排建议（V3）

生成时间：2026-05-01 18:08:00

## 总体原则

- 正文图只保留服务主论证链的图，不再把附属性算法图混入主线。
- 当前 V3 图表顺序遵循“需求结构 -> 模型递进 -> 问题一闭合 -> 问题二网络流 -> 问题三模板与结构 -> 结果对比 -> 鲁棒性评价”。
- 主线图与仓库产物已经统一到 `D:\dongbei3sheng\visualizations\mainline\fig01` 至 `fig11`。

## 图表目录

### 图1 总需求日-小时热力图

- 文件：`D:\dongbei3sheng\visualizations\mainline\fig01_total_demand_heatmap.png`
- 位置：问题重述或数据特征分析
- 用途：展示 10 天与 11 小时段上的需求峰谷结构

### 图2 小组-日期需求强度热力图

- 文件：`D:\dongbei3sheng\visualizations\mainline\fig02_group_day_demand_heatmap.png`
- 位置：问题分析
- 用途：说明问题一按小组分解的现实基础，以及问题二、三全局调配的必要性

### 图3 三问模型递进关系图

- 文件：`D:\dongbei3sheng\visualizations\mainline\fig03_model_progression.png`
- 位置：统一模型框架
- 用途：说明“聚合IP -> 下界+最大流 -> 模式扩展+ALNS”的递进逻辑

### 图4 问题一 411.375→415→417 下界闭合瀑布图

- 文件：`D:\dongbei3sheng\visualizations\mainline\fig04_q1_waterfall.png`
- 位置：问题一结果分析
- 用途：解释为什么 415 只是下界，417 才是整数可执行人数

### 图5 问题一逐组 LP 下界、取整下界与整数最优人数对比图

- 文件：`D:\dongbei3sheng\visualizations\mainline\fig05_q1_group_comparison.png`
- 位置：紧接图4
- 用途：定位小组 5 和小组 9 的整数化补差来源

### 图6 最大流工作日分解网络拓扑图

- 文件：`D:\dongbei3sheng\visualizations\mainline\fig06_maxflow_topology.png`
- 位置：问题二或统一方法说明
- 用途：解释“每天需要多少人”如何映射为“具体哪些员工在第几天出勤”

### 图7 问题二每日最少出勤人数与最终安排人数

- 文件：`D:\dongbei3sheng\visualizations\mainline\fig07_q2_daily_staffing.png`
- 位置：问题二结果分析
- 用途：展示 `3247 -> 406` 的下界闭合过程

### 图8 问题三 13 类基础时间模板与 370 个服务模式示意图

- 文件：`D:\dongbei3sheng\visualizations\mainline\fig08_q3_template_patterns.png`
- 位置：问题三模型建立
- 用途：解释 10 类同组模板、3 类跨组模板及 `100 + 270 = 370` 的模式计数来源

### 图9 问题三跨组班型使用结构图

- 文件：`D:\dongbei3sheng\visualizations\mainline\fig09_q3_cross_group_usage.png`
- 位置：问题三结果分析
- 用途：展示问题三节省人数的结构来源是日内跨组班型使用，而不是纯粹搜索波动

### 图10 三问最终最少招聘人数对比图

- 文件：`D:\dongbei3sheng\visualizations\mainline\fig10_final_worker_comparison.png`
- 位置：三问结果对比或结论部分
- 用途：总结 `417 -> 406 -> 400` 的边际节约效果

### 图11 需求扰动下原方案 UDR 对比图

- 文件：`D:\dongbei3sheng\visualizations\mainline\fig11_demand_perturbation_udr.png`
- 位置：灵敏度分析
- 用途：比较 `S1`、`S1+`、`S2` 场景下三问原方案的缺口率差异

## 表格建议

### 表1 问题一逐组结果表

- 列：小组、LP 松弛值、LP 向上取整、整数最优人数、覆盖缺口

### 表2 问题二和问题三下界闭合表

- 列：问题、每日最少出勤总和、`ceil(sum/8)`、单日峰值、理论下界、构造可行人数、是否达到下界

### 表3 三问管理特征对比表

- 列：问题、最少人数、是否固定小组、是否允许日内跨组、是否需要换组休息约束、执行复杂度评价

### 表4 需求扰动与随机缺勤指标表

- 列：场景、问题、总缺口、UDR、最大单元缺口、缺口时段数量

## 附录建议

- 附录保留：
  - `fig5_alns_convergence.png`
  - `fig7_operator_evolution.png`
  - `fig8_workload_raincloud.png`
  - `fig9_shift_transition.png`
  - `fig10_alns_phase_space.png`
- 主文不再强调：
  - `fig6_constraint_tightness.png`
  - 原因：该图基于旧补充脚本中的非主线口径，不适合作为当前 V3 正文证据
