# GeoAlign AI — Progress Review

**Student project status:** independent improved method has completed a full-village evaluation.

## 1. Problem

Official cadastral plot boundaries can be several metres away from their actual field boundary in
satellite imagery. The project must decide, for each plot, whether to correct its location or flag
it when evidence is not reliable enough.

## 2. Work completed

| Area | Progress | Evidence |
|---|---|---|
| Data pipeline | Complete | Reads GeoJSON plots, satellite GeoTIFF imagery, and optional boundary hints. |
| Baseline research | Complete | Compared three public approaches and selected an edge-based, confidence-aware benchmark. |
| Benchmark validation | Complete | All 15 benchmark unit tests passed; 25/25 sampled imagery matches succeeded. |
| Independent implementation | Complete | `fieldalign/pipeline.py` implements an original local-edge + robust drift-field method and produced all 2,457 village predictions. |
| Output contract | Complete | Produces a GeoJSON prediction for every plot with `corrected` / `flagged`, confidence, and a method note. |
| Final comparative evaluation | Complete | All six public reference plots improved; median IoU is 0.884. |

## 3. Baseline benchmark result (not claimed as my final method)

The evaluated reference benchmark processed the Vadnerbhairav village:

- **2,457** plots total
- **2,178** corrected and **279** flagged
- Public example-truth median IoU improved from **0.612 to 0.891**
- Median centroid error: **2.932 m**
- **6/6** public reference plots improved
- Final checked output had **0 invalid geometries**

This gives a measurable target. Public examples are used only to report accuracy, not to fit the
alignment parameters.

## 4. My improvement over the baseline

The independent method adds a **locally adaptive residual drift field**:

1. Estimate a stable global affine drift using only high-quality local edge matches and RANSAC.
2. Measure the remaining mismatch at reliable anchor plots.
3. Interpolate those residuals from nearby anchors using distance-based weighting.
4. Clip residual movement to prevent a noisy image edge from moving a parcel too far.

Why this matters: a single global transform assumes the entire village shifts uniformly. Historical
paper-map georeferencing can bend locally, so a controlled local adjustment can improve fit while
keeping the global model as a safety prior.

## 5. Verified independent result

The full independent run processed **2,457 plots**: **1,147 corrected** and **1,310 flagged**.
On the six public reference plots, median IoU improved from **0.584** for the official boundaries
to **0.884** for the independent predictions (+**0.300**). The median centroid error was
**2.739 m**, and all six examples improved over their official position. The final export was
validated with **zero invalid geometries**.

## 6. Live demo plan (3–4 minutes)

1. Open `README.md` and explain the task and five-stage method.
2. Open `fieldalign/pipeline.py` and show the local edge matcher plus `DriftField` class.
3. Show this command (do not use example truths as input):

```powershell
cd "C:\Users\Chait\OneDrive\Desktop\aiml el\bhume-field-alignment"
& "..\.venv-validate\Scripts\python.exe" .\main.py `
  "..\repo-lovekumar\data\34855_vadnerbhairav_chandavad_nashik" `
  --output ".\data\vadnerbhairav\predictions.geojson"
```

4. Explain that the output includes every parcel, confidence for each correction, and conservative
flagging when imagery is ambiguous.
5. Show the verified independent evaluation above and then open the visual review webpage.

## 7. Honest current limitations / next steps

- The independent improvement has completed its full-village run. The remaining technical work is
  visual QA of high-confidence corrections, low-confidence flags, and already-aligned controls.
- The public truth set is very small, so it is not appropriate to tune to it.
- Before final submission I will inspect high-confidence corrections, low-confidence flags, and
  already-aligned controls to protect against over-correction.
