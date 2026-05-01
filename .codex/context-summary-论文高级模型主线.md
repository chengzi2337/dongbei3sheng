# 项目上下文摘要（论文高级模型主线）

生成时间：2026-04-29 16:04:00

## 1. 相似实现与材料分析

- **材料1**: `D:\dongbei3sheng\.codex\advanced-model-next-window-notes.md`
  - 模式：将三问统一为一条独立高级模型路线，强调时空模式生成、理论下界、网络流映射与 ALNS 重构。
  - 可复用：论文总主线、三问章节结构、最优性表述边界、后续改进清单。
  - 需注意：问题二、问题三可用“下界等于可行解”证明人数最优；问题一若声称全局最优，需要展示整数主问题状态和 gap。

- **材料2**: `D:\dongbei3sheng\independent_advanced_staff_scheduling.py`
  - 模式：完全独立读取 `附件1.xlsx`，内置需求张量重构、合法班型生成、列生成、最大流、ALNS、结果导出。
  - 可复用：`read_demand`、`build_shift_pairs`、`solve_problem1_independent`、`solve_problem2_network_flow`、`solve_problem3_alns`、`write_outputs`。
  - 需注意：该脚本不导入原始简单模型，不读取旧结果表，不硬编码 417、406、400。

- **材料3**: `D:\dongbei3sheng\independent_advanced_summary.json`
  - 模式：以结构化 JSON 汇总三问人数、列生成过程、日最少出勤数、ALNS 指标和算子权重。
  - 可复用：问题一 417 人、问题二 406 人、问题三 400 人；问题二理论下界 406，问题三理论下界 400。
  - 需注意：问题一理论下界字段为空，论文中应把它写成列生成与整数恢复证据，而不是下界相等证据。

- **材料4**: `D:\dongbei3sheng\.codex\independent-verification-report.md`
  - 模式：验证源码独立性、编译、独立运行、约束满足和结果文件完整性。
  - 可复用：本地复现命令、验证结论、覆盖缺口为 0、每名员工工作天数为 8 天。
  - 需注意：该报告是附录和可复现说明的主要依据。

## 2. 项目约定

- **命名约定**: Python 函数与变量使用 snake_case，类使用 PascalCase，常量使用大写；论文过程文件使用中文语义文件名或明确英文技术名。
- **文件组织**: 核心求解脚本放在项目根目录；上下文摘要、验证脚本、验证报告、论文迁移材料放入项目本地 `.codex/`。
- **导入顺序**: 标准库、第三方库、项目内部逻辑；独立高级脚本当前无项目内部导入。
- **代码风格**: 4 空格缩进，使用 `numpy`、`pandas`、`scipy` 和稀疏矩阵构造 MILP；错误提示与文档使用简体中文。
- **论文风格**: 先定义符号与约束，再说明算法路径，最后用结果表和验证证据闭环。

## 3. 可复用产物清单

- `D:\dongbei3sheng\independent_advanced_staff_scheduling.py`: 独立高级求解链。
- `D:\dongbei3sheng\independent_advanced_summary.json`: 论文结果表和算法指标的数据来源。
- `D:\dongbei3sheng\independent_高级排班优化结果.xlsx`: 结果工作簿，包含 Summary、Q1_ColumnGeneration、Q2_NetworkFlow、Q3_ALNS_Daily、Q3_ALNS_Metrics、Q3_ALNS_Convergence、Q3_ALNS_Coverage、Q3_ALNS_WorkerSchedule。
- `D:\dongbei3sheng\independent_q3_alns_convergence.csv`: 问题三 ALNS 收敛曲线数据。
- `D:\dongbei3sheng\.codex\verify_independent_advanced_results.py`: 独立性与可行性验证脚本。
- `D:\dongbei3sheng\.codex\independent-verification-report.md`: 可复现验证报告。

## 4. 测试与验证策略

- **测试框架**: 仓库没有 pytest/unittest；采用本地脚本验证和结果文件一致性检查。
- **参考验证**: `python -m py_compile independent_advanced_staff_scheduling.py`、运行独立高级脚本、运行 `.codex\verify_independent_advanced_results.py`。
- **本次材料验证**: 读取 JSON、CSV、验证报告和生成的 Markdown，核对 417、406、400、理论下界、覆盖缺口、工作天数范围和文件路径。
- **覆盖要求**: 正常求解链、三问结果、下界论证、网络流满流、问题三覆盖缺口、逐人工工作天数、ALNS 收敛记录。

## 5. 依赖和集成点

- **业务输入**: `D:\dongbei3sheng\附件1.xlsx`。
- **外部依赖**: `numpy`、`pandas`、`scipy`、`openpyxl`。
- **官方接口依据**: Context7 查询 SciPy 文档后确认 `scipy.optimize.milp` 用于混合整数线性规划，`LinearConstraint` 表达 `lb <= A @ x <= ub`，`Bounds` 表达变量边界，`linprog` 的 HiGHS 方法用于线性松弛。
- **开源搜索状态**: 当前会话未暴露 `github.search_code` 工具；已记录工具缺口，继续以既有上下文中 ALNS 和列生成模式为依据，不新增未经验证的外部实现。
- **正式论文稿**: `D:\dongbei3sheng\B题 大型展销会临时工招聘与排班优化问题_20260429175705.doc` 为旧 Word 格式，当前工具无法安全解析；本轮先生成可迁移 Markdown 正文素材。

## 6. 论文主线抽象

- **总问题**: 将临时工排班抽象为带时空覆盖约束、连续服务约束、跨日工作天数约束和日内流动限制的人员调度优化问题。
- **问题一**: 固定小组服务，使用列生成和整数主问题恢复，结果为 417 人。
- **问题二**: 跨日可换组、日内单组服务，使用单日最小出勤人数推导理论下界，再用最大流构造个体工作日映射，结果为 406 人且达到下界。
- **问题三**: 日内最多双组服务，使用异构日内任务模式、理论下界、最大流初始化和 ALNS 精细重构，结果为 400 人且达到下界。

## 7. 关键风险点

- **问题一最优性边界**: 不能直接套用“下界等于可行解”；需要展示列生成、无人工松弛、整数主问题结果和求解状态。
- **ALNS 表述边界**: ALNS 只负责异构任务匹配和轨迹重构，不承担全局最优证明。
- **结果来源边界**: 不得引用 `排班优化求解结果.xlsx` 或原始简单模型作为高级模型输入。
- **敏感性分析边界**: 后续扰动实验必须从 `附件1.xlsx` 重新计算，或明确标注为基于已验证下界公式的派生分析。
- **文档集成风险**: 旧 `.doc` 文件暂不可安全编辑；需要后续转换为 `.docx` 或手工迁移 Markdown 内容。
