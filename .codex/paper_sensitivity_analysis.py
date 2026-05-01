from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT_PATH = ROOT / ".codex" / "paper-sensitivity-results.json"
Q1_SCHEDULE_PATH = ROOT / "q1_417_feasible_schedule.csv"
RANDOM_SEED = 20260501
ABSENCE_TRIALS = 200
PEAK_HOUR_COUNT = 3
Q3_ALNS_ITERATIONS = 180

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import independent_advanced_staff_scheduling as model  # noqa: E402


def find_input_file() -> Path:
    """使用文件结构识别原始附件，避免在脚本中写入旧结果依赖。"""

    candidates = [path for path in ROOT.glob("*.xlsx") if path.name.endswith("1.xlsx")]
    if len(candidates) != 1:
        raise RuntimeError(f"未能唯一识别原始附件：{candidates}")
    return candidates[0]


def q1_exact_total(demand: np.ndarray, shift_cover: np.ndarray) -> int:
    """问题一敏感性只重算精确人数，不重复运行列生成日志。"""

    total = 0
    for group_index in range(demand.shape[1]):
        total += model.solve_problem1_group_exact(demand[:, group_index, :], shift_cover)
    return int(total)


def q2_lower_bound(demand: np.ndarray, shift_cover: np.ndarray) -> tuple[int, int, list[int]]:
    day_minima: list[int] = []
    for day_index in range(demand.shape[0]):
        count, _, _ = model.solve_daily_problem2(demand[day_index], shift_cover)
        day_minima.append(int(count))
    total = int(sum(day_minima))
    return total, int(math.ceil(total / 8)), day_minima


def q3_lower_bound(
    demand: np.ndarray,
    group_count: int,
    hour_count: int,
    shift_cover_same: np.ndarray,
    shift_labels_same: list[tuple[int, int, int, int]],
    rest_gap: int,
) -> tuple[int, int, int, list[int]]:
    _, shift_cover_cross, shift_labels_cross = model.build_shift_pairs(rest_gap)
    patterns, pattern_cover = model.build_problem3_patterns(
        group_count,
        hour_count,
        shift_cover_same,
        shift_labels_same,
        shift_cover_cross,
        shift_labels_cross,
    )
    day_minima: list[int] = []
    for day_index in range(demand.shape[0]):
        count, _, _ = model.solve_daily_problem3(demand[day_index], pattern_cover)
        day_minima.append(int(count))
    total = int(sum(day_minima))
    return len(patterns), total, int(math.ceil(total / 8)), day_minima


def parse_clock(value: str) -> int:
    hour_str, minute_str = value.strip().split(":")
    return int(hour_str) * 60 + int(minute_str)


def build_slot_bounds(hours: list[str]) -> list[tuple[int, int]]:
    bounds = []
    for label in hours:
        start_text, end_text = str(label).split("-")
        bounds.append((parse_clock(start_text), parse_clock(end_text)))
    return bounds


def build_q1_worker_contributions(
    schedule_path: Path,
    days: list[int],
    hours: list[str],
    group_cols: list[str],
) -> np.ndarray:
    """从问题一逐人工排班 CSV 恢复 工人-天-组-小时 覆盖张量。"""

    df = pd.read_csv(schedule_path, encoding="utf-8-sig")
    if df.shape[1] < len(days) + 2:
        raise RuntimeError(f"问题一逐人工排班列数异常：{df.shape[1]}")
    group_map = {group: index for index, group in enumerate(group_cols)}
    slot_bounds = build_slot_bounds(hours)
    contributions = np.zeros((len(df), len(days), len(group_cols), len(hours)), dtype=int)
    day_columns = list(df.columns[2 : 2 + len(days)])
    time_pattern = re.compile(r"(\d{1,2}:\d{2})-(\d{1,2}:\d{2})")

    for worker_index, row in df.iterrows():
        group_text = str(row.iloc[1]).strip()
        group_match = re.search(r"(\d+)", group_text)
        if not group_match:
            raise RuntimeError(f"无法解析问题一工人所属小组：{group_text}")
        group_name = f"小组{int(group_match.group(1))}"
        if group_name not in group_map:
            raise RuntimeError(f"问题一排班中的小组名不在需求表中：{group_name}")
        group_index = group_map[group_name]
        for day_index, day_col in enumerate(day_columns):
            cell_text = str(row[day_col]).strip()
            if "休" in cell_text or cell_text.lower() == "nan":
                continue
            matches = time_pattern.findall(cell_text)
            if not matches:
                raise RuntimeError(f"无法解析问题一班型时间段：{cell_text}")
            for start_text, end_text in matches:
                start_minute = parse_clock(start_text)
                end_minute = parse_clock(end_text)
                for hour_index, (slot_start, slot_end) in enumerate(slot_bounds):
                    if slot_start >= start_minute and slot_end <= end_minute:
                        contributions[worker_index, day_index, group_index, hour_index] = 1
            cover_sum = int(contributions[worker_index, day_index, group_index].sum())
            if cover_sum not in (0, 8):
                raise RuntimeError(
                    f"问题一工人第{day_index + 1}天覆盖小时数异常：worker={worker_index}, cover={cover_sum}, text={cell_text}"
                )
    return contributions


def build_q2_pattern_cover(group_count: int, shift_cover: np.ndarray) -> np.ndarray:
    shift_count, hour_count = shift_cover.shape
    pattern_cover = np.zeros((group_count * shift_count, group_count, hour_count), dtype=int)
    pattern_index = 0
    for group_index in range(group_count):
        for shift_index in range(shift_count):
            pattern_cover[pattern_index, group_index, :] = shift_cover[shift_index]
            pattern_index += 1
    return pattern_cover


def expand_q2_patterns_with_extras(
    x_days: list[np.ndarray],
    daily_counts: np.ndarray,
    demand: np.ndarray,
    pattern_cover: np.ndarray,
) -> list[list[int]]:
    daily_pattern_ids: list[list[int]] = []
    shift_count = x_days[0].shape[1]
    for day_index, x_day in enumerate(x_days):
        ids: list[int] = []
        for group_index in range(x_day.shape[0]):
            for shift_index in range(shift_count):
                ids.extend([group_index * shift_count + shift_index] * int(x_day[group_index, shift_index]))
        coverage = np.zeros_like(demand[day_index])
        for pattern_id in ids:
            coverage += pattern_cover[pattern_id]
        while len(ids) < int(daily_counts[day_index]):
            best_pattern = 0
            best_penalty = float("inf")
            current_surplus = np.maximum(coverage - demand[day_index], 0)
            for pattern_id, cover in enumerate(pattern_cover):
                new_surplus = np.maximum(coverage + cover - demand[day_index], 0)
                penalty = float((new_surplus * new_surplus).sum() - (current_surplus * current_surplus).sum())
                if penalty < best_penalty:
                    best_penalty = penalty
                    best_pattern = pattern_id
            ids.append(best_pattern)
            coverage += pattern_cover[best_pattern]
        daily_pattern_ids.append(ids)
    return daily_pattern_ids


def worker_contributions_from_assignments(assignments: np.ndarray, pattern_cover: np.ndarray) -> np.ndarray:
    worker_count, day_count = assignments.shape
    group_count, hour_count = pattern_cover.shape[1], pattern_cover.shape[2]
    contributions = np.zeros((worker_count, day_count, group_count, hour_count), dtype=int)
    for worker_index in range(worker_count):
        for day_index in range(day_count):
            pattern_id = int(assignments[worker_index, day_index])
            if pattern_id >= 0:
                contributions[worker_index, day_index] = pattern_cover[pattern_id]
    return contributions


def build_q2_baseline(
    demand: np.ndarray,
    shift_cover_same: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, dict[str, object]]:
    result = model.solve_problem2_network_flow(demand, shift_cover_same)
    pattern_cover = build_q2_pattern_cover(demand.shape[1], shift_cover_same)
    daily_pattern_ids = expand_q2_patterns_with_extras(
        result["x_days"],
        np.array(result["daily_counts"], dtype=int),
        demand,
        pattern_cover,
    )
    assignments = model.initial_assignments_from_flow(result["work_matrix"], daily_pattern_ids)
    contributions = worker_contributions_from_assignments(assignments, pattern_cover)
    coverage = contributions.sum(axis=0)
    deficit = np.maximum(demand - coverage, 0)
    if int(deficit.sum()) != 0:
        raise RuntimeError(f"问题二基准排班仍存在覆盖缺口：{int(deficit.sum())}")
    return contributions, coverage, result


def build_q3_baseline(
    demand: np.ndarray,
    shift_cover_same: np.ndarray,
    shift_labels_same: list[tuple[int, int, int, int]],
) -> tuple[np.ndarray, np.ndarray, dict[str, object]]:
    _, shift_cover_cross, shift_labels_cross = model.build_shift_pairs(2)
    patterns, pattern_cover = model.build_problem3_patterns(
        demand.shape[1],
        demand.shape[2],
        shift_cover_same,
        shift_labels_same,
        shift_cover_cross,
        shift_labels_cross,
    )
    config = model.AlnsConfig(iterations=Q3_ALNS_ITERATIONS, seed=RANDOM_SEED)
    result = model.solve_problem3_alns(demand, patterns, pattern_cover, config)
    assignments = result["alns_result"].best_assignments
    contributions = worker_contributions_from_assignments(assignments, pattern_cover)
    coverage = model.coverage_from_assignments(assignments, pattern_cover)
    deficit = np.maximum(demand - coverage, 0)
    if int(deficit.sum()) != 0:
        raise RuntimeError(f"问题三基准排班仍存在覆盖缺口：{int(deficit.sum())}")
    return contributions, coverage, result


def shortage_metrics(adjusted_demand: np.ndarray, coverage: np.ndarray) -> dict[str, float]:
    deficit = np.maximum(adjusted_demand - coverage, 0)
    total_demand = int(adjusted_demand.sum())
    total_shortage = int(deficit.sum())
    return {
        "总需求": total_demand,
        "总缺口": total_shortage,
        "UDR": round(total_shortage / total_demand, 6) if total_demand else 0.0,
        "最大单元缺口": int(deficit.max(initial=0)),
        "缺口时段数量": int((deficit > 0).sum()),
    }


def aggregate_trial_metrics(metrics: list[dict[str, float]]) -> dict[str, float]:
    if not metrics:
        raise RuntimeError("随机缺勤模拟结果为空。")
    total_demand = int(metrics[0]["总需求"])
    return {
        "总需求": total_demand,
        "平均总缺口": round(float(np.mean([item["总缺口"] for item in metrics])), 3),
        "平均UDR": round(float(np.mean([item["UDR"] for item in metrics])), 6),
        "平均最大单元缺口": round(float(np.mean([item["最大单元缺口"] for item in metrics])), 3),
        "平均缺口时段数量": round(float(np.mean([item["缺口时段数量"] for item in metrics])), 3),
    }


def simulate_absence_metrics(
    contributions: np.ndarray,
    demand: np.ndarray,
    absence_rate: float,
    trials: int,
    seed: int,
) -> dict[str, float]:
    rng = np.random.default_rng(seed)
    active_mask = contributions.sum(axis=(2, 3)) > 0
    metrics: list[dict[str, float]] = []
    for _ in range(trials):
        absent_mask = (rng.random(active_mask.shape) < absence_rate) & active_mask
        available = (~absent_mask).astype(int)[..., None, None]
        coverage = (contributions * available).sum(axis=0)
        metrics.append(shortage_metrics(demand, coverage))
    return aggregate_trial_metrics(metrics)


def build_peak_hour_demand(demand: np.ndarray, hours: list[str]) -> tuple[np.ndarray, list[str]]:
    total_by_hour = demand.sum(axis=(0, 1))
    peak_indices = sorted(np.argsort(-total_by_hour)[:PEAK_HOUR_COUNT].tolist())
    adjusted = demand.copy()
    adjusted[:, :, peak_indices] = np.ceil(adjusted[:, :, peak_indices] * 1.10).astype(int)
    peak_labels = [hours[index] for index in peak_indices]
    return adjusted, peak_labels


def to_builtin(value: object) -> object:
    if isinstance(value, dict):
        return {str(key): to_builtin(item) for key, item in value.items()}
    if isinstance(value, list):
        return [to_builtin(item) for item in value]
    if isinstance(value, tuple):
        return [to_builtin(item) for item in value]
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    return value


def main() -> None:
    input_file = find_input_file()
    demand, days, hours, group_cols = model.read_demand(input_file)
    _same_pairs, shift_cover_same, shift_labels_same = model.build_shift_pairs(0)
    summary = json.loads((ROOT / "independent_advanced_summary.json").read_text(encoding="utf-8"))

    q1_contributions = build_q1_worker_contributions(Q1_SCHEDULE_PATH, days, hours, group_cols)
    q1_base_coverage = q1_contributions.sum(axis=0)
    if int(np.maximum(demand - q1_base_coverage, 0).sum()) != 0:
        raise RuntimeError("问题一基准 417 人排班存在覆盖缺口。")

    q2_contributions, q2_base_coverage, q2_result = build_q2_baseline(demand, shift_cover_same)
    q3_contributions, q3_base_coverage, q3_result = build_q3_baseline(demand, shift_cover_same, shift_labels_same)

    baseline_workers = {
        "问题一": int(q1_contributions.shape[0]),
        "问题二": int(q2_result["worker_count"]),
        "问题三": int(q3_result["worker_count"]),
    }

    baseline_metrics = {
        "问题一": shortage_metrics(demand, q1_base_coverage),
        "问题二": shortage_metrics(demand, q2_base_coverage),
        "问题三": shortage_metrics(demand, q3_base_coverage),
    }

    demand_sensitivity = []
    demand_cases = [
        ("S0", "基准", "原始需求", demand),
        ("S1", "所有需求增加5%", "所有需求整体上浮 5%", np.ceil(demand * 1.05).astype(int)),
        ("S1+", "所有需求增加10%", "所有需求整体上浮 10%", np.ceil(demand * 1.10).astype(int)),
    ]
    peak_demand, peak_hours = build_peak_hour_demand(demand, hours)
    demand_cases.append(("S2", "高峰小时增加10%", f"总需求最高的 {PEAK_HOUR_COUNT} 个小时槽上浮 10%", peak_demand))

    for code, scenario_name, description, adjusted in demand_cases:
        q1_workers = q1_exact_total(adjusted, shift_cover_same)
        q2_total, q2_workers, q2_days = q2_lower_bound(adjusted, shift_cover_same)
        q3_patterns, q3_total, q3_workers, q3_days = q3_lower_bound(
            adjusted,
            len(group_cols),
            len(hours),
            shift_cover_same,
            shift_labels_same,
            2,
        )
        demand_sensitivity.append(
            {
                "场景编号": code,
                "场景": scenario_name,
                "扰动方式": description,
                "高峰小时": peak_hours if code == "S2" else [],
                "问题一": {
                    "基准人数": baseline_workers["问题一"],
                    "重算最少人数": q1_workers,
                    "原方案缺口指标": shortage_metrics(adjusted, q1_base_coverage),
                },
                "问题二": {
                    "基准人数": baseline_workers["问题二"],
                    "重算单日最少出勤总人次": q2_total,
                    "重算人数下界": q2_workers,
                    "重算单日最少出勤序列": q2_days,
                    "原方案缺口指标": shortage_metrics(adjusted, q2_base_coverage),
                },
                "问题三": {
                    "基准人数": baseline_workers["问题三"],
                    "重算合法模式数": q3_patterns,
                    "重算单日最少出勤总人次": q3_total,
                    "重算人数下界": q3_workers,
                    "重算单日最少出勤序列": q3_days,
                    "原方案缺口指标": shortage_metrics(adjusted, q3_base_coverage),
                },
            }
        )
        print(f"finished demand scenario {code}: {scenario_name}")

    absence_sensitivity = []
    for code, absence_rate in [("S3-1", 0.01), ("S3-3", 0.03), ("S3-5", 0.05)]:
        absence_sensitivity.append(
            {
                "场景编号": code,
                "场景": f"随机缺勤{int(absence_rate * 100)}%",
                "扰动方式": f"基准排班中每个已分配工人-日期单元独立以 {int(absence_rate * 100)}% 概率缺勤",
                "模拟次数": ABSENCE_TRIALS,
                "随机种子": RANDOM_SEED,
                "问题一": simulate_absence_metrics(q1_contributions, demand, absence_rate, ABSENCE_TRIALS, RANDOM_SEED + 11),
                "问题二": simulate_absence_metrics(q2_contributions, demand, absence_rate, ABSENCE_TRIALS, RANDOM_SEED + 22),
                "问题三": simulate_absence_metrics(q3_contributions, demand, absence_rate, ABSENCE_TRIALS, RANDOM_SEED + 33),
            }
        )
        print(f"finished absence scenario {code}")

    q2_base_total = int(sum(summary["q2_day_minima"]))
    q3_base_total = int(sum(summary["q3_day_minima"]))
    workday_sensitivity = []
    for work_days in [7, 8, 9]:
        workday_sensitivity.append(
            {
                "每人工作天数": work_days,
                "问题二人数下界": int(math.ceil(q2_base_total / work_days)),
                "问题三人数下界": int(math.ceil(q3_base_total / work_days)),
            }
        )

    rest_gap_sensitivity = []
    for rest_gap in [1, 2, 3]:
        pattern_count, q3_total, q3_workers, q3_days = q3_lower_bound(
            demand,
            len(group_cols),
            len(hours),
            shift_cover_same,
            shift_labels_same,
            rest_gap,
        )
        rest_gap_sensitivity.append(
            {
                "跨组最小休息小时": rest_gap,
                "问题三合法模式数": pattern_count,
                "问题三单日最少出勤总人次": q3_total,
                "问题三人数下界": q3_workers,
                "问题三单日最少出勤序列": q3_days,
            }
        )
        print(f"finished rest gap {rest_gap}")

    result = {
        "数据来源": str(input_file),
        "基准方案人数": baseline_workers,
        "基准方案缺口指标": baseline_metrics,
        "论文建议场景": {
            "S0": "基准需求，用于校验三问基准排班的缺口指标应为 0。",
            "S1": "所有需求整体上浮 5%。",
            "S1+": "所有需求整体上浮 10%。",
            "S2": f"高峰小时需求上浮 10%，高峰小时定义为总需求最高的 {PEAK_HOUR_COUNT} 个小时槽。",
            "S3": f"随机缺勤场景，采用 {ABSENCE_TRIALS} 次固定种子 Monte Carlo 估计平均缺口指标。",
        },
        "需求扰动敏感性": demand_sensitivity,
        "随机缺勤敏感性": absence_sensitivity,
        "工作天数敏感性": workday_sensitivity,
        "休息间隔敏感性": rest_gap_sensitivity,
        "说明": [
            "需求扰动和休息间隔扰动均从原始附件重新求解最少人数或理论下界。",
            "随机缺勤场景不重算招聘人数，而是评估基准排班在缺勤冲击下的覆盖缺口表现。",
            "UDR 定义为 总缺口 / 扰动后总需求；若为 0 则表示原方案仍完全覆盖。",
        ],
    }
    OUT_PATH.write_text(json.dumps(to_builtin(result), ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
