from pathlib import Path
import json
import re
import pandas as pd

ROOT = Path(r"D:\dongbei3sheng")
script_path = ROOT / "independent_advanced_staff_scheduling.py"
summary_path = ROOT / "independent_advanced_summary.json"
xlsx_path = ROOT / "independent_高级排班优化结果.xlsx"
convergence_path = ROOT / "independent_q3_alns_convergence.csv"

source = script_path.read_text(encoding="utf-8")
for forbidden in [
    "large_expo_staff_scheduling_solver",
    "排班优化求解结果",
    "已有结果人数",
]:
    assert forbidden not in source, f"独立脚本含有禁止依赖：{forbidden}"
hardcoded_old_results = re.findall(r"(?<![0-9])(417|406|400)(?![0-9])", source)
assert not hardcoded_old_results, f"独立脚本疑似硬编码旧结果：{hardcoded_old_results}"
summary = json.loads(summary_path.read_text(encoding="utf-8"))
items = {item["问题"]: item for item in summary["summary"]}
assert set(items) == {"问题1", "问题2", "问题3"}, "摘要缺少三问结果"
assert "已有结果人数" not in json.dumps(summary, ensure_ascii=False), "摘要仍含原结果对照字段"
assert items["问题1"]["独立求解人数"] == sum(row["integer_workers"] for row in summary["q1_column_generation"])
assert all(row["integer_slack"] == 0 for row in summary["q1_column_generation"]), "问题一列生成存在人工松弛"
assert items["问题2"]["独立求解人数"] == items["问题2"]["理论下界"], "问题二未达到理论下界"
assert items["问题3"]["独立求解人数"] == items["问题3"]["理论下界"], "问题三未达到理论下界"
assert summary["q3_final_metrics"]["deficit"] == 0, "问题三存在覆盖缺口"
assert summary["q3_final_metrics"]["worker_day_deviation"] == 0, "问题三工人工作天数不是8天"
assert summary["q3_final_metrics"]["min_worker_days"] == 8
assert summary["q3_final_metrics"]["max_worker_days"] == 8

book = pd.ExcelFile(xlsx_path)
required_sheets = {
    "Summary", "Q1_IndependentExact", "Q1_ColumnGeneration", "Q2_NetworkFlow",
    "Q3_ALNS_Daily", "Q3_ALNS_Metrics", "Q3_ALNS_Convergence",
    "Q3_ALNS_Coverage", "Q3_ALNS_WorkerSchedule",
}
assert required_sheets.issubset(set(book.sheet_names)), "独立结果工作簿缺少必要工作表"
coverage = pd.read_excel(xlsx_path, sheet_name="Q3_ALNS_Coverage")
assert int(coverage["缺口"].sum()) == 0, "覆盖明细存在总缺口"
worker_schedule = pd.read_excel(xlsx_path, sheet_name="Q3_ALNS_WorkerSchedule")
day_cols = [col for col in worker_schedule.columns if str(col).startswith("第")]
work_days = (worker_schedule[day_cols] != "休息").sum(axis=1)
assert int(work_days.min()) == 8 and int(work_days.max()) == 8, "逐人工排班工作天数异常"
conv = pd.read_csv(convergence_path)
assert len(conv) >= 10, "ALNS收敛日志不足"
print("独立高级求解验证通过")
print(json.dumps({
    "独立结果": summary["summary"],
    "问题三指标": summary["q3_final_metrics"],
    "工作表": book.sheet_names,
    "收敛日志行数": len(conv),
}, ensure_ascii=False, indent=2))
