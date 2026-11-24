"""Train and save the Random Forest confidence model without exporting predictions."""

from __future__ import annotations

import argparse
from contextlib import nullcontext
from pathlib import Path

import geopandas as gpd
import rasterio

from fieldalign.ml_confidence import train_synthetic_confidence


def main() -> None:
    parser = argparse.ArgumentParser(description="Train BhuMe's synthetic-label Random Forest confidence model.")
    parser.add_argument("village", type=Path, help="Directory containing input.geojson and imagery.tif")
    parser.add_argument("--output", type=Path, default=Path("data/vadnerbhairav/ml_confidence_model.joblib"), help="Destination for the trained model")
    parser.add_argument("--samples", type=int, default=80, help="Number of parcels to sample for synthetic recovery training")
    args = parser.parse_args()

    plots = gpd.read_file(args.village / "input.geojson")
    hints = args.village / "boundaries.tif"
    hint_context = rasterio.open(hints) if hints.exists() else nullcontext(None)
    with rasterio.open(args.village / "imagery.tif") as source, hint_context as hint_source:
        model = train_synthetic_confidence(source, hint_source, plots, sample_size=args.samples)
    model.save(args.output)
    print(f"trained Random Forest model with {model.training_rows} synthetic recovery examples")
    print(f"saved model to {args.output}")


if __name__ == "__main__":
    main()
