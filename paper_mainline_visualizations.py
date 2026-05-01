from __future__ import annotations

import json
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import pandas as pd
import seaborn as sns

from large_expo_staff_scheduling_solver import build_shift_pairs, read_demand


ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "visualizations" / "mainline"
SENSITIVITY_PATH = ROOT / ".codex" / "paper-sensitivity-results.json"


mpl.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": ["Microsoft YaHei", "SimHei", "Arial", "Helvetica"],
        "axes.unicode_minus": False,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.labelsize": 12,
        "axes.titlesize": 14,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "figure.dpi": 300,
        "savefig.dpi": 600,
        "savefig.bbox": "tight",
    }
)


def ensure_output_dir() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)


def find_workbook_by_sheet(sheet_name: str) -> Path:
    for path in ROOT.glob("*.xlsx"):
        try:
            if sheet_name in pd.ExcelFile(path).sheet_names:
                return path
        except Exception:
            continue
    raise FileNotFoundError(f"未找到包含工作表 {sheet_name} 的工作簿。")


def load_json(path: Path) -> dict[str, object]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_inputs() -> dict[str, object]:
    audit_path = ROOT / "q1_video_discrepancy_audit.json"
    summary_path = ROOT / "advanced_summary.json"
    attachment_path = ROOT / "附件1.xlsx"
    if not attachment_path.exists():
        attachment_path = find_workbook_by_sheet("Sheet1")

    advanced_book = find_workbook_by_sheet("Q1_ExactBaseline")
    demand, days, hours, group_cols = read_demand(attachment_path)
    q3_worker = pd.read_excel(advanced_book, sheet_name="Q3_ALNS_WorkerSchedule")

    return {
        "audit": load_json(audit_path),
        "summary": load_json(summary_path),
        "sensitivity": load_json(SENSITIVITY_PATH),
        "attachment_path": attachment_path,
        "advanced_book": advanced_book,
        "demand": demand,
        "days": days,
        "hours": hours,
        "group_cols": group_cols,
        "q3_worker": q3_worker,
    }


def save_close(fig: plt.Figure, filename: str) -> None:
    fig.savefig(OUT_DIR / filename)
    plt.close(fig)


def fig01_total_demand_heatmap(data: dict[str, object]) -> None:
    demand = data["demand"]
    days = data["days"]
    hours = data["hours"]
    total_demand = demand.sum(axis=1)

    fig, ax = plt.subplots(figsize=(10, 5))
    sns.heatmap(
        total_demand,
        cmap="YlOrRd",
        annot=True,
        fmt="d",
        linewidths=0.5,
        cbar_kws={"label": "总需求人数"},
        xticklabels=hours,
        yticklabels=[f"第{day}天" for day in days],
        ax=ax,
    )
    ax.set_title("图1 总需求日-小时热力图")
    ax.set_xlabel("小时段")
    ax.set_ylabel("日期")
    save_close(fig, "fig01_total_demand_heatmap.png")


def fig02_group_day_demand_heatmap(data: dict[str, object]) -> None:
    demand = data["demand"]
    days = data["days"]
    group_cols = data["group_cols"]
    group_day_total = demand.sum(axis=2).T

    fig, ax = plt.subplots(figsize=(9, 5))
    sns.heatmap(
        group_day_total,
        cmap="Blues",
        annot=True,
        fmt="d",
        linewidths=0.5,
        cbar_kws={"label": "小组当日总需求人时"},
        xticklabels=[f"第{day}天" for day in days],
        yticklabels=group_cols,
        ax=ax,
    )
    ax.set_title("图2 小组-日期需求强度热力图")
    ax.set_xlabel("日期")
    ax.set_ylabel("小组")
    save_close(fig, "fig02_group_day_demand_heatmap.png")


def fig03_model_progression() -> None:
    fig, ax = plt.subplots(figsize=(14, 4))
    ax.axis("off")

    boxes = [
        (0.02, 0.22, 0.28, 0.56, "#d6eaf8", "统一覆盖优化框架\n小时级需求覆盖 + 每人工作8天"),
        (0.36, 0.22, 0.18, 0.56, "#fdebd0", "问题一\n固定小组\n聚合IP主求解"),
        (0.60, 0.22, 0.18, 0.56, "#d5f5e3", "问题二\n跨日换组\n下界 + 最大流"),
        (0.84, 0.22, 0.14, 0.56, "#f9ebea", "问题三\n日内跨组\n模式扩展 + ALNS"),
    ]
    notes = [
        "",
        "基础链路：逐组聚合IP\n扩展链路：列生成复核",
        "先求每日最少出勤\n再验证8天工作制可行",
        "13类模板\n370个合法日内模式",
    ]

    for idx, (x, y, w, h, color, title) in enumerate(boxes):
        rect = patches.FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0.02,rounding_size=0.02",
            linewidth=1.2,
            edgecolor="#34495e",
            facecolor=color,
        )
        ax.add_patch(rect)
        ax.text(x + w / 2, y + h * 0.64, title, ha="center", va="center", fontsize=12, fontweight="bold")
        if notes[idx]:
            ax.text(x + w / 2, y + h * 0.28, notes[idx], ha="center", va="center", fontsize=9)

    arrows = [(0.30, 0.50, 0.36, 0.50), (0.54, 0.50, 0.60, 0.50), (0.78, 0.50, 0.84, 0.50)]
    for x1, y1, x2, y2 in arrows:
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1), arrowprops={"arrowstyle": "->", "lw": 2, "color": "#2c3e50"})

    ax.set_title("图3 三问模型递进关系图", pad=12)
    save_close(fig, "fig03_model_progression.png")


def fig04_q1_waterfall(data: dict[str, object]) -> None:
    audit = data["audit"]
    lp = float(audit["total_lp_relaxation"])
    ceil_lp = int(audit["total_ceil_lp_bound"])
    integer_workers = int(audit["total_integer_workers"])

    labels = ["LP松弛", "逐组向上取整", "整数可行性补差", "最终人数"]
    values = [lp, ceil_lp - lp, integer_workers - ceil_lp, integer_workers]
    starts = [0, lp, ceil_lp, 0]
    colors = ["#7f8c8d", "#e67e22", "#c0392b", "#2e86c1"]

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(labels, values, bottom=starts, color=colors, edgecolor="black", width=0.55)
    ax.plot(range(len(labels)), [lp, ceil_lp, integer_workers, integer_workers], "--", color="#555555", alpha=0.7)

    for idx, (value, start) in enumerate(zip(values, starts)):
        if idx == 0:
            text = f"{lp:.3f}"
            ypos = value + 2
            color = "black"
        elif idx == 3:
            text = f"{integer_workers}"
            ypos = value + 2
            color = "black"
        else:
            text = f"+{value:.3f}" if idx == 1 else f"+{int(value)}"
            ypos = start + value / 2
            color = "white"
        ax.text(idx, ypos, text, ha="center", va="center", fontweight="bold", color=color)

    ax.text(
        1.5,
        integer_workers + 9,
        "415 是逐组下界，不是可执行排班\n额外 +2 来自整数可行性闭合",
        ha="center",
        va="bottom",
        fontsize=10,
        bbox={"facecolor": "white", "alpha": 0.9, "edgecolor": "#bdc3c7"},
    )
    ax.set_ylabel("人数")
    ax.set_title("图4 问题一 411.375→415→417 下界闭合瀑布图")
    save_close(fig, "fig04_q1_waterfall.png")


def fig05_q1_group_comparison(data: dict[str, object]) -> None:
    per_group = pd.DataFrame(data["audit"]["per_group"])
    x = np.arange(len(per_group))
    width = 0.24

    fig, ax = plt.subplots(figsize=(11, 5))
    ax.bar(x - width, per_group["lp_relaxation"], width=width, color="#95a5a6", label="LP松弛值")
    ax.bar(x, per_group["ceil_lp"], width=width, color="#f5b041", label="LP向上取整")
    integer_colors = ["#c0392b" if gap > 0 else "#2e86c1" for gap in per_group["gap_after_ceil"]]
    ax.bar(x + width, per_group["integer_workers"], width=width, color=integer_colors, label="整数最优人数")

    for idx, row in per_group.iterrows():
        if int(row["gap_after_ceil"]) > 0:
            ax.text(
                idx + width,
                row["integer_workers"] + 0.5,
                f"+{int(row['gap_after_ceil'])}",
                ha="center",
                color="#c0392b",
                fontweight="bold",
            )

    ax.set_xticks(x)
    ax.set_xticklabels(per_group["小组"])
    ax.set_ylabel("人数")
    ax.set_title("图5 问题一逐组 LP 下界、取整下界与整数最优人数对比图")
    ax.legend(loc="upper left")
    save_close(fig, "fig05_q1_group_comparison.png")


def fig06_maxflow_topology(data: dict[str, object]) -> None:
    summary = data["summary"]
    q2_daily = summary["q2_daily_counts"]

    fig, ax = plt.subplots(figsize=(12, 4.8))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    def draw_box(x: float, y: float, w: float, h: float, text: str, color: str) -> None:
        rect = patches.FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0.02,rounding_size=0.015",
            linewidth=1.2,
            edgecolor="#34495e",
            facecolor=color,
        )
        ax.add_patch(rect)
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=10)

    draw_box(0.03, 0.43, 0.10, 0.14, "源点 S\n容量总和=8N", "#d6eaf8")

    worker_y = np.linspace(0.18, 0.82, 5)
    day_y = np.linspace(0.12, 0.88, 10)
    day_labels = [f"D{i + 1}\n{q2_daily[i]}人" for i in range(10)]

    for idx, y in enumerate(worker_y):
        label = "员工节点\n每人容量=8" if idx == 2 else "E"
        draw_box(0.25, y - 0.045, 0.12, 0.09, label, "#fdebd0")
        ax.annotate("", xy=(0.25, y), xytext=(0.13, 0.50), arrowprops={"arrowstyle": "->", "lw": 1.2, "color": "#7f8c8d"})

    for idx, y in enumerate(day_y):
        draw_box(0.58, y - 0.035, 0.11, 0.07, day_labels[idx], "#d5f5e3")
        source_y = worker_y[idx // 2] if idx < 8 else worker_y[-1]
        ax.annotate("", xy=(0.58, y), xytext=(0.37, source_y), arrowprops={"arrowstyle": "->", "lw": 1.0, "color": "#a04000"})

    draw_box(0.84, 0.43, 0.10, 0.14, "汇点 T\n满足每日出勤", "#f9ebea")
    for y in day_y:
        ax.annotate("", xy=(0.84, 0.50), xytext=(0.69, y), arrowprops={"arrowstyle": "->", "lw": 1.0, "color": "#196f3d"})

    ax.text(0.47, 0.93, "员工→日期边容量 = 1，表示每名员工每天最多出勤一次", ha="center", fontsize=10)
    ax.text(0.49, 0.05, "问题二、三均复用这一工作日分解网络；当最大流满流时，说明‘每天需要多少人’可被映射为‘具体哪些人上班’。", ha="center", fontsize=9)
    ax.set_title("图6 最大流工作日分解网络拓扑图", pad=10)
    save_close(fig, "fig06_maxflow_topology.png")


def annotate_daily_bound(ax: plt.Axes, minima: np.ndarray, counts: np.ndarray, title: str) -> None:
    days = np.arange(1, len(minima) + 1)
    total_shifts = int(minima.sum())
    lower_bound = int(np.ceil(total_shifts / 8))
    ax.plot(days, minima, "o-", color="#2e86c1", lw=2, label="每日最少出勤人数")
    ax.plot(days, counts, "s--", color="#c0392b", lw=2, label="最终安排人数")
    ax.fill_between(days, minima, color="#aed6f1", alpha=0.35)
    ax.set_title(title)
    ax.set_xlabel("日期")
    ax.set_ylabel("人数")
    ax.set_xticks(days)
    ax.legend(loc="lower right")
    ax.text(
        0.5,
        0.04,
        f"总最少出勤人次 = {total_shifts}，下界 = ceil({total_shifts}/8) = {lower_bound}",
        transform=ax.transAxes,
        ha="center",
        va="bottom",
        fontsize=10,
        bbox={"facecolor": "white", "alpha": 0.85, "edgecolor": "#d5d8dc"},
    )


def fig07_q2_daily_staffing(data: dict[str, object]) -> None:
    summary = data["summary"]
    minima = np.array(summary["q2_day_minima"])
    counts = np.array(summary["q2_daily_counts"])
    fig, ax = plt.subplots(figsize=(9, 5))
    annotate_daily_bound(ax, minima, counts, "图7 问题二每日最少出勤人数与最终安排人数")
    save_close(fig, "fig07_q2_daily_staffing.png")


def draw_template_rows(
    ax: plt.Axes,
    labels: list[tuple[int, int, int, int]],
    hours: list[str],
    title: str,
    first_color: str,
    second_color: str,
) -> None:
    hour_labels = [label.split("-")[0] for label in hours] + [hours[-1].split("-")[1]]
    for row_index, (s1, e1, s2, e2) in enumerate(labels):
        y = len(labels) - row_index - 1
        ax.broken_barh([(s1, e1 - s1)], (y + 0.12, 0.32), facecolors=first_color)
        ax.broken_barh([(s2, e2 - s2)], (y + 0.56, 0.32), facecolors=second_color)
        ax.text(11.2, y + 0.5, f"({s1 + 1},{s2 + 1})", va="center", fontsize=9)
    ax.set_xlim(0, 12.4)
    ax.set_ylim(0, len(labels))
    ax.set_xticks(np.arange(0, 12, 1))
    ax.set_xticklabels(hour_labels, rotation=45, ha="right")
    ax.set_yticks(np.arange(len(labels)) + 0.5)
    ax.set_yticklabels([f"T{i + 1}" for i in range(len(labels) - 1, -1, -1)])
    ax.set_title(title)
    ax.set_xlabel("时间轴")
    ax.set_ylabel("模板")
    ax.grid(axis="x", alpha=0.25)


def fig08_q3_template_patterns(data: dict[str, object]) -> None:
    hours = data["hours"]
    _, _, same_labels = build_shift_pairs(min_break=0)
    _, _, cross_labels = build_shift_pairs(min_break=2)

    fig, axes = plt.subplots(2, 1, figsize=(12, 8), gridspec_kw={"height_ratios": [3, 1.4]})
    draw_template_rows(axes[0], same_labels, hours, "同组 8 小时模板（10类，不重叠 4+4）", "#5dade2", "#2874a6")
    draw_template_rows(axes[1], cross_labels, hours, "跨组 8 小时模板（3类，跨组间至少休息2小时）", "#f5b041", "#ca6f1e")

    fig.text(
        0.5,
        0.01,
        "模式计数：同组模式 = 10×10 = 100；跨组模式 = 10×9×3 = 270；综合合法日内服务模式总数 = 370。",
        ha="center",
        fontsize=10,
    )
    fig.suptitle("图8 问题三 13 类基础时间模板与 370 个服务模式示意图", y=0.98)
    fig.tight_layout(rect=(0, 0.04, 1, 0.96))
    save_close(fig, "fig08_q3_template_patterns.png")


def fig09_q3_cross_group_usage(data: dict[str, object]) -> None:
    q3_worker = data["q3_worker"].copy()
    day_cols = [col for col in q3_worker.columns if str(col).startswith("第") and str(col).endswith("天")]
    if not day_cols:
        day_cols = list(q3_worker.columns[1:])

    same_counts: list[int] = []
    cross_counts: list[int] = []
    for col in day_cols:
        labels = q3_worker[col].fillna("").astype(str)
        working = labels[~labels.str.contains("休息", na=False)]
        cross = working.str.contains("；", regex=False).sum()
        same = len(working) - int(cross)
        same_counts.append(int(same))
        cross_counts.append(int(cross))

    days = np.arange(1, len(day_cols) + 1)
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(days, same_counts, color="#5dade2", label="同组班型人数")
    ax.bar(days, cross_counts, bottom=same_counts, color="#eb984e", label="跨组班型人数")

    for day, same, cross in zip(days, same_counts, cross_counts):
        if cross > 0:
            ax.text(day, same + cross + 1.5, str(cross), ha="center", va="bottom", fontsize=9, color="#a04000")

    ax.set_title("图9 问题三跨组班型使用结构图")
    ax.set_xlabel("日期")
    ax.set_ylabel("人数")
    ax.set_xticks(days)
    ax.legend(loc="upper right")
    save_close(fig, "fig09_q3_cross_group_usage.png")


def fig10_final_worker_comparison() -> None:
    values = [417, 406, 400]
    labels = ["问题一", "问题二", "问题三"]
    colors = ["#5dade2", "#48c9b0", "#f5b041"]

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(labels, values, color=colors, edgecolor="#34495e", width=0.6)
    for bar, value in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, value + 1, str(value), ha="center", va="bottom", fontweight="bold")

    ax.annotate("较问题一减少 11 人", xy=(1, 406), xytext=(0.45, 424), textcoords="data", arrowprops={"arrowstyle": "->", "color": "#117864"}, color="#117864")
    ax.annotate("较问题二减少 6 人", xy=(2, 400), xytext=(1.45, 416), textcoords="data", arrowprops={"arrowstyle": "->", "color": "#af601a"}, color="#af601a")
    ax.annotate("较问题一累计减少 17 人", xy=(2, 400), xytext=(0.55, 432), textcoords="data", arrowprops={"arrowstyle": "->", "color": "#922b21"}, color="#922b21")
    ax.set_ylabel("最少招聘人数")
    ax.set_title("图10 三问最终最少招聘人数对比图")
    save_close(fig, "fig10_final_worker_comparison.png")


def fig11_demand_perturbation_udr(data: dict[str, object]) -> None:
    sensitivity = data["sensitivity"]
    rows = [row for row in sensitivity["需求扰动敏感性"] if row["场景编号"] in {"S1", "S1+", "S2"}]
    scenario_order = ["S1", "S1+", "S2"]
    rows.sort(key=lambda item: scenario_order.index(item["场景编号"]))

    scenario_labels = [row["场景"] for row in rows]
    q1_udr = [row["问题一"]["原方案缺口指标"]["UDR"] for row in rows]
    q2_udr = [row["问题二"]["原方案缺口指标"]["UDR"] for row in rows]
    q3_udr = [row["问题三"]["原方案缺口指标"]["UDR"] for row in rows]

    x = np.arange(len(rows))
    width = 0.24

    fig, ax = plt.subplots(figsize=(10, 5))
    bars1 = ax.bar(x - width, q1_udr, width=width, color="#5dade2", label="问题一原方案")
    bars2 = ax.bar(x, q2_udr, width=width, color="#48c9b0", label="问题二原方案")
    bars3 = ax.bar(x + width, q3_udr, width=width, color="#f5b041", label="问题三原方案")

    for bars in (bars1, bars2, bars3):
        for bar in bars:
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.0008,
                f"{bar.get_height():.4f}",
                ha="center",
                va="bottom",
                fontsize=9,
                rotation=90,
            )

    ax.set_xticks(x)
    ax.set_xticklabels(scenario_labels)
    ax.set_ylabel("UDR")
    ax.set_title("图11 需求扰动下原方案 UDR 对比图")
    ax.legend(loc="upper left")
    ax.grid(axis="y", alpha=0.25)
    ax.text(
        0.99,
        0.02,
        "UDR = 总缺口 / 扰动后总需求；数值越小表示原方案越稳健。",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=9,
        bbox={"facecolor": "white", "alpha": 0.9, "edgecolor": "#d5d8dc"},
    )
    save_close(fig, "fig11_demand_perturbation_udr.png")


def main() -> None:
    ensure_output_dir()
    data = load_inputs()
    fig01_total_demand_heatmap(data)
    fig02_group_day_demand_heatmap(data)
    fig03_model_progression()
    fig04_q1_waterfall(data)
    fig05_q1_group_comparison(data)
    fig06_maxflow_topology(data)
    fig07_q2_daily_staffing(data)
    fig08_q3_template_patterns(data)
    fig09_q3_cross_group_usage(data)
    fig10_final_worker_comparison()
    fig11_demand_perturbation_udr(data)
    print(f"论文 V3 主线图已输出到：{OUT_DIR}")


if __name__ == "__main__":
    main()
