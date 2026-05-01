from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd
from scipy.optimize import milp, LinearConstraint, Bounds
from scipy.sparse import lil_matrix

DAYS = range(1, 11)
GROUPS = range(1, 11)
HOURS = range(11)


@dataclass(frozen=True)
class SameGroupShift:
    sid: int
    s1: int
    s2: int


@dataclass(frozen=True)
class CrossGroupShift:
    sid: int
    g1: int
    s1: int
    g2: int
    s2: int


def hour_to_index(x) -> int:
    s = str(x)
    m = re.search(r"(\d{1,2})\s*:", s)
    if not m:
        raise ValueError(f"无法识别小时字段：{x}")
    h = int(m.group(1)) - 8
    if not 0 <= h <= 10:
        raise ValueError(f"小时字段超出8:00-19:00范围：{x}")
    return h


def read_demand(path: str | Path) -> np.ndarray:
    path = Path(path)
    try:
        df = pd.read_excel(path, header=1)
    except ImportError as e:
        if path.suffix.lower() == ".xls":
            raise ImportError("读取 .xls 需要安装 xlrd：pip install xlrd；也可以先把附件另存为 .xlsx。") from e
        raise

    day_col = df.columns[0]
    hour_col = df.columns[1]
    group_cols = list(df.columns[2:12])
    need = np.zeros((10, 10, 11), dtype=int)

    for _, row in df.iterrows():
        if pd.isna(row[day_col]) or pd.isna(row[hour_col]):
            continue
        d = int(row[day_col])
        h = hour_to_index(row[hour_col])
        if not 1 <= d <= 10:
            continue
        for j, col in enumerate(group_cols, start=1):
            need[d - 1, j - 1, h] = int(row[col])

    if need.sum() <= 0:
        raise ValueError("没有读到有效需求数据，请检查Excel是否为：第1列天、第2列小时、第3-12列为小组1-10。")
    return need


def time_block(start_hour_index: int) -> str:
    return f"{8 + start_hour_index}:00-{12 + start_hour_index}:00"


def generate_same_group_shifts() -> List[SameGroupShift]:
    shifts = []
    sid = 0
    for s1 in range(0, 8):
        for s2 in range(s1 + 4, 8):
            shifts.append(SameGroupShift(sid, s1, s2))
            sid += 1
    return shifts


def same_shift_cover(shift: SameGroupShift, h: int) -> int:
    return int(shift.s1 <= h < shift.s1 + 4 or shift.s2 <= h < shift.s2 + 4)


def generate_problem3_shifts() -> List[CrossGroupShift]:
    shifts = []
    sid = 0
    for g1 in GROUPS:
        for g2 in GROUPS:
            for s1 in range(0, 8):
                for s2 in range(s1 + 4, 8):
                    if g1 != g2 and s2 < s1 + 6:
                        continue
                    shifts.append(CrossGroupShift(sid, g1, s1, g2, s2))
                    sid += 1
    return shifts


def cross_shift_cover(shift: CrossGroupShift, g: int, h: int) -> int:
    return int(
        (shift.g1 == g and shift.s1 <= h < shift.s1 + 4)
        or (shift.g2 == g and shift.s2 <= h < shift.s2 + 4)
    )


def solve_milp(c, rows, lbs, ubs, n_vars: int, time_limit: int = 600):
    A = lil_matrix((len(rows), n_vars), dtype=float)
    for r, terms in enumerate(rows):
        for idx, val in terms:
            if val:
                A[r, idx] += val
    res = milp(
        c=np.array(c, dtype=float),
        integrality=np.ones(n_vars, dtype=int),
        bounds=Bounds(np.zeros(n_vars), np.full(n_vars, np.inf)),
        constraints=LinearConstraint(A.tocsr(), np.array(lbs, dtype=float), np.array(ubs, dtype=float)),
        options={"time_limit": time_limit, "mip_rel_gap": 0},
    )
    if not res.success:
        raise RuntimeError(f"MILP求解失败：{res.message}")
    sol = np.rint(res.x).astype(int)
    return int(round(res.fun)), sol


def solve_problem1(need: np.ndarray, out_dir: Path):
    shifts = generate_same_group_shifts()
    n_shift = len(shifts)
    x_idx = {}
    idx = 0
    for d in DAYS:
        for g in GROUPS:
            for p in range(n_shift):
                x_idx[(d, g, p)] = idx
                idx += 1
    n_idx = {g: idx + g - 1 for g in GROUPS}
    n_vars = idx + len(GROUPS)
    c = [0] * n_vars
    for g in GROUPS:
        c[n_idx[g]] = 1

    rows, lbs, ubs = [], [], []
    for d in DAYS:
        for g in GROUPS:
            for h in HOURS:
                rows.append([(x_idx[(d, g, p)], same_shift_cover(shifts[p], h)) for p in range(n_shift)])
                lbs.append(need[d - 1, g - 1, h])
                ubs.append(np.inf)

    for d in DAYS:
        for g in GROUPS:
            rows.append([(x_idx[(d, g, p)], 1) for p in range(n_shift)] + [(n_idx[g], -1)])
            lbs.append(-np.inf)
            ubs.append(0)

    for g in GROUPS:
        rows.append([(x_idx[(d, g, p)], 1) for d in DAYS for p in range(n_shift)] + [(n_idx[g], -8)])
        lbs.append(0)
        ubs.append(0)

    obj, sol = solve_milp(c, rows, lbs, ubs, n_vars)

    summary = pd.DataFrame({"group": list(GROUPS), "min_workers": [sol[n_idx[g]] for g in GROUPS]})
    schedule = []
    for d in DAYS:
        for g in GROUPS:
            for p, sh in enumerate(shifts):
                v = sol[x_idx[(d, g, p)]]
                if v > 0:
                    schedule.append([d, g, p + 1, time_block(sh.s1), time_block(sh.s2), int(v)])
    schedule = pd.DataFrame(schedule, columns=["day", "group", "shift_id", "block1", "block2", "workers"])
    summary.to_csv(out_dir / "problem1_summary.csv", index=False, encoding="utf-8-sig")
    schedule.to_csv(out_dir / "problem1_schedule.csv", index=False, encoding="utf-8-sig")
    return obj, summary, schedule


def solve_problem2(need: np.ndarray, out_dir: Path):
    shifts = generate_same_group_shifts()
    n_shift = len(shifts)
    x_idx = {}
    idx = 0
    for d in DAYS:
        for g in GROUPS:
            for p in range(n_shift):
                x_idx[(d, g, p)] = idx
                idx += 1
    N = idx
    n_vars = idx + 1
    c = [0] * n_vars
    c[N] = 1

    rows, lbs, ubs = [], [], []
    for d in DAYS:
        for g in GROUPS:
            for h in HOURS:
                rows.append([(x_idx[(d, g, p)], same_shift_cover(shifts[p], h)) for p in range(n_shift)])
                lbs.append(need[d - 1, g - 1, h])
                ubs.append(np.inf)

    for d in DAYS:
        rows.append([(x_idx[(d, g, p)], 1) for g in GROUPS for p in range(n_shift)] + [(N, -1)])
        lbs.append(-np.inf)
        ubs.append(0)

    rows.append([(x_idx[(d, g, p)], 1) for d in DAYS for g in GROUPS for p in range(n_shift)] + [(N, -8)])
    lbs.append(0)
    ubs.append(0)

    obj, sol = solve_milp(c, rows, lbs, ubs, n_vars)

    schedule = []
    for d in DAYS:
        for g in GROUPS:
            for p, sh in enumerate(shifts):
                v = sol[x_idx[(d, g, p)]]
                if v > 0:
                    schedule.append([d, g, p + 1, time_block(sh.s1), time_block(sh.s2), int(v)])
    schedule = pd.DataFrame(schedule, columns=["day", "group", "shift_id", "block1", "block2", "workers"])
    daily = schedule.groupby("day")["workers"].sum().reset_index(name="on_duty_workers")
    schedule.to_csv(out_dir / "problem2_schedule.csv", index=False, encoding="utf-8-sig")
    daily.to_csv(out_dir / "problem2_daily.csv", index=False, encoding="utf-8-sig")
    return obj, daily, schedule


def solve_problem3(need: np.ndarray, out_dir: Path):
    shifts = generate_problem3_shifts()
    n_shift = len(shifts)
    x_idx = {}
    idx = 0
    for d in DAYS:
        for p in range(n_shift):
            x_idx[(d, p)] = idx
            idx += 1
    N = idx
    n_vars = idx + 1
    c = [0] * n_vars
    c[N] = 1

    rows, lbs, ubs = [], [], []
    for d in DAYS:
        for g in GROUPS:
            for h in HOURS:
                rows.append([(x_idx[(d, p)], cross_shift_cover(shifts[p], g, h)) for p in range(n_shift)])
                lbs.append(need[d - 1, g - 1, h])
                ubs.append(np.inf)

    for d in DAYS:
        rows.append([(x_idx[(d, p)], 1) for p in range(n_shift)] + [(N, -1)])
        lbs.append(-np.inf)
        ubs.append(0)

    rows.append([(x_idx[(d, p)], 1) for d in DAYS for p in range(n_shift)] + [(N, -8)])
    lbs.append(0)
    ubs.append(0)

    obj, sol = solve_milp(c, rows, lbs, ubs, n_vars)

    schedule = []
    for d in DAYS:
        for p, sh in enumerate(shifts):
            v = sol[x_idx[(d, p)]]
            if v > 0:
                schedule.append([
                    d,
                    sh.g1,
                    time_block(sh.s1),
                    sh.g2,
                    time_block(sh.s2),
                    int(v),
                    "换组" if sh.g1 != sh.g2 else "不换组",
                ])
    schedule = pd.DataFrame(schedule, columns=["day", "group1", "block1", "group2", "block2", "workers", "type"])
    daily = schedule.groupby("day")["workers"].sum().reset_index(name="on_duty_workers")
    type_daily = schedule.pivot_table(index="day", columns="type", values="workers", aggfunc="sum", fill_value=0).reset_index()
    daily = daily.merge(type_daily, on="day", how="left")
    schedule.to_csv(out_dir / "problem3_schedule.csv", index=False, encoding="utf-8-sig")
    daily.to_csv(out_dir / "problem3_daily.csv", index=False, encoding="utf-8-sig")
    return obj, daily, schedule


def main():
    parser = argparse.ArgumentParser(description="大型展销会临时工招聘与排班优化：三个问题统一整数规划求解")
    parser.add_argument("--data", default="附件1(1).xls", help="附件1路径，支持xls/xlsx")
    parser.add_argument("--out", default="model_outputs", help="输出目录")
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    need = read_demand(args.data)

    ans1, sum1, _ = solve_problem1(need, out_dir)
    ans2, day2, _ = solve_problem2(need, out_dir)
    ans3, day3, _ = solve_problem3(need, out_dir)

    summary = pd.DataFrame({"problem": ["问题1", "问题2", "问题3"], "min_workers": [ans1, ans2, ans3]})
    summary.to_csv(out_dir / "summary.csv", index=False, encoding="utf-8-sig")

    print("最少招聘人数：")
    print(summary.to_string(index=False))
    print("\n问题1各小组人数：")
    print(sum1.to_string(index=False))
    print("\n问题2每日上岗人数：")
    print(day2.to_string(index=False))
    print("\n问题3每日上岗人数：")
    print(day3.to_string(index=False))
    print(f"\n详细排班CSV已输出到：{out_dir.resolve()}")


if __name__ == "__main__":
    main()
