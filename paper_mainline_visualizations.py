from __future__ import annotations

import json
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import pandas as pd
import seaborn as sns

from large_expo_staff_scheduling_solver import read_demand


ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "visualizations" / "mainline"


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


def load_inputs() -> dict[str, object]:
    audit_path = ROOT / "q1_video_discrepancy_audit.json"
    summary_path = ROOT / "advanced_summary.json"
    attachment_path = ROOT / "附件1.xlsx"
    if not attachment_path.exists():
        attachment_path = find_workbook_by_sheet("Sheet1")

    advanced_book = find_workbook_by_sheet("Q1_ExactBaseline")
    with audit_path.open("r", encoding="utf-8") as f:
        audit = json.load(f)
    with summary_path.open("r", encoding="utf-8") as f:
        summary = json.load(f)

    demand, days, hours, group_cols = read_demand(attachment_path)
    q3_coverage = pd.read_excel(advanced_book, sheet_name="Q3_ALNS_Coverage")
    q3_worker = pd.read_excel(advanced_book, sheet_name="Q3_ALNS_WorkerSchedule")
    q3_daily = pd.read_excel(advanced_book, sheet_name="Q3_ALNS_Daily")

    return {
        "audit": audit,
        "summary": summary,
        "attachment_path": attachment_path,
        "advanced_book": advanced_book,
        "demand": demand,
        "days": days,
        "hours": hours,
        "group_cols": group_cols,
        "q3_coverage": q3_coverage,
        "q3_worker": q3_worker,
        "q3_daily": q3_daily,
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
    ax.set_title("图1 原始总需求日-小时热力图")
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
    ax.set_title("图2 小组-日期总需求热力图")
    ax.set_xlabel("日期")
    ax.set_ylabel("小组")
    save_close(fig, "fig02_group_day_demand_heatmap.png")


def fig03_model_progression() -> None:
    fig, ax = plt.subplots(figsize=(14, 4))
    ax.axis("off")

    boxes = [
        (0.02, 0.22, 0.28, 0.56, "#d6eaf8", "统一覆盖优化框架\n小时级需求覆盖 + 每人工作8天"),
        (0.36, 0.22, 0.18, 0.56, "#fdebd0", "问题一\n固定小组\n逐组分解求解"),
        (0.60, 0.22, 0.18, 0.56, "#d5f5e3", "问题二\n取消固定小组\n建立全局人员池"),
        (0.84, 0.22, 0.14, 0.56, "#f9ebea", "问题三\n允许日内跨组\n加入换组休息约束"),
    ]
    notes = [
        "",
        "决策变量：小组内班型人数\n求解：逐组精确/列生成验证",
        "决策变量：全局日出勤人数\n求解：单日下界 + 最大流",
        "决策变量：综合班型与工人分配\n求解：下界 + 最大流初始化 + ALNS",
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

    labels = ["LP 松弛", "逐组向上取整", "整数可行性补差", "最终可执行人数"]
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
        "415 只是逐组下界汇总，不是可执行排班\n额外 +2 来自整数可行性，而非求解误差",
        ha="center",
        va="bottom",
        fontsize=10,
        bbox={"facecolor": "white", "alpha": 0.9, "edgecolor": "#bdc3c7"},
    )
    ax.set_ylabel("人数")
    ax.set_title("图4 问题一下界闭合瀑布图")
    save_close(fig, "fig04_q1_waterfall.png")


def fig05_q1_group_comparison(data: dict[str, object]) -> None:
    per_group = pd.DataFrame(data["audit"]["per_group"])
    x = np.arange(len(per_group))
    width = 0.24

    fig, ax = plt.subplots(figsize=(11, 5))
    ax.bar(x - width, per_group["lp_relaxation"], width=width, color="#95a5a6", label="LP 松弛值")
    ax.bar(x, per_group["ceil_lp"], width=width, color="#f5b041", label="LP 向上取整")
    integer_colors = ["#c0392b" if gap > 0 else "#2e86c1" for gap in per_group["gap_after_ceil"]]
    ax.bar(x + width, per_group["integer_workers"], width=width, color=integer_colors, label="整数最优人数")

    for idx, row in per_group.iterrows():
        if int(row["gap_after_ceil"]) > 0:
            ax.text(idx + width, row["integer_workers"] + 0.5, f"+{int(row['gap_after_ceil'])}", ha="center", color="#c0392b", fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels(per_group["小组"])
    ax.set_ylabel("人数")
    ax.set_title("图5 问题一逐组下界与整数最优对比图")
    ax.legend(loc="upper left")
    save_close(fig, "fig05_q1_group_comparison.png")


def annotate_daily_bound(ax: plt.Axes, minima: np.ndarray, counts: np.ndarray, title: str, label_count: str) -> None:
    days = np.arange(1, len(minima) + 1)
    total_shifts = int(minima.sum())
    lower_bound = int(np.ceil(total_shifts / 8))
    ax.plot(days, minima, "o-", color="#2e86c1", lw=2, label="每日最少出勤人数")
    ax.plot(days, counts, "s--", color="#c0392b", lw=2, label=label_count)
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


def fig06_q2_daily_staffing(data: dict[str, object]) -> None:
    summary = data["summary"]
    minima = np.array(summary["q2_day_minima"])
    counts = np.array(summary["q2_daily_counts"])
    fig, ax = plt.subplots(figsize=(9, 5))
    annotate_daily_bound(ax, minima, counts, "图6 问题二每日最少出勤人数与最终安排人数", "最终安排人数")
    save_close(fig, "fig06_q2_daily_staffing.png")


def fig07_q3_daily_staffing(data: dict[str, object]) -> None:
    summary = data["summary"]
    minima = np.array(summary["q3_day_minima"])
    counts = np.array(summary["q3_daily_counts_alns"])
    fig, ax = plt.subplots(figsize=(9, 5))
    annotate_daily_bound(ax, minima, counts, "图7 问题三每日最少出勤人数与最终安排人数", "最终安排人数")
    save_close(fig, "fig07_q3_daily_staffing.png")


def fig08_q3_cross_group_usage(data: dict[str, object]) -> None:
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

    ax.set_title("图8 问题三跨组班型使用结构图")
    ax.set_xlabel("日期")
    ax.set_ylabel("人数")
    ax.set_xticks(days)
    ax.legend(loc="upper right")
    save_close(fig, "fig08_q3_cross_group_usage.png")


def fig09_representative_coverage(data: dict[str, object]) -> None:
    q3_coverage = data["q3_coverage"].copy()
    summary = (
        q3_coverage.groupby(["天", "小组"], as_index=False)
        .agg({"需求": "sum", "覆盖": "sum", "冗余": "sum", "缺口": "sum"})
        .sort_values(["冗余", "覆盖"], ascending=[False, False])
    )
    case = summary.iloc[0]
    day = int(case["天"])
    group = str(case["小组"])
    detail = q3_coverage[(q3_coverage["天"] == day) & (q3_coverage["小组"] == group)].copy()

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.step(detail["小时"], detail["需求"], where="mid", color="#2e86c1", lw=2, label="需求人数")
    ax.step(detail["小时"], detail["覆盖"], where="mid", color="#cb4335", lw=2, label="实际覆盖人数")
    ax.fill_between(detail["小时"], detail["需求"], detail["覆盖"], step="mid", alpha=0.18, color="#f5b7b1")
    ax.set_title(f"图9 代表性覆盖效果图（第{day}天 {group}）")
    ax.set_xlabel("小时段")
    ax.set_ylabel("人数")
    ax.tick_params(axis="x", rotation=45)
    ax.legend(loc="upper left")
    ax.text(
        0.99,
        0.02,
        f"选择规则：总冗余最高的日-组组合\n总需求={int(case['需求'])}，总覆盖={int(case['覆盖'])}，总冗余={int(case['冗余'])}",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=9,
        bbox={"facecolor": "white", "alpha": 0.9, "edgecolor": "#d5d8dc"},
    )
    save_close(fig, "fig09_representative_coverage.png")


def fig10_final_worker_comparison(data: dict[str, object]) -> None:
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


def main() -> None:
    ensure_output_dir()
    data = load_inputs()
    fig01_total_demand_heatmap(data)
    fig02_group_day_demand_heatmap(data)
    fig03_model_progression()
    fig04_q1_waterfall(data)
    fig05_q1_group_comparison(data)
    fig06_q2_daily_staffing(data)
    fig07_q3_daily_staffing(data)
    fig08_q3_cross_group_usage(data)
    fig09_representative_coverage(data)
    fig10_final_worker_comparison(data)
    print(f"正文主线图已输出到：{OUT_DIR}")


if __name__ == "__main__":
    main()
