from __future__ import annotations

import json
from pathlib import Path


OUT_DIR = Path(__file__).resolve().parent
ROOT = OUT_DIR.parents[1]


def main() -> None:
    manifest_path = OUT_DIR / "figures-manifest.json"
    index_path = OUT_DIR / "visualization-index.md"
    summary_path = ROOT / "independent_advanced_summary.json"
    sensitivity_path = ROOT / ".codex" / "paper-sensitivity-results.json"

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    index = index_path.read_text(encoding="utf-8")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    sensitivity = json.loads(sensitivity_path.read_text(encoding="utf-8"))

    assert len(manifest) == 9, f"图表数量异常：{len(manifest)}"
    for item in manifest:
        png = Path(item["png"])
        svg = Path(item["svg"])
        assert png.exists(), f"缺少PNG：{png}"
        assert svg.exists(), f"缺少SVG：{svg}"
        assert png.stat().st_size > 50_000, f"PNG文件过小：{png}"
        assert svg.stat().st_size > 5_000, f"SVG文件过小：{svg}"
        assert Path(item["png"]).name in index, f"索引缺少PNG路径：{item['png']}"
        assert Path(item["svg"]).name in index, f"索引缺少SVG路径：{item['svg']}"

    for i in range(1, 10):
        assert f"图{i}" in index, f"索引缺少图{i}"

    items = {row["问题"]: row for row in summary["summary"]}
    assert items["问题1"]["独立求解人数"] == 417
    assert items["问题2"]["理论下界"] == 406
    assert items["问题2"]["独立求解人数"] == 406
    assert items["问题3"]["理论下界"] == 400
    assert items["问题3"]["独立求解人数"] == 400
    assert summary["q3_final_metrics"]["deficit"] == 0
    assert summary["q3_final_metrics"]["min_worker_days"] == 8
    assert summary["q3_final_metrics"]["max_worker_days"] == 8

    demand_rows = {row["场景"]: row for row in sensitivity["需求扰动敏感性"]}
    assert demand_rows["基准"]["问题一精确人数"] == 417
    assert demand_rows["需求上浮5%"]["问题三人数下界"] == 430
    assert demand_rows["需求上浮10%"]["问题二人数下界"] == 452

    print("学术可视化图表包验证通过")
    print(json.dumps({"图表数量": len(manifest), "输出目录": str(OUT_DIR)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
