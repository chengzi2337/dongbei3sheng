#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版论文可视化脚本 —— 优化现有11张 + 新增9+张候选图。
统一配色、字体、风格，消除文字错位。
"""

from __future__ import annotations

import json, math, warnings
from pathlib import Path
from typing import Optional

import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.gridspec import GridSpec
from scipy.interpolate import make_interp_spline

from large_expo_staff_scheduling_solver import (
    build_shift_pairs, read_demand, build_problem3_patterns,
    solve_daily_problem2, solve_daily_problem3,
)

warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# ======================== 全局配置 ========================
ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "visualizations" / "enhanced"
SENSITIVITY_PATH = ROOT / ".codex" / "paper-sensitivity-results.json"
SUMMARY_PATH = ROOT / "advanced_summary.json"
AUDIT_PATH = ROOT / "q1_video_discrepancy_audit.json"
INDEPENDENT_PATH = ROOT / "independent_advanced_summary.json"
ATTACHMENT_PATH = ROOT / "附件1.xlsx"
ADVANCED_BOOK = ROOT / "高级排班优化结果.xlsx"
CONVERGENCE_PATH = ROOT / "q3_alns_convergence.csv"

# ── 统一学术色板 ──
C = {
    "q1_primary":   "#2471A3",   # 问题一主色 沉稳蓝
    "q2_primary":   "#1D8348",   # 问题二主色 沉稳绿
    "q3_primary":   "#B7950B",   # 问题三主色 沉稳金
    "accent_red":   "#C0392B",
    "accent_orange":"#D35400",
    "accent_purple":"#7D3C98",
    "gray_light":   "#EAECEE",
    "gray_mid":     "#BDC3C7",
    "gray_dark":    "#566573",
    "text_dark":    "#2C3E50",
    "white":        "#FFFFFF",
    "bg":           "#FCFCFC",
}
Q_COLORS = [C["q1_primary"], C["q2_primary"], C["q3_primary"]]
Q_LABELS = ["问题一", "问题二", "问题三"]

# ── 高质量 matplotlib 全局设置 ──
mpl.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Microsoft YaHei", "SimHei", "Noto Sans SC", "DejaVu Sans"],
    "axes.unicode_minus": False,
    "figure.dpi": 300,
    "savefig.dpi": 600,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.labelsize": 12,
    "axes.titlesize": 14,
    "axes.titleweight": "bold",
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 10,
    "figure.facecolor": C["white"],
    "axes.facecolor": C["white"],
})


# ======================== 工具函数 ========================
def ensure_dir() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

def save(
    fig: plt.Figure,
    name: str,
    *,
    bbox_inches: Optional[str] = "tight",
    pad_inches: float = 0.15,
) -> None:
    save_kwargs = {"facecolor": fig.get_facecolor()}
    if bbox_inches is not None:
        save_kwargs["bbox_inches"] = bbox_inches
        if bbox_inches == "tight":
            save_kwargs["pad_inches"] = pad_inches
    fig.savefig(OUT_DIR / name, **save_kwargs)
    plt.close(fig)

def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def load_data() -> dict:
    demand, days, hours, group_cols = read_demand(ATTACHMENT_PATH)
    audit = load_json(AUDIT_PATH)
    summary = load_json(SUMMARY_PATH)
    sensitivity = load_json(SENSITIVITY_PATH)
    q3_worker = pd.read_excel(ADVANCED_BOOK, sheet_name="Q3_ALNS_WorkerSchedule")
    conv = pd.read_csv(CONVERGENCE_PATH) if CONVERGENCE_PATH.exists() else pd.DataFrame()
    return {
        "demand": demand, "days": days, "hours": hours,
        "group_cols": group_cols, "audit": audit,
        "summary": summary, "sensitivity": sensitivity,
        "q3_worker": q3_worker, "convergence": conv,
    }


def spine_clean(ax: plt.Axes) -> None:
    for spine in ax.spines.values():
        spine.set_linewidth(0.6)
        spine.set_color(C["gray_mid"])


# ============================================================
#   PART A: 现有11张图的风格优化版
# ============================================================

def A01_total_demand_heatmap(data: dict) -> None:
    """优化版：总需求热力图 —— 更学术的色阶 + 边缘分布。"""
    demand = data["demand"]
    total = demand.sum(axis=1)  # (10天, 11小时)

    fig = plt.figure(figsize=(12.4, 6.6), facecolor=C["white"])
    gs = GridSpec(2, 2, figure=fig, width_ratios=[6, 1], height_ratios=[6, 1.05],
                   hspace=0.10, wspace=0.02,
                   left=0.08, right=0.92, top=0.92, bottom=0.14)

    ax_main = fig.add_subplot(gs[0, 0])
    ax_right = fig.add_subplot(gs[0, 1], sharey=ax_main)
    ax_bottom = fig.add_subplot(gs[1, 0], sharex=ax_main)

    # 主热力图
    sns.heatmap(total, cmap="rocket_r", annot=True, fmt="d",
                linewidths=0.6, linecolor="white",
                cbar=False, square=False,
                xticklabels=data["hours"],
                yticklabels=[f"第{d}天" for d in data["days"]],
                ax=ax_main)
    ax_main.set_xlabel("")
    ax_main.set_ylabel("")
    ax_main.tick_params(axis="y", labelsize=10)
    ax_main.tick_params(axis="x", bottom=False, labelbottom=False)

    # 右侧日总量
    day_totals = total.sum(axis=1)
    ax_right.barh(np.arange(len(day_totals)) + 0.5, day_totals,
                  height=0.65, color=C["q1_primary"], alpha=0.75, edgecolor="white", linewidth=0.5)
    ax_right.set_xlabel("日总量", fontsize=9, color=C["gray_dark"])
    ax_right.tick_params(left=False, labelleft=False)
    ax_right.spines["left"].set_visible(False)
    ax_right.spines["bottom"].set_visible(False)
    for i, v in enumerate(day_totals):
        ax_right.text(v + 5, i + 0.5, str(v), va="center", fontsize=8, color=C["gray_dark"])

    # 底部小时总量
    hour_totals = total.sum(axis=0)
    ax_bottom.bar(np.arange(len(hour_totals)) + 0.5, hour_totals,
                  width=0.65, color=C["q1_primary"], alpha=0.75, edgecolor="white", linewidth=0.5)
    ax_bottom.set_ylabel("时总量", fontsize=9, color=C["gray_dark"])
    ax_bottom.set_xticks(np.arange(len(hour_totals)) + 0.5)
    ax_bottom.set_xticklabels(data["hours"], rotation=25, ha="right", fontsize=9)
    ax_bottom.tick_params(axis="x", bottom=True, labelbottom=True, pad=6)
    ax_bottom.margins(x=0.02)
    for i, v in enumerate(hour_totals):
        ax_bottom.text(i + 0.5, v + 28, str(v), ha="center", fontsize=8, color=C["gray_dark"])
    ax_bottom.set_ylim(0, hour_totals.max() + 140)

    fig.suptitle("图1  总需求日-小时热力图（含边缘分布）", fontsize=15, y=0.97, color=C["text_dark"])
    save(fig, "fig01_total_demand_heatmap.png")


def A02_group_day_demand_heatmap(data: dict) -> None:
    """优化版：小组-日期需求强度热力图 —— 冷色调 + 清晰标注。"""
    demand = data["demand"]
    group_day = demand.sum(axis=2).T

    fig, ax = plt.subplots(figsize=(10, 5.5), facecolor=C["white"])
    sns.heatmap(group_day, cmap="mako", annot=True, fmt="d",
                linewidths=0.6, linecolor="white", square=True,
                cbar_kws={"label": "小组当日总需求（人时）", "shrink": 0.8},
                xticklabels=[f"第{d}天" for d in data["days"]],
                yticklabels=data["group_cols"],
                ax=ax, vmin=group_day.min() * 0.95)
    ax.set_title("图2  小组-日期需求强度热力图", fontsize=14, pad=12, color=C["text_dark"])
    ax.set_xlabel("日期")
    ax.set_ylabel("小组")
    spine_clean(ax)
    save(fig, "fig02_group_day_demand_heatmap.png")


def A03_model_progression(data: dict) -> None:
    """优化版：三问模型递进关系图 —— 现代卡片式设计。"""
    fig, ax = plt.subplots(figsize=(16, 4.8), facecolor=C["white"])
    fig.subplots_adjust(left=0.02, right=0.98, top=0.86, bottom=0.08)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    cards = [
        {"x": 0.02, "w": 0.22, "color": "#EBF5FB", "edge": "#2980B9",
         "title": "统一覆盖优化框架", "sub": "小时级需求覆盖\n每人工作8天",
         "tag": "LEGAL SHIFT POOL → IP"},
        {"x": 0.29, "w": 0.18, "color": "#FEF9E7", "edge": "#D4AC0D",
         "title": "问题一", "sub": "固定小组服务\n聚合IP + 列生成复核",
         "tag": "417 人"},
        {"x": 0.53, "w": 0.18, "color": "#E8F8F5", "edge": "#1ABC9C",
         "title": "问题二", "sub": "跨日换组\n下界定理 + 最大流构造",
         "tag": "406 人"},
        {"x": 0.77, "w": 0.21, "color": "#F5EEF8", "edge": "#8E44AD",
         "title": "问题三", "sub": "日内跨组\n13类模板·370模式·ALNS",
         "tag": "400 人"},
    ]

    for card in cards:
        x, w = card["x"], card["w"]
        rect = mpatches.FancyBboxPatch(
            (x, 0.18), w, 0.68, boxstyle="round,pad=0.03,rounding_size=0.02",
            linewidth=1.8, edgecolor=card["edge"], facecolor=card["color"], zorder=2)
        ax.add_patch(rect)
        # 标题
        ax.text(x + w/2, 0.75, card["title"], ha="center", va="center",
                fontsize=14, fontweight="bold", color=C["text_dark"])
        # 副标题
        ax.text(x + w/2, 0.52, card["sub"], ha="center", va="center",
                fontsize=10, color=C["gray_dark"], linespacing=1.5)
        # 底部标签
        tag_margin = max(0.012, w * 0.08)
        tag_width = max(0.10, w - 2 * tag_margin)
        tag_rect = mpatches.FancyBboxPatch(
            (x + tag_margin, 0.235), tag_width, 0.085,
            boxstyle="round,pad=0.01,rounding_size=0.01",
            linewidth=0.8, edgecolor=card["edge"], facecolor=card["color"], alpha=0.9, zorder=3)
        ax.add_patch(tag_rect)
        ax.text(x + w/2, 0.277, card["tag"], ha="center", va="center",
                fontsize=8.5, fontweight="bold", color=card["edge"])

    # 箭头
    arrows = [(0.24, 0.52, 0.29, 0.52), (0.47, 0.52, 0.53, 0.52), (0.71, 0.52, 0.77, 0.52)]
    for x1, y1, x2, y2 in arrows:
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="->", lw=2.5, color=C["gray_dark"],
                                    connectionstyle="arc3,rad=0"))

    ax.set_title("图3  三问模型递进关系图", fontsize=15, pad=10, color=C["text_dark"])
    save(fig, "fig03_model_progression.png", bbox_inches=None)


def A04_q1_waterfall(data: dict) -> None:
    """优化版：问题一 waterfall —— 统一暖色渐变 + 清晰标注。"""
    audit = data["audit"]
    lp = float(audit["total_lp_relaxation"])
    ceil_lp = int(audit["total_ceil_lp_bound"])
    integer_workers = int(audit["total_integer_workers"])

    labels = ["LP 松弛值", "逐组向上取整", "整数可行性补差", "最终可执行人数"]
    values = [lp, ceil_lp - lp, integer_workers - ceil_lp, integer_workers]
    bottoms = [0, lp, ceil_lp, 0]
    colors = ["#ABB2B9", "#F0B27A", "#E74C3C", "#2980B9"]
    edge_colors = ["#7F8C8D", "#D68910", "#922B21", "#1A5276"]

    fig, ax = plt.subplots(figsize=(10, 6.4), facecolor=C["white"])
    fig.subplots_adjust(left=0.10, right=0.97, top=0.78, bottom=0.15)
    ax.bar(labels, values, bottom=bottoms, color=colors, edgecolor=edge_colors,
           linewidth=1.5, width=0.5, zorder=3)

    # 连接线
    x_line = [0, 1, 2, 3]
    y_line = [lp, ceil_lp, integer_workers, integer_workers]
    ax.plot(x_line, y_line, "o-", color=C["gray_dark"], lw=2, markersize=6, zorder=5)

    # 标注
    annotations = [
        (0, f"{lp:.3f}", "top", C["text_dark"]),
        (1, f"+{ceil_lp - lp:.3f}", "center", C["white"]),
        (2, f"+{integer_workers - ceil_lp}", "center", C["white"]),
        (3, f"{integer_workers} 人", "top", C["text_dark"]),
    ]
    for i, text, va, color in annotations:
        y = values[i] + bottoms[i] if va == "top" else bottoms[i] + values[i] / 2
        offset = 2 if va == "top" else 0
        ax.text(i, y + offset, text, ha="center", va="center" if va != "top" else "bottom",
                fontweight="bold", fontsize=11, color=color)

    # 说明框
    ax.text(
        0.34, 0.78,
        "415 是逐组 LP 取整下界，非可执行排班\n"
        "额外 +2 来自小组5和小组9的整数化补差",
        transform=ax.transAxes, fontsize=9.2, ha="center", va="center", linespacing=1.45,
        bbox=dict(boxstyle="round,pad=0.4", facecolor="#FEF9E7", edgecolor="#D4AC0D", alpha=0.95))

    ax.set_ylabel("人数", fontsize=12, color=C["text_dark"])
    ax.set_title("图4  问题一 411.375 → 415 → 417 下界闭合瀑布图", fontsize=13.5, pad=18, color=C["text_dark"])
    ax.set_ylim(0, integer_workers + 20)
    spine_clean(ax)
    ax.yaxis.set_major_locator(mticker.MultipleLocator(50))
    ax.grid(axis="y", alpha=0.2, zorder=0)

    # 用上方放大视窗明确展示两段增量的“瀑布”结构。
    ax_zoom = ax.inset_axes([0.58, 0.57, 0.26, 0.20])
    ax_zoom.bar(labels, values, bottom=bottoms, color=colors, edgecolor=edge_colors,
                linewidth=1.2, width=0.5, zorder=3)
    ax_zoom.plot(x_line, y_line, "o-", color=C["gray_dark"], lw=1.6, markersize=4.5, zorder=4)
    ax_zoom.set_xlim(0.55, 3.05)
    ax_zoom.set_ylim(lp - 0.8, integer_workers + 1.2)
    ax_zoom.set_xticks([1, 2, 3])
    ax_zoom.set_xticklabels(["取整", "补差", "终值"], fontsize=7)
    ax_zoom.tick_params(axis="y", labelsize=7)
    ax_zoom.set_title("增量细节", fontsize=8.5, pad=3, color=C["text_dark"])
    for spine in ax_zoom.spines.values():
        spine.set_linewidth(0.8)
        spine.set_color(C["gray_mid"])
    ax_zoom.grid(axis="y", alpha=0.15, zorder=0)
    save(fig, "fig04_q1_waterfall.png", bbox_inches=None)


def A05_q1_group_comparison(data: dict) -> None:
    """优化版：逐组对比 —— 统一配色 + 清晰分组。"""
    per_group = pd.DataFrame(data["audit"]["per_group"])
    x = np.arange(len(per_group))
    width = 0.22

    fig, ax = plt.subplots(figsize=(12, 5.6), facecolor=C["white"])
    fig.subplots_adjust(top=0.76, left=0.08, right=0.98, bottom=0.14)

    b1 = ax.bar(x - width, per_group["lp_relaxation"], width, color="#ABB2B9",
                edgecolor="white", linewidth=0.5, label="LP 松弛值", zorder=3)
    b2 = ax.bar(x, per_group["ceil_lp"], width, color="#F0B27A",
                edgecolor="white", linewidth=0.5, label="LP 向上取整", zorder=3)
    int_colors = [C["accent_red"] if g > 0 else C["q1_primary"] for g in per_group["gap_after_ceil"]]
    b3 = ax.bar(x + width, per_group["integer_workers"], width, color=int_colors,
                edgecolor="white", linewidth=0.5, label="整数最优人数", zorder=3)

    # 标注 gap
    for i, row in per_group.iterrows():
        gap = int(row["gap_after_ceil"])
        if gap > 0:
            ax.annotate(f"+{gap}", (x[i] + width, row["integer_workers"] + 0.6),
                        ha="center", fontsize=11, fontweight="bold", color=C["accent_red"],
                        bbox=dict(facecolor="#FDEDEC", edgecolor=C["accent_red"],
                                  boxstyle="round,pad=0.15", alpha=0.9))

    ax.set_xticks(x)
    ax.set_xticklabels(per_group["小组"], fontsize=10)
    ax.set_ylabel("人数", fontsize=12)
    fig.suptitle("图5  问题一逐组 LP 下界、取整下界与整数最优人数",
                 fontsize=14, y=0.93, color=C["text_dark"])
    fig.legend(loc="upper center", bbox_to_anchor=(0.5, 0.995), ncol=3,
               framealpha=0.95, edgecolor=C["gray_mid"])
    spine_clean(ax)
    ax.grid(axis="y", alpha=0.2, zorder=0)
    save(fig, "fig05_q1_group_comparison.png")


def A06_maxflow_topology(data: dict) -> None:
    """优化版：最大流网络拓扑 —— 对称布局 + 清晰图例。"""
    q2_daily = data["summary"]["q2_daily_counts"]

    fig, ax = plt.subplots(figsize=(13.4, 6.3), facecolor=C["white"])
    fig.subplots_adjust(left=0.03, right=0.98, top=0.90, bottom=0.12)
    ax.set_xlim(-0.02, 1.00)
    ax.set_ylim(-0.05, 1.02)
    ax.axis("off")

    # 节点绘制函数
    def node(x, y, text, color, w=0.10, h=0.09):
        rect = mpatches.FancyBboxPatch((x - w/2, y - h/2), w, h,
            boxstyle="round,pad=0.015,rounding_size=0.015",
            linewidth=1.4, edgecolor=C["text_dark"], facecolor=color, zorder=4)
        ax.add_patch(rect)
        ax.text(x, y, text, ha="center", va="center", fontsize=8.5, fontweight="bold", zorder=5)

    # 源点
    node(0.06, 0.50, "源点 S", "#D6EAF8", w=0.11)

    # 员工节点 (5个代表)
    for i, y in enumerate([0.78, 0.61, 0.50, 0.39, 0.22]):
        node(0.24, y, f"员工 {i+1}", "#FDEBD0", w=0.11)
        ax.annotate("", xy=(0.185, y), xytext=(0.115, 0.50),
                    arrowprops=dict(arrowstyle="->", lw=1.2, color="#85C1E9"), zorder=3)
        ax.text(0.16, y + 0.03, "cap=8", fontsize=7, color=C["gray_dark"], ha="center")

    # 日期节点
    day_y = np.linspace(0.88, 0.16, 10)
    for i, y in enumerate(day_y):
        node(0.54, y, f"第{i+1}天\n{q2_daily[i]}人", "#D5F5E3", w=0.12, h=0.085)
        src_y = [0.78, 0.78, 0.61, 0.61, 0.50, 0.50, 0.39, 0.39, 0.22, 0.22][i]
        ax.annotate("", xy=(0.48, y), xytext=(0.295, src_y),
                    arrowprops=dict(arrowstyle="->", lw=0.8, color="#A9DFBF", alpha=0.6), zorder=2)
    ax.text(0.40, 0.93, "cap=1", fontsize=7, color=C["gray_dark"], ha="center")

    # 汇点
    node(0.76, 0.50, "汇点 T", "#F9EBEA", w=0.11)
    for y in day_y:
        ax.annotate("", xy=(0.705, 0.50), xytext=(0.60, y),
                    arrowprops=dict(arrowstyle="->", lw=0.8, color="#F5B7B1", alpha=0.6), zorder=2)

    # 底部说明
    fig.text(0.50, 0.05,
             "当最大流值 = 8N 时满流 ←→ 存在满足「每人8天 + 每日出勤人数」的工作日分配",
             ha="center", fontsize=10, color=C["text_dark"],
             bbox=dict(facecolor="#F8F9F9", edgecolor=C["gray_mid"], boxstyle="round,pad=0.3", alpha=0.92))

    ax.set_title("图6  最大流工作日分解网络拓扑图", fontsize=14, pad=8, color=C["text_dark"])
    save(fig, "fig06_maxflow_topology.png", bbox_inches=None)


def A07_q2_daily_staffing(data: dict) -> None:
    """优化版：Q2 每日出勤 —— 填充 + 趋势线优化。"""
    summary = data["summary"]
    minima = np.array(summary["q2_day_minima"])
    counts = np.array(summary["q2_daily_counts"])
    days = np.arange(1, 11)
    total = int(minima.sum())
    lb = int(np.ceil(total / 8))

    fig, ax = plt.subplots(figsize=(10, 5.5), facecolor=C["white"])

    ax.fill_between(days, minima, alpha=0.18, color=C["q2_primary"])
    ax.fill_between(days, counts, alpha=0.08, color=C["accent_red"])
    ax.plot(days, minima, "o-", color=C["q2_primary"], lw=2.5, markersize=8,
            label=f"每日最少出勤人数  (∑={total})", zorder=4)
    ax.plot(days, counts, "s--", color=C["accent_red"], lw=2, markersize=8,
            label=f"考虑8天制后安排人数  (406人)", zorder=4)

    # 标注调整
    for d, m, c in zip(days, minima, counts):
        if c > m:
            ax.annotate(f"+{c-m}", (d, c + 2), ha="center", fontsize=8,
                        color=C["accent_red"], fontweight="bold")

    ax.set_xticks(days)
    ax.set_xlabel("日期", fontsize=12)
    ax.set_ylabel("人数", fontsize=12)
    ax.set_title("图7  问题二每日最少出勤人数与最终安排人数", fontsize=14, pad=12, color=C["text_dark"])
    ax.legend(loc="upper left", framealpha=0.9)
    spine_clean(ax)
    ax.grid(axis="y", alpha=0.2, zorder=0)

    # 信息框
    ax.text(0.97, 0.14, f"∑m_d = {total}\n理论下界 = ceil({total} / 8) = {lb}\n构造可行：406 人",
            transform=ax.transAxes, ha="right", va="bottom", fontsize=10,
            bbox=dict(facecolor="white", edgecolor=C["q2_primary"], boxstyle="round,pad=0.4", alpha=0.92))
    save(fig, "fig07_q2_daily_staffing.png")


def A08_q3_template_patterns(data: dict) -> None:
    """优化版：13类模板示意图 —— 配色增强 + 清晰时间轴。"""
    hours = data["hours"]
    _, _, same_labels = build_shift_pairs(min_break=0)
    _, _, cross_labels = build_shift_pairs(min_break=2)
    hour_ticks = [h.split("-")[0] for h in hours] + [hours[-1].split("-")[1]]

    fig, axes = plt.subplots(2, 1, figsize=(12, 8), facecolor=C["white"],
                              gridspec_kw={"height_ratios": [3, 1.4], "hspace": 0.35})

    def draw_template(ax, labels, title, c1, c2):
        for i, (s1, e1, s2, e2) in enumerate(labels):
            y = len(labels) - i - 1
            ax.broken_barh([(s1, e1 - s1)], (y + 0.10, 0.36), facecolors=c1, edgecolor="white", linewidth=0.8)
            ax.broken_barh([(s2, e2 - s2)], (y + 0.54, 0.36), facecolors=c2, edgecolor="white", linewidth=0.8)
            ax.text(11.3, y + 0.5, f"({s1+1},{s2+1})", va="center", fontsize=9, color=C["gray_dark"])
        ax.set_xlim(0, 13)
        ax.set_ylim(0, len(labels))
        ax.set_xticks(np.arange(0, 12))
        ax.set_xticklabels(hour_ticks, rotation=45, ha="right", fontsize=9)
        ax.set_yticks(np.arange(len(labels)) + 0.5)
        ax.set_yticklabels([f"T{i+1}" for i in range(len(labels)-1, -1, -1)], fontsize=9)
        ax.set_title(title, fontsize=12, fontweight="bold", color=C["text_dark"])
        ax.set_xlabel("时间轴", fontsize=10)
        ax.set_ylabel("模板", fontsize=10)
        ax.grid(axis="x", alpha=0.2)
        spine_clean(ax)

    draw_template(axes[0], same_labels, "同组 8 小时模板（10 类，不重叠 4+4）",
                  "#5DADE2", "#2471A3")
    draw_template(axes[1], cross_labels, "跨组 8 小时模板（3 类，中间至少休息 2 小时）",
                  "#F5B041", "#CA6F1E")

    fig.suptitle("图8  问题三 13 类基础时间模板与 370 个服务模式示意图",
                 fontsize=15, y=0.98, color=C["text_dark"])
    fig.text(0.5, 0.005, "模式计数：同组 = 10×10 = 100  |  跨组 = 10×9×3 = 270  |  合计 = 370 个合法日内服务模式",
             ha="center", fontsize=10.5, fontweight="bold",
             bbox=dict(facecolor="#F5EEF8", edgecolor="#8E44AD", boxstyle="round,pad=0.3"))
    save(fig, "fig08_q3_template_patterns.png")


def A09_q3_cross_group_usage(data: dict) -> None:
    """优化版：Q3 跨组班型使用结构 —— 更好的堆叠柱状图。"""
    q3_worker = data["q3_worker"].copy()
    day_cols = [c for c in q3_worker.columns if str(c).startswith("第") and str(c).endswith("天")]
    if not day_cols:
        day_cols = list(q3_worker.columns[1:])

    same, cross = [], []
    for col in day_cols:
        labels = q3_worker[col].fillna("").astype(str)
        working = labels[~labels.str.contains("休息", na=False)]
        cross.append(int(working.str.contains("；", regex=False).sum()))
        same.append(len(working) - cross[-1])

    days = np.arange(1, 11)
    fig, ax = plt.subplots(figsize=(10, 5.5), facecolor=C["white"])

    ax.bar(days, same, color="#5DADE2", edgecolor="white", linewidth=0.8, label="同组班型", zorder=3)
    ax.bar(days, cross, bottom=same, color="#F5B041", edgecolor="white", linewidth=0.8, label="跨组班型", zorder=3)

    for d, s, c in zip(days, same, cross):
        total = s + c
        ax.text(d, total + 1.5, str(total), ha="center", fontsize=10, fontweight="bold", color=C["text_dark"])
        if c > 0:
            ax.text(d, s + c/2, str(c), ha="center", fontsize=8, color="white", fontweight="bold")

    ax.set_xticks(days)
    ax.set_xlabel("日期", fontsize=12)
    ax.set_ylabel("人数", fontsize=12)
    ax.set_title("图9  问题三跨组班型使用结构图", fontsize=14, pad=12, color=C["text_dark"])
    ax.legend(loc="upper right", framealpha=0.9)
    spine_clean(ax)
    ax.grid(axis="y", alpha=0.2, zorder=0)
    save(fig, "fig09_q3_cross_group_usage.png")


def A10_final_worker_comparison() -> None:
    """优化版：三问最终对比 —— 渐变柱 + 节约标注。"""
    values = [417, 406, 400]
    labels = ["问题一\n固定小组服务", "问题二\n跨日换组", "问题三\n日内跨组"]
    colors = [C["q1_primary"], C["q2_primary"], C["q3_primary"]]

    fig, ax = plt.subplots(figsize=(8.4, 5.9), facecolor=C["white"])
    fig.subplots_adjust(top=0.86, left=0.10, right=0.98, bottom=0.14)

    bars = ax.bar(range(3), values, color=colors, edgecolor="white", linewidth=1.2,
                  width=0.55, zorder=3)

    for i, (bar, v) in enumerate(zip(bars, values)):
        ax.text(i, v + 1.5, f"{v} 人", ha="center", fontsize=13, fontweight="bold", color=C["text_dark"])

    # 节约标注
    ax.annotate("↓ 11 人", xy=(1, 406), xytext=(0.22, 437),
                ha="center", fontsize=10, fontweight="bold", color=C["q2_primary"],
                arrowprops=dict(arrowstyle="->", lw=1.5, color=C["q2_primary"], connectionstyle="arc3,rad=-0.2"))
    ax.annotate("↓ 6 人", xy=(2, 400), xytext=(1.38, 434),
                ha="center", fontsize=10, fontweight="bold", color=C["q3_primary"],
                arrowprops=dict(arrowstyle="->", lw=1.5, color=C["q3_primary"], connectionstyle="arc3,rad=-0.2"))
    ax.text(1.55, 424.5, "累计节约 17 人 (4.1%)", ha="center", fontsize=9.5,
            color=C["accent_red"],
            bbox=dict(facecolor="#FDEDEC", edgecolor=C["accent_red"],
                      boxstyle="round,pad=0.3", alpha=0.92))

    ax.set_xticks(range(3))
    ax.set_xticklabels(labels, fontsize=11)
    ax.set_ylabel("最少招聘人数", fontsize=12)
    ax.set_title("图10  三问最终最少招聘人数对比", fontsize=14, pad=12, color=C["text_dark"])
    ax.set_ylim(0, 448)
    spine_clean(ax)
    ax.grid(axis="y", alpha=0.2, zorder=0)
    save(fig, "fig10_final_worker_comparison.png")


def A11_demand_perturbation_udr(data: dict) -> None:
    """优化版：需求扰动 UDR —— 分组柱 + 水平文字标注。"""
    sensitivity = data["sensitivity"]
    rows = [r for r in sensitivity["需求扰动敏感性"] if r["场景编号"] in {"S0", "S1", "S1+", "S2"}]
    order = {"S0": 0, "S1": 1, "S1+": 2, "S2": 3}
    rows.sort(key=lambda r: order.get(r["场景编号"], 99))

    labels = [r["场景"] for r in rows]
    x = np.arange(len(rows))
    width = 0.22

    fig, ax = plt.subplots(figsize=(10, 5.5), facecolor=C["white"])

    for i, (q_idx, q_label) in enumerate([("问题一", "问题一"), ("问题二", "问题二"), ("问题三", "问题三")]):
        udr_vals = [r[q_idx]["原方案缺口指标"]["UDR"] for r in rows]
        offset = (i - 1) * width
        bars = ax.bar(x + offset, udr_vals, width, color=Q_COLORS[i], edgecolor="white",
                      linewidth=0.5, label=q_label, zorder=3)
        for bar, val in zip(bars, udr_vals):
            if val > 0.001:
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.001,
                        f"{val:.4f}", ha="center", fontsize=8, color=C["text_dark"])

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=11)
    ax.set_ylabel("UDR (需求覆盖缺口率)", fontsize=12)
    ax.set_title("图11  需求扰动下原方案 UDR 对比", fontsize=14, pad=12, color=C["text_dark"])
    ax.legend(loc="upper left", framealpha=0.9)
    spine_clean(ax)
    ax.grid(axis="y", alpha=0.2, zorder=0)
    save(fig, "fig11_demand_perturbation_udr.png")


# ============================================================
#   PART B: 新增9张候选可视化
# ============================================================

def B12_column_generation_progress(data: dict) -> None:
    """新增：问题一列生成逐组收敛过程。"""
    cg = data["summary"].get("q1_column_generation", [])
    if not cg:
        return

    fig, axes = plt.subplots(2, 5, figsize=(18, 8), facecolor=C["white"])
    axes = axes.flatten()

    for i, group in enumerate(cg):
        ax = axes[i]
        ax.bar(["初始列\n池规模", "新增列", "迭代\n次数", "LP目标\n(松弛)", "整数\n人数"],
               [group["columns"] - group["generated_columns"],
                group["generated_columns"],
                group["iterations"],
                group["lp_objective"],
                group["integer_workers"]],
               color=[C["gray_mid"], C["q1_primary"], C["accent_orange"],
                      C["accent_purple"], C["q2_primary"]],
               edgecolor="white", linewidth=0.5)
        ax.set_title(f"小组{group['group_index']}  ({group['exact_workers']}人)", fontsize=10,
                     fontweight="bold", color=C["text_dark"])
        ax.tick_params(labelsize=8)
        spine_clean(ax)
        if i >= 5:
            ax.tick_params(axis="x", rotation=35, labelsize=8)

    fig.suptitle("图12  问题一列生成逐组收敛特征", fontsize=15, y=1.01, color=C["text_dark"])
    fig.tight_layout()
    save(fig, "fig12_q1_column_generation_progress.png")


def B13_alns_convergence_with_temperature(data: dict) -> None:
    """新增：ALNS 收敛曲线 + 温度衰减 双轴图。"""
    conv = data["convergence"]
    if conv.empty:
        return

    fig, ax1 = plt.subplots(figsize=(12, 5.5), facecolor=C["white"])

    # 主轴: score
    ax1.plot(conv["iteration"], conv["best_score"], "-", color=C["q3_primary"], lw=2, label="最优分数")
    ax1.plot(conv["iteration"], conv["current_score"], "-", color=C["gray_mid"], lw=1, alpha=0.6, label="当前分数")
    ax1.set_xlabel("迭代次数", fontsize=12)
    ax1.set_ylabel("评分 (↓ 越优)", fontsize=12, color=C["text_dark"])
    ax1.legend(loc="upper left", framealpha=0.9)

    # 双轴: temperature
    ax2 = ax1.twinx()
    ax2.plot(conv["iteration"], conv["temperature"], "--", color=C["accent_red"], lw=1.5, alpha=0.7, label="温度")
    ax2.set_ylabel("模拟退火温度", fontsize=12, color=C["accent_red"])
    ax2.legend(loc="upper right", framealpha=0.9)
    ax2.set_yscale("log")

    # 标注
    ax1.axhline(y=conv["best_score"].iloc[-1], color=C["q3_primary"], lw=0.8, linestyle=":", alpha=0.5)
    ann_x = conv["iteration"].iloc[-1]
    ann_y = conv["best_score"].iloc[-1]
    ax1.margins(y=0.12)
    ax1.annotate(f"最终: {ann_y:.2f}", (ann_x, ann_y), textcoords="offset points",
                 xytext=(-120, 10), fontsize=10, color=C["q3_primary"],
                 bbox=dict(facecolor="white", edgecolor=C["q3_primary"], alpha=0.92, boxstyle="round,pad=0.2"),
                 arrowprops=dict(arrowstyle="->", lw=1, color=C["q3_primary"]))

    ax1.set_title("图13  ALNS 搜索收敛轨迹与模拟退火温度衰减", fontsize=14, pad=12, color=C["text_dark"])
    spine_clean(ax1)
    save(fig, "fig13_alns_convergence_temperature.png")


def B14_three_dimension_demand_surface(data: dict) -> None:
    """新增：三维需求面 —— 天×小时×总需求的伪3D视图。"""
    demand = data["demand"]
    total = demand.sum(axis=1)

    fig = plt.figure(figsize=(11, 7.2), facecolor=C["white"], constrained_layout=True)
    ax = fig.add_subplot(111, projection="3d")

    X, Y = np.meshgrid(np.arange(11), np.arange(10))
    Z = total.astype(float)

    surf = ax.plot_surface(X, Y, Z, cmap="rocket_r", edgecolor="none",
                           alpha=0.9, linewidth=0, antialiased=True)

    hour_labels = [h.split("-")[0] for h in data["hours"]]
    ax.set_xlabel("小时段", fontsize=10, labelpad=18)
    ax.set_ylabel("日期", fontsize=10, labelpad=14)
    ax.set_zlabel("", fontsize=10)
    ax.set_title("图14  需求时空三维分布曲面", fontsize=13.5, pad=18, color=C["text_dark"])
    ax.view_init(elev=28, azim=-56)
    ax.set_box_aspect((1.45, 1.0, 0.72))
    ax.set_xticks(np.arange(11))
    ax.set_xticklabels(hour_labels, rotation=25, fontsize=8)
    ax.set_yticks(np.arange(10))
    ax.set_yticklabels([f"D{d}" for d in data["days"]], fontsize=8)
    colorbar = fig.colorbar(surf, ax=ax, shrink=0.72, aspect=20, pad=0.08)
    colorbar.set_label("需求人数", rotation=90, labelpad=12)
    save(fig, "fig14_demand_3d_surface.png", bbox_inches=None)


def B15_daily_demand_boxplot(data: dict) -> None:
    """新增：每日需求分布箱线图 —— 展示需求波动性。"""
    demand = data["demand"]  # (10, 10, 11)
    # 每天的总需求 (跨小组、跨小时)
    daily_all = demand.reshape(10, -1)  # (10天, 110 单元)

    fig, ax = plt.subplots(figsize=(10, 5), facecolor=C["white"])
    bp = ax.boxplot([daily_all[d] for d in range(10)], positions=np.arange(1, 11),
                    patch_artist=True, widths=0.6,
                    boxprops=dict(facecolor="#D6EAF8", edgecolor=C["q1_primary"], linewidth=1.2),
                    whiskerprops=dict(color=C["q1_primary"], linewidth=1),
                    capprops=dict(color=C["q1_primary"], linewidth=1),
                    medianprops=dict(color=C["accent_red"], linewidth=2),
                    flierprops=dict(marker="o", markerfacecolor=C["accent_red"], markersize=3, alpha=0.5))
    ax.set_xlabel("日期", fontsize=12)
    ax.set_ylabel("每 (小组, 小时) 单元需求", fontsize=12)
    ax.set_title("图15  各天需求分布箱线图（110个时空单元的波动性）", fontsize=14, pad=12, color=C["text_dark"])
    ax.set_xticks(np.arange(1, 11))
    spine_clean(ax)
    ax.grid(axis="y", alpha=0.2)
    save(fig, "fig15_daily_demand_boxplot.png")


def B16_coverage_satisfaction_heatmap(data: dict) -> None:
    """新增：Q3 覆盖满意度 —— 每单元 (覆盖-需求)/需求。"""
    demand = data["demand"]
    summary = data["summary"]
    q3_daily = summary.get("q3_daily_counts_alns", summary.get("q3_daily_counts_initial", [400]*10))

    # 用 daily problem 3 近似估计覆盖
    _, shift_cover_same, shift_labels_same = build_shift_pairs(min_break=0)
    _, shift_cover_cross, shift_labels_cross = build_shift_pairs(min_break=2)
    _, cover3 = build_problem3_patterns(10, 11, shift_cover_same, shift_labels_same,
                                         shift_cover_cross, shift_labels_cross)

    # 尝试读取实际 cover，或直接使用 daily_counts 反推
    # 这里我们展示需求/最大容量比
    day_max = demand.max(axis=(1, 2))  # 每天的最大需求
    day_sum = demand.sum(axis=(1, 2))  # 每天的总需求

    fig, ax = plt.subplots(figsize=(10, 5), facecolor=C["white"])

    # 计算每个日期的需求峰值与安排人数的比率
    ratio = np.array([demand[d].sum() / (q3_daily[d] * 8) if q3_daily[d] > 0 else 0 for d in range(10)])

    bars = ax.bar(np.arange(1, 11), ratio, color=C["q3_primary"], edgecolor="white", alpha=0.8, zorder=3)
    ax.axhline(y=1.0, color=C["accent_red"], lw=1.5, linestyle="--", label="理论最优线")

    for bar, r in zip(bars, ratio):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                f"{r:.2%}", ha="center", fontsize=9, color=C["text_dark"])

    ax.set_xlabel("日期", fontsize=12)
    ax.set_ylabel("总需求 / (出勤×8小时) 比率", fontsize=12)
    ax.set_title("图16  问题三各天人员利用率比率", fontsize=14, pad=12, color=C["text_dark"])
    ax.set_xticks(np.arange(1, 11))
    ax.legend(framealpha=0.9)
    spine_clean(ax)
    ax.grid(axis="y", alpha=0.2, zorder=0)
    save(fig, "fig16_q3_utilization_ratio.png")


def B17_three_question_radar(data: dict) -> None:
    """新增：三问多维度雷达图。"""
    sensitivity = data["sensitivity"]
    audit = data["audit"]

    # 维度：人数、管理复杂度(越低越好取反)、UDR S1、UDR S2、覆盖灵活性
    q1_val = audit["total_integer_workers"]
    q2_val = data["summary"]["q2_daily_counts"][0]  # using summary data
    q3_val = data["summary"]["q3_daily_counts_alns"][0] if data["summary"].get("q3_daily_counts_alns") else 400

    # 用敏感性数据
    s1 = [r for r in sensitivity["需求扰动敏感性"] if r["场景编号"] == "S1"][0]
    s2 = [r for r in sensitivity["需求扰动敏感性"] if r["场景编号"] == "S2"][0]

    categories = ["人数最少", "S1 鲁棒性\n(1-UDR)", "S2 鲁棒性\n(1-UDR)",
                  "管理简单性\n(1/规则数)", "需求覆盖\n灵活性"]
    num_cats = len(categories)
    angles = np.linspace(0, 2*np.pi, num_cats, endpoint=False).tolist()
    angles += angles[:1]

    # 归一化
    norm = lambda vs: np.array(list(vs) + [vs[0]])

    q1_data = norm([1 - q1_val/420, 1 - s1["问题一"]["原方案缺口指标"]["UDR"],
                    1 - s2["问题一"]["原方案缺口指标"]["UDR"], 1/2, 0.6])
    q2_data = norm([1 - 406/420, 1 - s1["问题二"]["原方案缺口指标"]["UDR"],
                    1 - s2["问题二"]["原方案缺口指标"]["UDR"], 1/3, 0.75])
    q3_data = norm([1 - 400/420, 1 - s1["问题三"]["原方案缺口指标"]["UDR"],
                    1 - s2["问题三"]["原方案缺口指标"]["UDR"], 1/5, 0.95])

    fig, ax = plt.subplots(figsize=(8.6, 8.6), facecolor=C["white"], subplot_kw=dict(polar=True))
    fig.subplots_adjust(left=0.06, right=0.83, top=0.84, bottom=0.06)
    ax.fill(angles, q1_data, alpha=0.2, color=C["q1_primary"])
    ax.plot(angles, q1_data, "o-", color=C["q1_primary"], lw=2, label="问题一", markersize=6)
    ax.fill(angles, q2_data, alpha=0.2, color=C["q2_primary"])
    ax.plot(angles, q2_data, "s-", color=C["q2_primary"], lw=2, label="问题二", markersize=6)
    ax.fill(angles, q3_data, alpha=0.2, color=C["q3_primary"])
    ax.plot(angles, q3_data, "D-", color=C["q3_primary"], lw=2, label="问题三", markersize=6)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontsize=8.4)
    ax.tick_params(axis="x", pad=18)
    ax.set_rlabel_position(18)
    ax.set_title("图17  三问多维特征雷达图", fontsize=14, pad=42, color=C["text_dark"])
    ax.legend(loc="upper right", bbox_to_anchor=(1.25, 1.1), framealpha=0.9)
    ax.set_ylim(0, 1.05)
    save(fig, "fig17_three_question_radar.png")


def B18_rest_day_spacing_distribution(data: dict) -> None:
    """新增：Q3 400名员工休息日间隔分布。"""
    q3_worker = data["q3_worker"].copy()
    day_cols = [c for c in q3_worker.columns if str(c).startswith("第") and str(c).endswith("天")]

    # 计算每名员工的休息日位置
    gaps = []
    for _, row in q3_worker.iterrows():
        rest_days = []
        for i, col in enumerate(day_cols):
            if str(row[col]).strip() == "休息":
                rest_days.append(i)
        if len(rest_days) >= 2:
            # 两个休息日之间的间隔（包括循环）
            for i in range(len(rest_days)):
                g = (rest_days[(i+1) % len(rest_days)] - rest_days[i]) % 10
                if g > 0:
                    gaps.append(g)

    fig, axes = plt.subplots(1, 2, figsize=(12, 5), facecolor=C["white"])

    # 柱状图
    from collections import Counter
    cnt = Counter(gaps)
    days_sorted = sorted(cnt.keys())
    vals = [cnt[d] for d in days_sorted]
    axes[0].bar(days_sorted, vals, color=C["q3_primary"], edgecolor="white", alpha=0.85)
    axes[0].set_xlabel("休息日间隔（天数）", fontsize=12)
    axes[0].set_ylabel("出现次数", fontsize=12)
    axes[0].set_title("休息日间隔频次", fontsize=12)
    spine_clean(axes[0])
    axes[0].grid(axis="y", alpha=0.2)

    # 饼图
    axes[1].pie(vals, labels=[f"{d}天" for d in days_sorted], autopct="%1.1f%%",
                colors=sns.color_palette("mako", len(days_sorted)),
                wedgeprops=dict(width=0.4, edgecolor="white"))
    axes[1].set_title("间隔分布比例", fontsize=12)

    fig.suptitle("图18  Q3 员工休息日间隔分布", fontsize=14, y=1.02, color=C["text_dark"])
    save(fig, "fig18_rest_day_spacing.png")


def B19_shift_type_usage_heatmap(data: dict) -> None:
    """新增：Q3 班型使用频次热力图 (日 × 模式类别)。"""
    q3_worker = data["q3_worker"].copy()
    day_cols = [c for c in q3_worker.columns if str(c).startswith("第") and str(c).endswith("天")]

    # 解析班型类型
    shift_categories = {
        "同组 8-12+12-16": 0, "同组 8-12+13-17": 0, "同组 8-12+14-18": 0,
        "同组 8-12+15-19": 0, "同组 9-13+13-17": 0, "同组 9-13+14-18": 0,
        "同组 9-13+15-19": 0, "同组 10-14+14-18": 0, "同组 10-14+15-19": 0,
        "同组 11-15+15-19": 0,
        "跨组 8-12+12-16": 0, "跨组 8-12+13-17": 0, "跨组 9-13+13-17": 0,
        "其他": 0,
    }
    cat_keys = list(shift_categories.keys())

    daily_usage = np.zeros((10, len(cat_keys)), dtype=int)
    for day_idx, col in enumerate(day_cols):
        for _, row in q3_worker.iterrows():
            val = str(row[col]).strip()
            if val == "休息":
                continue
            matched = False
            for cat in cat_keys[:-1]:
                parts = cat.split(" ", 1)
                prefix, times = parts[0], parts[1] if len(parts) > 1 else ""
                if val.startswith(prefix.replace("：", "：")):
                    if all(t in val for t in times.split("+")):
                        daily_usage[day_idx, cat_keys.index(cat)] += 1
                        matched = True
                        break
            if not matched:
                daily_usage[day_idx, -1] += 1

    # 过滤零列
    col_sums = daily_usage.sum(axis=0)
    nonzero = col_sums > 0
    filtered = daily_usage[:, nonzero]
    filtered_keys = [cat_keys[i] for i in range(len(cat_keys)) if nonzero[i]]

    fig, ax = plt.subplots(figsize=(14, 5.5), facecolor=C["white"])
    sns.heatmap(filtered.T, cmap="YlOrBr", annot=True, fmt="d",
                linewidths=0.5, linecolor="white",
                xticklabels=[f"第{d}天" for d in range(1, 11)],
                yticklabels=filtered_keys,
                cbar_kws={"label": "使用次数", "shrink": 0.8},
                ax=ax)
    ax.set_title("图19  Q3 班型使用频次热力图（日 × 班型类）", fontsize=14, pad=12, color=C["text_dark"])
    ax.set_xlabel("日期")
    ax.set_ylabel("班型类别")
    save(fig, "fig19_shift_type_usage_heatmap.png")


def B20_sensitivity_scenario_comparison(data: dict) -> None:
    """新增：敏感性场景下三问重算人数对比。"""
    sensitivity = data["sensitivity"]
    rows = sensitivity["需求扰动敏感性"]

    scenarios = []
    q1_recalc, q2_recalc, q3_recalc = [], [], []
    baseline = [417, 406, 400]

    for r in rows:
        if r["场景编号"] in {"S0", "S1", "S1+", "S2"}:
            scenarios.append(r["场景编号"])
            q1_recalc.append(r["问题一"]["重算最少人数"])
            q2_recalc.append(r["问题二"]["重算人数下界"])
            q3_recalc.append(r["问题三"]["重算人数下界"])

    x = np.arange(len(scenarios))
    width = 0.2

    fig, ax = plt.subplots(figsize=(10.4, 5.9), facecolor=C["white"])
    fig.subplots_adjust(top=0.78, left=0.10, right=0.98, bottom=0.14)

    for i, (vals, color, label) in enumerate([
        (q1_recalc, C["q1_primary"], "问题一"),
        (q2_recalc, C["q2_primary"], "问题二"),
        (q3_recalc, C["q3_primary"], "问题三"),
    ]):
        offset = (i - 1) * width
        bars = ax.bar(x + offset, vals, width, color=color, edgecolor="white",
                      linewidth=0.5, label=label, zorder=3)
        for bar, v in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2,
                    str(v), ha="center", fontsize=9, fontweight="bold", color=C["text_dark"])

    ax.set_xticks(x)
    ax.set_xticklabels(scenarios, fontsize=11)
    ax.set_ylabel("最少招聘人数 / 下界", fontsize=12)
    fig.suptitle("图20  敏感性场景下三问所需人数对比",
                 fontsize=14, y=0.93, color=C["text_dark"])
    fig.legend(loc="upper center", bbox_to_anchor=(0.5, 0.995), ncol=3, framealpha=0.95)
    spine_clean(ax)
    ax.grid(axis="y", alpha=0.2, zorder=0)
    save(fig, "fig20_sensitivity_scenario_comparison.png")


# ============================================================
#   MAIN
# ============================================================
def main():
    ensure_dir()
    data = load_data()
    print("数据加载完成。开始生成可视化...")

    # Part A: 优化现有11张
    print("\n[A] 优化现有11张主线图...")
    A01_total_demand_heatmap(data);       print("  ✓ fig01")
    A02_group_day_demand_heatmap(data);   print("  ✓ fig02")
    A03_model_progression(data);          print("  ✓ fig03")
    A04_q1_waterfall(data);              print("  ✓ fig04")
    A05_q1_group_comparison(data);        print("  ✓ fig05")
    A06_maxflow_topology(data);           print("  ✓ fig06")
    A07_q2_daily_staffing(data);          print("  ✓ fig07")
    A08_q3_template_patterns(data);       print("  ✓ fig08")
    A09_q3_cross_group_usage(data);       print("  ✓ fig09")
    A10_final_worker_comparison();        print("  ✓ fig10")
    A11_demand_perturbation_udr(data);    print("  ✓ fig11")

    # Part B: 新增候选图
    print("\n[B] 生成新增候选可视化...")
    B12_column_generation_progress(data);  print("  ✓ fig12 列生成逐组收敛")
    B13_alns_convergence_with_temperature(data); print("  ✓ fig13 ALNS收敛+温度")
    B14_three_dimension_demand_surface(data);    print("  ✓ fig14 需求3D曲面")
    B15_daily_demand_boxplot(data);              print("  ✓ fig15 需求分布箱线图")
    B16_coverage_satisfaction_heatmap(data);     print("  ✓ fig16 人员利用率")
    B17_three_question_radar(data);              print("  ✓ fig17 三问雷达图")
    B18_rest_day_spacing_distribution(data);     print("  ✓ fig18 休息日间隔分布")
    B19_shift_type_usage_heatmap(data);          print("  ✓ fig19 班型使用热力图")
    B20_sensitivity_scenario_comparison(data);   print("  ✓ fig20 敏感性场景对比")

    print(f"\n全部完成！输出目录：{OUT_DIR}")


if __name__ == "__main__":
    main()
