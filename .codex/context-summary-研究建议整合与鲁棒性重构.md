# 项目上下文摘要（研究建议整合与鲁棒性重构）

生成时间：2026-05-01 16:40:00

## 1. 相似实现分析

- **实现1**：`D:\dongbei3sheng\q1_video_discrepancy_audit.md`
  - 模式：问题一采用“LP 下界 → 向上取整下界 → 整数可行解”的证据链。
  - 可复用：`411.375 → 415 → 417` 的口径解释、逐组整数最优人数表、逐人工可行排班证据。
  - 需注意：`415` 只是下界，不是可执行排班人数；问题一最优性叙事必须与问题二、三区分开。
- **实现2**：`D:\dongbei3sheng\.codex\paper-advanced-model-mainline.md`
  - 模式：现有论文主线已采用三问递进叙事，并写入问题二、三的“理论下界 + 可行构造闭合”证明。
  - 可复用：问题二 `3247 → 406`、问题三 `3198 → 400` 的下界推导；ALNS 仅承担重构职责的表述。
  - 需注意：当前敏感性分析仍偏“参数扫描”，尚未按原方案在扰动下的缺口表现组织。
- **实现3**：`D:\dongbei3sheng\.codex\paper_sensitivity_analysis.py`
  - 模式：已能从 `附件1.xlsx` 重新计算需求倍率、工作天数、跨组休息间隔三类敏感性结果。
  - 可复用：`q1_exact_total`、`q2_lower_bound`、`q3_lower_bound` 三类重算入口。
  - 需注意：尚未计算 `UDR`、总缺口、最大单元缺口、缺口时段数量，也未覆盖随机缺勤场景。
- **实现4**：`D:\dongbei3sheng\independent_advanced_staff_scheduling.py`
  - 模式：合法班型池、单日整数覆盖、最大流工作日映射、ALNS 重构的统一求解链。
  - 可复用：`solve_problem2_network_flow`、`solve_problem3_alns`、`coverage_from_assignments`、`build_problem3_patterns`、`initial_assignments_from_flow`。
  - 需注意：不要新建平行求解体系，应直接复用这些函数扩展鲁棒性评价。

## 2. 项目约定

- **命名约定**：Python 函数与变量使用 `snake_case`，类使用 `PascalCase`，常量使用全大写。
- **文件组织**：论文工作底稿与验证文档集中放在 `D:\dongbei3sheng\.codex\`，求解脚本位于项目根目录。
- **导入顺序**：标准库 → 第三方库 → 项目内模块。
- **代码风格**：中文注释说明意图和约束，避免重复代码逻辑；文档以 Markdown 为主。

## 3. 可复用组件清单

- `D:\dongbei3sheng\independent_advanced_staff_scheduling.py`
  - `read_demand`：读取原始需求张量。
  - `build_shift_pairs`：生成合法 8 小时班型。
  - `solve_problem2_network_flow`：问题二“单日最少出勤 + 工作日映射”主入口。
  - `solve_problem3_alns`：问题三“理论下界 + 最大流初始化 + ALNS”主入口。
  - `coverage_from_assignments`：从逐人工排班恢复覆盖矩阵。
  - `initial_assignments_from_flow`：把日工作矩阵映射为逐人工排班。
- `D:\dongbei3sheng\advanced_summary.json`
  - 问题二、三基准下界、每日出勤序列与 ALNS 指标摘要。
- `D:\dongbei3sheng\q1_417_feasible_schedule.csv`
  - 问题一 417 人逐人工排班，可恢复基准覆盖矩阵并评估缺勤扰动。

## 4. 测试策略

- 本轮核心验证命令：
  - `python D:\dongbei3sheng\.codex\paper_sensitivity_analysis.py`
- 验证重点：
  - 新脚本是否能输出 `UDR`、总缺口、最大单元缺口、缺口时段数量。
  - 是否覆盖三类论文建议场景：整体需求上浮、高峰小时上浮、随机缺勤。
  - 结果 JSON 与论文底稿表述是否一致。

## 5. 依赖和集成点

- **外部依赖**：`numpy`、`pandas`、`scipy`、`openpyxl`。
- **内部依赖**：鲁棒性分析直接复用 `independent_advanced_staff_scheduling.py` 的求解与覆盖恢复函数。
- **集成方式**：更新 `paper_sensitivity_analysis.py` 生成新的 `paper-sensitivity-results.json`，再同步修改论文主线与表格文档。
- **配置来源**：输入数据固定为项目根目录下唯一满足 `*1.xlsx` 的原始附件。

## 6. 技术选型理由

- **为什么用现有求解链扩展鲁棒性评价**：三问基准解已经存在，且可从逐人工排班或日班型计数恢复覆盖矩阵，直接在现有代码上做扰动评估最稳妥。
- **优势**：不引入新模型口径，结果可追溯到原始附件与既有最优解。
- **风险**：高峰小时需要明确 operational definition；随机缺勤场景需要说明采用固定种子 Monte Carlo 估计。

## 7. 关键风险点

- **口径风险**：外部研究中的示例数字不能直接写成本文结论。
- **边界风险**：问题一鲁棒性评价依赖 CSV 排班文本解析，必须先验证时间段解析与小时槽映射正确。
- **性能风险**：问题三 ALNS 重跑存在计算耗时，需控制迭代次数并记录实际运行结果。
- **表达风险**：鲁棒性评价应放在“模型检验、灵敏度分析、模型推广”层，不能改写主模型最优答案。
