"""Fast classroom demonstration of satellite-evidence matching for one parcel."""

from __future__ import annotations

import argparse
from pathlib import Path

import geopandas as gpd
import rasterio

from fieldalign.pipeline import _match_one


def main() -> None:
    parser = argparse.ArgumentParser(description="Demonstrate one parcel's image-based alignment.")
    parser.add_argument("village", type=Path, help="Folder containing input.geojson and imagery.tif")
    parser.add_argument("--plot", default="1", help="Plot number to demonstrate (default: 1)")
    args = parser.parse_args()

    plots = gpd.read_file(args.village / "input.geojson")
    plots["plot_number"] = plots["plot_number"].astype(str)
    chosen = plots.loc[plots["plot_number"] == str(args.plot)]
    if chosen.empty:
        raise SystemExit(f"Plot {args.plot!r} was not found.")
    row = chosen.iloc[0]

    hint_path = args.village / "boundaries.tif"
    with rasterio.open(args.village / "imagery.tif") as image:
        result = _match_one(
            image,
            hint_path if hint_path.exists() else None,
            str(row.plot_number),
            row.geometry,
            row.get("map_area_sqm"),
        )

    print(f"Plot: {result.plot_number}")
    print(f"Usable image evidence: {result.usable}")
    print(f"Estimated local correction: east {result.dx:.2f} m, north {result.dy:.2f} m")
    print(f"Total shift: {result.shift:.2f} m")
    print(f"Edge support: {result.original_score:.3f} -> {result.score:.3f}")
    print(f"Peak sharpness (PSR): {result.psr:.2f}")
    print("Interpretation: a correction is accepted later only when this local evidence agrees with")
    print("the robust village model and passes confidence/area safeguards.")


if __name__ == "__main__":
    main()
