"""Rank public reference parcels by ML alignment improvement for a classroom demo."""

from __future__ import annotations

import argparse
from pathlib import Path

import geopandas as gpd


def iou(a, b) -> float:
    union = a.union(b).area
    return float(a.intersection(b).area / union) if union else 0.0


def main() -> None:
    parser = argparse.ArgumentParser(description="Rank validated BhuMe demo examples.")
    parser.add_argument("village", type=Path)
    parser.add_argument("predictions", type=Path)
    args = parser.parse_args()
    frames = [
        gpd.read_file(args.predictions),
        gpd.read_file(args.village / "input.geojson"),
        gpd.read_file(args.village / "example_truths.geojson"),
    ]
    for frame in frames:
        frame["plot_number"] = frame["plot_number"].astype(str)
    predicted, official, truth = [frame.set_index("plot_number").to_crs("EPSG:32643") for frame in frames]
    common = sorted(set(predicted.index) & set(official.index) & set(truth.index))
    rows = []
    for plot in common:
        official_iou = iou(official.geometry.loc[plot], truth.geometry.loc[plot])
        prediction_iou = iou(predicted.geometry.loc[plot], truth.geometry.loc[plot])
        centroid_error = predicted.geometry.loc[plot].centroid.distance(truth.geometry.loc[plot].centroid)
        rows.append((prediction_iou - official_iou, plot, official_iou, prediction_iou, centroid_error))
    for improvement, plot, official_iou, prediction_iou, centroid_error in sorted(rows, reverse=True):
        print(
            f"plot={plot}; official_iou={official_iou:.3f}; predicted_iou={prediction_iou:.3f}; "
            f"improvement={improvement:+.3f}; centroid_error_m={centroid_error:.3f}"
        )


if __name__ == "__main__":
    main()
