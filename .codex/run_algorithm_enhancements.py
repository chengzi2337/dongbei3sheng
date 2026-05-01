from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / ".codex"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import independent_advanced_staff_scheduling as model  # noqa: E402


def parse_seeds(value: str) -> list[int]:
    return [int(part.strip()) for part in value.split(",") if part.strip()]


def markdown_table(rows: list[dict[str, object]], columns: list[str]) -> str:
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    lines = [header, separator]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(column, "")) for column in columns) + " |")
    return "\n".join(lines)


def find_input_file() -> Path:
    candidates = [path for path in ROOT.glob("*.xlsx") if path.name.endswith("1.xlsx")]
    if len(candidates) != 1:
        raise RuntimeError(f"未能唯一识别原始附件：{candidates}")
    return candidates[0]


def build_q3_base() -> dict[str, object]:
    input_file = find_input_file()
    demand, days, hours, group_cols = model.read_demand(input_file)
    _same_pairs, shift_cover_same, shift_labels_same = model.build_shift_pairs(0)
    _cross_pairs, shift_cover_cross, shift_labels_cross = model.build_shift_pairs(2)
    patterns, pattern_cover = model.build_problem3_patterns(
        demand.shape[1],
        demand.shape[2],
        shift_cover_same,
        shift_labels_same,
        shift_cover_cross,
        shift_labels_cross,
    )

    day_minima: list[int] = []
    x_days: list[np.ndarray] = []
    for day in range(demand.shape[0]):
        count, x_day, _ = model.solve_daily_problem3(demand[day], pattern_cover)
        day_minima.append(int(count))
        x_days.append(x_day)
    worker_count, daily_counts = model.choose_daily_counts(day_minima)
    work_matrix = model.build_workday_assignment(worker_count, daily_counts, "max_flow")
    daily_pattern_ids = model.expand_pattern_ids_with_extras(x_days, daily_counts, demand, pattern_cover)
    initial_assignments = model.initial_assignments_from_flow(work_matrix, daily_pattern_ids)
    initial_metrics = model.validate_feasible("增强实验初始排班", initial_assignments, demand, pattern_cover)
    return {
        "input_file": str(input_file),
        "demand": demand,
        "days": days,
        "hours": hours,
        "group_cols": group_cols,
        "patterns": patterns,
        "pattern_cover": pattern_cover,
        "day_minima": day_minima,
        "lower_bound": model.theoretical_worker_bound(day_minima),
        "worker_count": worker_count,
        "daily_counts": daily_counts,
        "initial_assignments": initial_assignments,
        "initial_metrics": initial_metrics,
    }


def run_alns_case(base: dict[str, object], name: str, config: model.AlnsConfig) -> dict[str, object]:
    started = time.perf_counter()
    alns = model.Q3Alns(
        base["demand"],  # type: ignore[arg-type]
        base["pattern_cover"],  # type: ignore[arg-type]
        base["initial_assignments"],  # type: ignore[arg-type]
        config,
    )
    result = alns.run()
    elapsed = time.perf_counter() - started
    metrics = model.validate_feasible(
        f"{name}增强实验",
        result.best_assignments,
        base["demand"],  # type: ignore[arg-type]
        base["pattern_cover"],  # type: ignore[arg-type]
    )
    return {
        "场景": name,
        "seed": config.seed,
        "iterations": config.iterations,
        "best_score": float(result.best_score),
        "deficit": metrics["deficit"],
        "surplus": metrics["surplus"],
        "max_surplus": metrics["max_surplus"],
        "surplus_square": metrics["surplus_square"],
        "day_worker_std": metrics["day_worker_std"],
        "elapsed_seconds": elapsed,
        "destroy_operators": ",".join(config.destroy_operators),
        "repair_operators": ",".join(config.repair_operators),
    }


def run_operator_ablation(base: dict[str, object], iterations: int, seed: int) -> pd.DataFrame:
    cases = [
        ("默认算子", model.AlnsConfig(iterations=iterations, seed=seed)),
        (
            "增强目标",
            model.AlnsConfig(
                iterations=iterations,
                seed=seed,
                max_surplus_weight=0.2,
                surplus_square_weight=0.002,
            ),
        ),
        (
            "去除高冗余破坏",
            model.AlnsConfig(
                iterations=iterations,
                seed=seed,
                destroy_operators=("random_assignments", "whole_workers", "whole_days"),
            ),
        ),
        (
            "仅高冗余破坏",
            model.AlnsConfig(iterations=iterations, seed=seed, destroy_operators=("high_surplus",)),
        ),
        (
            "仅regret修复",
            model.AlnsConfig(iterations=iterations, seed=seed, repair_operators=("regret",)),
        ),
    ]
    return pd.DataFrame([run_alns_case(base, name, config) for name, config in cases])


def run_seed_stability(base: dict[str, object], iterations: int, seeds: Iterable[int]) -> pd.DataFrame:
    rows = []
    for seed in seeds:
        config = model.AlnsConfig(
            iterations=iterations,
            seed=int(seed),
            max_surplus_weight=0.2,
            surplus_square_weight=0.002,
        )
        rows.append(run_alns_case(base, "多随机种子稳定性", config))
    return pd.DataFrame(rows)


def run_min_cost_smoke() -> dict[str, object]:
    worker_count = 5
    daily_counts = np.full(10, 4, dtype=int)
    work = model.build_workday_assignment(worker_count, daily_counts, "min_cost")
    return {
        "worker_count": worker_count,
        "daily_counts": daily_counts.tolist(),
        "worker_day_sums": work.sum(axis=1).astype(int).tolist(),
        "day_worker_sums": work.sum(axis=0).astype(int).tolist(),
        "passed": bool(np.all(work.sum(axis=1) == 8) and np.all(work.sum(axis=0) == daily_counts)),
    }


def write_sensitivity_markdown() -> Path | None:
    source = OUT_DIR / "paper-sensitivity-results.json"
    if not source.exists():
        return None
    data = json.loads(source.read_text(encoding="utf-8"))
    sections = ["# 敏感性分析论文表格\n"]
    demand_rows = [
        {
            "场景": row["场景"],
            "需求倍率": row["需求倍率"],
            "问题一人数": row["问题一精确人数"],
            "问题二下界": row["问题二人数下界"],
            "问题三下界": row["问题三人数下界"],
        }
        for row in data["需求扰动敏感性"]
    ]
    sections.append("## 需求扰动\n")
    sections.append(markdown_table(demand_rows, ["场景", "需求倍率", "问题一人数", "问题二下界", "问题三下界"]))

    sections.append("\n## 工作天数扰动\n")
    sections.append(markdown_table(data["工作天数敏感性"], ["每人工作天数", "问题二人数下界", "问题三人数下界"]))

    sections.append("\n## 跨组休息间隔扰动\n")
    rest_rows = [
        {
            "跨组最小休息小时": row["跨组最小休息小时"],
            "合法模式数": row["问题三合法模式数"],
            "问题三总人次": row["问题三单日最少出勤总人次"],
            "问题三下界": row["问题三人数下界"],
        }
        for row in data["休息间隔敏感性"]
    ]
    sections.append(markdown_table(rest_rows, ["跨组最小休息小时", "合法模式数", "问题三总人次", "问题三下界"]))
    output = OUT_DIR / "sensitivity-paper-table.md"
    output.write_text("\n\n".join(sections), encoding="utf-8")
    return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="六点保守算法增强实验")
    parser.add_argument("--iterations", type=int, default=60, help="每个ALNS实验的轻量迭代次数")
    parser.add_argument("--seeds", default="20260429,20260430,20260431", help="逗号分隔的稳定性随机种子")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    base = build_q3_base()
    ablation = run_operator_ablation(base, args.iterations, 20260429)
    stability = run_seed_stability(base, args.iterations, parse_seeds(args.seeds))
    min_cost_smoke = run_min_cost_smoke()
    sensitivity_path = write_sensitivity_markdown()

    ablation_path = OUT_DIR / "q3_operator_ablation.csv"
    stability_path = OUT_DIR / "q3_seed_stability.csv"
    result_path = OUT_DIR / "algorithm-enhancement-results.json"
    ablation.to_csv(ablation_path, index=False, encoding="utf-8-sig")
    stability.to_csv(stability_path, index=False, encoding="utf-8-sig")
    result = {
        "数据来源": base["input_file"],
        "问题三理论下界": base["lower_bound"],
        "问题三人数": base["worker_count"],
        "问题三单日最少出勤": base["day_minima"],
        "初始指标": base["initial_metrics"],
        "算子消融输出": str(ablation_path),
        "多随机种子输出": str(stability_path),
        "最小费用工作日映射烟测": min_cost_smoke,
        "敏感性论文表": str(sensitivity_path) if sensitivity_path else "未找到paper-sensitivity-results.json",
    }
    result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"写入：{result_path}")
    print(f"写入：{ablation_path}")
    print(f"写入：{stability_path}")
    if sensitivity_path:
        print(f"写入：{sensitivity_path}")


if __name__ == "__main__":
    main()
