# Baseline and improvement evaluation

The public reference implementation is used only as an external benchmark. Its public Nashik
score was median IoU `0.891` from an official baseline of `0.612`.

This project should be evaluated in three reproducible runs on the same village bundle:

| Run | Method | Purpose |
|---|---|---|
| A | Official geometry | Establish the starting IoU and centroid error. |
| B | Global affine drift only | Measure the value of coherent village correction. |
| C | Affine + local residual field + local edge evidence | Measure the contribution of the new method. |

Use public example truths only to report results, never to fit offsets or thresholds. Inspect
high-confidence corrections, low-confidence flags, and parcels beside sharp imagery edges before
submission. Hidden-set performance matters more than a tiny public sample.
