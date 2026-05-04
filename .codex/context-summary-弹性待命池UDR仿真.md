## 项目上下文摘要（弹性待命池UDR仿真）

生成时间：2026-05-04 21:25:36

### 1. 相似实现分析

- **实现1**: [independent_advanced_staff_scheduling.py](D:\dongbei3sheng\independent_advanced_staff_scheduling.py)
  - 关键位置：`read_demand`、`build_shift_pairs`、`build_problem3_patterns`、`solve_daily_problem3`、`build_workday_flow`、`build_workday_assignment`、`coverage_from_assignments`、`metrics_for_assignments`、`solve_problem3_alns`
  - 模式：问题三的 370 个合法模式由“同组双 4 小时段 + 跨组双 4 小时段”统一生成；日层 MILP 采用 `scipy.optimize.milp + LinearConstraint + Bounds`；全期“每人 8 天”一致性由最大流验证。
  - 可复用：需求读取、模式构造、覆盖统计、问题三标签生成、工作日最大流建模思路。
  - 需注意：原 `build_workday_flow` 强制每人恰好工作 8 天，不适用于本次“待命人员最多工作 8 天”的宽松约束，需要新增“至多 8 天”的验证流函数。

- **实现2**: [advanced_staff_scheduling_methods.py](D:\dongbei3sheng\advanced_staff_scheduling_methods.py)
  - 关键位置：`build_workday_flow`、`coverage_from_assignments`、`metrics_for_assignments`
  - 模式：与独立版相同，但从 `large_expo_staff_scheduling_solver.py` 复用基础建模函数，说明项目内对“模式构造 + 覆盖矩阵 + 最大流验证”的接口已经稳定。
  - 可复用：`coverage_from_assignments` / `metrics_for_assignments` 的指标定义，可作为本次基准排班校验标准。
  - 需注意：这里同样只支持“恰好 8 天”的流验证。

- **实现3**: [.codex/paper_sensitivity_analysis.py](D:\dongbei3sheng\.codex\paper_sensitivity_analysis.py)
  - 关键位置：`build_q3_baseline`、`worker_contributions_from_assignments`、`shortage_metrics`、`simulate_absence_metrics`
  - 模式：先构造问题三基准排班，再对“工人-日期”单元做独立 Bernoulli 缺勤仿真，统计总缺口、UDR、最大单元缺口和缺口时段数。
  - 可复用：随机种子 `20260501`、Monte Carlo 缺勤建模口径、总需求 `17682` 的既有统计、JSON 结果组织方式。
  - 需注意：该脚本只评估缺勤后原排班的缺口，不含待命补位；本次必须在缺勤后继续求解补位模型。

- **实现4**: [paper_mainline_visualizations.py](D:\dongbei3sheng\paper_mainline_visualizations.py)
  - 关键位置：`OUT_DIR`、`save_close`、`mpl.rcParams.update`
  - 模式：论文主线图统一输出到 `visualizations/mainline/`，使用中文字体配置，PNG 直接供论文引用。
  - 可复用：输出目录、图像风格、`save_close` 风格的简单保存模式。

### 2. 数据与结果文件

- 需求文件：
  - [附件1.xlsx](D:\dongbei3sheng\附件1.xlsx)
  - [附件1.xls](D:\dongbei3sheng\附件1.xls)
- 结果摘要：
  - [advanced_summary.json](D:\dongbei3sheng\advanced_summary.json)
  - [independent_advanced_summary.json](D:\dongbei3sheng\independent_advanced_summary.json)
  - [.codex/paper-sensitivity-results.json](D:\dongbei3sheng\.codex\paper-sensitivity-results.json)
- 问题三排班结果工作簿：
  - [independent_高级排班优化结果.xlsx](D:\dongbei3sheng\independent_高级排班优化结果.xlsx)
  - [高级排班优化结果.xlsx](D:\dongbei3sheng\高级排班优化结果.xlsx)
  - 两者均包含 `Q3_ALNS_WorkerSchedule`、`Q3_ALNS_Coverage`、`Q3_ALNS_Daily` 等工作表，可用于恢复 400 人基准排班。

### 3. 项目约定

- **命名约定**：
  - Python 标识符使用英文蛇形命名。
  - 文档、日志、表头、图题使用简体中文。
- **文件组织**：
  - 过程性脚本和分析产物写入项目本地 `.codex/`。
  - 论文主线图写入 `visualizations/mainline/`。
- **建模风格**：
  - 优先复用 `scipy.optimize.milp` 与稀疏矩阵建模，不新引入求解库。
  - 覆盖矩阵统一使用 `pattern_cover[pattern_id, group, hour]`。
- **输入输出协议**：
  - `read_demand` 返回 `(demand, days, hours, group_cols)`。
  - `coverage_from_assignments` 接收 `assignments[worker, day]` 与 `pattern_cover`，返回 `(day, group, hour)` 覆盖。

### 4. 可复用组件清单

- [independent_advanced_staff_scheduling.py](D:\dongbei3sheng\independent_advanced_staff_scheduling.py)
  - `read_demand`
  - `build_shift_pairs`
  - `build_problem3_patterns`
  - `coverage_from_assignments`
  - `metrics_for_assignments`
  - `pattern_label`
- [.codex/paper_sensitivity_analysis.py](D:\dongbei3sheng\.codex\paper_sensitivity_analysis.py)
  - `worker_contributions_from_assignments`
  - `shortage_metrics`
- [paper_mainline_visualizations.py](D:\dongbei3sheng\paper_mainline_visualizations.py)
  - 中文字体与 `visualizations/mainline` 输出模式

### 5. 测试与验证策略

- 现状：仓库中未检索到现成 `test_*.py`、`*.spec.*` 或 `*.test.*` 文件。
- 本次验证方式：
  - 基准排班重建后，验证总人数为 400、总缺口为 0。
  - 缺勤样本在 `N_sb=0` 时与直接缺口统计一致。
  - 每个样本、每个 `N_sb` 的待命出勤向量都通过“每人每天最多 1 次、全期最多 8 天”的最大流验证。
  - 运行 `--runs 50 --max-standby 30` 与默认 `--runs 200 --max-standby 30` 两次脚本，检查 CSV/JSON/MD/PNG 产物与控制台摘要。

### 6. 依赖和集成点

- **外部依赖**：
  - `numpy`
  - `pandas`
  - `scipy.optimize.milp`
  - `matplotlib`
  - `openpyxl`
- **内部依赖**：
  - 直接导入 `independent_advanced_staff_scheduling.py`
  - 读取既有 JSON / Excel 结果文件
- **求解器信息**：
  - 继续使用 SciPy/HiGHS MILP；`time_limit` 由脚本传参控制，默认 30 秒。

### 7. 技术选型理由

- **为什么不直接用 64*N_sb 扣缺口**：
  - 该口径忽略了问题三合法模式约束与跨组休息约束，不能反映真实补位能力。
- **为什么采用“按天 MILP + 跨天 DP”的精确分解**：
  - 用户给出的聚合模型跨天唯一耦合是 `sum_d sum_p x_{d,p} <= 8*N_sb`，目标函数按天可加。
  - 因此可先求每一天在给定待命人数上限 `k` 下的最优缺口函数，再用动态规划组合 10 天结果；这是精确等价变换，不是假设或近似。
- **为什么需要新增最大流验证函数**：
  - 现有 `build_workday_flow` 要求总工作日恰好等于 `8*N`，而待命池允许“不被完全调用”，所以必须改成“至多 8 天”的可行性验证。

### 8. 关键风险点

- **数据风险**：
  - 若 `Q3_ALNS_WorkerSchedule` 文本标签与 `pattern_label` 生成文本不一致，无法无损恢复模式编号。
- **性能风险**：
  - `runs=200`、`max_standby=30` 下仍有较多 MILP，需要依赖分解、逐日提前停止和样本级提前停止。
- **验证风险**：
  - SciPy `milp` 超时后状态与当前解可用性需要脚本显式记录；若无可用 `x`，需标记 `solve_success=false` 并给出保守上界。

