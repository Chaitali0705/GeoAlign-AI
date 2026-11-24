"""Create three compact, independently validated parcel-alignment demos."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from PIL import Image
from pyproj import Transformer
from rasterio.windows import Window, from_bounds

PLOTS = ("1145", "2647", "1710")


def iou(a, b) -> float:
    union = a.union(b).area
    return float(a.intersection(b).area / union) if union else 0.0


def to_rgb(data: np.ndarray) -> np.ndarray:
    rgb = np.moveaxis(data, 0, -1)
    if rgb.dtype == np.uint8:
        return rgb
    low, high = np.percentile(rgb, (1, 99))
    return np.clip((rgb - low) * 255 / max(high - low, 1), 0, 255).astype(np.uint8)


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare three validated image-and-GeoJSON classroom demonstrations.")
    parser.add_argument("village", type=Path)
    parser.add_argument("predictions", type=Path)
    parser.add_argument("--output", type=Path, default=Path("data/vadnerbhairav/validation_demo"))
    parser.add_argument("--padding-px", type=int, default=110)
    args = parser.parse_args()

    predicted = gpd.read_file(args.predictions)
    official = gpd.read_file(args.village / "input.geojson")
    truth = gpd.read_file(args.village / "example_truths.geojson")
    for frame in (predicted, official, truth):
        frame["plot_number"] = frame["plot_number"].astype(str)
    predicted_m, official_m, truth_m = [frame.to_crs("EPSG:32643").set_index("plot_number") for frame in (predicted, official, truth)]

    args.output.mkdir(parents=True, exist_ok=True)
    summary = []
    with rasterio.open(args.village / "imagery.tif") as source:
        transformer = Transformer.from_crs(source.crs, "EPSG:4326", always_xy=True)
        for plot in PLOTS:
            if plot not in predicted_m.index or plot not in official_m.index or plot not in truth_m.index:
                raise SystemExit(f"Plot {plot} is missing from one of the three validation layers")
            geom_raster = gpd.GeoSeries(
                [predicted.loc[predicted.plot_number.eq(plot)].geometry.iloc[0],
                 official.loc[official.plot_number.eq(plot)].geometry.iloc[0],
                 truth.loc[truth.plot_number.eq(plot)].geometry.iloc[0]],
                crs="EPSG:4326",
            ).to_crs(source.crs)
            left, bottom, right, top = geom_raster.union_all().bounds
            base = from_bounds(left, bottom, right, top, transform=source.transform)
            window = Window(
                max(0, int(base.col_off) - args.padding_px),
                max(0, int(base.row_off) - args.padding_px),
                min(source.width, int(base.col_off + base.width) + args.padding_px) - max(0, int(base.col_off) - args.padding_px),
                min(source.height, int(base.row_off + base.height) + args.padding_px) - max(0, int(base.row_off) - args.padding_px),
            )
            Image.fromarray(to_rgb(source.read([1, 2, 3], window=window))).save(args.output / f"plot_{plot}_satellite.png")
            bounds = rasterio.windows.bounds(window, source.transform)
            west, south = transformer.transform(bounds[0], bounds[1])
            east, north = transformer.transform(bounds[2], bounds[3])
            for label, frame in (("official", official), ("ml_prediction", predicted), ("reference_truth", truth)):
                frame.loc[frame.plot_number.eq(plot)].to_file(args.output / f"plot_{plot}_{label}.geojson", driver="GeoJSON")
            official_iou = iou(official_m.geometry.loc[plot], truth_m.geometry.loc[plot])
            predicted_iou = iou(predicted_m.geometry.loc[plot], truth_m.geometry.loc[plot])
            summary.append({
                "plot": plot,
                "satellite_preview": f"plot_{plot}_satellite.png",
                "official_input": f"plot_{plot}_official.geojson",
                "ml_prediction": f"plot_{plot}_ml_prediction.geojson",
                "reference_truth": f"plot_{plot}_reference_truth.geojson",
                "bounds_epsg4326": {"west": west, "east": east, "south": south, "north": north},
                "official_iou": round(official_iou, 3),
                "ml_prediction_iou": round(predicted_iou, 3),
                "iou_improvement": round(predicted_iou - official_iou, 3),
                "ml_centroid_error_m": round(predicted_m.geometry.loc[plot].centroid.distance(truth_m.geometry.loc[plot].centroid), 3),
            })
    (args.output / "validation_summary.json").write_text(json.dumps(summary, indent=2))
    print(f"created {len(summary)} validation demo packs in {args.output}")
    for item in summary:
        print(f"plot {item['plot']}: IoU {item['official_iou']:.3f} -> {item['ml_prediction_iou']:.3f} ({item['iou_improvement']:+.3f})")


if __name__ == "__main__":
    main()
