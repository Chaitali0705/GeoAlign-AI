# Webpage demonstration

Open `viewer/index.html` in a browser. For tomorrow's demo, use these local files:

| Viewer field | File |
|---|---|
| Satellite preview image | `viewer/satellite-preview.png` |
| Predictions GeoJSON | `data/vadnerbhairav/independent_predictions.geojson` *(full independent 2,457-plot output)* |
| Official input GeoJSON | `../repo-lovekumar/data/34855_vadnerbhairav_chandavad_nashik/input.geojson` |

Enter the following geographic extent values:

```text
West:  73.99351041
East:  74.07453458
South: 20.21899388
North: 20.30635702
```

Then select **Render overlay**. The dashboard shows correction counts and confidence summary.
Click a green or orange parcel to display its plot number, confidence, status, and method note.

Explain that this viewer is a review interface: it makes model decisions inspectable rather than
presenting the prediction file as a black box.

This full output covers all 2,457 plots. It is the correct file to use for the final demonstration,
visual review, and evaluation.
