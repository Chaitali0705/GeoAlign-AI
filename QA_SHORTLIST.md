# Visual QA shortlist — independent full run

The full `independent_predictions.geojson` is structurally valid: 2,457 rows, 1,147 corrected,
1,310 flagged, and no invalid geometries. Use the webpage viewer to inspect this shortlist.

## High-confidence corrected plots

These should have clear satellite-edge alignment and are the best examples to show in a demo.

| Plot | Confidence | Decision path | Shift |
|---:|---:|---|---:|
| 1707 | 0.833 | local-edge | 15.0 m |
| 646 | 0.831 | local-edge | 10.0 m |
| 2083 | 0.821 | local-edge | 16.1 m |
| 1403 | 0.820 | local-edge | 15.5 m |
| 1143 | 0.816 | local-edge | 14.6 m |

## Borderline corrected plots

These sit near the confidence threshold and should be reviewed for over-correction.

| Plot | Confidence | Decision path | Shift |
|---:|---:|---|---:|
| 1308 | 0.341 | local-edge | 21.3 m |
| 545 | 0.341 | local+village | 16.7 m |
| 2056 | 0.342 | local-edge | 24.8 m |
| 2219 | 0.342 | local-edge | 23.0 m |
| 1199 | 0.342 | local-edge | 14.2 m |

## Flagged plots

These show the system’s restraint when evidence is insufficient or conflicting:
`1001`, `1003`, `1006`, `1007`, `1009`.

## Confidence distribution

Among corrected plots, confidence ranges from `0.341` to `0.833`, with a median of `0.444`.
The 90th percentile is `0.648`. The model is therefore conservative: it does not assign near-1.0
confidence simply because it found a possible image edge.
