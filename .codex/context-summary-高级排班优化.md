## 项目上下文摘要（高级排班优化）

生成时间：2026-04-29 23:15:00

### 1. 相似实现分析

- **实现1**: `D:\dongbei3sheng\large_expo_staff_scheduling_solver.py`
  - 模式：读取附件、枚举合法班型、用 SciPy MILP 求解三问，并导出 Excel。
  - 可复用：`read_demand`、`build_shift_pairs`、`build_problem3_patterns`、`solve_daily_problem2`、`solve_daily_problem3`、`time_label`。
  - 需注意：问题2/3采用单日最小人数后再平衡到每人工作8天，属于可行构造与下界验证结合。
- **实现2**: `D:\dongbei3sheng\temporary_staff_scheduling_mip.py`
  - 模式：统一 MIP 建模，直接设置全局招聘人数变量 `N`，结果输出为 CSV。
  - 可复用：`SameGroupShift`、`CrossGroupShift`、`solve_milp` 的建模风格和稀疏约束构造。
  - 需注意：默认数据文件名与当前仓库不一致，需要显式传入 `附件1.xlsx`。
- **实现3**: `D:\dongbei3sheng\排班优化求解结果.xlsx`
  - 模式：已有结果按 Summary、日汇总、班型计数、工人排班分 sheet 输出。
  - 可复用：结果对比口径；当前结果为问题1=417、问题2=406、问题3=400。
### 2. 项目约定

- **命名约定**: Python 文件使用 snake_case 函数名，常量使用大写，结果文件使用中文名称。
- **文件组织**: 当前为脚本式项目，核心求解脚本直接放在项目根目录，过程文件放入 `.codex/`。
- **导入顺序**: 标准库、第三方库、项目内脚本函数。
- **代码风格**: 4 空格缩进，使用 `pandas/numpy/scipy`，中文报错和中文输出。

### 3. 可复用组件清单

- `large_expo_staff_scheduling_solver.read_demand`: 读取附件需求，返回三维需求矩阵与标签。
- `large_expo_staff_scheduling_solver.build_shift_pairs`: 生成同组和跨组时间模板。
- `large_expo_staff_scheduling_solver.solve_daily_problem2`: 精确求解问题2单日班型。
- `large_expo_staff_scheduling_solver.solve_daily_problem3`: 精确求解问题3单日受限模板覆盖。
- `large_expo_staff_scheduling_solver.time_label`: 输出可读时间段标签。

### 4. 测试策略

- **测试框架**: 仓库没有独立 pytest/unittest 测试；采用本地脚本自检。
- **测试模式**: 读取附件、运行高级脚本、校验覆盖需求、校验每人工作8天、校验目标值与已有结果一致。
- **参考文件**: `排班优化求解结果.xlsx` 的 Summary、Q2/Q3 日汇总。
- **覆盖要求**: 正常流程、下界不可突破、网络流可行性、ALNS 可行性和收敛日志。

### 5. 依赖和集成点

- **外部依赖**: `numpy`、`pandas`、`scipy`、`openpyxl`，均已在本地 Python 环境可用。
- **内部依赖**: 新脚本导入 `large_expo_staff_scheduling_solver.py` 的数据读取、班型枚举和单日 MILP。
- **输入协议**: `附件1.xlsx` 包含 110 行需求，字段为天、小时、小组1至小组10。
- **输出协议**: 生成 `高级排班优化结果.xlsx`、`advanced_summary.json`、`q3_alns_convergence.csv`。

### 6. 技术选型理由

- **SciPy MILP/linprog**: 官方文档确认 `milp` 支持整数变量、Bounds、LinearConstraint，`linprog` 的 HiGHS 支持 LP 与对偶边际值。
- **最大流**: 对问题2/3的“每人工作8天、每天需要 y_d 人”构造为二部图可行流，证明下界人数可实现。
- **ALNS**: 第三个文档明确推荐，用于问题3的联合优化验证，包含破坏、修复、自适应权重和退火接受。
### 7. 关键风险点

- **并发问题**: 无并发写入；所有输出文件由单进程生成。
- **边界条件**: 问题3跨组班型必须只允许 3 个满足至少2小时休息的模板；同组班型允许不重叠即可。
- **性能瓶颈**: ALNS 若每次全量重算覆盖会慢，需使用数组评分并限制迭代次数。
- **验证考虑**: 若 ALNS 未找到更优解，仍需用理论下界 `ceil(sum(N_d)/8)` 证明 400 已是问题3全局最优。

### 8. 外部参考

- Context7 SciPy 文档：`scipy.optimize.milp`、`LinearConstraint`、`Bounds`、`linprog`/HiGHS 对偶边际值。
- GitHub 搜索参考：`N-Wouda/ALNS` 示例、VRPTW-ALNS 仓库，用于确认 ALNS 的 destroy/repair/自适应算子结构。
