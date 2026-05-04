from __future__ import annotations

import argparse
import json
import math
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import csr_matrix, lil_matrix


ROOT = Path(__file__).resolve().parents[1]
OUT_CSV = ROOT / ".codex" / "standby_pool_udr_curve.csv"
OUT_JSON = ROOT / ".codex" / "standby_pool_udr_curve.json"
OUT_MD = ROOT / ".codex" / "standby_pool_udr_curve.md"
OUT_PNG = ROOT / "visualizations" / "mainline" / "fig_standby_pool_udr_curve.png"

DEFAULT_RUNS = 200
DEFAULT_MAX_STANDBY = 30
DEFAULT_SEED = 20260501
DEFAULT_TIME_LIMIT = 30
DEFAULT_ZERO_STOP_SPAN = 3
ABSENCE_RATES = (0.01, 0.03, 0.05)
PRIMARY_WEIGHT = 1.0
SECONDARY_WEIGHT = 1e-6

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import independent_advanced_staff_scheduling as model  # noqa: E402


@dataclass(frozen=True)
class DayOption:
    cap: int
    used: int
    total_deficit: int
    max_cell_deficit: int
    shortage_cells: int
    deficit_matrix: np.ndarray
    solve_success: bool
    runtime_seconds: float
    solver_status: int | None
    solver_message: str


@dataclass(frozen=True)
class SampleResult:
    standby_workers: int
    total_deficit: int
    udr: float
    max_cell_deficit: int
    shortage_cells: int
    standby_workdays_used: int
    daily_standby_max: int
    solve_success: bool
    runtime_seconds: float


class MaxFlow:
    def __init__(self, node_count: int) -> None:
        self.graph: list[list[list[int]]] = [[] for _ in range(node_count)]

    def add_edge(self, src: int, dst: int, cap: int) -> None:
        forward = [dst, len(self.graph[dst]), cap]
        backward = [src, len(self.graph[src]), 0]
        self.graph[src].append(forward)
        self.graph[dst].append(backward)

    def max_flow(self, source: int, sink: int) -> int:
        flow = 0
        while True:
            level = [-1] * len(self.graph)
            level[source] = 0
            queue = [source]
            for node in queue:
                for to, _, cap in self.graph[node]:
                    if cap > 0 and level[to] < 0:
                        level[to] = level[node] + 1
                        queue.append(to)
            if level[sink] < 0:
                return flow
            it = [0] * len(self.graph)
            while True:
                pushed = self._dfs(source, sink, 10**18, level, it)
                if pushed == 0:
                    break
                flow += pushed

    def _dfs(self, node: int, sink: int, amount: int, level: list[int], it: list[int]) -> int:
        if node == sink:
            return amount
        while it[node] < len(self.graph[node]):
            edge = self.graph[node][it[node]]
            to, rev, cap = edge
            if cap > 0 and level[to] == level[node] + 1:
                pushed = self._dfs(to, sink, min(amount, cap), level, it)
                if pushed > 0:
                    edge[2] -= pushed
                    self.graph[to][rev][2] += pushed
                    return pushed
            it[node] += 1
        return 0


class DailyRecourseModel:
    def __init__(self, pattern_cover: np.ndarray, max_standby: int, time_limit: int) -> None:
        self.pattern_cover = pattern_cover.astype(int)
        self.pattern_count, self.group_count, self.hour_count = pattern_cover.shape
        self.cell_count = self.group_count * self.hour_count
        self.max_standby = max_standby
        self.time_limit = time_limit
        self.var_count = self.pattern_count + self.cell_count
        self.integrality = np.concatenate(
            [np.ones(self.pattern_count, dtype=int), np.zeros(self.cell_count, dtype=int)]
        )
        upper_bounds = np.concatenate(
            [
                np.full(self.pattern_count, float(max_standby)),
                np.full(self.cell_count, np.inf),
            ]
        )
        self.bounds = Bounds(np.zeros(self.var_count), upper_bounds)
        self.objective = np.concatenate(
            [
                np.full(self.pattern_count, SECONDARY_WEIGHT, dtype=float),
                np.full(self.cell_count, PRIMARY_WEIGHT, dtype=float),
            ]
        )
        self.base_matrix = self._build_matrix()

    def _build_matrix(self) -> csr_matrix:
        matrix = lil_matrix((self.cell_count + 1, self.var_count), dtype=float)
        row = 0
        for group in range(self.group_count):
            for hour in range(self.hour_count):
                for pattern_id in range(self.pattern_count):
                    if self.pattern_cover[pattern_id, group, hour]:
                        matrix[row, pattern_id] = 1.0
                matrix[row, self.pattern_count + row] = 1.0
                row += 1
        for pattern_id in range(self.pattern_count):
            matrix[self.cell_count, pattern_id] = 1.0
        return matrix.tocsr()

    def solve(self, residual_day: np.ndarray, standby_cap: int) -> DayOption:
        if standby_cap < 0:
            raise ValueError(f"待命池人数上限不能为负：{standby_cap}")
        residual = residual_day.astype(int, copy=False)
        if int(residual.sum()) == 0 or standby_cap == 0:
            deficit = residual.copy()
            return DayOption(
                cap=standby_cap,
                used=0,
                total_deficit=int(deficit.sum()),
                max_cell_deficit=int(deficit.max(initial=0)),
                shortage_cells=int((deficit > 0).sum()),
                deficit_matrix=deficit,
                solve_success=True,
                runtime_seconds=0.0,
                solver_status=0,
                solver_message="无需补位求解",
            )

        lower = np.concatenate([residual.reshape(-1).astype(float), np.array([-np.inf])])
        upper = np.concatenate([np.full(self.cell_count, np.inf), np.array([float(standby_cap)])])
        started = time.perf_counter()
        result = milp(
            c=self.objective,
            integrality=self.integrality,
            bounds=self.bounds,
            constraints=LinearConstraint(self.base_matrix, lower, upper),
            options={"time_limit": self.time_limit, "mip_rel_gap": 0},
        )
        elapsed = time.perf_counter() - started

        has_x = getattr(result, "x", None) is not None and len(result.x) == self.var_count
        if result.success:
            x = np.rint(result.x[: self.pattern_count]).astype(int)
        elif has_x:
            # 超时或其他非最优退出时，向下取整得到保守可行的整数上界解。
            x = np.floor(np.maximum(result.x[: self.pattern_count], 0.0) + 1e-9).astype(int)
        else:
            deficit = residual.copy()
            return DayOption(
                cap=standby_cap,
                used=0,
                total_deficit=int(deficit.sum()),
                max_cell_deficit=int(deficit.max(initial=0)),
                shortage_cells=int((deficit > 0).sum()),
                deficit_matrix=deficit,
                solve_success=False,
                runtime_seconds=elapsed,
                solver_status=getattr(result, "status", None),
                solver_message=str(getattr(result, "message", "MILP 无可用解")),
            )

        x = np.clip(x, 0, standby_cap)
        used = int(x.sum())
        if used > standby_cap:
            raise RuntimeError(f"日补位解违反上限：used={used}, cap={standby_cap}")
        standby_cover = np.tensordot(x, self.pattern_cover, axes=(0, 0))
        deficit = np.maximum(residual - standby_cover, 0).astype(int)
        return DayOption(
            cap=standby_cap,
            used=used,
            total_deficit=int(deficit.sum()),
            max_cell_deficit=int(deficit.max(initial=0)),
            shortage_cells=int((deficit > 0).sum()),
            deficit_matrix=deficit,
            solve_success=bool(result.success),
            runtime_seconds=elapsed,
            solver_status=getattr(result, "status", None),
            solver_message=str(getattr(result, "message", "")),
        )


class SampleRecourseEvaluator:
    def __init__(
        self,
        residual: np.ndarray,
        total_demand: int,
        daily_model: DailyRecourseModel,
        max_standby: int,
    ) -> None:
        self.residual = residual.astype(int)
        self.total_demand = total_demand
        self.daily_model = daily_model
        self.max_standby = max_standby
        self.day_count = residual.shape[0]
        self.day_options: list[dict[int, DayOption]] = [{0: self._base_option(day)} for day in range(self.day_count)]
        self.day_zero_caps: list[int | None] = [
            0 if self.day_options[day][0].total_deficit == 0 else None for day in range(self.day_count)
        ]

    def _base_option(self, day: int) -> DayOption:
        deficit = self.residual[day].copy()
        return DayOption(
            cap=0,
            used=0,
            total_deficit=int(deficit.sum()),
            max_cell_deficit=int(deficit.max(initial=0)),
            shortage_cells=int((deficit > 0).sum()),
            deficit_matrix=deficit,
            solve_success=True,
            runtime_seconds=0.0,
            solver_status=0,
            solver_message="N_sb=0",
        )

    def get_day_option(self, day: int, cap: int) -> tuple[DayOption, float]:
        if cap in self.day_options[day]:
            return self.day_options[day][cap], 0.0
        zero_cap = self.day_zero_caps[day]
        if zero_cap is not None and zero_cap < cap:
            option = self.day_options[day][zero_cap]
            copied = DayOption(
                cap=cap,
                used=option.used,
                total_deficit=option.total_deficit,
                max_cell_deficit=option.max_cell_deficit,
                shortage_cells=option.shortage_cells,
                deficit_matrix=option.deficit_matrix,
                solve_success=option.solve_success,
                runtime_seconds=0.0,
                solver_status=option.solver_status,
                solver_message=f"沿用 cap={zero_cap} 的零缺口解",
            )
            self.day_options[day][cap] = copied
            return copied, 0.0
        option = self.daily_model.solve(self.residual[day], cap)
        self.day_options[day][cap] = option
        if option.total_deficit == 0 and self.day_zero_caps[day] is None:
            self.day_zero_caps[day] = cap
        return option, option.runtime_seconds

    def _candidate_options_for_n(self, day: int, standby_workers: int) -> list[DayOption]:
        options = [self.day_options[day][cap] for cap in range(0, standby_workers + 1) if cap in self.day_options[day]]
        best_by_key: dict[tuple[int, int], DayOption] = {}
        for option in options:
            key = (option.used, option.total_deficit)
            current = best_by_key.get(key)
            if current is None:
                best_by_key[key] = option
                continue
            better = (
                option.max_cell_deficit,
                option.shortage_cells,
                option.cap,
            ) < (
                current.max_cell_deficit,
                current.shortage_cells,
                current.cap,
            )
            if better:
                best_by_key[key] = option
        return sorted(best_by_key.values(), key=lambda item: (item.used, item.total_deficit, item.cap))

    def evaluate(self, standby_workers: int) -> SampleResult:
        if standby_workers < 0:
            raise ValueError(f"待命池人数不能为负：{standby_workers}")
        incremental_runtime = 0.0
        for day in range(self.day_count):
            _, day_runtime = self.get_day_option(day, standby_workers)
            incremental_runtime += day_runtime

        if standby_workers == 0:
            deficit = self.residual
            return SampleResult(
                standby_workers=0,
                total_deficit=int(deficit.sum()),
                udr=float(deficit.sum() / self.total_demand) if self.total_demand else 0.0,
                max_cell_deficit=int(deficit.max(initial=0)),
                shortage_cells=int((deficit > 0).sum()),
                standby_workdays_used=0,
                daily_standby_max=0,
                solve_success=True,
                runtime_seconds=incremental_runtime,
            )

        dp_started = time.perf_counter()
        states: dict[int, tuple[int, list[DayOption]]] = {0: (0, [])}
        for day in range(self.day_count):
            new_states: dict[int, tuple[int, list[DayOption]]] = {}
            for used_so_far, (deficit_so_far, path) in states.items():
                for option in self._candidate_options_for_n(day, standby_workers):
                    total_used = used_so_far + option.used
                    if total_used > 8 * standby_workers:
                        continue
                    total_deficit = deficit_so_far + option.total_deficit
                    candidate = (total_deficit, path + [option])
                    current = new_states.get(total_used)
                    if current is None or candidate[0] < current[0]:
                        new_states[total_used] = candidate
            if not new_states:
                raise RuntimeError(f"样本 DP 无法扩展到第 {day + 1} 天")
            states = new_states

        best_used, (best_deficit, best_path) = min(states.items(), key=lambda item: (item[1][0], item[0]))
        incremental_runtime += time.perf_counter() - dp_started
        daily_counts = np.array([option.used for option in best_path], dtype=int)
        flow_ok = validate_standby_assignment(standby_workers, daily_counts)
        if not flow_ok:
            raise RuntimeError(f"待命池工作日分解失败：N_sb={standby_workers}, daily_counts={daily_counts.tolist()}")
        max_cell = max((option.max_cell_deficit for option in best_path), default=0)
        shortage_cells = int(sum(option.shortage_cells for option in best_path))
        solve_success = flow_ok and all(option.solve_success for option in best_path)
        return SampleResult(
            standby_workers=standby_workers,
            total_deficit=int(best_deficit),
            udr=float(best_deficit / self.total_demand) if self.total_demand else 0.0,
            max_cell_deficit=int(max_cell),
            shortage_cells=shortage_cells,
            standby_workdays_used=int(best_used),
            daily_standby_max=int(daily_counts.max(initial=0)),
            solve_success=solve_success,
            runtime_seconds=incremental_runtime,
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="问题三弹性待命池真实补位 UDR 仿真")
    parser.add_argument("--runs", type=int, default=DEFAULT_RUNS, help="Monte Carlo 仿真次数，默认 200")
    parser.add_argument("--max-standby", type=int, default=DEFAULT_MAX_STANDBY, help="待命池搜索上限，默认 30")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="随机种子，默认 20260501")
    parser.add_argument("--time-limit", type=int, default=DEFAULT_TIME_LIMIT, help="单个日补位 MILP 的 time_limit 秒数")
    parser.add_argument(
        "--zero-stop-span",
        type=int,
        default=DEFAULT_ZERO_STOP_SPAN,
        help="当 mean_UDR 连续若干个 N_sb 为 0 时提前停止，默认 3",
    )
    parser.add_argument("--workbook", default="", help="显式指定问题三排班工作簿路径")
    parser.add_argument("--input", default="", help="显式指定附件1路径")
    return parser.parse_args()


def find_input_file(explicit: str) -> Path:
    if explicit:
        path = Path(explicit)
        if not path.exists():
            raise FileNotFoundError(f"找不到指定需求文件：{path}")
        return path
    candidates = [ROOT / "附件1.xlsx", ROOT / "附件1.xls"]
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError("找不到附件1.xlsx 或 附件1.xls")


def find_q3_workbook(explicit: str) -> tuple[Path, str]:
    if explicit:
        path = Path(explicit)
        if not path.exists():
            raise FileNotFoundError(f"找不到指定工作簿：{path}")
        sheet = detect_q3_sheet(path)
        return path, sheet
    preferred = [
        ROOT / "independent_高级排班优化结果.xlsx",
        ROOT / "高级排班优化结果.xlsx",
        ROOT / "排班优化求解结果.xlsx",
    ]
    tried: list[str] = []
    for path in preferred:
        tried.append(str(path))
        if path.exists():
            try:
                sheet = detect_q3_sheet(path)
                return path, sheet
            except ValueError:
                continue
    raise FileNotFoundError(
        "无法读取问题三最终排班，请检查以下工作簿是否存在且包含 Q3_ALNS_WorkerSchedule 或 Q3_WorkerSchedule："
        + "；".join(tried)
    )


def detect_q3_sheet(workbook_path: Path) -> str:
    with pd.ExcelFile(workbook_path) as book:
        for sheet in ("Q3_ALNS_WorkerSchedule", "Q3_WorkerSchedule"):
            if sheet in book.sheet_names:
                return sheet
    raise ValueError(f"工作簿缺少问题三工人排班工作表：{workbook_path}")


def ensure_dirs() -> None:
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    OUT_PNG.parent.mkdir(parents=True, exist_ok=True)


def load_summary_json(path: Path) -> dict[str, object]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def normalize_schedule_text(value: object) -> str:
    text = "" if value is None else str(value).strip()
    if not text or text.lower() == "nan":
        return "休息"
    return text.replace(" ", "").replace("：", ":").replace("＋", "+")


def build_pattern_label_map(
    patterns: list[dict[str, object]],
    hours: list[str],
    group_cols: list[str],
) -> dict[str, int]:
    label_map: dict[str, int] = {}
    for pattern_id, pattern in enumerate(patterns):
        label = str(model.pattern_label(pattern, hours, group_cols))
        normalized = normalize_schedule_text(label)
        if normalized in label_map:
            raise RuntimeError(f"模式标签不唯一：{normalized}")
        label_map[normalized] = pattern_id
    return label_map


def load_baseline_assignments(
    workbook_path: Path,
    sheet_name: str,
    patterns: list[dict[str, object]],
    pattern_cover: np.ndarray,
    demand: np.ndarray,
    days: list[int],
    hours: list[str],
    group_cols: list[str],
) -> tuple[np.ndarray, dict[str, float]]:
    df = pd.read_excel(workbook_path, sheet_name=sheet_name)
    if df.empty:
        raise RuntimeError(f"问题三排班工作表为空：{workbook_path}::{sheet_name}")
    if df.shape[1] < len(days) + 1:
        raise RuntimeError(
            f"问题三排班工作表列数不足：{workbook_path}::{sheet_name}，期望至少 {len(days) + 1} 列，实际 {df.shape[1]} 列"
        )
    label_map = build_pattern_label_map(patterns, hours, group_cols)
    day_columns = list(df.columns[1 : 1 + len(days)])
    assignments = np.full((len(df), len(days)), -1, dtype=int)
    for worker_index, (_, row) in enumerate(df.iterrows()):
        for day_index, column in enumerate(day_columns):
            text = normalize_schedule_text(row[column])
            if text == "休息":
                continue
            pattern_id = label_map.get(text)
            if pattern_id is None:
                raise RuntimeError(
                    f"无法将工作表文本映射到问题三合法模式：worker={worker_index + 1}, day={day_index + 1}, text={row[column]!r}"
                )
            assignments[worker_index, day_index] = pattern_id
    metrics = model.metrics_for_assignments(assignments, demand, pattern_cover)
    if int(metrics["deficit"]) != 0:
        raise RuntimeError(f"重建的基准问题三排班仍有缺口：{metrics['deficit']}")
    if assignments.shape[0] != 400:
        raise RuntimeError(f"重建的基准问题三人数不是 400，而是 {assignments.shape[0]}")
    return assignments, metrics


def worker_contributions_from_assignments(assignments: np.ndarray, pattern_cover: np.ndarray) -> np.ndarray:
    worker_count, day_count = assignments.shape
    group_count, hour_count = pattern_cover.shape[1], pattern_cover.shape[2]
    contributions = np.zeros((worker_count, day_count, group_count, hour_count), dtype=int)
    for worker in range(worker_count):
        for day in range(day_count):
            pattern_id = int(assignments[worker, day])
            if pattern_id >= 0:
                contributions[worker, day] = pattern_cover[pattern_id]
    return contributions


def validate_standby_assignment(worker_count: int, daily_counts: np.ndarray) -> bool:
    if worker_count < 0:
        return False
    if worker_count == 0:
        return bool(int(daily_counts.sum()) == 0)
    if np.any(daily_counts < 0) or np.any(daily_counts > worker_count):
        return False
    if int(daily_counts.sum()) > 8 * worker_count:
        return False
    source = 0
    worker_offset = 1
    day_offset = worker_offset + worker_count
    sink = day_offset + len(daily_counts)
    flow = MaxFlow(sink + 1)
    for worker in range(worker_count):
        flow.add_edge(source, worker_offset + worker, 8)
    for worker in range(worker_count):
        for day in range(len(daily_counts)):
            flow.add_edge(worker_offset + worker, day_offset + day, 1)
    for day, count in enumerate(daily_counts):
        flow.add_edge(day_offset + day, sink, int(count))
    required = int(daily_counts.sum())
    return flow.max_flow(source, sink) == required


def first_threshold(records: list[dict[str, object]], key: str, predicate) -> int | None:
    for record in records:
        value = record[key]
        if predicate(value):
            return int(record["standby_workers"])
    return None


def summarize_records(records: list[SampleResult], absence_rate: float, total_demand: int) -> dict[str, object]:
    deficits = np.array([item.total_deficit for item in records], dtype=float)
    udrs = np.array([item.udr for item in records], dtype=float)
    max_cells = np.array([item.max_cell_deficit for item in records], dtype=float)
    shortage_cells = np.array([item.shortage_cells for item in records], dtype=float)
    workdays = np.array([item.standby_workdays_used for item in records], dtype=float)
    daily_max = np.array([item.daily_standby_max for item in records], dtype=float)
    runtimes = np.array([item.runtime_seconds for item in records], dtype=float)
    success = np.array([1.0 if item.solve_success else 0.0 for item in records], dtype=float)
    standby_workers = int(records[0].standby_workers) if records else 0
    return {
        "absence_rate": float(absence_rate),
        "standby_workers": standby_workers,
        "monte_carlo_runs": int(len(records)),
        "total_demand": int(total_demand),
        "mean_total_deficit": round(float(deficits.mean()), 6),
        "median_total_deficit": round(float(np.median(deficits)), 6),
        "p90_total_deficit": round(float(np.percentile(deficits, 90)), 6),
        "mean_UDR": round(float(udrs.mean()), 8),
        "median_UDR": round(float(np.median(udrs)), 8),
        "p90_UDR": round(float(np.percentile(udrs, 90)), 8),
        "mean_max_cell_deficit": round(float(max_cells.mean()), 6),
        "mean_shortage_cells": round(float(shortage_cells.mean()), 6),
        "mean_standby_workdays_used": round(float(workdays.mean()), 6),
        "mean_daily_standby_max": round(float(daily_max.mean()), 6),
        "zero_deficit_rate": round(float((deficits == 0).mean()), 8),
        "solve_success_rate": round(float(success.mean()), 8),
        "mean_runtime_seconds_per_recourse": round(float(runtimes.mean()), 6),
    }


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


def run_absence_scenario(
    assignments: np.ndarray,
    contributions: np.ndarray,
    demand: np.ndarray,
    pattern_cover: np.ndarray,
    daily_model: DailyRecourseModel,
    absence_rate: float,
    runs: int,
    seed: int,
    max_standby: int,
    zero_stop_span: int,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    rng = np.random.default_rng(seed)
    active_mask = assignments >= 0
    total_demand = int(demand.sum())
    sample_results: list[list[SampleResult]] = []
    for _ in range(runs):
        absent_mask = (rng.random(active_mask.shape) < absence_rate) & active_mask
        available = (~absent_mask).astype(int)[..., None, None]
        coverage_after_absence = (contributions * available).sum(axis=0)
        residual = np.maximum(demand - coverage_after_absence, 0)
        evaluator = SampleRecourseEvaluator(residual, total_demand, daily_model, max_standby)
        sample_row: list[SampleResult] = []
        for standby_workers in range(0, max_standby + 1):
            result = evaluator.evaluate(standby_workers)
            sample_row.append(result)
            if result.total_deficit == 0:
                for next_workers in range(standby_workers + 1, max_standby + 1):
                    sample_row.append(
                        SampleResult(
                            standby_workers=next_workers,
                            total_deficit=0,
                            udr=0.0,
                            max_cell_deficit=0,
                            shortage_cells=0,
                            standby_workdays_used=result.standby_workdays_used,
                            daily_standby_max=result.daily_standby_max,
                            solve_success=result.solve_success,
                            runtime_seconds=0.0,
                        )
                    )
                break
        if len(sample_row) != max_standby + 1:
            raise RuntimeError("样本结果长度异常")
        sample_results.append(sample_row)

    aggregated_rows: list[dict[str, object]] = []
    zero_streak = 0
    stopped_early = False
    stop_at: int | None = None
    for standby_workers in range(0, max_standby + 1):
        records = [sample[standby_workers] for sample in sample_results]
        row = summarize_records(records, absence_rate, total_demand)
        aggregated_rows.append(row)
        if row["mean_total_deficit"] == 0:
            zero_streak += 1
        else:
            zero_streak = 0
        if zero_streak >= zero_stop_span:
            stopped_early = standby_workers < max_standby
            stop_at = standby_workers
            break

    meta = {
        "absence_rate": absence_rate,
        "scenario_seed": seed,
        "zero_stop_span": zero_stop_span,
        "stopped_early": stopped_early,
        "stop_at_standby_workers": stop_at,
        "evaluated_standby_range": [0, int(aggregated_rows[-1]["standby_workers"])],
    }
    return aggregated_rows, meta


def build_threshold_summary(rows: list[dict[str, object]]) -> dict[float, dict[str, int | None]]:
    grouped: dict[float, list[dict[str, object]]] = {}
    for row in rows:
        grouped.setdefault(float(row["absence_rate"]), []).append(row)
    summary: dict[float, dict[str, int | None]] = {}
    for absence_rate, items in grouped.items():
        summary[absence_rate] = {
            "udr_le_1pct": first_threshold(items, "mean_UDR", lambda value: float(value) <= 0.01),
            "udr_eq_0": first_threshold(items, "mean_UDR", lambda value: float(value) == 0.0),
        }
    return summary


def format_threshold(value: int | None) -> str:
    return str(value) if value is not None else "未在搜索范围内达到"


def write_markdown(
    rows: list[dict[str, object]],
    config: dict[str, object],
    thresholds: dict[float, dict[str, int | None]],
    scenario_meta: dict[float, dict[str, object]],
) -> None:
    lines: list[str] = []
    lines.append("# 弹性待命池 UDR 仿真结果")
    lines.append("")
    lines.append("## 配置")
    lines.append("")
    lines.append(f"- 基准方案：问题三 400 人确定性最优排班")
    lines.append(f"- Monte Carlo 次数：{config['runs']}")
    lines.append(f"- 随机种子：{config['seed']}")
    lines.append(f"- 缺勤率场景：1%、3%、5%")
    lines.append(f"- 搜索上限：N_sb = 0..{config['max_standby']}")
    lines.append(f"- 单个日补位 MILP time_limit：{config['time_limit_seconds']} 秒")
    lines.append(
        f"- 提前停止条件：某一缺勤率下，mean_UDR 连续 {config['zero_stop_span']} 个 N_sb 为 0 时停止该场景后续搜索"
    )
    lines.append("")
    lines.append("## 论文摘要")
    lines.append("")
    lines.append(
        "为进一步量化弹性待命池规模，本文在问题三 400 人基准排班基础上进行 "
        f"{config['runs']} 次 Monte Carlo 随机缺勤仿真。每次缺勤后，重新求解待命人员补位整数规划，而非采用总容量折算。"
        "结果显示，在随机缺勤 1%、3%、5% 场景下，使平均 UDR 降至 1% 以下分别需要约 "
        f"{format_threshold(thresholds[0.01]['udr_le_1pct'])}、"
        f"{format_threshold(thresholds[0.03]['udr_le_1pct'])}、"
        f"{format_threshold(thresholds[0.05]['udr_le_1pct'])} 名待命人员；"
        "若要求平均缺口为 0，则分别需要约 "
        f"{format_threshold(thresholds[0.01]['udr_eq_0'])}、"
        f"{format_threshold(thresholds[0.03]['udr_eq_0'])}、"
        f"{format_threshold(thresholds[0.05]['udr_eq_0'])} 名待命人员。"
        "该结果表明，400 人方案是确定性条件下的成本极限，实际运营中需要配置适度弹性待命池。"
    )
    lines.append("")
    lines.append("## 阈值汇总")
    lines.append("")
    lines.append("| 缺勤率 | mean_UDR ≤ 1% 的最小 N_sb | mean_UDR = 0 的最小 N_sb |")
    lines.append("| --- | ---: | ---: |")
    for absence_rate in ABSENCE_RATES:
        lines.append(
            f"| {int(absence_rate * 100)}% | {format_threshold(thresholds[absence_rate]['udr_le_1pct'])} | "
            f"{format_threshold(thresholds[absence_rate]['udr_eq_0'])} |"
        )
    lines.append("")
    lines.append("## 结果表")
    lines.append("")
    lines.append(
        "| 缺勤率 | N_sb | mean_total_deficit | median_total_deficit | p90_total_deficit | "
        "mean_UDR | median_UDR | p90_UDR | mean_max_cell_deficit | mean_shortage_cells | "
        "mean_standby_workdays_used | mean_daily_standby_max | zero_deficit_rate | solve_success_rate | "
        "mean_runtime_seconds_per_recourse |"
    )
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for row in rows:
        lines.append(
            f"| {int(float(row['absence_rate']) * 100)}% | {row['standby_workers']} | {row['mean_total_deficit']} | "
            f"{row['median_total_deficit']} | {row['p90_total_deficit']} | {row['mean_UDR']} | {row['median_UDR']} | "
            f"{row['p90_UDR']} | {row['mean_max_cell_deficit']} | {row['mean_shortage_cells']} | "
            f"{row['mean_standby_workdays_used']} | {row['mean_daily_standby_max']} | {row['zero_deficit_rate']} | "
            f"{row['solve_success_rate']} | {row['mean_runtime_seconds_per_recourse']} |"
        )
    lines.append("")
    lines.append("## 提前停止说明")
    lines.append("")
    for absence_rate in ABSENCE_RATES:
        meta = scenario_meta[absence_rate]
        lines.append(
            f"- 缺勤率 {int(absence_rate * 100)}%："
            f"{'已提前停止' if meta['stopped_early'] else '未提前停止'}；"
            f"评估区间 {meta['evaluated_standby_range'][0]}..{meta['evaluated_standby_range'][1]}；"
            f"停止阈值 N_sb={meta['stop_at_standby_workers'] if meta['stop_at_standby_workers'] is not None else '无'}。"
        )
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def plot_curve(rows: list[dict[str, object]], thresholds: dict[float, dict[str, int | None]]) -> None:
    mpl.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Microsoft YaHei", "SimHei", "Arial", "Helvetica"],
            "axes.unicode_minus": False,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "figure.dpi": 300,
            "savefig.dpi": 600,
            "savefig.bbox": "tight",
        }
    )
    color_map = {0.01: "#2F5D8C", 0.03: "#C97832", 0.05: "#B8514A"}
    grouped: dict[float, list[dict[str, object]]] = {}
    for row in rows:
        grouped.setdefault(float(row["absence_rate"]), []).append(row)

    fig, ax = plt.subplots(figsize=(10, 5.6))
    for absence_rate in ABSENCE_RATES:
        items = grouped.get(absence_rate, [])
        xs = [int(item["standby_workers"]) for item in items]
        ys = [float(item["mean_UDR"]) for item in items]
        ax.plot(xs, ys, marker="o", linewidth=2.2, markersize=4.5, color=color_map[absence_rate], label=f"缺勤率 {int(absence_rate * 100)}%")
        hit_1pct = thresholds[absence_rate]["udr_le_1pct"]
        if hit_1pct is not None:
            y_value = next(float(item["mean_UDR"]) for item in items if int(item["standby_workers"]) == hit_1pct)
            ax.annotate(
                f"≤1%: N={hit_1pct}",
                xy=(hit_1pct, y_value),
                xytext=(hit_1pct + 0.5, y_value + 0.003),
                color=color_map[absence_rate],
                fontsize=9,
                arrowprops={"arrowstyle": "->", "color": color_map[absence_rate], "lw": 1.0},
            )
        hit_zero = thresholds[absence_rate]["udr_eq_0"]
        if hit_zero is not None:
            ax.annotate(
                f"=0: N={hit_zero}",
                xy=(hit_zero, 0.0),
                xytext=(hit_zero + 0.5, 0.0015),
                color=color_map[absence_rate],
                fontsize=9,
                arrowprops={"arrowstyle": "->", "color": color_map[absence_rate], "lw": 1.0},
            )

    ax.axhline(0.01, color="#6B7280", linestyle="--", linewidth=1.2, label="UDR = 1%")
    ax.set_title("问题三弹性待命池规模与平均 UDR 曲线")
    ax.set_xlabel("待命池人数 N_sb")
    ax.set_ylabel("平均 UDR")
    ax.yaxis.set_major_formatter(mpl.ticker.PercentFormatter(xmax=1.0, decimals=1))
    ax.grid(True, axis="y", linestyle="--", alpha=0.35)
    ax.legend(frameon=False, ncol=2)
    fig.savefig(OUT_PNG)
    plt.close(fig)


def print_final_summary(
    total_demand: int,
    baseline_workers: int,
    thresholds: dict[float, dict[str, int | None]],
    output_paths: Iterable[Path],
    total_runtime: float,
) -> None:
    print(f"总需求：{total_demand}")
    print(f"基准问题三人数：{baseline_workers}")
    for absence_rate in ABSENCE_RATES:
        one_pct = format_threshold(thresholds[absence_rate]["udr_le_1pct"])
        zero_pct = format_threshold(thresholds[absence_rate]["udr_eq_0"])
        print(f"缺勤率 {int(absence_rate * 100)}%：mean_UDR <= 1% 的最小 N_sb = {one_pct}")
        print(f"缺勤率 {int(absence_rate * 100)}%：mean_UDR = 0 的最小 N_sb = {zero_pct}")
    print("输出文件：")
    for path in output_paths:
        print(f"- {path}")
    print(f"总运行时间：{total_runtime:.3f} 秒")


def main() -> None:
    args = parse_args()
    started = time.perf_counter()
    ensure_dirs()

    input_path = find_input_file(args.input)
    workbook_path, workbook_sheet = find_q3_workbook(args.workbook)
    demand, days, hours, group_cols = model.read_demand(input_path)
    total_demand = int(demand.sum())

    _, shift_cover_same, shift_labels_same = model.build_shift_pairs(min_break=0)
    _, shift_cover_cross, shift_labels_cross = model.build_shift_pairs(min_break=2)
    patterns, pattern_cover = model.build_problem3_patterns(
        demand.shape[1],
        demand.shape[2],
        shift_cover_same,
        shift_labels_same,
        shift_cover_cross,
        shift_labels_cross,
    )

    baseline_assignments, baseline_metrics = load_baseline_assignments(
        workbook_path,
        workbook_sheet,
        patterns,
        pattern_cover,
        demand,
        days,
        hours,
        group_cols,
    )
    contributions = worker_contributions_from_assignments(baseline_assignments, pattern_cover)
    daily_model = DailyRecourseModel(pattern_cover, args.max_standby, args.time_limit)

    advanced_summary = load_summary_json(ROOT / "advanced_summary.json")
    independent_summary = load_summary_json(ROOT / "independent_advanced_summary.json")
    paper_sensitivity = load_summary_json(ROOT / ".codex" / "paper-sensitivity-results.json")

    all_rows: list[dict[str, object]] = []
    scenario_meta: dict[float, dict[str, object]] = {}
    for index, absence_rate in enumerate(ABSENCE_RATES, start=1):
        rows, meta = run_absence_scenario(
            baseline_assignments,
            contributions,
            demand,
            pattern_cover,
            daily_model,
            absence_rate,
            args.runs,
            args.seed + index * 100,
            args.max_standby,
            args.zero_stop_span,
        )
        all_rows.extend(rows)
        scenario_meta[absence_rate] = meta

    df = pd.DataFrame(all_rows)
    df.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
    thresholds = build_threshold_summary(all_rows)
    plot_curve(all_rows, thresholds)

    config = {
        "runs": args.runs,
        "max_standby": args.max_standby,
        "seed": args.seed,
        "time_limit_seconds": args.time_limit,
        "zero_stop_span": args.zero_stop_span,
        "absence_rates": list(ABSENCE_RATES),
        "total_demand": total_demand,
        "baseline_workers_problem3": int(baseline_assignments.shape[0]),
        "baseline_metrics_problem3": to_builtin(baseline_metrics),
        "legal_pattern_count_problem3": int(len(patterns)),
        "days": list(map(int, days)),
        "hours": list(map(str, hours)),
        "groups": list(map(str, group_cols)),
    }

    solver_info = {
        "library": "scipy.optimize.milp",
        "time_limit_seconds": args.time_limit,
        "objective": "min total_deficit + 1e-6 * standby_assignments",
        "day_level_decomposition": "先按天求给定上限 k 的最优缺口函数，再在 Σused_d <= 8*N_sb 且 used_d <= N_sb 下做动态规划组合；该分解与原聚合模型等价",
        "standby_decomposition_validation": "最大流验证每名待命人员最多工作8天且每天最多1次",
    }

    payload = {
        "config": config,
        "input_paths": {
            "demand_file": str(input_path),
            "problem3_workbook": str(workbook_path),
            "problem3_sheet": workbook_sheet,
            "advanced_summary": str(ROOT / "advanced_summary.json"),
            "independent_advanced_summary": str(ROOT / "independent_advanced_summary.json"),
            "paper_sensitivity_results": str(ROOT / ".codex" / "paper-sensitivity-results.json"),
        },
        "baseline_references": {
            "advanced_summary_problem3": to_builtin(advanced_summary.get("summary", [])),
            "independent_summary_problem3": to_builtin(independent_summary.get("summary", [])),
            "paper_sensitivity_problem3": to_builtin(paper_sensitivity.get("基准方案人数", {})),
        },
        "solver_info": solver_info,
        "scenario_meta": to_builtin(scenario_meta),
        "threshold_summary": {
            f"{int(rate * 100)}%": {
                "min_standby_for_mean_udr_le_1pct": thresholds[rate]["udr_le_1pct"],
                "min_standby_for_mean_udr_eq_0": thresholds[rate]["udr_eq_0"],
            }
            for rate in ABSENCE_RATES
        },
        "rows": to_builtin(all_rows),
    }
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(all_rows, config, thresholds, scenario_meta)

    total_runtime = time.perf_counter() - started
    print_final_summary(
        total_demand=total_demand,
        baseline_workers=int(baseline_assignments.shape[0]),
        thresholds=thresholds,
        output_paths=[OUT_CSV, OUT_JSON, OUT_MD, OUT_PNG],
        total_runtime=total_runtime,
    )


if __name__ == "__main__":
    main()
