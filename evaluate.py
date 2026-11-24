"""Validate a prediction GeoJSON and score it against optional public example truths."""

from __future__ import annotations

import argparse
from pathlib import Path

import geopandas as gpd
import numpy as np


def iou(a, b) -> float:
    union = a.union(b).area
    return float(a.intersection(b).area / union) if union else 0.0


def main() -> None:
    parser = argparse.ArgumentParser(description="Check BhuMe output and report public-truth metrics.")
    parser.add_argument("village", type=Path)
    parser.add_argument("predictions", type=Path)
    args = parser.parse_args()
    predicted = gpd.read_file(args.predictions)
    required = {"plot_number", "status", "geometry"}
    missing = required - set(predicted.columns)
    if missing:
        raise SystemExit(f"Missing required columns: {sorted(missing)}")
    predicted["plot_number"] = predicted["plot_number"].astype(str)
    corrected = predicted["status"].eq("corrected")
    print(f"Rows: {len(predicted)}")
    print(f"Corrected: {int(corrected.sum())}; flagged: {int((~corrected).sum())}")
    print(f"Invalid geometries: {int((~predicted.geometry.is_valid).sum())}")
    if "confidence" in predicted:
        print(f"Corrected rows missing confidence: {int(predicted.loc[corrected, 'confidence'].isna().sum())}")

    truth_path = args.village / "example_truths.geojson"
    input_path = args.village / "input.geojson"
    if not truth_path.exists():
        return
    truth = gpd.read_file(truth_path)
    official = gpd.read_file(input_path)
    for frame in (truth, official):
        frame["plot_number"] = frame["plot_number"].astype(str)
    common = set(truth.plot_number) & set(predicted.plot_number) & set(official.plot_number)
    if not common:
        print("No public truth plots appear in this prediction file.")
        return
    # Maharashtra is in UTM zone 43N; evaluate areas/distances in metres, not degrees.
    epsg = "EPSG:32643"
    p = predicted.set_index("plot_number").loc[sorted(common)].to_crs(epsg)
    t = truth.set_index("plot_number").loc[sorted(common)].to_crs(epsg)
    o = official.set_index("plot_number").loc[sorted(common)].to_crs(epsg)
    pred_iou = np.array([iou(p.geometry.loc[x], t.geometry.loc[x]) for x in p.index])
    official_iou = np.array([iou(o.geometry.loc[x], t.geometry.loc[x]) for x in p.index])
    centroid_error = np.array([p.geometry.loc[x].centroid.distance(t.geometry.loc[x].centroid) for x in p.index])
    print(f"Public truths scored: {len(p)}")
    print(f"Median IoU: official={np.median(official_iou):.3f}; predicted={np.median(pred_iou):.3f}; improvement={np.median(pred_iou)-np.median(official_iou):+.3f}")
    print(f"Median centroid error: {np.median(centroid_error):.3f} m")
    print(f"Plots improved over official: {np.mean(pred_iou > official_iou):.3f}")


if __name__ == "__main__":
    main()
