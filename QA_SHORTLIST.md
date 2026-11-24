# Visual QA shortlist — GeoAlign AI ML full run

The ML-enabled predictions.geojson is structurally valid: 2,457 rows, 1,892 corrected,
565 flagged, and no invalid geometries. Use the webpage viewer to inspect this shortlist.

## High-confidence corrected plots

These should have clear satellite-edge alignment and are the best examples to show in a demo.

| Plot | Confidence | Decision path | Shift |
|---:|---:|---|---:|
| 1707 | 0.708 | local-edge | 15.0 m |
| 1569 | 0.704 | local-edge | 16.1 m |
| 763 | 0.696 | local-edge | 15.5 m |
| 2051 | 0.692 | local-edge | 15.2 m |
| 1305 | 0.689 | local-edge | 13.6 m |

## Borderline corrected plots

These sit near the confidence threshold and should be reviewed for over-correction.

| Plot | Confidence | Decision path | Shift |
|---:|---:|---|---:|
| 1819 | 0.340 | local-edge | 10.6 m |
| 2768 | 0.340 | local-edge | 11.6 m |
| 1727 | 0.340 | local-edge | 16.2 m |
| 1191 | 0.340 | local-edge | 22.0 m |
| 104 | 0.340 | local-edge | 24.8 m |

## Flagged plots

These show the system’s restraint when evidence is insufficient or conflicting:
`1006`, `1014`, `1025`, `1026`, `1028`.

## Confidence distribution

Among corrected plots, confidence ranges from `0.340` to `0.708`, with a median of `0.449`.
The 90th percentile is `0.563`. The model is therefore conservative: it does not assign near-1.0
confidence simply because it found a possible image edge.
