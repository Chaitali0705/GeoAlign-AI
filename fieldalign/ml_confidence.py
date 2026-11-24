"""Self-supervised machine-learning confidence scoring for parcel alignment.

The public hand-aligned examples are intentionally excluded from training. Instead, the module
creates known synthetic translations of parcel outlines, attempts to recover them from imagery,
and learns which evidence patterns predict a high recovery IoU.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import geopandas as gpd
import joblib
import numpy as np
from shapely.affinity import translate
from sklearn.ensemble import RandomForestRegressor

from .pipeline import LocalEvidence, _match_one, _utm_crs


def _translate_metric(geometry, dx: float, dy: float, utm: str):
    metric = gpd.GeoSeries([geometry], crs="EPSG:4326").to_crs(utm)
    moved = translate(metric.iloc[0], xoff=dx, yoff=dy)
    return gpd.GeoSeries([moved], crs=utm).to_crs("EPSG:4326").iloc[0]


def _iou(a, b, utm: str) -> float:
    metric = gpd.GeoSeries([a, b], crs="EPSG:4326").to_crs(utm)
    union = metric.iloc[0].union(metric.iloc[1]).area
    return float(metric.iloc[0].intersection(metric.iloc[1]).area / union) if union else 0.0


def evidence_features(evidence: LocalEvidence, area_sqm: float | None, area_ratio: float | None) -> list[float]:
    """Features available both in synthetic training and real inference."""
    area = max(float(area_sqm or 1.0), 1.0)
    ratio = float(area_ratio) if area_ratio is not None and np.isfinite(area_ratio) else 1.0
    return [
        float(evidence.psr),
        float(evidence.score),
        float(max(evidence.score - evidence.original_score, 0.0)),
        float(evidence.shift),
        float(np.log10(area)),
        float(min(ratio, 3.0)),
        float(evidence.usable),
    ]


@dataclass
class MLConfidenceModel:
    model: RandomForestRegressor
    training_rows: int

    def predict(self, evidence: LocalEvidence, area_sqm: float | None, area_ratio: float | None) -> float:
        value = self.model.predict([evidence_features(evidence, area_sqm, area_ratio)])[0]
        return float(np.clip(value, 0.0, 1.0))

    def save(self, path: Path) -> None:
        """Persist the fitted estimator and training metadata for reproducibility."""
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, path)


def train_synthetic_confidence(
    src,
    hints,
    plots: gpd.GeoDataFrame,
    *,
    sample_size: int = 80,
    perturbations_per_plot: int = 4,
    seed: int = 7,
) -> MLConfidenceModel:
    """Train a Random Forest regressor on imagery-based synthetic recovery tasks.

    A sampled official parcel is treated as a pseudo-reference, displaced by a known random metric
    translation, and passed through the same local matcher used at inference. The target is the IoU
    between the matcher-recovered geometry and the pseudo-reference. This makes confidence learning
    possible without fitting to public hand-aligned truth examples.
    """
    candidates = plots.loc[plots.geometry.is_valid & ~plots.geometry.is_empty]
    if candidates.empty:
        raise ValueError("Cannot train ML confidence model without valid parcel geometries")
    rng = np.random.default_rng(seed)
    take = min(sample_size, len(candidates))
    selected = candidates.iloc[rng.choice(len(candidates), size=take, replace=False)]
    X, y = [], []
    for plot_number, row in selected.iterrows():
        reference = row.geometry
        utm = _utm_crs(reference)
        area = row.get("map_area_sqm")
        record = row.get("recorded_area_sqm")
        kharaba = row.get("pot_kharaba_ha")
        total = (float(record) if record is not None and np.isfinite(record) else 0.0) + (float(kharaba) * 10000 if kharaba is not None and np.isfinite(kharaba) else 0.0)
        ratio = float(area) / total if area and total > 0 else None
        radius = float(np.clip(0.45 * np.sqrt(max(float(area or 1), 1)), 10, 28))
        for synthetic_id in range(perturbations_per_plot):
            angle = rng.uniform(0, 2 * np.pi)
            distance = rng.uniform(4.0, radius)
            shifted = _translate_metric(reference, distance * np.cos(angle), distance * np.sin(angle), utm)
            evidence = _match_one(src, hints, f"synthetic-{plot_number}-{synthetic_id}", shifted, area)
            recovered = _translate_metric(shifted, evidence.dx, evidence.dy, utm) if evidence.usable else shifted
            X.append(evidence_features(evidence, area, ratio))
            y.append(_iou(reference, recovered, utm) if evidence.usable else 0.0)
    if len(X) < 12:
        raise ValueError("Synthetic ML training requires at least 12 generated examples")
    model = RandomForestRegressor(
        n_estimators=180,
        min_samples_leaf=max(2, len(X) // 30),
        max_features="sqrt",
        random_state=seed,
        n_jobs=-1,
    )
    model.fit(np.asarray(X, dtype=float), np.asarray(y, dtype=float))
    return MLConfidenceModel(model, len(X))
