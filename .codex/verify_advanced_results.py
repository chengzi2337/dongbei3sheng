from pathlib import Path
import json
import pandas as pd

ROOT = Path(r"D:\dongbei3sheng")
json_path = ROOT / "advanced_summary.json"
xlsx_path = ROOT / "高级排班优化结果.xlsx"
conv_path = ROOT / "q3_alns_convergence.csv"

summary = json.loads(json_path.read_text(encoding="utf-8"))
assert all(item["是否一致"] for item in summary["summary"]), "Summary存在不一致结论"
assert summary["summary"][0]["高级方法人数"] == 417, "问题1列生成人数不是417"
assert all(row["integer_slack"] == 0 for row in summary["q1_column_generation"]), "问题1列生成存在人工松弛"
assert sum(row["integer_workers"] for row in summary["q1_column_generation"]) == 417, "问题1列生成各组合计不是417"
assert summary["summary"][1]["高级方法人数"] == 406, "问题2人数不是406"
assert summary["summary"][2]["高级方法人数"] == 400, "问题3人数不是400"
assert summary["q3_final_metrics"]["deficit"] == 0, "问题3存在覆盖缺口"
assert summary["q3_final_metrics"]["worker_day_deviation"] == 0, "问题3工人工作天数偏离8天"
assert summary["q3_final_metrics"]["min_worker_days"] == 8, "问题3存在少于8天的工人"
assert summary["q3_final_metrics"]["max_worker_days"] == 8, "问题3存在多于8天的工人"

book = pd.ExcelFile(xlsx_path)
required = {
    "Summary", "Q1_ExactBaseline", "Q1_ColumnGeneration", "Q2_NetworkFlow", "Q3_ALNS_Daily",
    "Q3_ALNS_Metrics", "Q3_ALNS_Convergence", "Q3_ALNS_Coverage", "Q3_ALNS_WorkerSchedule",
}
missing = required.difference(book.sheet_names)
assert not missing, f"缺少工作表: {missing}"
coverage = pd.read_excel(xlsx_path, sheet_name="Q3_ALNS_Coverage")
assert int(coverage["缺口"].sum()) == 0, "覆盖表存在总缺口"
assert int(coverage["缺口"].max()) == 0, "覆盖表存在小时缺口"
workers = pd.read_excel(xlsx_path, sheet_name="Q3_ALNS_WorkerSchedule")
day_cols = [c for c in workers.columns if str(c).startswith("第")]
work_days = (workers[day_cols] != "休息").sum(axis=1)
assert int(work_days.min()) == 8 and int(work_days.max()) == 8, "输出排班表工作天数不是8天"
conv = pd.read_csv(conv_path)
assert len(conv) >= 10, "ALNS收敛日志过短"
print("验证通过")
print(json.dumps({
    "summary": summary["summary"],
    "q3_final_metrics": summary["q3_final_metrics"],
    "sheets": book.sheet_names,
    "convergence_rows": len(conv),
}, ensure_ascii=False, indent=2))
