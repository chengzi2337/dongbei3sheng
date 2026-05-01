## 项目上下文摘要（论文主线可视化重构）

生成时间：2026-05-01 16:12:00

### 1. 相似实现分析

- **实现1**: `D:\dongbei3sheng\batch1_visualizations.py`
  - 模式：单脚本集中生成多张图，统一 `matplotlib` 风格配置，输出到 `visualizations/`
  - 可复用：统一配色、导出分辨率设置、问题一瀑布图和三问总对比图的基本组织方式
  - 需注意：标题、坐标轴和注释以英文为主，不符合当前论文正文中文化要求
- **实现2**: `D:\dongbei3sheng\batch1_supplement.py`
  - 模式：围绕 `advanced_summary.json` 补充问题二、三解释图
  - 可复用：每日最少出勤人数与最终安排人数的双图结构
  - 需注意：`fig6_constraint_tightness()` 内存在“Mock up Maximum Supply Capacity”口径，不能作为正文图
- **实现3**: `D:\dongbei3sheng\batch2_visualizations.py`
  - 模式：算法过程型与统计型附属图集中输出
  - 可复用：ALNS 收敛图、图像批量生成入口
  - 需注意：`operator evolution`、`raincloud`、`phase space` 更适合附录，不应继续承担正文主叙事
- **实现4**: `D:\dongbei3sheng\advanced_staff_scheduling_methods.py`
  - 模式：高级验证脚本统一读取原始需求、生成问题二三摘要、覆盖明细和 ALNS 工人排班结果
  - 可复用：`read_demand()`、`coverage_detail_table()`、`Q3_ALNS_Coverage` 与 `Q3_ALNS_WorkerSchedule` 数据口径
  - 需注意：当前摘要文件未直接输出“问题三按天跨组班型人数”，需要在新脚本中从工人排班或工作簿解析

### 2. 项目约定

- **命名约定**: 现有 Python 文件以蛇形命名，图函数以 `figN_xxx` 命名，输出图片以 `figN_*.png` 命名
- **文件组织**: 求解逻辑在根目录 Python 脚本中；图像统一写入 `visualizations/`；本轮审计文件必须写入项目本地 `.codex/`
- **导入顺序**: 标准库在前，第三方库在后，项目内导入最后
- **代码风格**: 以直接、清晰的过程式绘图函数为主，少量辅助函数；适合继续沿用

### 3. 可复用组件清单

- `D:\dongbei3sheng\large_expo_staff_scheduling_solver.py::read_demand`：从原始附件恢复 `天-小组-小时` 需求张量
- `D:\dongbei3sheng\large_expo_staff_scheduling_solver.py::build_problem3_patterns`：问题三同组/跨组班型定义
- `D:\dongbei3sheng\advanced_summary.json`：问题二、三每日最少出勤与最终出勤摘要
- `D:\dongbei3sheng\q1_video_discrepancy_audit.json`：问题一逐组 LP 下界、向上取整、整数最优审计数据
- `D:\dongbei3sheng\高级排班优化结果.xlsx`：问题三覆盖明细与 ALNS 工人排班
- `D:\dongbei3sheng\排班优化求解结果.xlsx`：问题三模式统计表，可用于交叉核验跨组班型口径

### 4. 测试策略

- **测试框架**: 当前仓库没有单独的自动化测试框架，主要通过本地脚本运行和结果文件核验
- **验证模式**: 本轮采用“脚本执行 + 输出文件检查 + 关键数字抽查”方式
- **参考文件**: `advanced_summary.json`、`q1_video_discrepancy_audit.json`、`高级排班优化结果.xlsx`
- **覆盖要求**: 至少验证图片是否成功生成、标题是否中文化、关键数字是否与摘要文件一致、正文图不再包含 mock 口径图

### 5. 依赖和集成点

- **外部依赖**: `pandas`、`numpy`、`matplotlib`、`seaborn`、`openpyxl`
- **内部依赖**: 新绘图脚本需要与 `large_expo_staff_scheduling_solver.py` 的数据读取函数以及现有 JSON/XLSX 结果文件对齐
- **集成方式**: 直接读取结果文件，不改动求解器核心逻辑；如需跨组统计，优先解析 `Q3_ALNS_WorkerSchedule`
- **配置来源**: 输入文件主要为 `附件1.xlsx`、`advanced_summary.json`、`q1_video_discrepancy_audit.json`、两个结果工作簿

### 6. 技术选型理由

- **为什么用独立正文图脚本**: 现有脚本已经混入附录型算法图和 mock 图，继续叠加会让主线更散
- **优势**: 新脚本可以按“需求展示→模型递进→下界闭合→结构解释→结论对比”组织，更贴合论文论证链
- **劣势和风险**: 论文 `.doc` 正文无法直接读取，暂时只能先产出图和图表说明文档，再由后续手工或另行工具接入正文

### 7. 关键风险点

- **数据口径风险**: 问题三跨组班型结构图若直接读取基础求解工作簿，会与 ALNS 结果口径不一致，应优先解析 `Q3_ALNS_WorkerSchedule`
- **编码风险**: Windows 控制台读取中文文件名存在乱码，脚本中应使用 `glob` 或 `Path` 自动定位文件
- **边界条件**: 代表性覆盖图的案例选择必须有明确规则，不能凭主观硬选
- **性能风险**: 本轮文件规模小，主要风险不在性能，而在图文口径是否一致
- **安全/可信性风险**: `fig6_constraint_tightness` 属于手工构造口径，必须明确降级或停用，不能作为正文证据
