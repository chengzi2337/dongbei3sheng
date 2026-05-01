from __future__ import annotations

import json
from pathlib import Path

import matplotlib
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = Path(__file__).resolve().parent
SUMMARY_PATH = ROOT / "independent_advanced_summary.json"
SENSITIVITY_PATH = ROOT / ".codex" / "paper-sensitivity-results.json"
CONVERGENCE_PATH = ROOT / "independent_q3_alns_convergence.csv"
WORKBOOK_PATH = next(ROOT.glob("independent_*.xlsx"))
Q1_AUDIT_PATH = ROOT / "q1_video_discrepancy_audit.json"


COLORS = {
    "blue": "#2F5D8C",
    "blue_light": "#8FB3D9",
    "green": "#3B7D5C",
    "green_light": "#9CC9A4",
    "orange": "#C97832",
    "red": "#B8514A",
    "purple": "#6B5C9A",
    "gray": "#4D5562",
    "gray_light": "#D8DEE8",
    "paper": "#FBFBF8",
    "ink": "#1F2933",
}


FIGURES: list[dict[str, str]] = []


def setup_style() -> None:
    font_candidates = [
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simhei.ttf",
        "C:/Windows/Fonts/simsun.ttc",
        "C:/Windows/Fonts/Deng.ttf",
    ]
    for font_path in font_candidates:
        if Path(font_path).exists():
            fm.fontManager.addfont(font_path)
            font_name = fm.FontProperties(fname=font_path).get_name()
            break
    else:
        font_name = "DejaVu Sans"

    matplotlib.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": [font_name, "DejaVu Sans"],
            "axes.unicode_minus": False,
            "figure.dpi": 120,
            "savefig.dpi": 300,
            "figure.facecolor": COLORS["paper"],
            "axes.facecolor": COLORS["paper"],
            "axes.edgecolor": "#9AA3AF",
            "axes.labelcolor": COLORS["ink"],
            "xtick.color": COLORS["gray"],
            "ytick.color": COLORS["gray"],
            "text.color": COLORS["ink"],
            "axes.titleweight": "bold",
            "axes.titlesize": 13,
            "axes.titlepad": 10,
            "axes.labelsize": 10.5,
            "legend.frameon": False,
            "grid.color": "#D6DBE2",
            "grid.linewidth": 0.7,
            "grid.alpha": 0.75,
            "svg.fonttype": "none",
        }
    )


def load_data() -> dict[str, object]:
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    sensitivity = json.loads(SENSITIVITY_PATH.read_text(encoding="utf-8"))
    q1_audit = json.loads(Q1_AUDIT_PATH.read_text(encoding="utf-8"))
    convergence = pd.read_csv(CONVERGENCE_PATH)
    coverage = pd.read_excel(WORKBOOK_PATH, sheet_name="Q3_ALNS_Coverage")
    schedule = pd.read_excel(WORKBOOK_PATH, sheet_name="Q3_ALNS_WorkerSchedule")
    return {
        "summary": summary,
        "sensitivity": sensitivity,
        "q1_audit": q1_audit,
        "convergence": convergence,
        "coverage": coverage,
        "schedule": schedule,
    }


def save_figure(fig: plt.Figure, stem: str, title: str, chapter: str) -> None:
    png = OUT_DIR / f"{stem}.png"
    svg = OUT_DIR / f"{stem}.svg"
    fig.savefig(png, bbox_inches="tight", facecolor=fig.get_facecolor())
    fig.savefig(svg, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    FIGURES.append({"stem": stem, "png": str(png), "svg": str(svg), "title": title, "chapter": chapter})


def add_caption(fig: plt.Figure, text: str) -> None:
    fig.text(0.01, -0.035, text, ha="left", va="top", fontsize=8.5, color=COLORS["gray"])


def annotate_bars(ax: plt.Axes, bars, fmt: str = "{:.0f}", dy: float = 2) -> None:
    for bar in bars:
        value = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value + dy,
            fmt.format(value),
            ha="center",
            va="bottom",
            fontsize=9,
            color=COLORS["ink"],
        )


def group_sort_key(label: object) -> tuple[int, str]:
    text = str(label)
    digits = "".join(ch for ch in text if ch.isdigit())
    return (int(digits) if digits else 10_000, text)


def figure_model_framework() -> None:
    fig, ax = plt.subplots(figsize=(13.5, 5.2), layout="constrained")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    boxes = [
        ("原始需求张量\n附件1.xlsx\n10天 × 10组 × 11小时", 0.03, 0.58, 0.17, 0.22, COLORS["gray_light"]),
        ("问题一\n固定小组服务\n列生成 + 整数恢复\n417人", 0.29, 0.62, 0.18, 0.25, "#E7EEF7"),
        ("问题二\n跨日可换组\n单日下界 + 最大流\n406人 = 下界", 0.54, 0.62, 0.18, 0.25, "#E8F2EC"),
        ("问题三\n日内双组服务\n下界 + 最大流 + ALNS\n400人 = 下界", 0.79, 0.62, 0.18, 0.25, "#F7EDE2"),
        ("可复现验证\n覆盖缺口=0\n每人工作8天\n独立链路审计通过", 0.38, 0.14, 0.24, 0.22, "#EFEAF7"),
    ]

    for text, x, y, w, h, color in boxes:
        rect = FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0.018,rounding_size=0.018",
            facecolor=color,
            edgecolor="#5C6674",
            linewidth=1.2,
        )
        ax.add_patch(rect)
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=11, linespacing=1.45)

    arrow_pairs = [
        ((0.20, 0.69), (0.29, 0.74)),
        ((0.47, 0.74), (0.54, 0.74)),
        ((0.72, 0.74), (0.79, 0.74)),
        ((0.38, 0.62), (0.45, 0.36)),
        ((0.63, 0.62), (0.52, 0.36)),
        ((0.88, 0.62), (0.62, 0.32)),
    ]
    for start, end in arrow_pairs:
        arrow = FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=16, linewidth=1.2, color=COLORS["gray"])
        ax.add_patch(arrow)

    ax.text(0.5, 0.95, "独立高级模型求解链路与论文证据闭环", ha="center", fontsize=15, fontweight="bold")
    ax.text(0.5, 0.48, "流动约束逐步放宽：固定小组 → 跨日换组 → 日内双组", ha="center", fontsize=11, color=COLORS["gray"])
    add_caption(fig, "数据来源：independent_advanced_summary.json；图中人数均由独立高级脚本重新求解得到。")
    save_figure(fig, "fig01_model_framework", "独立高级模型求解链路与论文证据闭环", "论文总主线")


def figure_optimality_evidence(summary: dict[str, object], q1_audit: dict[str, object]) -> None:
    items = summary["summary"]
    labels = ["问题一  固定小组", "问题二  跨日换组", "问题三  日内双组"]
    feasible = np.array([int(row["独立求解人数"]) for row in items], dtype=float)
    reference = np.array(
        [
            float(q1_audit["total_ceil_lp_bound"]),
            float(items[1]["理论下界"]),
            float(items[2]["理论下界"]),
        ]
    )
    evidence_text = ["LP取整下界", "理论下界", "理论下界"]
    y = np.arange(len(labels))[::-1]

    fig, ax = plt.subplots(figsize=(10.4, 5.2), layout="constrained")
    for idx, yi in enumerate(y):
        ax.hlines(yi, reference[idx], feasible[idx], color=COLORS["gray_light"], linewidth=6, zorder=1)
        ax.scatter(reference[idx], yi, s=210, marker="D", color=COLORS["red"], edgecolor="white", linewidth=1.3, zorder=3)
        ax.scatter(feasible[idx], yi, s=170, marker="o", color=[COLORS["blue"], COLORS["green"], COLORS["orange"]][idx], zorder=4)
        ax.text(reference[idx] - 0.4, yi + 0.16, f"{int(reference[idx])}", ha="right", va="bottom", fontsize=9.5, color=COLORS["red"])
        ax.text(feasible[idx] + 0.4, yi + 0.16, f"{int(feasible[idx])}", ha="left", va="bottom", fontsize=10.5, color=COLORS["ink"], fontweight="bold")
        if idx == 0:
            ax.text((reference[idx] + feasible[idx]) / 2, yi - 0.22, "整数恢复较 LP 取整高 2 人", ha="center", fontsize=9, color=COLORS["gray"])
        else:
            ax.text((reference[idx] + feasible[idx]) / 2, yi - 0.22, "下界 = 可行解", ha="center", fontsize=9, color=COLORS["gray"])
        ax.text(reference[idx] - 1.0, yi - 0.22, evidence_text[idx], ha="right", fontsize=8.8, color=COLORS["gray"])
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.set_xlim(398, 419)
    ax.set_xlabel("招聘人数")
    ax.set_title("三问招聘人数与下界/恢复证据对比")
    ax.grid(axis="x")
    ax.spines["left"].set_visible(False)
    ax.scatter([], [], s=210, marker="D", color=COLORS["red"], label="下界或 LP 取整下界")
    ax.scatter([], [], s=170, marker="o", color=COLORS["blue"], label="最终可行解人数")
    ax.legend(loc="lower right")
    add_caption(fig, "问题二与问题三由“理论下界 = 可行解”证明人数目标最优；问题一展示 LP 取整下界 415 与整数恢复 417 的差异。")
    save_figure(fig, "fig02_optimality_evidence", "三问招聘人数与下界/恢复证据对比", "结果总览")


def figure_q1_column_generation(summary: dict[str, object]) -> None:
    df = pd.DataFrame(summary["q1_column_generation"])
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.2), layout="constrained")

    x = df["group_index"].to_numpy()
    axes[0].bar(x - 0.18, df["exact_workers"], width=0.36, label="精确人数", color=COLORS["blue"])
    axes[0].bar(x + 0.18, df["integer_workers"], width=0.36, label="列生成整数人数", color=COLORS["blue_light"])
    axes[0].set_title("问题一各小组人数恢复结果")
    axes[0].set_xlabel("小组编号")
    axes[0].set_ylabel("人数")
    axes[0].set_xticks(x)
    axes[0].grid(axis="y")
    axes[0].legend()

    axes[1].plot(x, df["columns"], marker="o", color=COLORS["purple"], linewidth=2.2, label="最终列池规模")
    axes[1].bar(x, df["generated_columns"], color=COLORS["orange"], alpha=0.75, label="新增列数")
    axes[1].set_title("列池规模与动态生成强度")
    axes[1].set_xlabel("小组编号")
    axes[1].set_ylabel("列数量")
    axes[1].set_xticks(x)
    axes[1].grid(axis="y")
    axes[1].legend()

    add_caption(fig, "各组整数主问题人工松弛均为0，说明列生成恢复结果满足时空覆盖约束。")
    save_figure(fig, "fig03_q1_column_generation", "问题一列生成规模与整数恢复结果", "问题一")


def figure_daily_attendance(summary: dict[str, object]) -> None:
    days = np.arange(1, 11)
    q2_min = np.array(summary["q2_day_minima"])
    q2_count = np.array(summary["q2_daily_counts"])
    q3_min = np.array(summary["q3_day_minima"])
    q3_count = np.array(summary["q3_daily_counts_alns"])

    fig, axes = plt.subplots(2, 1, figsize=(12.5, 7.2), sharex=True, layout="constrained")
    for ax, title, minima, arranged, color in [
        (axes[0], "问题二：每日最少出勤与最大流安排", q2_min, q2_count, COLORS["green"]),
        (axes[1], "问题三：异构任务下每日最少出勤与ALNS安排", q3_min, q3_count, COLORS["orange"]),
    ]:
        ax.plot(days, minima, marker="o", color=color, linewidth=2.2, label="单日最少出勤")
        ax.bar(days, arranged, color=color, alpha=0.24, label="最终安排出勤")
        ax.fill_between(days, minima, arranged, color=color, alpha=0.15)
        ax.set_title(title)
        ax.set_ylabel("出勤人次")
        ax.set_xticks(days)
        ax.grid(axis="y")
        ax.legend(loc="upper left", ncol=2)
        for d, m, a in zip(days, minima, arranged):
            if a > m:
                ax.text(d, a + 2, f"+{a-m}", ha="center", fontsize=9, color=COLORS["red"])
    axes[1].set_xlabel("日期")
    add_caption(fig, "问题二因3247不能被8整除出现1个额外人次；问题三因3198不能被8整除出现2个额外人次。")
    save_figure(fig, "fig04_daily_attendance", "问题二与问题三每日出勤结构对比", "问题二与问题三")


def figure_q3_coverage_heatmap(coverage: pd.DataFrame) -> None:
    pivot = coverage.pivot_table(index="小组", columns="天", values="冗余", aggfunc="sum")
    pivot = pivot.loc[sorted(pivot.index, key=group_sort_key), sorted(pivot.columns)]
    fig, ax = plt.subplots(figsize=(10.8, 6.2), layout="constrained")
    im = ax.imshow(pivot.to_numpy(), cmap="YlGnBu", aspect="auto")
    ax.set_title("问题三覆盖冗余热力图（按小组-日期聚合）")
    ax.set_xlabel("日期")
    ax.set_ylabel("小组")
    ax.set_xticks(np.arange(len(pivot.columns)))
    ax.set_xticklabels([f"第{c}天" for c in pivot.columns], rotation=0)
    ax.set_yticks(np.arange(len(pivot.index)))
    ax.set_yticklabels(pivot.index)
    for i in range(pivot.shape[0]):
        for j in range(pivot.shape[1]):
            value = int(pivot.iloc[i, j])
            color = "white" if value > np.nanmax(pivot.to_numpy()) * 0.55 else COLORS["ink"]
            ax.text(j, i, str(value), ha="center", va="center", fontsize=8, color=color)
    cbar = fig.colorbar(im, ax=ax, shrink=0.82)
    cbar.set_label("覆盖冗余人时")
    add_caption(fig, "覆盖缺口总和为0；热力图只展示冗余在日期和小组维度上的分布，用于解释可行排班的剩余覆盖结构。")
    save_figure(fig, "fig05_q3_coverage_heatmap", "问题三覆盖冗余热力图", "问题三")


def figure_worker_schedule_matrix(schedule: pd.DataFrame) -> None:
    day_cols = [col for col in schedule.columns if str(col).startswith("第")]
    subset = schedule.head(80).copy()
    matrix = (subset[day_cols] != "休息").astype(int).to_numpy()
    fig, ax = plt.subplots(figsize=(10.5, 7.0), layout="constrained")
    im = ax.imshow(matrix, aspect="auto", cmap=matplotlib.colors.ListedColormap(["#F1F3F5", COLORS["blue"]]))
    ax.set_title("问题三前80名员工工作日矩阵示例")
    ax.set_xlabel("日期")
    ax.set_ylabel("员工序号")
    ax.set_xticks(np.arange(len(day_cols)))
    ax.set_xticklabels(day_cols)
    ax.set_yticks(np.arange(0, len(subset), 10))
    ax.set_yticklabels([str(i + 1) for i in range(0, len(subset), 10)])
    ax.text(0.99, -0.08, "深色=工作，浅色=休息", transform=ax.transAxes, ha="right", fontsize=9, color=COLORS["gray"])
    add_caption(fig, "完整排班表含400名员工；此图展示前80名员工，每行均对应8个工作日和2个休息日的结构。")
    save_figure(fig, "fig06_worker_schedule_matrix", "问题三员工工作日矩阵示例", "问题三附录")


def figure_alns_convergence(summary: dict[str, object], convergence: pd.DataFrame) -> None:
    weights = summary["q3_operator_weights"]
    fig, axes = plt.subplots(1, 2, figsize=(13.2, 5.2), layout="constrained")
    baseline = float(convergence["best_score"].min())
    current_delta = (convergence["current_score"] - baseline) * 1000
    best_delta = (convergence["best_score"] - baseline) * 1000
    accepted_mask = convergence["accepted"].astype(bool)
    axes[0].plot(convergence["iteration"], current_delta, color=COLORS["gray"], linewidth=1.7, label="当前解相对最优差值")
    axes[0].plot(convergence["iteration"], best_delta, color=COLORS["red"], linewidth=2.3, label="历史最优差值")
    axes[0].scatter(
        convergence.loc[accepted_mask, "iteration"],
        current_delta.loc[accepted_mask],
        s=28,
        color=COLORS["purple"],
        alpha=0.8,
        label="接受更新",
        zorder=4,
    )
    axes[0].axhline(0, color=COLORS["blue"], linewidth=1.2, linestyle="--", alpha=0.8)
    axes[0].set_title("ALNS收敛轨迹（相对最优差值）")
    axes[0].set_xlabel("迭代次数")
    axes[0].set_ylabel("相对历史最优差值 x 10^-3")
    axes[0].grid(True)
    axes[0].legend()

    labels = [label.replace("destroy_", "D:").replace("repair_", "R:").replace("_", "\n") for label in weights]
    values = list(weights.values())
    y = np.arange(len(labels))
    axes[1].barh(y, values, color=[COLORS["blue"], COLORS["blue"], COLORS["blue"], COLORS["blue"], COLORS["green"], COLORS["green"], COLORS["green"]])
    axes[1].set_yticks(y)
    axes[1].set_yticklabels(labels, fontsize=8.5)
    axes[1].invert_yaxis()
    axes[1].set_xlabel("自适应权重")
    axes[1].set_title("破坏/修复算子权重")
    axes[1].grid(axis="x")
    for yi, value in zip(y, values):
        axes[1].text(value + 0.003, yi, f"{value:.3f}", va="center", fontsize=8.5)
    add_caption(fig, "收敛日志显示初始最大流解已可行并达到人数下界；ALNS用于异构任务匹配与轨迹重构。")
    save_figure(fig, "fig07_alns_convergence", "问题三ALNS相对最优差值轨迹与算子权重", "问题三")


def figure_sensitivity(sensitivity: dict[str, object]) -> None:
    demand_df = pd.DataFrame(sensitivity["需求扰动敏感性"])
    workday_df = pd.DataFrame(sensitivity["工作天数敏感性"])
    rest_df = pd.DataFrame(sensitivity["休息间隔敏感性"])

    fig = plt.figure(figsize=(14.5, 7.0), layout="constrained")
    grid = fig.add_gridspec(2, 2)
    ax_demand = fig.add_subplot(grid[0, :])
    ax_workday = fig.add_subplot(grid[1, 0])
    ax_rest = fig.add_subplot(grid[1, 1])

    x = np.arange(len(demand_df))
    ax_demand.plot(x, demand_df["问题一精确人数"], marker="o", color=COLORS["blue"], linewidth=2.2, label="问题一")
    ax_demand.plot(x, demand_df["问题二人数下界"], marker="s", color=COLORS["green"], linewidth=2.2, label="问题二")
    ax_demand.plot(x, demand_df["问题三人数下界"], marker="^", color=COLORS["orange"], linewidth=2.2, label="问题三")
    ax_demand.set_xticks(x)
    ax_demand.set_xticklabels(demand_df["场景"])
    ax_demand.set_ylabel("人数")
    ax_demand.set_title("需求扰动响应")
    ax_demand.grid(True)
    ax_demand.legend(ncol=3, loc="upper left")

    ax_workday.plot(workday_df["每人工作天数"], workday_df["问题二人数下界"], marker="s", color=COLORS["green"], linewidth=2.2, label="问题二")
    ax_workday.plot(workday_df["每人工作天数"], workday_df["问题三人数下界"], marker="^", color=COLORS["orange"], linewidth=2.2, label="问题三")
    ax_workday.set_xlabel("每人工作天数")
    ax_workday.set_ylabel("人数下界")
    ax_workday.set_title("工作天数参数敏感性")
    ax_workday.grid(True)
    ax_workday.legend()

    ax_rest.bar(rest_df["跨组最小休息小时"], rest_df["问题三合法模式数"], color=COLORS["purple"], alpha=0.72, width=0.32, label="合法模式数")
    ax_rest_twin = ax_rest.twinx()
    ax_rest_twin.plot(rest_df["跨组最小休息小时"], rest_df["问题三人数下界"], marker="o", color=COLORS["red"], linewidth=2.2, label="人数下界")
    ax_rest.set_xlabel("跨组最小休息小时")
    ax_rest.set_ylabel("合法模式数")
    ax_rest_twin.set_ylabel("人数下界")
    ax_rest.set_title("休息间隔约束敏感性")
    ax_rest.grid(axis="y")
    lines, labels = ax_rest.get_legend_handles_labels()
    lines2, labels2 = ax_rest_twin.get_legend_handles_labels()
    ax_rest.legend(lines + lines2, labels + labels2, loc="upper right")

    add_caption(fig, "需求扰动和休息间隔扰动从原始附件重新求解；工作天数扰动为理论下界敏感性。")
    save_figure(fig, "fig08_sensitivity_analysis", "三问关键参数敏感性分析", "敏感性分析")


def figure_improvement_gradient(summary: dict[str, object]) -> None:
    workers = [417, 406, 400]
    stages = ["固定小组\n问题一", "跨日换组\n问题二", "日内双组\n问题三"]
    delta = [0, workers[0] - workers[1], workers[1] - workers[2]]
    fig, ax = plt.subplots(figsize=(9.8, 5.4), layout="constrained")
    ax.plot(stages, workers, marker="o", linewidth=2.6, color=COLORS["blue"])
    ax.fill_between(range(len(workers)), workers, min(workers) - 5, color=COLORS["blue"], alpha=0.12)
    for idx, value in enumerate(workers):
        ax.text(idx, value + 2, f"{value}人", ha="center", fontsize=11, fontweight="bold")
    ax.annotate("减少11人", xy=(0.5, 411), xytext=(0.5, 426), arrowprops={"arrowstyle": "->", "color": COLORS["green"]}, ha="center", color=COLORS["green"])
    ax.annotate("再减少6人", xy=(1.5, 403), xytext=(1.5, 417), arrowprops={"arrowstyle": "->", "color": COLORS["orange"]}, ha="center", color=COLORS["orange"])
    ax.set_ylabel("招聘人数")
    ax.set_ylim(392, 430)
    ax.set_title("流动规则放宽带来的边际人力节约")
    ax.grid(axis="y")
    add_caption(fig, "从固定小组到跨日换组再到日内双组服务，招聘人数由417降至400，体现约束放宽的边际收益。")
    save_figure(fig, "fig09_improvement_gradient", "流动规则放宽带来的边际人力节约", "结果讨论")


def write_manifest() -> None:
    (OUT_DIR / "figures-manifest.json").write_text(json.dumps(FIGURES, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    setup_style()
    data = load_data()
    summary = data["summary"]
    sensitivity = data["sensitivity"]
    q1_audit = data["q1_audit"]
    convergence = data["convergence"]
    coverage = data["coverage"]
    schedule = data["schedule"]

    figure_model_framework()
    figure_optimality_evidence(summary, q1_audit)
    figure_q1_column_generation(summary)
    figure_daily_attendance(summary)
    figure_q3_coverage_heatmap(coverage)
    figure_worker_schedule_matrix(schedule)
    figure_alns_convergence(summary, convergence)
    figure_sensitivity(sensitivity)
    figure_improvement_gradient(summary)
    write_manifest()
    print(f"已生成 {len(FIGURES)} 张论文图表，输出目录：{OUT_DIR}")


if __name__ == "__main__":
    main()
