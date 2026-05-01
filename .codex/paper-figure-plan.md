## 正文图表目录与设计说明

生成时间：2026-05-01 16:22:00

### 总体原则

- 正文图只服务论证链，不再继续堆叠附属性算法图。
- 图的顺序遵循“需求难点 → 模型递进 → 下界闭合 → 结构解释 → 结论对比”。
- 现有 `constraint tightness`、`raincloud`、`phase space`、`operator evolution` 不进入正文。

### 正文图目录

#### 图1 原始总需求日-小时热力图

- **文件**: `D:\dongbei3sheng\visualizations\mainline\fig01_total_demand_heatmap.png`
- **建议位置**: 问题重述/数据特征分析
- **数据来源**: `附件1.xlsx`
- **用途**: 说明需求在 10 天和 11 个小时段上存在明显峰谷变化
- **应表达的结论**: 问题难点首先来自时段波动，而不是求解方法本身

#### 图2 小组-日期总需求热力图

- **文件**: `D:\dongbei3sheng\visualizations\mainline\fig02_group_day_demand_heatmap.png`
- **建议位置**: 数据特征分析，紧接图1
- **数据来源**: `附件1.xlsx`
- **用途**: 展示不同小组在不同日期上的强度差异
- **应表达的结论**: 问题一按小组分解有现实基础，问题二和三的全局调配也有必要

#### 图3 三问模型递进关系图

- **文件**: `D:\dongbei3sheng\visualizations\mainline\fig03_model_progression.png`
- **建议位置**: 模型建立总览
- **数据来源**: 静态结构图，基于三问建模逻辑
- **用途**: 把问题一、二、三放回统一覆盖优化框架
- **应表达的结论**: 三问不是割裂解题，而是逐步放宽资源流动性的递进建模

#### 图4 问题一下界闭合瀑布图

- **文件**: `D:\dongbei3sheng\visualizations\mainline\fig04_q1_waterfall.png`
- **建议位置**: 问题一结果分析
- **数据来源**: `q1_video_discrepancy_audit.json`
- **用途**: 说明 411.375 → 415 → 417 的下界闭合过程
- **应表达的结论**: 415 是逐组下界，不是可执行排班；417 的额外 2 人来自整数可行性

#### 图5 问题一逐组下界与整数最优对比图

- **文件**: `D:\dongbei3sheng\visualizations\mainline\fig05_q1_group_comparison.png`
- **建议位置**: 紧接图4
- **数据来源**: `q1_video_discrepancy_audit.json`
- **用途**: 定位导致总人数从 415 增加到 417 的关键小组
- **应表达的结论**: 小组5、小组9各多出 1 人，是问题一整数化差异的主要来源

#### 图6 问题二每日最少出勤人数与最终安排人数

- **文件**: `D:\dongbei3sheng\visualizations\mainline\fig06_q2_daily_staffing.png`
- **建议位置**: 问题二结果分析
- **数据来源**: `advanced_summary.json`
- **用途**: 展示问题二如何由单日下界闭合到 406 人
- **应表达的结论**: 理论下界来自每日最少出勤总和与每人工作 8 天的结合

#### 图7 问题三每日最少出勤人数与最终安排人数

- **文件**: `D:\dongbei3sheng\visualizations\mainline\fig07_q3_daily_staffing.png`
- **建议位置**: 问题三结果分析
- **数据来源**: `advanced_summary.json`
- **用途**: 展示问题三如何由单日下界闭合到 400 人
- **应表达的结论**: 问题三同样达到了理论下界，400 不是启发式“碰巧找到”的结果

#### 图8 问题三跨组班型使用结构图

- **文件**: `D:\dongbei3sheng\visualizations\mainline\fig08_q3_cross_group_usage.png`
- **建议位置**: 问题三机制解释
- **数据来源**: `高级排班优化结果.xlsx` 中 `Q3_ALNS_WorkerSchedule`
- **用途**: 按天拆解同组班型与跨组班型人数结构
- **应表达的结论**: 节省人数来自更灵活的日内跨组班型，而不是单纯搜索波动

#### 图9 代表性覆盖效果图

- **文件**: `D:\dongbei3sheng\visualizations\mainline\fig09_representative_coverage.png`
- **建议位置**: 问题三机制解释，紧接图8
- **数据来源**: `高级排班优化结果.xlsx` 中 `Q3_ALNS_Coverage`
- **用途**: 在具体日-组案例上展示需求与实际覆盖的小时级关系
- **应表达的结论**: 方案在小时级别满足覆盖约束，且可解释冗余出现在哪些时段
- **说明**: 当前脚本按“总冗余最高的日-组组合”自动选取案例，后续可根据正文叙事手动替换

#### 图10 三问最终最少招聘人数对比图

- **文件**: `D:\dongbei3sheng\visualizations\mainline\fig10_final_worker_comparison.png`
- **建议位置**: 总结或结论部分
- **数据来源**: `q1_video_discrepancy_audit.json`、`advanced_summary.json`
- **用途**: 总结 417、406、400 三个最终结果
- **应表达的结论**: 全局调配相对固定小组减少 11 人，允许跨组后再减少 6 人，总计减少 17 人

### 附录建议

- **可保留到附录**:
  - `fig5_alns_convergence.png`：算法稳定性验证
  - `fig9_shift_transition.png`：排班状态转移补充观察
- **建议移出正文且不强调**:
  - `fig7_operator_evolution.png`
  - `fig8_workload_raincloud.png`
  - `fig10_alns_phase_space.png`
- **建议停用**:
  - `fig6_constraint_tightness.png`
  - 原因：脚本中存在 mock 口径，不是由模型结果直接推出

### 表格建议

#### 表1 问题一逐组结果表

- 列：小组、LP 松弛值、LP 向上取整、整数最优人数、整数缺口、覆盖缺口
- 对应章节：问题一结果分析

#### 表2 问题二、三下界闭合表

- 列：问题、每日最少出勤总和、`ceil(sum/8)`、单日峰值、理论下界、构造可行人数、是否达到下界
- 对应章节：问题二、三结果分析

#### 表3 三问管理特征对比表

- 列：问题、最少人数、是否固定小组、是否允许日内跨组、是否需要换组休息约束、执行复杂度评价
- 对应章节：总结与管理启示
