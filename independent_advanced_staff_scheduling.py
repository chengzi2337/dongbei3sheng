from __future__ import annotations

import argparse
import json
import math
import random
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from scipy.optimize import Bounds, LinearConstraint, linprog, milp
from scipy.sparse import csr_matrix, lil_matrix


DEFAULT_INPUT = "附件1.xlsx"
DEFAULT_OUTPUT = "independent_高级排班优化结果.xlsx"
DEFAULT_JSON = "independent_advanced_summary.json"
DEFAULT_CONVERGENCE = "independent_q3_alns_convergence.csv"
MIP_TIME_LIMIT = 300


def read_demand(path: str | Path) -> tuple[np.ndarray, list[int], list[str], list[str]]:
    """从原始附件重构 天-小组-小时 三维需求张量。"""

    file_path = Path(path)
    if file_path.suffix.lower() in {".xlsx", ".xlsm"}:
        df = pd.read_excel(file_path, engine="openpyxl", header=1)
    elif file_path.suffix.lower() == ".xls":
        df = pd.read_excel(file_path, engine="xlrd", header=1)
    else:
        df = pd.read_csv(file_path)

    df = df.dropna(how="all")
    df.columns = [str(col).strip() for col in df.columns]
    day_col = next(col for col in df.columns if col == "天" or "天" in col)
    hour_col = next(col for col in df.columns if col == "小时" or "时" in col)
    group_cols = [col for col in df.columns if col.startswith("小组")]
    if len(group_cols) != 10:
        raise ValueError(f"原始附件中未识别到10个小组列：{group_cols}")

    df[day_col] = pd.to_numeric(df[day_col], errors="coerce").astype(int)
    for col in group_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    days = sorted(int(day) for day in df[day_col].unique())
    hours = list(df[df[day_col] == days[0]][hour_col].astype(str))
    demand = np.zeros((len(days), len(group_cols), len(hours)), dtype=int)
    for day_index, day in enumerate(days):
        sub = df[df[day_col] == day]
        if len(sub) != len(hours):
            raise ValueError(f"第{day}天小时行数异常：{len(sub)}")
        for group_index, col in enumerate(group_cols):
            demand[day_index, group_index, :] = sub[col].to_numpy(dtype=int)
    return demand, days, hours, group_cols


def build_shift_pairs(min_break: int = 0) -> tuple[list[tuple[int, int]], np.ndarray, list[tuple[int, int, int, int]]]:
    pairs: list[tuple[int, int]] = []
    covers: list[np.ndarray] = []
    labels: list[tuple[int, int, int, int]] = []
    for first_start in range(0, 8):
        for second_start in range(first_start + 4 + min_break, 8):
            cover = np.zeros(11, dtype=int)
            cover[first_start : first_start + 4] = 1
            cover[second_start : second_start + 4] = 1
            pairs.append((first_start, second_start))
            covers.append(cover)
            labels.append((first_start, first_start + 4, second_start, second_start + 4))
    return pairs, np.array(covers, dtype=int), labels


def time_label(hours: list[str], shift_tuple: tuple[int, int, int, int]) -> str:
    s1, e1, s2, e2 = shift_tuple
    return f"{hours[s1].split('-')[0]}-{hours[e1 - 1].split('-')[1]} + {hours[s2].split('-')[0]}-{hours[e2 - 1].split('-')[1]}"


def solve_milp_minimize(
    objective: np.ndarray,
    matrix: csr_matrix,
    lower: np.ndarray,
    upper: np.ndarray,
    time_limit: int = MIP_TIME_LIMIT,
) -> object:
    result = milp(
        c=objective,
        integrality=np.ones(len(objective), dtype=int),
        bounds=Bounds(np.zeros(len(objective)), np.full(len(objective), np.inf)),
        constraints=LinearConstraint(matrix, lower, upper),
        options={"time_limit": time_limit, "mip_rel_gap": 0},
    )
    if not result.success:
        raise RuntimeError(f"独立MILP求解失败：{result.message}")
    return result


def solve_problem1_group_exact(req_group: np.ndarray, shift_cover: np.ndarray) -> int:
    day_count, hour_count = req_group.shape
    shift_count = shift_cover.shape[0]
    var_count = day_count * shift_count + 1
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
    worker_var = day_count * shift_count
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
    result = solve_milp_minimize(objective, matrix.tocsr(), lower, upper)
    return int(round(result.x[worker_var]))


def solve_daily_problem2(req_day: np.ndarray, shift_cover: np.ndarray) -> tuple[int, np.ndarray, object]:
    group_count, hour_count = req_day.shape
    shift_count = shift_cover.shape[0]
    var_count = group_count * shift_count
    matrix = lil_matrix((group_count * hour_count, var_count), dtype=float)
    lower = np.zeros(group_count * hour_count)
    upper = np.full(group_count * hour_count, np.inf)
    row = 0
    for group in range(group_count):
        for hour in range(hour_count):
            for shift_id in range(shift_count):
                if shift_cover[shift_id, hour]:
                    matrix[row, group * shift_count + shift_id] = 1
            lower[row] = req_day[group, hour]
            row += 1
    objective = np.ones(var_count)
    result = solve_milp_minimize(objective, matrix.tocsr(), lower, upper)
    solution = np.rint(result.x).astype(int).reshape(group_count, shift_count)
    return int(solution.sum()), solution, result


def build_problem3_patterns(
    group_count: int,
    hour_count: int,
    shift_cover_same: np.ndarray,
    shift_labels_same: list[tuple[int, int, int, int]],
    shift_cover_cross: np.ndarray,
    shift_labels_cross: list[tuple[int, int, int, int]],
) -> tuple[list[dict], np.ndarray]:
    patterns: list[dict] = []
    covers: list[np.ndarray] = []
    for group in range(group_count):
        for shift_id, cover in enumerate(shift_cover_same):
            matrix = np.zeros((group_count, hour_count), dtype=int)
            matrix[group, :] = cover
            patterns.append({"type": "same_group", "g1": group, "g2": group, "shift": shift_labels_same[shift_id]})
            covers.append(matrix)
    for first_group in range(group_count):
        for second_group in range(group_count):
            if first_group == second_group:
                continue
            for s1, e1, s2, e2 in shift_labels_cross:
                matrix = np.zeros((group_count, hour_count), dtype=int)
                matrix[first_group, s1:e1] = 1
                matrix[second_group, s2:e2] = 1
                patterns.append(
                    {"type": "cross_group", "g1": first_group, "g2": second_group, "shift": (s1, e1, s2, e2)}
                )
                covers.append(matrix)
    return patterns, np.array(covers, dtype=int)


def solve_daily_problem3(req_day: np.ndarray, pattern_cover: np.ndarray) -> tuple[int, np.ndarray, object]:
    pattern_count, group_count, hour_count = pattern_cover.shape
    matrix = lil_matrix((group_count * hour_count, pattern_count), dtype=float)
    lower = np.zeros(group_count * hour_count)
    upper = np.full(group_count * hour_count, np.inf)
    row = 0
    for group in range(group_count):
        for hour in range(hour_count):
            for pattern_id in range(pattern_count):
                if pattern_cover[pattern_id, group, hour]:
                    matrix[row, pattern_id] = 1
            lower[row] = req_day[group, hour]
            row += 1
    objective = np.ones(pattern_count)
    result = solve_milp_minimize(objective, matrix.tocsr(), lower, upper)
    solution = np.rint(result.x).astype(int)
    return int(solution.sum()), solution, result


@dataclass(frozen=True)
class FlowEdge:
    to: int
    rev: int
    cap: int


class Dinic:
    """用于验证“每天出勤人数”和“每人工作8天”能否同时满足。"""

    def __init__(self, node_count: int) -> None:
        self.graph: list[list[FlowEdge]] = [[] for _ in range(node_count)]

    def add_edge(self, src: int, dst: int, cap: int) -> None:
        forward = FlowEdge(dst, len(self.graph[dst]), cap)
        backward = FlowEdge(src, len(self.graph[src]), 0)
        self.graph[src].append(forward)
        self.graph[dst].append(backward)

    def max_flow(self, src: int, sink: int) -> int:
        flow = 0
        node_count = len(self.graph)
        while True:
            level = [-1] * node_count
            level[src] = 0
            queue = [src]
            for node in queue:
                for edge in self.graph[node]:
                    if edge.cap > 0 and level[edge.to] < 0:
                        level[edge.to] = level[node] + 1
                        queue.append(edge.to)
            if level[sink] < 0:
                return flow
            it = [0] * node_count
            while True:
                pushed = self._dfs(src, sink, 10**18, level, it)
                if pushed == 0:
                    break
                flow += pushed

    def _dfs(self, node: int, sink: int, amount: int, level: list[int], it: list[int]) -> int:
        if node == sink:
            return amount
        while it[node] < len(self.graph[node]):
            idx = it[node]
            edge = self.graph[node][idx]
            if edge.cap > 0 and level[node] + 1 == level[edge.to]:
                pushed = self._dfs(edge.to, sink, min(amount, edge.cap), level, it)
                if pushed:
                    self._add_flow(node, idx, pushed)
                    return pushed
            it[node] += 1
        return 0

    def _add_flow(self, node: int, edge_index: int, amount: int) -> None:
        edge = self.graph[node][edge_index]
        reverse_index = edge.rev
        self.graph[node][edge_index] = FlowEdge(edge.to, edge.rev, edge.cap - amount)
        reverse = self.graph[edge.to][reverse_index]
        self.graph[edge.to][reverse_index] = FlowEdge(reverse.to, reverse.rev, reverse.cap + amount)


@dataclass
class AlnsConfig:
    iterations: int = 900
    seed: int = 20260429
    initial_temperature: float = 1200.0
    cooling_rate: float = 0.992
    reaction: float = 0.18
    destroy_min: int = 16
    destroy_max: int = 72
    deficit_weight: float = 1_000_000.0
    worker_day_deviation_weight: float = 100_000.0
    surplus_weight: float = 1.0
    max_surplus_weight: float = 0.0
    surplus_square_weight: float = 0.0
    day_worker_std_weight: float = 0.01
    destroy_operators: tuple[str, ...] = (
        "random_assignments",
        "whole_workers",
        "whole_days",
        "high_surplus",
    )
    repair_operators: tuple[str, ...] = ("greedy_deficit", "regret", "balanced_day")


@dataclass
class AlnsResult:
    best_assignments: np.ndarray
    best_score: float
    best_metrics: dict[str, float]
    history: pd.DataFrame
    operator_weights: dict[str, float]


@dataclass(frozen=True)
class Q1Column:
    shifts: tuple[int, ...]
    cover: np.ndarray

    @property
    def key(self) -> tuple[int, ...]:
        return self.shifts


def theoretical_worker_bound(day_minima: Iterable[int]) -> int:
    values = np.array(list(day_minima), dtype=int)
    return max(int(values.max()), int(math.ceil(values.sum() / 8)))


def choose_daily_counts(day_minima: Iterable[int]) -> tuple[int, np.ndarray]:
    minima = np.array(list(day_minima), dtype=int)
    worker_count = theoretical_worker_bound(minima)
    daily_counts = minima.copy()
    extra = 8 * worker_count - int(daily_counts.sum())
    while extra > 0:
        candidates = np.where(daily_counts < worker_count)[0]
        if len(candidates) == 0:
            raise RuntimeError("无法分配额外出勤日：所有日期已达到总人数上限。")
        day = int(candidates[np.argmin(daily_counts[candidates])])
        daily_counts[day] += 1
        extra -= 1
    if int(daily_counts.sum()) != 8 * worker_count:
        raise RuntimeError("每日出勤人数总和不等于每人8天工作制要求。")
    if int(daily_counts.max()) > worker_count:
        raise RuntimeError("某天出勤人数超过总招聘人数。")
    return worker_count, daily_counts


def build_workday_flow(worker_count: int, daily_counts: np.ndarray) -> np.ndarray:
    day_count = len(daily_counts)
    if int(daily_counts.sum()) != 8 * worker_count:
        raise ValueError("最大流输入不满足总工作日数量。")
    source = 0
    worker_offset = 1
    day_offset = worker_offset + worker_count
    sink = day_offset + day_count
    dinic = Dinic(sink + 1)
    worker_day_edges: dict[tuple[int, int], int] = {}

    for worker in range(worker_count):
        dinic.add_edge(source, worker_offset + worker, 8)
    for worker in range(worker_count):
        worker_node = worker_offset + worker
        for day in range(day_count):
            worker_day_edges[(worker, day)] = len(dinic.graph[worker_node])
            dinic.add_edge(worker_node, day_offset + day, 1)
    for day, count in enumerate(daily_counts):
        dinic.add_edge(day_offset + day, sink, int(count))

    flow = dinic.max_flow(source, sink)
    required = int(daily_counts.sum())
    if flow != required:
        raise RuntimeError(f"最大流未满流：flow={flow}, required={required}")

    work = np.zeros((worker_count, day_count), dtype=bool)
    for worker in range(worker_count):
        worker_node = worker_offset + worker
        for day in range(day_count):
            edge = dinic.graph[worker_node][worker_day_edges[(worker, day)]]
            work[worker, day] = edge.cap == 0
    if not np.all(work.sum(axis=1) == 8):
        raise RuntimeError("最大流结果存在工人工作天数不是8天。")
    if not np.all(work.sum(axis=0) == daily_counts):
        raise RuntimeError("最大流结果每日出勤人数不匹配。")
    return work


def build_workday_min_cost_flow(worker_count: int, daily_counts: np.ndarray) -> np.ndarray:
    """用低成本休息日组合生成工作日矩阵，偏向分散休息日。"""

    day_count = len(daily_counts)
    rest_counts = worker_count - np.array(daily_counts, dtype=int)
    if int(daily_counts.sum()) != 8 * worker_count:
        raise ValueError("最小费用工作日映射输入不满足总工作日数量。")
    if int(rest_counts.sum()) != 2 * worker_count:
        raise ValueError("最小费用工作日映射只适用于10天中工作8天的当前题设。")

    rest_patterns = [(first, second) for first in range(day_count) for second in range(first + 1, day_count)]
    pattern_count = len(rest_patterns)
    variable_count = worker_count * pattern_count
    row_count = worker_count + day_count
    matrix = lil_matrix((row_count, variable_count), dtype=float)
    lower = np.zeros(row_count)
    upper = np.zeros(row_count)
    objective = np.zeros(variable_count)

    target_gap = day_count / 2.0
    pattern_costs = []
    for first, second in rest_patterns:
        gap = abs(second - first)
        cyclic_gap = min(gap, day_count - gap)
        pattern_costs.append((target_gap - cyclic_gap) ** 2)

    for worker in range(worker_count):
        lower[worker] = 1
        upper[worker] = 1
        for pattern_index, (first, second) in enumerate(rest_patterns):
            variable = worker * pattern_count + pattern_index
            matrix[worker, variable] = 1
            matrix[worker_count + first, variable] = 1
            matrix[worker_count + second, variable] = 1
            objective[variable] = pattern_costs[pattern_index]
    for day, rest_count in enumerate(rest_counts):
        lower[worker_count + day] = int(rest_count)
        upper[worker_count + day] = int(rest_count)

    result = milp(
        c=objective,
        integrality=np.ones(variable_count, dtype=int),
        bounds=Bounds(np.zeros(variable_count), np.ones(variable_count)),
        constraints=LinearConstraint(csr_matrix(matrix), lower, upper),
        options={"time_limit": MIP_TIME_LIMIT, "mip_rel_gap": 0},
    )
    if not result.success:
        raise RuntimeError(f"最小费用工作日映射失败：{result.message}")

    chosen = np.rint(result.x).astype(int).reshape(worker_count, pattern_count)
    work = np.ones((worker_count, day_count), dtype=bool)
    for worker in range(worker_count):
        selected = np.where(chosen[worker] == 1)[0]
        if len(selected) != 1:
            raise RuntimeError(f"第{worker + 1}名工人的休息模式不唯一。")
        first, second = rest_patterns[int(selected[0])]
        work[worker, first] = False
        work[worker, second] = False
    if not np.all(work.sum(axis=1) == 8):
        raise RuntimeError("最小费用工作日映射存在工人工作天数不是8天。")
    if not np.all(work.sum(axis=0) == daily_counts):
        raise RuntimeError("最小费用工作日映射每日出勤人数不匹配。")
    return work


def build_workday_assignment(worker_count: int, daily_counts: np.ndarray, method: str = "max_flow") -> np.ndarray:
    if method == "min_cost":
        return build_workday_min_cost_flow(worker_count, daily_counts)
    if method != "max_flow":
        raise ValueError(f"未知工作日映射方法：{method}")
    return build_workday_flow(worker_count, daily_counts)


def flow_method_label(method: object) -> str:
    return "最小费用工作日映射" if method == "min_cost" else "最大流工作日映射"


def flatten_cover(pattern_cover: np.ndarray) -> np.ndarray:
    return pattern_cover.reshape(pattern_cover.shape[0], -1).astype(int)


def coverage_from_assignments(assignments: np.ndarray, pattern_cover: np.ndarray) -> np.ndarray:
    day_count = assignments.shape[1]
    group_count, hour_count = pattern_cover.shape[1], pattern_cover.shape[2]
    coverage = np.zeros((day_count, group_count, hour_count), dtype=int)
    for day in range(day_count):
        pattern_ids, counts = np.unique(assignments[:, day][assignments[:, day] >= 0], return_counts=True)
        for pattern_id, count in zip(pattern_ids, counts):
            coverage[day] += int(count) * pattern_cover[int(pattern_id)]
    return coverage


def metrics_for_assignments(
    assignments: np.ndarray,
    demand: np.ndarray,
    pattern_cover: np.ndarray,
) -> dict[str, float]:
    coverage = coverage_from_assignments(assignments, pattern_cover)
    deficit = np.maximum(demand - coverage, 0)
    surplus = np.maximum(coverage - demand, 0)
    worker_days = (assignments >= 0).sum(axis=1)
    day_workers = (assignments >= 0).sum(axis=0)
    max_worker_days = int(worker_days.max()) if worker_days.size else 0
    min_worker_days = int(worker_days.min()) if worker_days.size else 0
    return {
        "deficit": float(deficit.sum()),
        "max_deficit": float(deficit.max(initial=0)),
        "surplus": float(surplus.sum()),
        "max_surplus": float(surplus.max(initial=0)),
        "surplus_square": float((surplus * surplus).sum()),
        "worker_day_deviation": float(np.abs(worker_days - 8).sum()),
        "max_worker_days": float(max_worker_days),
        "min_worker_days": float(min_worker_days),
        "day_worker_std": float(day_workers.std()),
        "total_assignments": float((assignments >= 0).sum()),
    }


def score_metrics(metrics: dict[str, float], config: AlnsConfig | None = None) -> float:
    config = config or AlnsConfig()
    return (
        metrics["deficit"] * config.deficit_weight
        + metrics["worker_day_deviation"] * config.worker_day_deviation_weight
        + metrics["surplus"] * config.surplus_weight
        + metrics["max_surplus"] * config.max_surplus_weight
        + metrics["surplus_square"] * config.surplus_square_weight
        + metrics["day_worker_std"] * config.day_worker_std_weight
    )


def pattern_label(pattern: dict, hours: list[str], group_cols: list[str]) -> str:
    s1, e1, s2, e2 = pattern["shift"]
    first = f"{hours[s1].split('-')[0]}-{hours[e1 - 1].split('-')[1]}"
    second = f"{hours[s2].split('-')[0]}-{hours[e2 - 1].split('-')[1]}"
    if pattern["type"] == "same_group":
        return f"{group_cols[pattern['g1']]}：{first} + {second}"
    return f"{group_cols[pattern['g1']]} {first}；{group_cols[pattern['g2']]} {second}"


def expand_pattern_ids_with_extras(
    x_days: list[np.ndarray],
    daily_counts: np.ndarray,
    demand: np.ndarray,
    pattern_cover: np.ndarray,
) -> list[list[int]]:
    daily_pattern_ids: list[list[int]] = []
    for day, x_day in enumerate(x_days):
        ids: list[int] = []
        for pattern_id, count in enumerate(x_day):
            ids.extend([pattern_id] * int(count))
        coverage = np.zeros_like(demand[day])
        for pattern_id in ids:
            coverage += pattern_cover[pattern_id]
        while len(ids) < int(daily_counts[day]):
            best_pattern = 0
            best_penalty = float("inf")
            current_surplus = np.maximum(coverage - demand[day], 0)
            for pattern_id, cover in enumerate(pattern_cover):
                new_surplus = np.maximum(coverage + cover - demand[day], 0)
                penalty = float((new_surplus * new_surplus).sum() - (current_surplus * current_surplus).sum())
                if penalty < best_penalty:
                    best_penalty = penalty
                    best_pattern = pattern_id
            ids.append(best_pattern)
            coverage += pattern_cover[best_pattern]
        daily_pattern_ids.append(ids)
    return daily_pattern_ids


def initial_assignments_from_flow(work_matrix: np.ndarray, daily_pattern_ids: list[list[int]]) -> np.ndarray:
    worker_count, day_count = work_matrix.shape
    assignments = np.full((worker_count, day_count), -1, dtype=int)
    for day in range(day_count):
        workers = np.where(work_matrix[:, day])[0]
        ids = daily_pattern_ids[day]
        if len(workers) != len(ids):
            raise RuntimeError(f"第{day + 1}天工人数与班型数量不一致。")
        for worker, pattern_id in zip(workers, ids):
            assignments[int(worker), day] = int(pattern_id)
    return assignments


class Q3Alns:
    def __init__(
        self,
        demand: np.ndarray,
        pattern_cover: np.ndarray,
        initial_assignments: np.ndarray,
        config: AlnsConfig,
    ) -> None:
        self.demand = demand
        self.pattern_cover = pattern_cover
        self.pattern_flat = flatten_cover(pattern_cover)
        self.initial = initial_assignments
        self.config = config
        self.rng = random.Random(config.seed)
        valid_destroy = {"random_assignments", "whole_workers", "whole_days", "high_surplus"}
        valid_repair = {"greedy_deficit", "regret", "balanced_day"}
        unknown_destroy = set(config.destroy_operators).difference(valid_destroy)
        unknown_repair = set(config.repair_operators).difference(valid_repair)
        if unknown_destroy or unknown_repair:
            raise ValueError(f"未知ALNS算子：destroy={unknown_destroy}, repair={unknown_repair}")
        if not config.destroy_operators or not config.repair_operators:
            raise ValueError("ALNS破坏算子和修复算子均至少保留一个。")
        self.destroy_weights = {name: 1.0 for name in config.destroy_operators}
        self.repair_weights = {name: 1.0 for name in config.repair_operators}

    def run(self) -> AlnsResult:
        current = self.initial.copy()
        current_metrics = metrics_for_assignments(current, self.demand, self.pattern_cover)
        current_score = score_metrics(current_metrics, self.config)
        best = current.copy()
        best_score = current_score
        best_metrics = current_metrics
        temperature = self.config.initial_temperature
        history: list[dict[str, float | int | str]] = []

        for iteration in range(1, self.config.iterations + 1):
            destroy_name = self._weighted_choice(self.destroy_weights)
            repair_name = self._weighted_choice(self.repair_weights)
            candidate = current.copy()
            removed = self._destroy(candidate, destroy_name)
            self._repair(candidate, repair_name)
            candidate_metrics = metrics_for_assignments(candidate, self.demand, self.pattern_cover)
            candidate_score = score_metrics(candidate_metrics, self.config)
            accepted = self._accept(candidate_score, current_score, temperature)
            reward = 0.0
            if candidate_score < best_score:
                best = candidate.copy()
                best_score = candidate_score
                best_metrics = candidate_metrics
                reward = 8.0
            elif accepted and candidate_score < current_score:
                reward = 3.0
            elif accepted:
                reward = 1.0
            if accepted:
                current = candidate
                current_score = candidate_score
            self._update_weight(self.destroy_weights, destroy_name, reward)
            self._update_weight(self.repair_weights, repair_name, reward)
            temperature *= self.config.cooling_rate
            if iteration == 1 or iteration % 10 == 0 or reward >= 8.0:
                history.append(
                    {
                        "iteration": iteration,
                        "current_score": current_score,
                        "best_score": best_score,
                        "candidate_score": candidate_score,
                        "temperature": temperature,
                        "accepted": int(accepted),
                        "removed": int(removed),
                        "destroy": destroy_name,
                        "repair": repair_name,
                        "best_deficit": best_metrics["deficit"],
                        "best_surplus": best_metrics["surplus"],
                        "best_max_surplus": best_metrics["max_surplus"],
                        "best_surplus_square": best_metrics["surplus_square"],
                    }
                )
        weights = {f"destroy_{k}": v for k, v in self.destroy_weights.items()}
        weights.update({f"repair_{k}": v for k, v in self.repair_weights.items()})
        return AlnsResult(best, best_score, best_metrics, pd.DataFrame(history), weights)

    def _weighted_choice(self, weights: dict[str, float]) -> str:
        total = sum(max(v, 1e-9) for v in weights.values())
        point = self.rng.random() * total
        cumulative = 0.0
        for key, value in weights.items():
            cumulative += max(value, 1e-9)
            if cumulative >= point:
                return key
        return next(iter(weights))

    def _update_weight(self, weights: dict[str, float], name: str, reward: float) -> None:
        weights[name] = (1.0 - self.config.reaction) * weights[name] + self.config.reaction * max(reward, 0.1)

    def _accept(self, candidate_score: float, current_score: float, temperature: float) -> bool:
        if candidate_score <= current_score:
            return True
        if temperature <= 1e-9:
            return False
        probability = math.exp(-(candidate_score - current_score) / temperature)
        return self.rng.random() < probability

    def _destroy(self, assignments: np.ndarray, name: str) -> int:
        if name == "whole_workers":
            return self._destroy_whole_workers(assignments)
        if name == "whole_days":
            return self._destroy_whole_days(assignments)
        if name == "high_surplus":
            return self._destroy_high_surplus(assignments)
        return self._destroy_random_assignments(assignments)

    def _destroy_random_assignments(self, assignments: np.ndarray) -> int:
        active = np.argwhere(assignments >= 0)
        remove_count = min(len(active), self.rng.randint(self.config.destroy_min, self.config.destroy_max))
        for index in self.rng.sample(range(len(active)), remove_count):
            worker, day = active[index]
            assignments[int(worker), int(day)] = -1
        return remove_count

    def _destroy_whole_workers(self, assignments: np.ndarray) -> int:
        worker_count = assignments.shape[0]
        chosen = self.rng.sample(range(worker_count), self.rng.randint(2, 8))
        removed = 0
        for worker in chosen:
            removed += int((assignments[worker] >= 0).sum())
            assignments[worker, :] = -1
        return removed

    def _destroy_whole_days(self, assignments: np.ndarray) -> int:
        day_count = assignments.shape[1]
        chosen_days = self.rng.sample(range(day_count), self.rng.randint(1, 2))
        removed = 0
        for day in chosen_days:
            workers = np.where(assignments[:, day] >= 0)[0]
            if len(workers) == 0:
                continue
            remove_count = max(1, int(len(workers) * self.rng.uniform(0.08, 0.18)))
            for worker in self.rng.sample(list(map(int, workers)), remove_count):
                assignments[worker, day] = -1
                removed += 1
        return removed

    def _destroy_high_surplus(self, assignments: np.ndarray) -> int:
        coverage = coverage_from_assignments(assignments, self.pattern_cover)
        surplus = np.maximum(coverage - self.demand, 0)
        active = np.argwhere(assignments >= 0)
        scored: list[tuple[float, int, int]] = []
        for worker, day in active:
            pattern_id = int(assignments[int(worker), int(day)])
            contribution = float((self.pattern_cover[pattern_id] * surplus[int(day)]).sum())
            scored.append((contribution, int(worker), int(day)))
        scored.sort(reverse=True)
        remove_count = min(len(scored), self.rng.randint(self.config.destroy_min, self.config.destroy_max))
        removed = 0
        for _, worker, day in scored[:remove_count]:
            if assignments[worker, day] >= 0:
                assignments[worker, day] = -1
                removed += 1
        return removed

    def _repair(self, assignments: np.ndarray, name: str) -> None:
        guard = 0
        while True:
            missing_workers = np.where((assignments >= 0).sum(axis=1) < 8)[0]
            if len(missing_workers) == 0:
                return
            guard += 1
            if guard > assignments.size:
                raise RuntimeError("ALNS修复阶段超过安全迭代上限。")
            if name == "regret":
                worker, day, pattern_id = self._select_regret_move(assignments, missing_workers)
            elif name == "balanced_day":
                worker, day, pattern_id = self._select_balanced_move(assignments, missing_workers)
            else:
                worker, day, pattern_id = self._select_greedy_move(assignments, missing_workers)
            assignments[worker, day] = pattern_id

    def _select_greedy_move(self, assignments: np.ndarray, missing_workers: np.ndarray) -> tuple[int, int, int]:
        coverage = coverage_from_assignments(assignments, self.pattern_cover)
        best_tuple = None
        best_value = -float("inf")
        for worker in map(int, missing_workers):
            for day in np.where(assignments[worker] < 0)[0]:
                pattern_id, value = self._best_pattern_for_day(coverage, int(day))
                jitter = self.rng.random() * 1e-6
                if value + jitter > best_value:
                    best_value = value + jitter
                    best_tuple = (worker, int(day), int(pattern_id))
        if best_tuple is None:
            raise RuntimeError("ALNS贪心修复未找到可插入位置。")
        return best_tuple

    def _select_balanced_move(self, assignments: np.ndarray, missing_workers: np.ndarray) -> tuple[int, int, int]:
        coverage = coverage_from_assignments(assignments, self.pattern_cover)
        day_deficits = np.maximum(self.demand - coverage, 0).sum(axis=(1, 2))
        day_workers = (assignments >= 0).sum(axis=0)
        best_tuple = None
        best_value = -float("inf")
        for worker in map(int, missing_workers):
            rest_days = np.where(assignments[worker] < 0)[0]
            for day in rest_days:
                pattern_id, value = self._best_pattern_for_day(coverage, int(day))
                balance_bonus = float(day_deficits[int(day)] * 10.0 - day_workers[int(day)] * 0.02)
                total = value + balance_bonus + self.rng.random() * 1e-6
                if total > best_value:
                    best_value = total
                    best_tuple = (worker, int(day), int(pattern_id))
        if best_tuple is None:
            raise RuntimeError("ALNS均衡修复未找到可插入位置。")
        return best_tuple

    def _select_regret_move(self, assignments: np.ndarray, missing_workers: np.ndarray) -> tuple[int, int, int]:
        coverage = coverage_from_assignments(assignments, self.pattern_cover)
        best_tuple = None
        best_regret = -float("inf")
        for worker in map(int, missing_workers[: min(40, len(missing_workers))]):
            candidates: list[tuple[float, int, int]] = []
            for day in np.where(assignments[worker] < 0)[0]:
                pattern_id, value = self._best_pattern_for_day(coverage, int(day))
                candidates.append((value, int(day), int(pattern_id)))
            if not candidates:
                continue
            candidates.sort(reverse=True)
            first = candidates[0]
            second_value = candidates[1][0] if len(candidates) > 1 else 0.0
            regret = first[0] - second_value + self.rng.random() * 1e-6
            if regret > best_regret:
                best_regret = regret
                best_tuple = (worker, first[1], first[2])
        if best_tuple is None:
            return self._select_greedy_move(assignments, missing_workers)
        return best_tuple

    def _best_pattern_for_day(self, coverage: np.ndarray, day: int) -> tuple[int, float]:
        deficit = np.maximum(self.demand[day] - coverage[day], 0).reshape(-1)
        surplus = np.maximum(coverage[day] - self.demand[day], 0).reshape(-1)
        gains = self.pattern_flat @ deficit
        surplus_penalty = self.pattern_flat @ (surplus + 1)
        values = gains * 1000.0 - surplus_penalty
        best_pattern = int(np.argmax(values))
        return best_pattern, float(values[best_pattern])


def validate_feasible(name: str, assignments: np.ndarray, demand: np.ndarray, pattern_cover: np.ndarray) -> dict[str, float]:
    metrics = metrics_for_assignments(assignments, demand, pattern_cover)
    if metrics["deficit"] > 0:
        raise RuntimeError(f"{name} 存在未覆盖需求：{metrics['deficit']}")
    if metrics["worker_day_deviation"] > 0:
        raise RuntimeError(f"{name} 存在工人工作天数偏差：{metrics['worker_day_deviation']}")
    return metrics


def make_q1_column(shifts: tuple[int, ...], shift_cover: np.ndarray) -> Q1Column:
    day_count = len(shifts)
    hour_count = shift_cover.shape[1]
    cover = np.zeros((day_count, hour_count), dtype=int)
    for day, shift_id in enumerate(shifts):
        if shift_id >= 0:
            cover[day] = shift_cover[shift_id]
    return Q1Column(shifts=shifts, cover=cover.reshape(-1))


def initial_q1_columns(day_count: int, shift_cover: np.ndarray) -> list[Q1Column]:
    columns: list[Q1Column] = []
    seen: set[tuple[int, ...]] = set()
    shift_count = shift_cover.shape[0]
    for rest1 in range(day_count):
        for rest2 in range(rest1 + 1, day_count):
            for shift_id in range(shift_count):
                shifts = tuple(-1 if day in (rest1, rest2) else shift_id for day in range(day_count))
                if shifts not in seen:
                    seen.add(shifts)
                    columns.append(make_q1_column(shifts, shift_cover))
    return columns


def solve_q1_master_lp(columns: list[Q1Column], demand_vector: np.ndarray) -> tuple[np.ndarray, float, float]:
    matrix = np.column_stack([column.cover for column in columns])
    row_count = len(demand_vector)
    slack = np.eye(row_count)
    objective = np.concatenate([np.ones(len(columns)), np.full(row_count, 100_000.0)])
    lhs = -np.hstack([matrix, slack])
    result = linprog(
        c=objective,
        A_ub=lhs,
        b_ub=-demand_vector,
        bounds=[(0, None)] * len(objective),
        method="highs",
    )
    if not result.success:
        raise RuntimeError(f"列生成主问题LP失败：{result.message}")
    dual = -np.array(result.ineqlin.marginals, dtype=float)
    slack_sum = float(result.x[len(columns) :].sum())
    return dual, float(result.fun), slack_sum


def price_q1_columns(
    dual: np.ndarray,
    shift_cover: np.ndarray,
    existing: set[tuple[int, ...]],
    max_new_columns: int = 8,
    per_day_top: int = 4,
) -> list[tuple[float, Q1Column]]:
    day_count = dual.size // shift_cover.shape[1]
    hour_count = shift_cover.shape[1]
    shift_scores = np.zeros((day_count, shift_cover.shape[0]), dtype=float)
    for day in range(day_count):
        day_dual = dual[day * hour_count : (day + 1) * hour_count]
        shift_scores[day] = shift_cover @ day_dual

    per_day_top = max(1, min(per_day_top, shift_cover.shape[0]))
    per_day_order = [list(np.argsort(-shift_scores[day])[:per_day_top]) for day in range(day_count)]
    best_day_score = np.array([shift_scores[day, per_day_order[day][0]] for day in range(day_count)])
    selected_days = set(map(int, np.argsort(-best_day_score)[:8]))
    base = [-1] * day_count
    for day in selected_days:
        base[day] = int(per_day_order[day][0])

    candidates: list[tuple[int, ...]] = [tuple(base)]
    for day in selected_days:
        for alternative in per_day_order[day][1:]:
            modified = list(base)
            modified[day] = int(alternative)
            candidates.append(tuple(modified))
    for rest_day in set(range(day_count)).difference(selected_days):
        weakest_work_day = min(selected_days, key=lambda day: best_day_score[day])
        modified = list(base)
        modified[weakest_work_day] = -1
        modified[rest_day] = int(per_day_order[rest_day][0])
        candidates.append(tuple(modified))

    priced: list[tuple[float, Q1Column]] = []
    for shifts in candidates:
        if shifts in existing or shifts.count(-1) != 2:
            continue
        column = make_q1_column(shifts, shift_cover)
        reduced_cost = 1.0 - float(column.cover @ dual)
        if reduced_cost < -1e-7:
            priced.append((reduced_cost, column))
    priced.sort(key=lambda item: item[0])
    return priced[:max_new_columns]


def solve_q1_integer_master(columns: list[Q1Column], demand_vector: np.ndarray) -> tuple[int, float]:
    matrix = np.column_stack([column.cover for column in columns])
    row_count = len(demand_vector)
    constraints = LinearConstraint(np.hstack([matrix, np.eye(row_count)]), demand_vector, np.full(row_count, np.inf))
    objective = np.concatenate([np.ones(len(columns)), np.full(row_count, 100_000.0)])
    integrality = np.concatenate([np.ones(len(columns), dtype=int), np.zeros(row_count, dtype=int)])
    result = milp(
        c=objective,
        integrality=integrality,
        bounds=Bounds(np.zeros(len(objective)), np.full(len(objective), np.inf)),
        constraints=constraints,
        options={"time_limit": 120, "mip_rel_gap": 0},
    )
    if not result.success:
        raise RuntimeError(f"列生成整数主问题失败：{result.message}")
    slack_sum = float(result.x[len(columns) :].sum())
    return int(round(result.fun - 100_000.0 * slack_sum)), slack_sum


def solve_q1_column_generation_group(
    req_group: np.ndarray,
    shift_cover: np.ndarray,
    max_iterations: int = 80,
    max_new_columns: int = 8,
    per_day_top: int = 4,
) -> dict[str, float | int]:
    demand_vector = req_group.reshape(-1).astype(float)
    columns = initial_q1_columns(req_group.shape[0], shift_cover)
    existing = {column.key for column in columns}
    lp_objective = float("nan")
    lp_slack = float("nan")
    iterations = 0
    generated = 0
    for iteration in range(1, max_iterations + 1):
        dual, lp_objective, lp_slack = solve_q1_master_lp(columns, demand_vector)
        new_columns = price_q1_columns(
            dual,
            shift_cover,
            existing,
            max_new_columns=max_new_columns,
            per_day_top=per_day_top,
        )
        iterations = iteration
        if not new_columns:
            break
        for _, column in new_columns:
            existing.add(column.key)
            columns.append(column)
        generated += len(new_columns)
    integer_objective, integer_slack = solve_q1_integer_master(columns, demand_vector)
    return {
        "columns": len(columns),
        "generated_columns": generated,
        "iterations": iterations,
        "lp_objective": lp_objective,
        "lp_slack": lp_slack,
        "integer_workers": integer_objective,
        "integer_slack": integer_slack,
    }


def assignments_to_worker_table(
    assignments: np.ndarray,
    patterns: list[dict],
    hours: list[str],
    days: list[int],
    group_cols: list[str],
) -> pd.DataFrame:
    labels = [pattern_label(pattern, hours, group_cols) for pattern in patterns]
    rows = []
    for worker in range(assignments.shape[0]):
        row = {"工人编号": f"ALNS-{worker + 1:03d}"}
        for day_index, day in enumerate(days):
            pattern_id = int(assignments[worker, day_index])
            row[f"第{day}天"] = "休息" if pattern_id < 0 else labels[pattern_id]
        rows.append(row)
    return pd.DataFrame(rows)


def coverage_detail_table(
    assignments: np.ndarray,
    demand: np.ndarray,
    pattern_cover: np.ndarray,
    days: list[int],
    hours: list[str],
    group_cols: list[str],
) -> pd.DataFrame:
    coverage = coverage_from_assignments(assignments, pattern_cover)
    rows = []
    for day_index, day in enumerate(days):
        for group_index, group in enumerate(group_cols):
            for hour_index, hour in enumerate(hours):
                cover = int(coverage[day_index, group_index, hour_index])
                need = int(demand[day_index, group_index, hour_index])
                rows.append(
                    {
                        "天": day,
                        "小组": group,
                        "小时": hour,
                        "需求": need,
                        "覆盖": cover,
                        "冗余": max(cover - need, 0),
                        "缺口": max(need - cover, 0),
                    }
                )
    return pd.DataFrame(rows)


def solve_problem2_network_flow(
    demand: np.ndarray,
    shift_cover: np.ndarray,
    flow_method: str = "max_flow",
) -> dict[str, object]:
    day_minima: list[int] = []
    x_days: list[np.ndarray] = []
    for day in range(demand.shape[0]):
        count, x_day, _ = solve_daily_problem2(demand[day], shift_cover)
        day_minima.append(count)
        x_days.append(x_day)
    worker_count, daily_counts = choose_daily_counts(day_minima)
    work_matrix = build_workday_assignment(worker_count, daily_counts, flow_method)
    return {
        "day_minima": day_minima,
        "worker_count": worker_count,
        "daily_counts": daily_counts,
        "work_matrix": work_matrix,
        "x_days": x_days,
        "lower_bound": theoretical_worker_bound(day_minima),
        "flow_method": flow_method,
    }


def solve_problem3_alns(
    demand: np.ndarray,
    patterns: list[dict],
    pattern_cover: np.ndarray,
    config: AlnsConfig,
    flow_method: str = "max_flow",
) -> dict[str, object]:
    day_minima: list[int] = []
    x_days: list[np.ndarray] = []
    for day in range(demand.shape[0]):
        count, x_day, _ = solve_daily_problem3(demand[day], pattern_cover)
        day_minima.append(count)
        x_days.append(x_day)
    lower_bound = theoretical_worker_bound(day_minima)
    worker_count, daily_counts = choose_daily_counts(day_minima)
    work_matrix = build_workday_assignment(worker_count, daily_counts, flow_method)
    daily_pattern_ids = expand_pattern_ids_with_extras(x_days, daily_counts, demand, pattern_cover)
    initial_assignments = initial_assignments_from_flow(work_matrix, daily_pattern_ids)
    initial_metrics = validate_feasible("问题3初始最大流排班", initial_assignments, demand, pattern_cover)

    alns = Q3Alns(demand, pattern_cover, initial_assignments, config)
    started = time.perf_counter()
    result = alns.run()
    elapsed = time.perf_counter() - started
    final_metrics = validate_feasible("问题3 ALNS 最优排班", result.best_assignments, demand, pattern_cover)
    return {
        "day_minima": day_minima,
        "lower_bound": lower_bound,
        "worker_count": worker_count,
        "daily_counts": daily_counts,
        "initial_assignments": initial_assignments,
        "initial_metrics": initial_metrics,
        "alns_result": result,
        "final_metrics": final_metrics,
        "elapsed_seconds": elapsed,
        "x_days": x_days,
        "patterns": patterns,
        "flow_method": flow_method,
    }


def solve_problem1_independent(
    demand: np.ndarray,
    shift_cover: np.ndarray,
    q1_max_new_columns: int = 8,
    q1_per_day_top: int = 4,
) -> dict[str, object]:
    group_workers = []
    column_rows = []
    for group in range(demand.shape[1]):
        count = solve_problem1_group_exact(demand[:, group, :], shift_cover)
        group_workers.append(count)
        cg = solve_q1_column_generation_group(
            demand[:, group, :],
            shift_cover,
            max_new_columns=q1_max_new_columns,
            per_day_top=q1_per_day_top,
        )
        column_rows.append({"group_index": group + 1, "exact_workers": count, **cg})
    cg_total = int(sum(int(row["integer_workers"]) for row in column_rows))
    return {
        "group_workers": group_workers,
        "worker_count": int(sum(group_workers)),
        "column_generation_rows": column_rows,
        "column_generation_workers": cg_total,
    }


def write_outputs(
    output_path: Path,
    summary_path: Path,
    convergence_path: Path,
    q1: dict[str, object],
    q2: dict[str, object],
    q3: dict[str, object],
    demand: np.ndarray,
    pattern_cover: np.ndarray,
    days: list[int],
    hours: list[str],
    group_cols: list[str],
) -> None:
    alns_result: AlnsResult = q3["alns_result"]  # type: ignore[assignment]
    summary = pd.DataFrame(
        [
            {
                "问题": "问题1",
                "独立高级方法": "列生成主问题LP + 定价子问题 + 整数主问题",
                "理论下界": "",
                "独立求解人数": q1["column_generation_workers"],
                "可行性结论": "列生成整数主问题无人工松弛",
            },
            {
                "问题": "问题2",
                "独立高级方法": f"理论下界 + {flow_method_label(q2.get('flow_method', 'max_flow'))}",
                "理论下界": q2["lower_bound"],
                "独立求解人数": q2["worker_count"],
                "可行性结论": "理论下界达到且工作日映射满流可行",
            },
            {
                "问题": "问题3",
                "独立高级方法": f"理论下界 + {flow_method_label(q3.get('flow_method', 'max_flow'))}初始化 + ALNS联合搜索",
                "理论下界": q3["lower_bound"],
                "独立求解人数": q3["worker_count"],
                "可行性结论": "理论下界达到、覆盖缺口为0、每人工作8天",
            },
        ]
    )
    q2_daily = pd.DataFrame(
        {
            "天": days,
            "单日最少出勤人数": q2["day_minima"],
            "最大流安排出勤人数": q2["daily_counts"],
        }
    )
    q3_daily = pd.DataFrame(
        {
            "天": days,
            "单日最少出勤人数": q3["day_minima"],
            "ALNS安排出勤人数": (alns_result.best_assignments >= 0).sum(axis=0),
            "下界平衡出勤人数": q3["daily_counts"],
        }
    )
    q1_group = pd.DataFrame({"小组": group_cols, "精确人数": q1["group_workers"]})
    q1_cg = pd.DataFrame(q1["column_generation_rows"])
    q3_worker = assignments_to_worker_table(alns_result.best_assignments, q3["patterns"], hours, days, group_cols)  # type: ignore[arg-type]
    q3_coverage = coverage_detail_table(alns_result.best_assignments, demand, pattern_cover, days, hours, group_cols)
    q3_metrics = pd.DataFrame(
        [
            {"指标": key, "数值": value}
            for key, value in {
                **q3["initial_metrics"],  # type: ignore[arg-type]
                **{f"ALNS_{k}": v for k, v in q3["final_metrics"].items()},  # type: ignore[union-attr]
                "ALNS_best_score": alns_result.best_score,
                "ALNS_elapsed_seconds": q3["elapsed_seconds"],
                **alns_result.operator_weights,
            }.items()
        ]
    )

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        summary.to_excel(writer, sheet_name="Summary", index=False)
        q1_group.to_excel(writer, sheet_name="Q1_IndependentExact", index=False)
        q1_cg.to_excel(writer, sheet_name="Q1_ColumnGeneration", index=False)
        q2_daily.to_excel(writer, sheet_name="Q2_NetworkFlow", index=False)
        q3_daily.to_excel(writer, sheet_name="Q3_ALNS_Daily", index=False)
        q3_metrics.to_excel(writer, sheet_name="Q3_ALNS_Metrics", index=False)
        alns_result.history.to_excel(writer, sheet_name="Q3_ALNS_Convergence", index=False)
        q3_coverage.to_excel(writer, sheet_name="Q3_ALNS_Coverage", index=False)
        q3_worker.to_excel(writer, sheet_name="Q3_ALNS_WorkerSchedule", index=False)

    alns_result.history.to_csv(convergence_path, index=False, encoding="utf-8-sig")
    json_summary = {
        "summary": summary.to_dict(orient="records"),
        "q2_day_minima": list(map(int, q2["day_minima"])),
        "q1_column_generation": q1["column_generation_rows"],
        "q2_daily_counts": list(map(int, q2["daily_counts"])),
        "q3_day_minima": list(map(int, q3["day_minima"])),
        "q3_daily_counts_initial": list(map(int, q3["daily_counts"])),
        "q3_daily_counts_alns": list(map(int, (alns_result.best_assignments >= 0).sum(axis=0))),
        "q3_initial_metrics": q3["initial_metrics"],
        "q3_final_metrics": q3["final_metrics"],
        "q3_operator_weights": alns_result.operator_weights,
        "q3_elapsed_seconds": q3["elapsed_seconds"],
        "q2_flow_method": q2.get("flow_method", "max_flow"),
        "q3_flow_method": q3.get("flow_method", "max_flow"),
    }
    summary_path.write_text(json.dumps(json_summary, ensure_ascii=False, indent=2), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="大型展销会排班完全独立高级优化求解：列生成、网络流与ALNS")
    parser.add_argument("--data", default=DEFAULT_INPUT, help="附件需求文件路径，默认使用附件1.xlsx")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="独立高级方法结果工作簿")
    parser.add_argument("--json", default=DEFAULT_JSON, help="独立高级方法摘要JSON")
    parser.add_argument("--convergence", default=DEFAULT_CONVERGENCE, help="ALNS收敛日志CSV")
    parser.add_argument("--iterations", type=int, default=900, help="ALNS迭代次数")
    parser.add_argument("--seed", type=int, default=20260429, help="ALNS随机种子")
    parser.add_argument("--flow-method", choices=["max_flow", "min_cost"], default="max_flow", help="工作日映射方法")
    parser.add_argument("--q1-max-new-columns", type=int, default=8, help="问题一每轮最多新增列数")
    parser.add_argument("--q1-per-day-top", type=int, default=4, help="问题一定价中每天保留的候选班型数")
    parser.add_argument("--alns-surplus-weight", type=float, default=1.0, help="ALNS总冗余权重")
    parser.add_argument("--alns-max-surplus-weight", type=float, default=0.0, help="ALNS最大单点冗余权重")
    parser.add_argument("--alns-surplus-square-weight", type=float, default=0.0, help="ALNS冗余平方权重")
    parser.add_argument("--alns-day-worker-std-weight", type=float, default=0.01, help="ALNS每日人数波动权重")
    parser.add_argument("--destroy-operators", default="", help="逗号分隔的ALNS破坏算子列表，留空使用默认算子")
    parser.add_argument("--repair-operators", default="", help="逗号分隔的ALNS修复算子列表，留空使用默认算子")
    return parser.parse_args()


def parse_operator_list(value: str, default: tuple[str, ...]) -> tuple[str, ...]:
    if not value:
        return default
    operators = tuple(part.strip() for part in value.split(",") if part.strip())
    if not operators:
        raise ValueError("算子列表不能为空。")
    return operators


def main() -> None:
    args = parse_args()
    demand, days, hours, group_cols = read_demand(args.data)
    _, shift_cover_same, shift_labels_same = build_shift_pairs(min_break=0)
    _, shift_cover_cross, shift_labels_cross = build_shift_pairs(min_break=2)
    patterns3, cover3 = build_problem3_patterns(
        demand.shape[1],
        demand.shape[2],
        shift_cover_same,
        shift_labels_same,
        shift_cover_cross,
        shift_labels_cross,
    )
    default_config = AlnsConfig()
    config = AlnsConfig(
        iterations=args.iterations,
        seed=args.seed,
        surplus_weight=args.alns_surplus_weight,
        max_surplus_weight=args.alns_max_surplus_weight,
        surplus_square_weight=args.alns_surplus_square_weight,
        day_worker_std_weight=args.alns_day_worker_std_weight,
        destroy_operators=parse_operator_list(args.destroy_operators, default_config.destroy_operators),
        repair_operators=parse_operator_list(args.repair_operators, default_config.repair_operators),
    )
    print("开始问题1完全独立列生成求解...")
    q1 = solve_problem1_independent(
        demand,
        shift_cover_same,
        q1_max_new_columns=args.q1_max_new_columns,
        q1_per_day_top=args.q1_per_day_top,
    )
    print(f"问题1列生成人数：{q1['column_generation_workers']}")
    print("开始问题2理论下界与最大流验证...")
    q2 = solve_problem2_network_flow(demand, shift_cover_same, flow_method=args.flow_method)
    print(f"问题2下界/人数：{q2['lower_bound']} / {q2['worker_count']}")
    print("开始问题3最大流初始化与ALNS联合搜索...")
    q3 = solve_problem3_alns(demand, patterns3, cover3, config, flow_method=args.flow_method)
    print(f"问题3下界/人数：{q3['lower_bound']} / {q3['worker_count']}")
    print(f"问题3ALNS最终指标：{q3['final_metrics']}")

    output_path = Path(args.output)
    summary_path = Path(args.json)
    convergence_path = Path(args.convergence)
    write_outputs(output_path, summary_path, convergence_path, q1, q2, q3, demand, cover3, days, hours, group_cols)
    print(f"高级结果已保存：{output_path.resolve()}")
    print(f"摘要JSON已保存：{summary_path.resolve()}")
    print(f"ALNS收敛日志已保存：{convergence_path.resolve()}")


if __name__ == "__main__":
    main()
