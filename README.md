# GeoAlign AI

An ML-assisted method for correcting cadastral parcel placement against satellite imagery.
It treats a correction as reliable only when the parcel outline lands on visible field edges,
the local match is unambiguous, and the result agrees with neighbouring parcels through a
village-wide affine drift model.

## Method

1. Build an edge-affinity raster from image gradients, Canny edges, and optional boundary hints.
2. Correlate each parcel outline against a local image patch to obtain a candidate translation.
3. Fit a RANSAC affine village-drift model from high-quality local anchors.
4. Combine the local match with the smooth village model; protect likely already-aligned plots.
5. Train a Random Forest confidence estimator on synthetic parcel shifts, then combine its predicted
   recovery quality with visual and spatial evidence to correct or flag each parcel.

## Run

```powershell
& "..\.venv-validate\Scripts\python.exe" .\main.py "C:\path\to\village"
```

The command writes `predictions.geojson` into the specified village directory. It requires
`input.geojson`, `imagery.tif`, and optionally `boundaries.tif`.
Random Forest confidence training is included in every standard run and does not use public
example truths as labels.

Train and save the model separately when you want a reproducible model artifact without
creating predictions:

```powershell
& "..\.venv-validate\Scripts\python.exe" .\train_ml_model.py "C:\path\to\village" --samples 80
```

Read the complete [technical report](TECHNICAL_REPORT.md) for architecture, AI/ML details,
evaluation, trade-offs, and reproducibility.

For a teacher-ready, three-case proof of output validity, use the prepared
[validation demonstration](VALIDATION_DEMO.md).

## Fast classroom demonstration

Run one parcel through the satellite-edge matcher without waiting for the whole village:

```powershell
& "..\.venv-validate\Scripts\python.exe" .\demo_one_plot.py "C:\path\to\village" --plot 1
```

## Visual output viewer

Open `viewer/index.html` in a browser. Upload a PNG/JPG satellite preview and the generated
`predictions.geojson`; enter the preview's west, south, east, and north coordinates to overlay
the parcels. Click any boundary to see its plot number, correction status, confidence, and method note.

Create the preview from the supplied GeoTIFF with:

```powershell
& "..\.venv-validate\Scripts\python.exe" .\make_preview.py "C:\path\to\village"
```

## Full evaluation

From PowerShell, run the full village and automatically validate the resulting GeoJSON:

```powershell
.\run_full.ps1
```

## Submission notes

- The output covers every input plot and follows the required `corrected` / `flagged` contract.
- Large raster files are ignored by Git; retain them locally for reproducibility or provide them
  separately when requested.
- This implementation was written independently for this project. Public BhuMe repositories were
  examined as references during problem exploration; they are not vendored here. Keep AI-session
  records in `transcripts/` as required by the challenge.
