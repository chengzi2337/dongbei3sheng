## 编码前检查 - 论文主线可视化重构

时间：2026-05-01 16:13:00

□ 已查阅上下文摘要文件：`D:\dongbei3sheng\.codex\context-summary-论文主线可视化重构.md`
□ 将使用以下可复用组件：

- `read_demand`: `D:\dongbei3sheng\large_expo_staff_scheduling_solver.py` - 读取原始需求数据
- `advanced_summary.json`: `D:\dongbei3sheng\advanced_summary.json` - 问题二、三下界与最终人数摘要
- `q1_video_discrepancy_audit.json`: `D:\dongbei3sheng\q1_video_discrepancy_audit.json` - 问题一逐组审计数据
- `Q3_ALNS_Coverage`: `D:\dongbei3sheng\高级排班优化结果.xlsx` - 代表性覆盖图数据源
- `Q3_ALNS_WorkerSchedule`: `D:\dongbei3sheng\高级排班优化结果.xlsx` - 问题三跨组班型统计数据源

□ 将遵循命名约定：Python 文件使用蛇形命名；图像文件使用 `fig编号_主题.png`
□ 将遵循代码风格：沿用现有 `matplotlib + seaborn + 过程式函数` 结构，补充必要中文注释
□ 确认不重复造轮子，证明：已检查 `batch1_visualizations.py`、`batch1_supplement.py`、`batch2_visualizations.py`、`advanced_staff_scheduling_methods.py`，确认现有脚本未形成按论文论证链组织的正文主线图集合

## 决策记录

时间：2026-05-01 16:14:00

1. 现有图表按用途分层：
   - 保留并升级：问题一瀑布图、问题二三每日最少出勤人数图、ALNS 收敛图
   - 新增正文主图：原始需求热力图、模型递进关系图、问题一逐组对比图、问题三跨组结构图、代表性覆盖图、三问最终人数对比图
   - 降级到附录：工作量 raincloud、ALNS 相空间图、算子演化图、状态转移图
2. `fig6_constraint_tightness` 判定为禁止进入正文：
   - 证据：`D:\dongbei3sheng\batch1_supplement.py` 中明确写有 `Mock up "Maximum Supply Capacity"`
   - 处理：新正文主线脚本不生成该图，后续文档中将其标记为停用
3. 正文改造策略：
   - 不继续在 `batch2_visualizations.py` 叠加图
   - 新增独立脚本 `paper_mainline_visualizations.py`
   - 新增图表目录文档 `D:\dongbei3sheng\.codex\paper-figure-plan.md`

## 编码中监控

时间：2026-05-01 16:15:00

□ 是否使用了摘要中列出的可复用组件？
✅ 是：已使用 `read_demand`、`advanced_summary.json`、`q1_video_discrepancy_audit.json`、`Q3_ALNS_Coverage`、`Q3_ALNS_WorkerSchedule`

□ 命名是否符合项目约定？
✅ 是：新增脚本命名为 `paper_mainline_visualizations.py`，图片输出命名为 `fig01_...png` 至 `fig10_...png`

□ 代码风格是否一致？
✅ 是：沿用了现有 `matplotlib + seaborn + 多函数入口` 的过程式组织方式

## 编码后声明 - 论文主线可视化重构

时间：2026-05-01 16:28:00

### 1. 复用了以下既有组件

- `read_demand`: 用于读取原始需求矩阵，位于 `D:\dongbei3sheng\large_expo_staff_scheduling_solver.py`
- `q1_video_discrepancy_audit.json`: 用于问题一下界闭合和逐组对比，位于 `D:\dongbei3sheng\q1_video_discrepancy_audit.json`
- `advanced_summary.json`: 用于问题二、三每日最少出勤与最终人数图，位于 `D:\dongbei3sheng\advanced_summary.json`
- `高级排班优化结果.xlsx`: 用于问题三覆盖明细和 ALNS 工人排班解析，位于 `D:\dongbei3sheng\高级排班优化结果.xlsx`

### 2. 遵循了以下项目约定

- 命名约定：脚本使用蛇形命名，图像使用 `fig编号_主题.png`
- 代码风格：沿用根目录绘图脚本的统一 `matplotlib` 配置和按图拆函数写法
- 文件组织：新图输出到 `D:\dongbei3sheng\visualizations\mainline`，审计文档输出到项目本地 `.codex`

### 3. 对比了以下相似实现

- `batch1_visualizations.py`：保留其“单脚本多图”的组织方式，但改为中文主线叙事
- `batch1_supplement.py`：保留问题二三每日出勤对比的核心思路，但去掉了 mock 约束紧张度图
- `batch2_visualizations.py`：未沿用其正文叙事角色，仅将其视为附录型算法图参考

### 4. 未重复造轮子的证明

- 已检查 `batch1_visualizations.py`、`batch1_supplement.py`、`batch2_visualizations.py`、`advanced_staff_scheduling_methods.py`
- 结论：仓库中不存在一套按论文论证链组织的正文主线图脚本，因此新增 `paper_mainline_visualizations.py` 属于补齐而非重复实现

## 编码前检查 - 研究建议整合与鲁棒性重构

时间：2026-05-01 16:40:00

□ 已查阅上下文摘要文件：`D:\dongbei3sheng\.codex\context-summary-研究建议整合与鲁棒性重构.md`
□ 将使用以下可复用组件：

- `D:\dongbei3sheng\q1_video_discrepancy_audit.md` - 问题一 `411.375 → 415 → 417` 证据链与口径纠偏
- `D:\dongbei3sheng\.codex\paper-advanced-model-mainline.md` - 现有论文主线与最优性表述基础
- `D:\dongbei3sheng\.codex\paper_sensitivity_analysis.py` - 现有敏感性分析脚本入口
- `D:\dongbei3sheng\independent_advanced_staff_scheduling.py` - 合法班型池、覆盖恢复、最大流与 ALNS 复用函数
- `D:\dongbei3sheng\q1_417_feasible_schedule.csv` - 问题一逐人工排班，用于恢复基准覆盖矩阵

□ 将遵循命名约定：Python 使用 `snake_case`；新增 Markdown 文档使用 `context-summary-*`、`paper-*`、`verification-report` 命名
□ 将遵循代码风格：沿用现有“标准库 → 第三方 → 项目模块”导入顺序；中文注释只说明设计意图和指标定义
□ 确认不重复造轮子，证明：已检查 `paper_sensitivity_analysis.py`、`paper-advanced-model-mainline.md`、`paper-organization-draft.md`、`independent_advanced_staff_scheduling.py`，确认现有材料尚未把 `UDR`、高峰小时扰动和随机缺勤场景整合到论文主线中，因此应在原有脚本与文档上增量扩展，而不是新建平行体系

## 决策记录 - 研究建议整合与鲁棒性重构

时间：2026-05-01 16:41:00

1. 用户提出的七类改进建议总体可行，但必须分成“可直接落入论文表述”和“需本地重算后才能写入结果”两层。
2. 直接落地项：
   - 主线改为“确定性最优 + 鲁棒性评价”
   - 算法统一命名为“合法班型池驱动的覆盖优化方法”
   - 明确区分“数学最优解”与“运营执行方案”
   - 将 ALNS 降级为修复、重构与可行性验证工具
3. 需要本地重算项：
   - `UDR`、总缺口、最大单元缺口、缺口时段数量
   - 高峰小时上浮 10% 场景
   - 随机缺勤 1% / 3% / 5% 场景
4. 文档实现策略：
   - 先扩展 `paper_sensitivity_analysis.py` 与 `paper-sensitivity-results.json`
   - 再同步修改 `paper-advanced-model-mainline.md`、`paper-organization-draft.md`、`sensitivity-paper-table.md`
   - 最后运行本地验证并回写 `verification-report.md`

## 编码中监控 - 研究建议整合与鲁棒性重构

时间：2026-05-01 16:58:00

□ 是否使用了摘要中列出的可复用组件？
✅ 是：已复用 `independent_advanced_staff_scheduling.py` 中的 `solve_problem2_network_flow`、`solve_problem3_alns`、`coverage_from_assignments`、`initial_assignments_from_flow`，并沿用 `q1_417_feasible_schedule.csv` 作为问题一基准排班来源。

□ 命名是否符合项目约定？
✅ 是：新增函数如 `build_q1_worker_contributions`、`shortage_metrics`、`simulate_absence_metrics` 均使用 `snake_case`；文档文件名继续沿用 `.codex/paper-*`、`.codex/context-summary-*` 体系。

□ 代码风格是否一致？
✅ 是：脚本延续“标准库 → 第三方库 → 项目模块”的导入顺序，中文注释聚焦设计意图和场景定义；Markdown 文档延续现有论文底稿风格。

## 编码后声明 - 研究建议整合与鲁棒性重构

时间：2026-05-01 17:02:00

### 1. 复用了以下既有组件

- `D:\dongbei3sheng\independent_advanced_staff_scheduling.py`：用于问题二、三的覆盖恢复、最大流工作日映射与 ALNS 重构。
- `D:\dongbei3sheng\q1_417_feasible_schedule.csv`：用于恢复问题一 417 人基准排班的覆盖矩阵。
- `D:\dongbei3sheng\q1_video_discrepancy_audit.md`：用于维持问题一 `411.375 → 415 → 417` 的口径一致性。
- `D:\dongbei3sheng\independent_advanced_summary.json`：用于问题二、三的基准下界与每日最少出勤序列。

### 2. 遵循了以下项目约定

- 命名约定：Python 使用 `snake_case`，Markdown 文件使用既有论文底稿命名风格。
- 代码风格：复用现有求解链，不新建平行模型；新增逻辑只围绕鲁棒性指标与场景构造展开。
- 文件组织：所有新增与更新文档均落在项目本地 `.codex/` 目录下。

### 3. 对比了以下相似实现

- `paper_sensitivity_analysis.py`：原脚本只做参数扫描，本轮扩展为“重算最少人数 + 原方案缺口评价”的双层输出。
- `paper-advanced-model-mainline.md`：原主线偏重最优性与参数扫描，本轮重写为“确定性最优 + 鲁棒性评价”主线。
- `paper-organization-draft.md`：原结构已完整，本轮主要收缩敏感性分析范围并加入运营执行边界说明。

### 4. 未重复造轮子的证明

- 检查了 `paper_sensitivity_analysis.py`、`paper-advanced-model-mainline.md`、`paper-organization-draft.md`、`independent_advanced_staff_scheduling.py`。
- 结论：现有仓库没有可直接复用的 `UDR`、随机缺勤 Monte Carlo 或“原方案在扰动下的缺口指标”输出，因此本轮扩展属于对现有分析链的必要补全，而非重复实现同类功能。

## 编码前检查 - 论文V3缺口补齐

时间：2026-05-01 17:50:00

□ 已查阅上下文摘要文件：`D:\dongbei3sheng\.codex\context-summary-论文V3缺口补齐.md`
□ 将使用以下可复用组件：

- `D:\dongbei3sheng\large_expo_staff_scheduling_solver.py` - 问题一聚合 IP、问题二/三基础覆盖模型
- `D:\dongbei3sheng\independent_advanced_staff_scheduling.py` - 问题一列生成复核、问题二最大流、问题三 ALNS 验证
- `D:\dongbei3sheng\paper_mainline_visualizations.py` - 根目录主线图脚本
- `D:\dongbei3sheng\.codex\paper_sensitivity_analysis.py` - `UDR` 与扰动场景结果来源
- `D:\dongbei3sheng\q1_video_discrepancy_audit.md` - 问题一 `411.375 -> 415 -> 417` 审计口径

□ 将遵循命名约定：Python 使用 `snake_case`；图文件使用 `fig编号_主题.png`；V3 相关文稿继续放在项目本地 `.codex\`
□ 将遵循代码风格：沿用现有 `matplotlib + seaborn + 过程式函数` 绘图结构，文稿采用学术论文风格中文表述
□ 确认不重复造轮子，证明：已检查 `paper_mainline_visualizations.py`、`.codex\paper_sensitivity_analysis.py`、`batch1_visualizations.py`、`batch2_visualizations.py`、`.codex\academic_visualizations\generate_academic_visualizations.py`，确认缺失点主要是 V3 证据编排层，而非基础算法本体

## 决策记录 - 论文V3缺口补齐

时间：2026-05-01 17:52:00

1. 本轮不重写求解器，优先复用现有基础模型、独立高级验证链和敏感性脚本。
2. 问题一论文口径改为“聚合 IP 主求解 + 列生成复核与扩展框架”，避免与用户最新修正冲突。
3. 主线图改造目标不是增加花哨图，而是让仓库图号和用户当前 V3 图表目录一致。
4. 待命池建议必须降强度，只能写成“15–20 人初始管理方案，后续结合历史缺勤率或分位数仿真校准”。

## 编码中监控 - 论文V3缺口补齐

时间：2026-05-01 18:18:00

□ 是否使用了摘要中列出的可复用组件？
✅ 是：已复用 `read_demand`、`build_shift_pairs`、`advanced_summary.json`、`q1_video_discrepancy_audit.json`、`.codex\paper-sensitivity-results.json`、`independent_advanced_summary.json`

□ 命名是否符合项目约定？
✅ 是：主线图输出统一为 `fig01` 至 `fig11`；新增文稿和报告均位于 `.codex\`

□ 代码风格是否一致？
✅ 是：图脚本沿用 `matplotlib + seaborn + 过程式函数` 结构，文稿与报告采用学术化中文表达

## 编码后声明 - 论文V3缺口补齐

时间：2026-05-01 18:20:00

### 1. 复用了以下既有组件

- `D:\dongbei3sheng\large_expo_staff_scheduling_solver.py`：用于需求读取、模板生成和问题三 13 类时间模板示意。
- `D:\dongbei3sheng\advanced_summary.json`：用于问题二每日出勤图与问题三结果摘要。
- `D:\dongbei3sheng\q1_video_discrepancy_audit.json`：用于问题一下界闭合图和逐组对比图。
- `D:\dongbei3sheng\.codex\paper-sensitivity-results.json`：用于图11 的 `UDR` 场景数据。

### 2. 遵循了以下项目约定

- 命名约定：Python 使用 `snake_case`，图文件采用 `fig编号_主题.png`
- 文件组织：主线图仍输出到 `D:\dongbei3sheng\visualizations\mainline`，论文底稿与验证文档放在项目本地 `.codex\`
- 代码风格：不重建并行模型，只在既有求解链之上补齐 V3 证据资产

### 3. 对比了以下相似实现

- `paper_mainline_visualizations.py`：在原有 10 图主线基础上补成 11 图 V3 结构
- `.codex\paper_sensitivity_analysis.py`：不重写扰动求解，只复用其结果做主线 `UDR` 图
- `.codex\academic_visualizations\generate_academic_visualizations.py`：参考其敏感性表达方式，但未直接搬运其图号体系

### 4. 未重复造轮子的证明

- 已检查 `batch1_visualizations.py`、`batch2_visualizations.py`、`paper_mainline_visualizations.py`、`.codex\academic_visualizations\generate_academic_visualizations.py`
- 结论：本轮新增的是 V3 缺失的主线图、文稿同步和验证约束，不是对已有算法的重复实现

## 编码前检查 - 旧版资产清理与GitHub同步

时间：2026-05-01 19:05:00

□ 已查阅上下文摘要文件：`D:\dongbei3sheng\.codex\context-summary-论文V3缺口补齐.md`
□ 将使用以下可复用组件：

- `D:\dongbei3sheng\.codex\paper-v3-gap-report.md` - 明确区分 V3 保留资产与被替代资产
- `D:\dongbei3sheng\.codex\paper-figure-plan.md` - 判断哪些图保留为主文或附录，哪些旧图删除
- `D:\dongbei3sheng\.codex\paper-advanced-model-mainline.md` - 确认当前保留的论文主线口径
- `D:\dongbei3sheng\.codex\verify_paper_mainline.py` - 清理后的本地一致性验证入口

□ 将遵循命名约定：不新建平行资源目录；保留当前 V3 命名体系 `fig01` 至 `fig11`
□ 将遵循代码风格：本轮不改求解器，只做资产治理、留痕和验证
□ 确认不重复造轮子，证明：旧版 batch 图脚本和旧图已被 V3 主线图与 `.codex` 中的 V3 文稿完全替代

## 决策记录 - 旧版资产清理与GitHub同步

时间：2026-05-01 19:08:00

1. 删除根目录旧版可视化脚本：`batch1_visualizations.py`、`batch1_supplement.py`、`batch2_visualizations.py`。
2. 删除被 V3 替代的旧图：
   - 根目录旧主线图：`visualizations/fig1_lb_audit_waterfall.png`、`fig2_lb_vs_feasible_dumbbell.png`、`fig3_q1_schedule_heatmap.png`、`fig5_daily_bottleneck_area.png`、`fig6_constraint_tightness.png`
   - mainline 过渡图号：`fig06_q2_daily_staffing.png`、`fig07_q3_daily_staffing.png`、`fig08_q3_cross_group_usage.png`、`fig09_representative_coverage.png`
3. 保留附录图：`fig5_alns_convergence.png`、`fig7_operator_evolution.png`、`fig8_workload_raincloud.png`、`fig9_shift_transition.png`、`fig10_alns_phase_space.png`
4. 本地残留说明：
   - `D:\dongbei3sheng\.codex\gemini-core-files-manifest.md` 受 ACL 限制，未能在当前权限下删除
   - `D:\dongbei3sheng\下面给出一版重新_2026-05-01-17-12-48.docx` 被 Word 占用，未纳入 Git，不影响 GitHub 同步
## 编码前检查 - 增强图布局修复

时间：2026-05-01 19:34:18

□ 已查阅上下文摘要文件：`D:\dongbei3sheng\.codex\context-summary-增强图布局修复.md`
□ 将使用以下可复用组件：
- `D:\dongbei3sheng\enhanced_visualizations.py::save` - 统一导出入口，用于局部控制 `bbox_inches`
- `D:\dongbei3sheng\enhanced_visualizations.py::spine_clean` - 统一坐标轴边框样式
- `D:\dongbei3sheng\paper_mainline_visualizations.py` - 作为更保守布局的参考实现
□ 将遵循命名约定：Python 使用 `snake_case`；输出文件继续沿用 `fig编号_主题.png`
□ 将遵循代码风格：保持一图一函数的过程式绘图结构，不新增独立脚本，不手工改 PNG
□ 确认不重复造轮子，证明：已检查 `enhanced_visualizations.py`、`paper_mainline_visualizations.py` 以及现有增强版输出目录，确认问题属于现有布局实现缺陷，应在统一脚本内修复

## 决策记录 - 增强图布局修复

时间：2026-05-01 19:34:18

1. 本轮只修明确存在重叠的 `fig03`、`fig04`、`fig14`，其余图片先保持不动，避免过度修改。
2. 根因优先级排序为：局部元素布局失衡 > 全局 `bbox=tight` 对复杂图的放大效应 > 画布尺寸不足。
3. 导出函数将改为支持按图覆盖 `bbox_inches`，从而对复杂图关闭紧边界裁切，对普通图保持原有输出风格。
## 编码中监控 - 增强图布局修复

时间：2026-05-01 19:46:16

□ 是否使用了摘要中列出的可复用组件？
✅ 是：沿用 `save()` 统一导出入口，并继续使用 `spine_clean()`、既有色板 `C`、既有一图一函数结构

□ 命名是否符合项目约定？
✅ 是：未改动图片命名规则；新增参数名使用 `bbox_inches`、`pad_inches` 等 Matplotlib 既有术语

□ 代码风格是否一致？
✅ 是：仍然在 `enhanced_visualizations.py` 内做局部函数修复，没有拆出新模块，也没有手工改图

## 编码后声明 - 增强图布局修复

时间：2026-05-01 19:46:16

### 1. 复用了以下既有组件

- `D:\dongbei3sheng\enhanced_visualizations.py::save`：扩展为支持局部覆盖 `bbox_inches`，继续作为统一导出入口
- `D:\dongbei3sheng\enhanced_visualizations.py::spine_clean`：维持现有坐标轴清理风格
- `D:\dongbei3sheng\paper_mainline_visualizations.py`：作为保守布局的对照参考

### 2. 遵循了以下项目约定

- 命名约定：输出文件仍为 `fig03_model_progression.png`、`fig04_q1_waterfall.png`、`fig14_demand_3d_surface.png`
- 代码风格：保持过程式绘图函数组织，不新增旁路脚本，不在 PNG 上做手工修补
- 文件组织：所有留痕继续写入项目本地 `.codex\`

### 3. 对比了以下相似实现

- `enhanced_visualizations.py:188-240`：保留原卡片式表达，只把底部标签宽度收回卡片内部
- `enhanced_visualizations.py:242-290`：保留瀑布图主结构，只下调说明框并放宽顶部留白
- `paper_mainline_visualizations.py` 对应主线图：借鉴其“更少外置元素、更克制标题层级”的布局策略

### 4. 未重复造轮子的证明

- 已检查 `enhanced_visualizations.py` 与 `paper_mainline_visualizations.py`，确认问题来自现有布局参数和导出边界，而不是缺失绘图能力
- 本轮没有引入新绘图库、没有创建替代脚本、没有手工编辑成品图像

### 5. 本地验证结果

- 执行：`$env:PYTHONIOENCODING='utf-8'; python D:\dongbei3sheng\enhanced_visualizations.py`
- 结果：脚本完整生成 20 张增强版图，`fig03`、`fig04`、`fig14` 已复核通过
- 备注：Windows 默认 `gbk` 控制台下，原脚本的 `✓` 打印会触发 `UnicodeEncodeError`；设置 `PYTHONIOENCODING='utf-8'` 后不影响本地自动验证
## 决策记录 - 增强图布局修复（第二轮）

时间：2026-05-01 20:34:11

1. 根据用户第二轮反馈，将修复范围扩展到 `fig01`、`fig04`、`fig05`、`fig06`、`fig07`、`fig10`、`fig13`、`fig17`、`fig20`。
2. 本轮优先处理“标题/图例/图注与图元竞争同一块上边距”的共性问题，策略是增加顶部留白、把图例提升为 `figure` 级元素，或将说明框迁移到图内空白区。
3. `fig04` 的中间两段增量因为数值太小，在全局坐标下不具备可见瀑布形态，因此补充了增量放大视窗，而不是篡改真实数值高度。

## 编码后声明 - 增强图布局修复（第二轮）

时间：2026-05-01 20:34:11

### 1. 新增修复点

- `fig01_total_demand_heatmap.png`：将时间轴标签移到底部柱图，避免与“时总量”数值重叠
- `fig04_q1_waterfall.png`：加入增量放大视窗，明确显示“取整”“补差”的瀑布细节
- `fig05_q1_group_comparison.png`：将图例提升为 `figure` 级并置于标题上方
- `fig06_maxflow_topology.png`：扩大画布和坐标边界，将底部图注改为 `figure` 级文本，消除裁切
- `fig07_q2_daily_staffing.png`：信息框下移并将公式改为 `ceil(...)` 文本，避免渲染与遮挡
- `fig10_final_worker_comparison.png`：分离累计节约说明与箭头区域
- `fig13_alns_convergence_temperature.png`：最终值注释移出曲线并加白底框
- `fig17_three_question_radar.png`：继续上提标题并压缩方向标签字号
- `fig20_sensitivity_scenario_comparison.png`：图例提升为 `figure` 级并置于标题上方

### 2. 本地验证

- 再次执行：`$env:PYTHONIOENCODING='utf-8'; python D:\dongbei3sheng\enhanced_visualizations.py`
- 结果：20 张增强图全部重新生成成功
- 复核：上述 9 张图均完成多模态检查，未再发现用户点名的重叠位置
