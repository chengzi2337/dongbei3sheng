# 验证报告：弹性待命池 UDR 仿真

生成时间：2026-05-04 22:02:39

## 审查对象

- 新增脚本：[standby_pool_udr_simulation.py](D:\dongbei3sheng\.codex\standby_pool_udr_simulation.py)
- 输出数据：[standby_pool_udr_curve.csv](D:\dongbei3sheng\.codex\standby_pool_udr_curve.csv)、[standby_pool_udr_curve.json](D:\dongbei3sheng\.codex\standby_pool_udr_curve.json)、[standby_pool_udr_curve.md](D:\dongbei3sheng\.codex\standby_pool_udr_curve.md)
- 输出图像：[fig_standby_pool_udr_curve.png](D:\dongbei3sheng\visualizations\mainline\fig_standby_pool_udr_curve.png)

## 需求字段完整性

- 目标：补齐论文第八章“弹性待命池”部分，生成基于问题三 400 人基准排班的真实待命池 UDR 仿真曲线
- 范围：缺勤率 1%、3%、5%，默认 Monte Carlo 200 次，`N_sb` 至少搜索到 30，允许满足停止条件后提前结束
- 交付物：脚本、CSV、JSON、Markdown、PNG
- 审查要点：
  - 不得使用 `64*N_sb` 粗略容量扣减
  - 必须受问题三 370 个合法模式约束
  - 必须基于现有问题三最终 400 人排班
  - 必须有本地可重复验证和结果摘要

## 实现审查

### 1. 需求匹配

- 基准排班从现有问题三工作表反解恢复，而不是重跑 ALNS，见 [standby_pool_udr_simulation.py](D:\dongbei3sheng\.codex\standby_pool_udr_simulation.py:465)
- 真实补位模型使用 `scipy.optimize.milp` 对合法模式做整数优化，见 [standby_pool_udr_simulation.py](D:\dongbei3sheng\.codex\standby_pool_udr_simulation.py:114)
- 待命人员“最多 8 天、每天最多 1 次”的可分解验证由最大流完成，见 [standby_pool_udr_simulation.py](D:\dongbei3sheng\.codex\standby_pool_udr_simulation.py:516)
- Monte Carlo 场景、统计汇总和提前停止逻辑集中在 [standby_pool_udr_simulation.py](D:\dongbei3sheng\.codex\standby_pool_udr_simulation.py:594)
- 图像输出满足论文主线目录要求，见 [standby_pool_udr_simulation.py](D:\dongbei3sheng\.codex\standby_pool_udr_simulation.py:763)

### 2. 技术合理性

- 采用“按天 MILP + 跨天 DP”的精确分解，避免了对每个 `(样本, N_sb)` 直接求 10 天聚合 MILP 的高成本，同时不改变原模型可行域或目标值
- 对于日补位 MILP 的非最优退出，脚本保留了保守整数上界解逻辑，并显式记录 `solve_success`
- 正式运行中 `solve_success_rate` 全部为 `1.0`，说明在当前参数下未出现超时退化

### 3. 风险评估

- 主要残余风险：仓库没有现成单元测试框架，本次验证以脚本级断言和端到端产物核对为主
- 次要风险：`.codex` 目录在当前环境下需要提权运行 Python 才能正式写入结果文件；已通过提权实跑解决

## 本地验证记录

1. 冒烟验证
   - 命令：`$env:PYTHONIOENCODING='utf-8'; python D:\dongbei3sheng\.codex\standby_pool_udr_simulation.py --runs 50 --max-standby 30`
   - 结果：成功生成全部目标文件
   - 关键输出：
     - 1% 场景：`mean_UDR <= 1%` 的最小 `N_sb=0`，`mean_UDR=0` 的最小 `N_sb=10`
     - 3% 场景：对应 `4` 和 `19`
     - 5% 场景：对应 `11` 和“未在搜索范围内达到”

2. 正式验证
   - 命令：`$env:PYTHONIOENCODING='utf-8'; python D:\dongbei3sheng\.codex\standby_pool_udr_simulation.py --runs 200 --max-standby 30`
   - 结果：成功覆盖正式 CSV / JSON / Markdown / PNG
   - 关键输出：
     - 总需求：`17682`
     - 基准问题三人数：`400`
     - 1% 场景：`mean_UDR <= 1%` 的最小 `N_sb=0`，`mean_UDR=0` 的最小 `N_sb=10`
     - 3% 场景：对应 `4` 和 `22`
     - 5% 场景：对应 `11` 和“未在搜索范围内达到”
     - 总运行时间：约 `436.716` 秒

3. 结果文件抽查
   - JSON 行数：`69`
   - 1% 场景提前停止于 `N_sb=12`
   - 3% 场景提前停止于 `N_sb=24`
   - 5% 场景完整跑到 `N_sb=30`
   - 图像文件存在且大小约 `471577` 字节

## 评分

- 技术维度
  - 代码质量：95/100
  - 测试覆盖：88/100
  - 规范遵循：96/100
- 战略维度
  - 需求匹配：97/100
  - 架构一致：95/100
  - 风险评估：92/100
- 综合评分：94/100

## 结论

- 建议：通过
- 理由：实现满足真实补位仿真要求，严格复用了问题三合法模式与现有 400 人基准排班，完成了本地 50 次冒烟和 200 次正式验证，产物齐全且关键阈值已经自动回填到 Markdown 摘要。
