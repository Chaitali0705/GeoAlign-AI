# Local village bundles

Place each provided village bundle here before running the project:

```text
data/<village>/
  input.geojson
  imagery.tif
  boundaries.tif            # optional
  example_truths.geojson    # optional, validation only
```

The raster files are intentionally ignored by Git because they are challenge-provided data.
Run `main.py data/<village>` to generate `data/<village>/predictions.geojson`.
