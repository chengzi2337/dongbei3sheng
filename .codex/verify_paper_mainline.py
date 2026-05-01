from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CODEX = ROOT / ".codex"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def assert_contains(text: str, snippets: list[str], name: str) -> None:
    missing = [snippet for snippet in snippets if snippet not in text]
    if missing:
        raise AssertionError(f"{name} 缺少关键内容：{missing}")


def main() -> None:
    summary = json.loads((ROOT / "independent_advanced_summary.json").read_text(encoding="utf-8"))
    sensitivity = json.loads((CODEX / "paper-sensitivity-results.json").read_text(encoding="utf-8"))
    mainline = read_text(CODEX / "paper-advanced-model-mainline.md")
    context = read_text(CODEX / "context-summary-论文高级模型主线.md")
    independent_report = read_text(CODEX / "independent-verification-report.md")

    items = {item["问题"]: item for item in summary["summary"]}
    assert items["问题1"]["独立求解人数"] == 417
    assert items["问题2"]["理论下界"] == 406
    assert items["问题2"]["独立求解人数"] == 406
    assert items["问题3"]["理论下界"] == 400
    assert items["问题3"]["独立求解人数"] == 400
    assert sum(row["integer_workers"] for row in summary["q1_column_generation"]) == 417
    assert all(row["integer_slack"] == 0 for row in summary["q1_column_generation"])
    assert summary["q3_final_metrics"]["deficit"] == 0
    assert summary["q3_final_metrics"]["min_worker_days"] == 8
    assert summary["q3_final_metrics"]["max_worker_days"] == 8

    demand_rows = {row["场景"]: row for row in sensitivity["需求扰动敏感性"]}
    assert demand_rows["基准"]["问题一精确人数"] == 417
    assert demand_rows["需求上浮5%"]["问题二人数下界"] == 436
    assert demand_rows["需求上浮10%"]["问题三人数下界"] == 447
    rest_rows = {row["跨组最小休息小时"]: row for row in sensitivity["休息间隔敏感性"]}
    assert rest_rows[2]["问题三合法模式数"] == 370
    assert rest_rows[3]["问题三人数下界"] == 401

    with (ROOT / "independent_q3_alns_convergence.csv").open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) >= 10
    assert rows[-1]["iteration"] == "180"
    assert float(rows[-1]["best_deficit"]) == 0.0

    assert_contains(
        mainline,
        [
            "问题一：列生成精确优化模型",
            "问题二：理论下界与网络流映射模型",
            "问题三：异构任务匹配与 ALNS 精细重构模型",
            "| 问题二 | 单日最少出勤下界、最大流工作日映射 | 406 | 406",
            "| 问题三 | 异构任务下界、最大流初始化、ALNS 重构 | 400 | 400",
            "ALNS 不承担全局最优证明",
            "重新生成敏感性分析",
        ],
        "论文主线材料",
    )
    assert_contains(
        context,
        ["不导入原始简单模型", "不读取旧结果表", "不硬编码 417、406、400"],
        "上下文摘要",
    )
    assert_contains(
        independent_report,
        ["独立求解运行：通过", "问题2：理论下界为 406", "问题3：理论下界为 400"],
        "独立验证报告",
    )

    print("论文高级模型主线一致性验证通过")


if __name__ == "__main__":
    main()
