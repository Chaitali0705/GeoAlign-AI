# 90-second talk track

“My project corrects land-parcel boundaries that are displaced from the real field boundaries in
satellite imagery. I first established a reproducible benchmark, then designed my own method rather
than submitting the reference approach.

The method creates an edge map from the satellite image and optional field-boundary hints. Each plot
outline is matched against its nearby image region to identify a possible translation. Because local
edges can be noisy, I only trust sharp, improving matches. I fit a robust village-wide affine drift
from those reliable matches using RANSAC.

My improvement is a locally adaptive residual field. It lets the correction vary smoothly across the
village where old-map georeferencing has local distortion, but clips the local residual so one noisy
edge cannot create a large false movement. Each result is either corrected with a confidence score,
or flagged and retained when evidence is weak or area records conflict.

The benchmark currently improves the public examples from 0.612 to 0.891 median IoU. My next step is
to run the independent version over the complete village, compare it fairly against that benchmark,
and visually audit its strongest and weakest predictions.”
