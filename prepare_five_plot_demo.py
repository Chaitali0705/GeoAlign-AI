"""Create a compact five-parcel viewer demo centred on a validated reference plot."""

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


def to_rgb(data: np.ndarray) -> np.ndarray:
    rgb = np.moveaxis(data, 0, -1)
    if rgb.dtype == np.uint8:
        return rgb
    low, high = np.percentile(rgb, (1, 99))
    return np.clip((rgb - low) * 255 / max(high - low, 1), 0, 255).astype(np.uint8)


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare a five-parcel GeoAlign AI viewer demo.")
    parser.add_argument("village", type=Path)
    parser.add_argument("predictions", type=Path)
    parser.add_argument("--centre-plot", default="1145")
    parser.add_argument("--output", type=Path, default=Path("data/vadnerbhairav/five_plot_demo"))
    parser.add_argument("--padding-px", type=int, default=180)
    args = parser.parse_args()

    predicted = gpd.read_file(args.predictions)
    official = gpd.read_file(args.village / "input.geojson")
    truth = gpd.read_file(args.village / "example_truths.geojson")
    for frame in (predicted, official, truth):
        frame["plot_number"] = frame["plot_number"].astype(str)
    metric = predicted.to_crs("EPSG:32643").copy()
    centre = metric.loc[metric.plot_number.eq(str(args.centre_plot))]
    if centre.empty:
        raise SystemExit(f"Centre plot {args.centre_plot} was not found in the predictions")
    centre_point = centre.geometry.iloc[0].centroid
    metric["distance_to_centre_m"] = metric.geometry.centroid.distance(centre_point)
    selected_ids = metric.nsmallest(5, "distance_to_centre_m")["plot_number"].tolist()
    selected_predictions = predicted.loc[predicted.plot_number.isin(selected_ids)].copy()
    selected_official = official.loc[official.plot_number.isin(selected_ids)].copy()
    selected_truth = truth.loc[truth.plot_number.eq(str(args.centre_plot))].copy()
    args.output.mkdir(parents=True, exist_ok=True)

    with rasterio.open(args.village / "imagery.tif") as source:
        geometries = gpd.GeoSeries(
            list(selected_predictions.geometry) + list(selected_official.geometry) + list(selected_truth.geometry),
            crs="EPSG:4326",
        ).to_crs(source.crs)
        left, bottom, right, top = geometries.union_all().bounds
        raw = from_bounds(left, bottom, right, top, transform=source.transform)
        col = max(0, int(raw.col_off) - args.padding_px)
        row = max(0, int(raw.row_off) - args.padding_px)
        window = Window(
            col,
            row,
            min(source.width, int(raw.col_off + raw.width) + args.padding_px) - col,
            min(source.height, int(raw.row_off + raw.height) + args.padding_px) - row,
        )
        Image.fromarray(to_rgb(source.read([1, 2, 3], window=window))).save(args.output / "five_plot_satellite.png")
        bounds = rasterio.windows.bounds(window, source.transform)
        transformer = Transformer.from_crs(source.crs, "EPSG:4326", always_xy=True)
        west, south = transformer.transform(bounds[0], bounds[1])
        east, north = transformer.transform(bounds[2], bounds[3])

    selected_predictions.to_file(args.output / "five_plot_ml_predictions.geojson", driver="GeoJSON")
    selected_official.to_file(args.output / "five_plot_official_input.geojson", driver="GeoJSON")
    selected_truth.to_file(args.output / "five_plot_reference_truth.geojson", driver="GeoJSON")
    metadata = {
        "centre_plot": str(args.centre_plot),
        "included_plots": selected_ids,
        "bounds_epsg4326": {"west": west, "east": east, "south": south, "north": north},
    }
    (args.output / "five_plot_demo.json").write_text(json.dumps(metadata, indent=2))
    print(f"created five-plot demo centred on {args.centre_plot}")
    print(f"included plots: {', '.join(selected_ids)}")
    print(f"west={west:.8f} east={east:.8f} south={south:.8f} north={north:.8f}")


if __name__ == "__main__":
    main()
