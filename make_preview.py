"""Create a browser-friendly PNG preview from the challenge GeoTIFF imagery."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import rasterio
from PIL import Image
from pyproj import Transformer
from rasterio.enums import Resampling


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert imagery.tif to a PNG preview for the review webpage.")
    parser.add_argument("village", type=Path)
    parser.add_argument("--output", type=Path, default=Path("viewer") / "satellite-preview.png")
    parser.add_argument("--max-size", type=int, default=1600)
    args = parser.parse_args()
    with rasterio.open(args.village / "imagery.tif") as source:
        scale = min(1.0, args.max_size / max(source.width, source.height))
        width, height = max(1, round(source.width * scale)), max(1, round(source.height * scale))
        data = source.read([1, 2, 3], out_shape=(3, height, width), resampling=Resampling.bilinear)
        rgb = np.moveaxis(data, 0, -1)
        if rgb.dtype != np.uint8:
            low, high = np.percentile(rgb, (1, 99))
            rgb = np.clip((rgb - low) * 255 / max(high - low, 1), 0, 255).astype(np.uint8)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        Image.fromarray(rgb).save(args.output)
        transformer = Transformer.from_crs(source.crs, "EPSG:4326", always_xy=True)
        west, south = transformer.transform(source.bounds.left, source.bounds.bottom)
        east, north = transformer.transform(source.bounds.right, source.bounds.top)
    print(f"Saved preview: {args.output.resolve()}")
    print("Copy these into the webpage extent fields:")
    print(f"west={west:.8f}  east={east:.8f}  south={south:.8f}  north={north:.8f}")


if __name__ == "__main__":
    main()
