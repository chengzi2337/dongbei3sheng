from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import lil_matrix


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from independent_advanced_staff_scheduling import build_shift_pairs, build_workday_flow, read_demand


DATA_PATH = ROOT / "附件1.xlsx"
JSON_PATH = ROOT / "q1_video_discrepancy_audit.json"
REPORT_PATH = ROOT / "q1_video_discrepancy_audit.md"
SCHEDULE_PATH = ROOT / "q1_417_feasible_schedule.csv"


def solve_group_model(req_group: np.ndarray, shift_cover: np.ndarray, integral: bool) -> dict[str, object]:
    day_count, hour_count = req_group.shape
    shift_count = shift_cover.shape[0]
    worker_var = day_count * shift_count
    var_count = worker_var + 1
    rows = day_count * hour_count + day_count + 1
    matrix = lil_matrix((rows, var_count), dtype=float)
    lower = np.full(rows, -np.inf)
    upper = np.full(rows, np.inf)

    row = 0
    for day in range(day_count):
        for hour in range(hour_count):
            for shift_id in range(shift_count):
                if shift_cover[shift_id, hour]:
                    matrix[row, day * shift_count + shift_id] = 1
            lower[row] = req_group[day, hour]
            row += 1

    for day in range(day_count):
        for shift_id in range(shift_count):
            matrix[row, day * shift_count + shift_id] = 1
        matrix[row, worker_var] = -1
        upper[row] = 0
        row += 1

    for day in range(day_count):
        for shift_id in range(shift_count):
            matrix[row, day * shift_count + shift_id] = 1
    matrix[row, worker_var] = -8
    lower[row] = 0
    upper[row] = 0

    objective = np.zeros(var_count)
    objective[worker_var] = 1
    integrality = np.ones(var_count, dtype=int) if integral else np.zeros(var_count, dtype=int)
    result = milp(
        c=objective,
        integrality=integrality,
        bounds=Bounds(np.zeros(var_count), np.full(var_count, np.inf)),
        constraints=LinearConstraint(matrix.tocsr(), lower, upper),
        options={"time_limit": 300, "mip_rel_gap": 0},
    )
    if not result.success:
        raise RuntimeError(f"第{req_group.shape}组模型求解失败：{result.message}")

    x = np.array(result.x[:worker_var]).reshape(day_count, shift_count)
    if integral:
        x = np.rint(x).astype(int)
    return {
        "objective": float(result.x[worker_var]),
        "x": x,
        "status": int(result.status),
        "message": str(result.message),
        "mip_gap": float(getattr(result, "mip_gap", 0.0) or 0.0),
    }


def shift_label(hours: list[str], label: tuple[int, int, int, int]) -> str:
    s1, e1, s2, e2 = label
    return f"{hours[s1].split('-')[0]}-{hours[e1 - 1].split('-')[1]} + {hours[s2].split('-')[0]}-{hours[e2 - 1].split('-')[1]}"


def decompose_group_schedule(
    group_name: str,
    worker_start: int,
    x_counts: np.ndarray,
    shift_labels: list[tuple[int, int, int, int]],
    shift_cover: np.ndarray,
    hours: list[str],
    days: list[int],
) -> tuple[list[dict[str, object]], dict[str, float]]:
    worker_count = int(x_counts.sum() // 8)
    daily_counts = x_counts.sum(axis=1).astype(int)
    work_matrix = build_workday_flow(worker_count, daily_counts)
    schedule = np.full((worker_count, len(days)), -1, dtype=int)

    for day in range(len(days)):
        shifts: list[int] = []
        for shift_id, count in enumerate(x_counts[day]):
            shifts.extend([shift_id] * int(count))
        workers = np.where(work_matrix[:, day])[0]
        if len(workers) != len(shifts):
            raise RuntimeError(f"{group_name} 第{day + 1}天工作人数与班型数量不一致")
        for worker, shift_id in zip(workers, shifts):
            schedule[int(worker), day] = int(shift_id)

    rows: list[dict[str, object]] = []
    labels = [shift_label(hours, item) for item in shift_labels]
    for worker in range(worker_count):
        row: dict[str, object] = {"工号": worker_start + worker, "小组": group_name}
        for day_index, day in enumerate(days):
            shift_id = int(schedule[worker, day_index])
            row[f"第{day}天"] = "休息" if shift_id < 0 else labels[shift_id]
        rows.append(row)

    worker_days = (schedule >= 0).sum(axis=1)
    reconstructed_counts = np.zeros_like(x_counts, dtype=int)
    for day in range(len(days)):
        ids, counts = np.unique(schedule[:, day][schedule[:, day] >= 0], return_counts=True)
        for shift_id, count in zip(ids, counts):
            reconstructed_counts[day, int(shift_id)] = int(count)
    if not np.array_equal(reconstructed_counts, x_counts):
        raise RuntimeError(f"{group_name} 逐人工排班未能还原日-班型计数")

    metrics = {
        "worker_count": float(worker_count),
        "min_worker_days": float(worker_days.min()),
        "max_worker_days": float(worker_days.max()),
        "day_count_min": float(daily_counts.min()),
        "day_count_max": float(daily_counts.max()),
    }
    return rows, metrics


def coverage_metrics(req_group: np.ndarray, x_counts: np.ndarray, shift_cover: np.ndarray) -> dict[str, float]:
    coverage = x_counts @ shift_cover
    deficit = np.maximum(req_group - coverage, 0)
    surplus = np.maximum(coverage - req_group, 0)
    return {
        "deficit_sum": float(deficit.sum()),
        "max_deficit": float(deficit.max(initial=0)),
        "surplus_sum": float(surplus.sum()),
        "max_surplus": float(surplus.max(initial=0)),
    }


def main() -> None:
    demand, days, hours, group_cols = read_demand(DATA_PATH)
    _, shift_cover, shift_labels = build_shift_pairs(min_break=0)

    records: list[dict[str, object]] = []
    schedule_rows: list[dict[str, object]] = []
    worker_start = 1

    for group_index, group_name in enumerate(group_cols):
        req_group = demand[:, group_index, :]
        lp_result = solve_group_model(req_group, shift_cover, integral=False)
        int_result = solve_group_model(req_group, shift_cover, integral=True)
        x_int = np.asarray(int_result["x"], dtype=int)
        coverage = coverage_metrics(req_group, x_int, shift_cover)
        rows, schedule_metrics = decompose_group_schedule(
            group_name=group_name,
            worker_start=worker_start,
            x_counts=x_int,
            shift_labels=shift_labels,
            shift_cover=shift_cover,
            hours=hours,
            days=days,
        )
        schedule_rows.extend(rows)
        worker_start += int(schedule_metrics["worker_count"])

        lp_value = float(lp_result["objective"])
        ceil_lp = int(math.ceil(lp_value - 1e-8))
        integer_value = int(round(float(int_result["objective"])))
        records.append(
            {
                "小组": group_name,
                "lp_relaxation": round(lp_value, 6),
                "ceil_lp": ceil_lp,
                "integer_workers": integer_value,
                "gap_after_ceil": integer_value - ceil_lp,
                "daily_min_workers": int(x_int.sum(axis=1).min()),
                "daily_max_workers": int(x_int.sum(axis=1).max()),
                "coverage_deficit": coverage["deficit_sum"],
                "max_deficit": coverage["max_deficit"],
                "surplus": coverage["surplus_sum"],
                "worker_day_min": schedule_metrics["min_worker_days"],
                "worker_day_max": schedule_metrics["max_worker_days"],
                "mip_gap": float(int_result["mip_gap"]),
            }
        )

    total_lp = sum(float(item["lp_relaxation"]) for item in records)
    total_ceil_lp = sum(int(item["ceil_lp"]) for item in records)
    total_integer = sum(int(item["integer_workers"]) for item in records)
    total_gap = total_integer - total_ceil_lp
    all_deficit = sum(float(item["coverage_deficit"]) for item in records)
    worker_days = [
        sum(1 for key, value in row.items() if key.startswith("第") and value != "休息")
        for row in schedule_rows
    ]

    audit = {
        "data_path": str(DATA_PATH),
        "shift_count": int(shift_cover.shape[0]),
        "group_count": int(demand.shape[1]),
        "day_count": int(demand.shape[0]),
        "hour_count": int(demand.shape[2]),
        "total_lp_relaxation": round(total_lp, 6),
        "total_ceil_lp_bound": int(total_ceil_lp),
        "total_integer_workers": int(total_integer),
        "gap_integer_minus_ceil_lp": int(total_gap),
        "total_coverage_deficit": float(all_deficit),
        "schedule_worker_count": len(schedule_rows),
        "schedule_worker_day_min": int(min(worker_days)),
        "schedule_worker_day_max": int(max(worker_days)),
        "per_group": records,
    }

    pd.DataFrame(schedule_rows).to_csv(SCHEDULE_PATH, index=False, encoding="utf-8-sig")
    JSON_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(audit)


def write_report(audit: dict[str, object]) -> None:
    per_group = audit["per_group"]
    assert isinstance(per_group, list)
    table_lines = [
        "| 小组 | LP松弛 | LP向上取整 | 整数最优人数 | 整数缺口 | 覆盖缺口 | 每人工日 |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for item in per_group:
        assert isinstance(item, dict)
        table_lines.append(
            "| {小组} | {lp_relaxation:.6g} | {ceil_lp} | {integer_workers} | {gap_after_ceil} | {coverage_deficit:.0f} | {worker_day_min:.0f}-{worker_day_max:.0f} |".format(
                **item
            )
        )

    report = f"""# 第一问视频结果冲突审计报告

生成时间：2026-04-30

## 1. 审计结论

- 使用原始数据：`{audit["data_path"]}`。
- 第一问同组固定服务约束下，重新逐组求解 LP 松弛与整数 MILP。
- LP 松弛目标值合计为 `{audit["total_lp_relaxation"]}`。
- 各组 LP 向上取整后合计为 `{audit["total_ceil_lp_bound"]}`，这对应视频中提到的 415 口径。
- 整数可执行排班合计为 `{audit["total_integer_workers"]}` 人。
- 整数可执行排班相对 415 下界的差值为 `{audit["gap_integer_minus_ceil_lp"]}` 人。
- 导出的逐人工排班人数为 `{audit["schedule_worker_count"]}` 人。
- 全部时空覆盖缺口为 `{audit["total_coverage_deficit"]}`。
- 每名员工工作天数范围为 `{audit["schedule_worker_day_min"]}-{audit["schedule_worker_day_max"]}` 天。

结论：在当前 `附件1.xlsx` 数据和“每天两个连续 4 小时段、全期固定同一小组、每人工作 8 天休息 2 天”的解释下，417 人是已经构造出逐人工排班的可执行整数解。415 是 LP 下界取整汇总，不是可执行排班人数。420 是一个可行上界或受限整数化结果，但不是当前精确整数模型下的最小人数。

## 2. 逐组结果

{chr(10).join(table_lines)}

## 3. 与视频结果不一致的原因

1. 视频中的 415 本质上是“每组连续松弛目标值向上取整后求和”，它只提供整数问题的下界，不能直接作为可执行排班。
2. 视频中的 420 来自后续整数化和详细排班导出，但字幕显示其列池从初始 100 个模式扩展到约 105、116 个模式。这种有限列池整数化可能只能得到可行上界，不能保证等于全局整数最优。
3. 我们的审计模型没有把每名工人的完整 10 天模式提前限制在有限列池中，而是直接用日-班型计数 MILP 求每组整数最优，再用最大流把日工作量分解为逐人工排班。因此不会因为列池不足导致人数偏大。
4. 小组 1 是关键例子：视频字幕称 LP 下界 39、实际整数 40；本次审计在同一类约束下构造出小组 1 的 39 人逐人工可执行排班，说明 40 更可能是其整数恢复策略或列池限制导致的可行上界。
5. 若对题目有额外隐藏解释，例如两个 4 小时段之间必须休息、或者每人每天只能采用同一种固定班型，则模型会变成另一个问题；但这些额外限制不属于当前题面第一问的已知硬约束。

## 4. 本地验证产物

- 审计 JSON：`{JSON_PATH}`
- 417 人逐人工排班：`{SCHEDULE_PATH}`
- 审计脚本：`{Path(__file__).resolve()}`

## 5. 建议论文表述

建议写成：第一问的连续松弛下界为 415，但该数值不能直接作为排班人数；进一步恢复整数约束并构造逐人工排班后，本文得到 417 人可执行方案，且每组 MILP 均达到求解器证明的整数最优，所有时空需求覆盖缺口为 0。因此，在当前题面约束和原始附件数据下，417 比 420 更优，420 可作为外部方案的可行上界对照。
"""
    REPORT_PATH.write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
