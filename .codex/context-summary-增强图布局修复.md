## 项目上下文摘要（增强图布局修复）

生成时间：2026-05-01 19:34:18

### 1. 相似实现分析

- **实现1**: `enhanced_visualizations.py:61-89`
  - 模式：统一 `matplotlib` 全局样式 + `save()` 导出封装。
  - 可复用：`save()`、`spine_clean()`、统一色板 `C`。
  - 需注意：全局 `savefig.bbox = "tight"` 会把标题、图例、说明框、色条都纳入裁剪边界，复杂图更容易出现布局拥挤。

- **实现2**: `enhanced_visualizations.py:188-290`
  - 模式：主线图使用卡片式排版、说明框、折线标注等装饰性元素。
  - 可复用：`FancyBboxPatch` 卡片绘制、统一标题与标注风格。
  - 需注意：`A03_model_progression` 的底部标签条宽度超过卡片宽度；`A04_q1_waterfall` 的标题、说明框和柱顶标注都集中在上沿区域。

- **实现3**: `enhanced_visualizations.py:573-810`
  - 模式：新增图覆盖多子图、双轴、三维图、极坐标和复合图。
  - 可复用：`B12_column_generation_progress` 的多子图组织方式、`B13` 的双轴结构、`B18` 的复合图结构。
  - 需注意：`B14_three_dimension_demand_surface` 同时有 3D 轴标签、刻度和色条，属于最容易发生文字挤压的布局类型。

- **实现4**: `paper_mainline_visualizations.py:336-520`
  - 模式：主线图的保守版实现，装饰元素更少，标题字号和边距更克制。
  - 可复用：保守标题层级、较简洁的说明文本放置方式。
  - 需注意：增强版修复时应尽量向该模式靠拢，而不是继续增加额外装饰层。

### 2. 项目约定

- **命名约定**：Python 使用 `snake_case`；图片输出使用 `fig编号_主题.png`。
- **文件组织**：增强版图片统一输出到 `visualizations/enhanced/`；过程文档与验证留痕写入项目本地 `.codex/`。
- **导入顺序**：标准库 → 第三方库 → 项目内模块。
- **代码风格**：过程式绘图函数，一图一函数，统一调用 `save()` 收尾。

### 3. 可复用组件清单

- `enhanced_visualizations.py::save`：统一导出入口，本次优先在这里增加可选边界框控制。
- `enhanced_visualizations.py::spine_clean`：统一坐标轴边框样式。
- `paper_mainline_visualizations.py`：主线图较保守布局的参考实现。

### 4. 多模态巡检结果

- **明确存在问题**
  - `fig03_model_progression.png`：底部人数标签条横向跨出卡片，彼此覆盖，且弱化了卡片分区。
  - `fig04_q1_waterfall.png`：标题、说明框、折线和柱顶标注堆叠在上方狭窄区域，存在明显遮挡。
  - `fig14_demand_3d_surface.png`：左下角 x 轴标题与刻度过近，右侧 z 轴标题与色条标签重复并拥挤。

- **有轻微拥挤风险但暂不列为主问题**
  - `fig08_q3_template_patterns.png`
  - `fig12_q1_column_generation_progress.png`
  - `fig17_three_question_radar.png`
  - `fig18_rest_day_spacing.png`

### 5. 依赖和集成点

- **外部依赖**：`matplotlib`、`seaborn`、`numpy`、`pandas`。
- **内部依赖**：`large_expo_staff_scheduling_solver.py` 提供需求读入和班型模板构造。
- **配置来源**：全局 `mpl.rcParams` 位于 `enhanced_visualizations.py:61-80`。
- **输出入口**：`main()` 会串行生成全部 20 张增强版图片。

### 6. 技术选型理由

- 优先修脚本而不是手工改图：可重复、可审计、便于后续重新生成。
- 优先局部覆盖 `bbox_inches`：问题集中在少数复杂图，没必要粗暴取消全局所有图的紧边界导出。
- 对复杂图使用更保守的标题字号、边距和说明框布局：与仓库内主线图风格更一致，也更稳定。

### 7. 测试策略

- **执行方式**：运行 `python D:\dongbei3sheng\enhanced_visualizations.py` 重新生成全部 20 张图。
- **重点复核**：`fig03`、`fig04`、`fig14` 逐张多模态检查。
- **补充检查**：确认 `fig08`、`fig12`、`fig17`、`fig18` 未因导出参数变化引入新裁切或新重叠。

### 8. 关键风险点

- 修改 `save()` 影响范围较广，必须保证默认行为保持兼容。
- 三维图使用 `constrained_layout` 与色条时，需避免新的裁切或轴标签被挤出。
- 如果说明框和标题仍共用顶部空间，`fig04` 容易在高 DPI 导出时再次拥挤。
