# Three-Case Validation Demo

Use these three prepared examples to show the ML result and its validity in under three minutes. They were selected from the six public hand-aligned reference plots after the ML pipeline ran. The reference truth files were not used to train the Random Forest model.

## What to upload in the viewer

Open viewer/index.html. For one plot at a time, upload the four matching files from data/vadnerbhairav/validation_demo/:

1. Satellite preview — plot_<number>_satellite.png
2. Corrected predictions — plot_<number>_ml_prediction.geojson
3. Official parcel input — plot_<number>_official.geojson
4. Reference truth — plot_<number>_reference_truth.geojson

Then enter that plot's bounds and press **Render parcel overlay**.

The viewer colours are:

- Green: ML-corrected prediction
- Navy blue: original official parcel
- Purple dotted line: independent hand-aligned reference truth

The key visual evidence is simple: the green ML boundary should sit much closer to the purple reference than the navy official input.

## Recommended examples

| Show | Plot | West | East | South | North | Official IoU | ML IoU | Improvement | ML centroid error |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1145 | 74.03222005 | 74.03569619 | 20.24542944 | 20.24793585 | 0.495 | 0.948 | +0.453 | 2.231 m |
| 2 | 2647 | 74.02381937 | 74.02699511 | 20.24915381 | 20.25200240 | 0.414 | 0.805 | +0.391 | 4.614 m |
| 3 | 1710 | 74.01452820 | 74.01773612 | 20.22351422 | 20.22672569 | 0.612 | 0.910 | +0.298 | 2.372 m |

## What to say

### Start

> “The input is an official cadastral boundary that may be misplaced on satellite imagery. The model reads satellite edges, estimates the correction, and assigns an ML-backed confidence score.”

### For each plot

> “Blue is the original official boundary. Green is our ML-enabled prediction. Purple is an independent hand-aligned reference used only for validation. The green boundary is visibly closer to purple than blue.”

For plot 1145:

> “The overlap score improved from 0.495 to 0.948. That is a +0.453 improvement, while the remaining centroid error is only 2.231 metres.”

### Explain the validity

> “Validity is not based only on appearance. We compare the output with reference polygons that were not used as labels during training. Across all six available public references, median IoU improved from 0.584 to 0.884, and all six improved.”

### Explain the ML contribution

> “The Random Forest model is trained on synthetic shifts: we intentionally move known parcel outlines, ask the matcher to recover them, and learn which evidence patterns lead to high IoU. It then estimates recovery quality for real parcels. It does not train on the public reference examples.”

## Important accuracy note

Do not say that every parcel is legally correct. Say:

> “This is a decision-support system. It corrects parcels with sufficient visual and spatial evidence, and flags uncertain cases for human review.”

The full ML run corrected 1,892 of 2,457 parcels and flagged 565 for review. Final output contains zero invalid geometries.
