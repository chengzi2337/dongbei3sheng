## 项目上下文摘要（故事线重构）

生成时间：2026-04-30 13:45:00

### 1. 相似实现与材料分析

- **材料1**: `D:\dongbei3sheng\.codex\paper-advanced-model-mainline.md`
  - 模式：把三问统一为“时空覆盖、流动约束、下界构造、可行性验证”的递进模型线。
  - 可复用：统一符号、三问章节结构、下界-可行解-验证闭环。
  - 需注意：问题一不能直接套用问题二、三的下界相等证明。
- **材料2**: `D:\dongbei3sheng\.codex\advanced-model-next-window-notes.md`
  - 模式：建议不再围绕旧简单模型，而是使用独立高级求解链。
  - 可复用：列生成、网络流、ALNS 的角色边界和论文表述边界。
  - 需注意：ALNS 只作为异构任务匹配与精细重构工具。
- **材料3**: `D:\dongbei3sheng\independent_advanced_summary.json`
  - 模式：结构化汇总三问结果、列生成过程、日最少出勤数、ALNS 指标。
  - 可复用：问题一 417 人、问题二 406 人、问题三 400 人。
  - 需注意：问题二、三有理论下界字段，问题一理论下界字段为空。

### 2. 项目约定

- **文件组织**: 求解脚本与结果文件在项目根目录，分析和验证文档在项目本地 `.codex/`。
- **论文风格**: 先定义统一问题，再分场景说明约束放宽、模型变化、结果证据。
- **验证方式**: 仓库无 pytest/unittest，采用本地脚本和结果文件一致性验证。

### 3. 可复用组件清单

- `D:\dongbei3sheng\independent_advanced_staff_scheduling.py`: 独立高级求解链。
- `D:\dongbei3sheng\independent_高级排班优化结果.xlsx`: 论文表格与结果工作簿。
- `D:\dongbei3sheng\.codex\verify_independent_advanced_results.py`: 本地独立性与可行性验证脚本。
- `D:\dongbei3sheng\.codex\paper-sensitivity-results.json`: 敏感性分析素材。

### 4. 测试策略

- 已运行 `python D:\dongbei3sheng\.codex\verify_independent_advanced_results.py`。
- 验证结论：独立高级求解验证通过；工作簿包含 Summary、Q1、Q2、Q3、覆盖与工人排班等关键工作表。
- 核心结果：问题一 417 人；问题二 406 人并达到理论下界；问题三 400 人并达到理论下界。

### 5. 依赖和集成点

- **业务输入**: `D:\dongbei3sheng\附件1.xlsx`。
- **外部依赖**: `numpy`、`pandas`、`scipy`、`openpyxl`。
- **论文集成点**: 摘要、问题分析、模型建立、结果分析、敏感性分析和附录验证说明。

### 6. 技术选型理由

- 列生成适合问题一的“完整个体排班模式空间大”场景。
- 网络流适合问题二、三的“每日任务量到具体人员工作日映射”场景。
- ALNS 适合问题三的异构日内任务匹配和轨迹重构，但不单独承担最优性证明。

### 7. 关键风险点

- 问题一的最优性表述要依赖整数主问题求解状态、人工松弛和 gap，不要照搬下界证明。
- 问题三不能写成“ALNS 证明全局最优”，应写成“下界等于可行解证明人数最优”。
- 故事线不要按算法名串联，应按业务约束放宽和证据链串联。
