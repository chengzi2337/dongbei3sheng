from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CODEX = ROOT / ".codex"
MAINLINE_DIR = ROOT / "visualizations" / "mainline"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def assert_contains(text: str, snippets: list[str], name: str) -> None:
    missing = [snippet for snippet in snippets if snippet not in text]
    if missing:
        raise AssertionError(f"{name} 缺少关键内容：{missing}")


def assert_not_contains(text: str, snippets: list[str], name: str) -> None:
    hits = [snippet for snippet in snippets if snippet in text]
    if hits:
        raise AssertionError(f"{name} 仍包含不应出现的旧表述：{hits}")


def assert_exists(paths: list[Path], name: str) -> None:
    missing = [str(path) for path in paths if not path.exists()]
    if missing:
        raise AssertionError(f"{name} 缺少文件：{missing}")


def main() -> None:
    audit = read_json(ROOT / "q1_video_discrepancy_audit.json")
    summary = read_json(ROOT / "advanced_summary.json")
    independent = read_json(ROOT / "independent_advanced_summary.json")
    sensitivity = read_json(CODEX / "paper-sensitivity-results.json")
    mainline = read_text(CODEX / "paper-advanced-model-mainline.md")
    figure_plan = read_text(CODEX / "paper-figure-plan.md")
    gap_report = read_text(CODEX / "paper-v3-gap-report.md")
    context = read_text(CODEX / "context-summary-论文V3缺口补齐.md")

    assert audit["total_lp_relaxation"] == 411.375
    assert audit["total_ceil_lp_bound"] == 415
    assert audit["total_integer_workers"] == 417
    assert audit["gap_integer_minus_ceil_lp"] == 2

    advanced_items = {item["问题"]: item for item in summary["summary"]}
    assert advanced_items["问题1"]["高级方法人数"] == 417
    assert advanced_items["问题2"]["理论下界"] == 406
    assert advanced_items["问题2"]["高级方法人数"] == 406
    assert advanced_items["问题3"]["理论下界"] == 400
    assert advanced_items["问题3"]["高级方法人数"] == 400

    independent_items = {item["问题"]: item for item in independent["summary"]}
    assert independent_items["问题1"]["独立求解人数"] == 417
    assert independent_items["问题2"]["理论下界"] == 406
    assert independent_items["问题3"]["理论下界"] == 400

    demand_rows = {row["场景编号"]: row for row in sensitivity["需求扰动敏感性"]}
    assert demand_rows["S0"]["问题三"]["重算合法模式数"] == 370
    assert demand_rows["S1"]["问题一"]["重算最少人数"] == 447
    assert demand_rows["S1"]["问题二"]["重算人数下界"] == 436
    assert demand_rows["S1"]["问题三"]["重算人数下界"] == 430
    assert demand_rows["S2"]["高峰小时"] == ["9:00-10:00", "14:00-15:00", "15:00-16:00"]

    absence_rows = {row["场景编号"]: row for row in sensitivity["随机缺勤敏感性"]}
    assert absence_rows["S3-3"]["问题一"]["平均UDR"] == 0.014172
    assert absence_rows["S3-3"]["问题二"]["平均UDR"] == 0.014059
    assert absence_rows["S3-3"]["问题三"]["平均UDR"] == 0.016517

    rest_rows = {row["跨组最小休息小时"]: row for row in sensitivity["休息间隔敏感性"]}
    assert rest_rows[2]["问题三合法模式数"] == 370
    assert rest_rows[3]["问题三人数下界"] == 401

    figure_files = [
        MAINLINE_DIR / "fig01_total_demand_heatmap.png",
        MAINLINE_DIR / "fig02_group_day_demand_heatmap.png",
        MAINLINE_DIR / "fig03_model_progression.png",
        MAINLINE_DIR / "fig04_q1_waterfall.png",
        MAINLINE_DIR / "fig05_q1_group_comparison.png",
        MAINLINE_DIR / "fig06_maxflow_topology.png",
        MAINLINE_DIR / "fig07_q2_daily_staffing.png",
        MAINLINE_DIR / "fig08_q3_template_patterns.png",
        MAINLINE_DIR / "fig09_q3_cross_group_usage.png",
        MAINLINE_DIR / "fig10_final_worker_comparison.png",
        MAINLINE_DIR / "fig11_demand_perturbation_udr.png",
    ]
    assert_exists(figure_files, "V3主线图")

    assert_contains(
        mainline,
        [
            "主要求解采用小规模聚合整数规划",
            "列生成仅作为复核与规模扩展框架使用",
            "13 类基础时间模板",
            "370 个合法日内服务模式",
            "15–20 人规模的待命储备池",
            "结合历史缺勤率或进一步分位数仿真",
            "问题三人数目标的全局最优性来自理论下界 400 与可行解 400 相等",
        ],
        "V3主线文稿",
    )
    assert_not_contains(
        mainline,
        [
            "15–20 人待命池可吸收 95% 以上扰动风险",
            "属于极小规模",
        ],
        "V3主线文稿",
    )

    assert_contains(
        figure_plan,
        [
            "图6 最大流工作日分解网络拓扑图",
            "图8 问题三 13 类基础时间模板与 370 个服务模式示意图",
            "图11 需求扰动下原方案 UDR 对比图",
            "fig11_demand_perturbation_udr.png",
        ],
        "V3图表规划",
    )

    assert_contains(
        gap_report,
        [
            "主要缺口不在算法本体",
            "fig06_maxflow_topology.png",
            "fig08_q3_template_patterns.png",
            "fig11_demand_perturbation_udr.png",
        ],
        "V3缺口报告",
    )

    assert_contains(
        context,
        [
            "问题一“小规模聚合 IP”证据",
            "主线图目录仍是旧 10 图版本",
            "待命池若写成“95% 风险保障”会超出现有仿真证据",
        ],
        "V3上下文摘要",
    )

    print("论文 V3 主线一致性验证通过")


if __name__ == "__main__":
    main()
