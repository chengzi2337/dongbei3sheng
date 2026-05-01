from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
OUT_PATH = ROOT / ".codex" / "paper-sensitivity-results.json"

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


def main() -> None:
    input_file = find_input_file()
    demand, _days, hours, group_cols = model.read_demand(input_file)
    _same_pairs, shift_cover_same, shift_labels_same = model.build_shift_pairs(0)
    summary = json.loads((ROOT / "independent_advanced_summary.json").read_text(encoding="utf-8"))

    demand_sensitivity = []
    for factor, name in [(1.00, "基准"), (1.05, "需求上浮5%"), (1.10, "需求上浮10%")]:
        adjusted = np.ceil(demand * factor).astype(int)
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
                "场景": name,
                "需求倍率": factor,
                "问题一精确人数": q1_workers,
                "问题二单日最少出勤总人次": q2_total,
                "问题二人数下界": q2_workers,
                "问题二单日最少出勤序列": q2_days,
                "问题三合法模式数": q3_patterns,
                "问题三单日最少出勤总人次": q3_total,
                "问题三人数下界": q3_workers,
                "问题三单日最少出勤序列": q3_days,
            }
        )
        print(f"finished demand factor {factor}")

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
        "需求扰动敏感性": demand_sensitivity,
        "工作天数敏感性": workday_sensitivity,
        "休息间隔敏感性": rest_gap_sensitivity,
        "说明": "需求扰动和休息间隔扰动均从原始附件重新求解；工作天数扰动基于单日最少出勤总人次推导理论下界。",
    }
    OUT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
