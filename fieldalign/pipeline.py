"""Satellite-evidence parcel alignment pipeline.

The module intentionally keeps the method compact and inspectable: every movement is a rigid
translation, estimated from local visual evidence and regularised by a robust village-wide drift.
"""

from __future__ import annotations

import argparse
from contextlib import nullcontext
from dataclasses import dataclass
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from pyproj import Transformer
from rasterio.features import rasterize
from rasterio.windows import Window, from_bounds
from scipy.ndimage import gaussian_filter
from scipy.spatial import cKDTree
from shapely.affinity import translate
from shapely import make_valid
from shapely.geometry.base import BaseGeometry
from shapely.ops import transform as transform_geometry
from skimage.feature import canny
from skimage.filters import scharr
from skimage.measure import ransac
from skimage.transform import AffineTransform


@dataclass
class LocalEvidence:
    plot_number: str
    geometry: BaseGeometry
    dx: float
    dy: float
    score: float
    original_score: float
    psr: float
    usable: bool

    @property
    def shift(self) -> float:
        return float(np.hypot(self.dx, self.dy))


@dataclass
class DriftField:
    """Affine village drift plus a clipped, locally interpolated residual field."""

    affine: AffineTransform
    centre: np.ndarray
    anchors: np.ndarray
    residuals: np.ndarray
    residual_limit: float

    def shift(self, x: float, y: float) -> tuple[float, float]:
        point = np.array([[x, y]])
        affine_point = self.affine(point - self.centre)[0] + self.centre
        base = affine_point - point[0]
        if len(self.anchors) < 4:
            return float(base[0]), float(base[1])
        distances, indices = cKDTree(self.anchors).query(point[0], k=min(10, len(self.anchors)))
        distances, indices = np.atleast_1d(distances), np.atleast_1d(indices)
        weights = 1.0 / np.maximum(distances, 15.0) ** 2
        residual = np.average(self.residuals[indices], axis=0, weights=weights)
        magnitude = np.linalg.norm(residual)
        if magnitude > self.residual_limit:
            residual *= self.residual_limit / magnitude
        total = base + residual
        return float(total[0]), float(total[1])


def _utm_crs(geometry: BaseGeometry) -> str:
    zone = int((geometry.centroid.x + 180) // 6) + 1
    return f"EPSG:{32600 + zone if geometry.centroid.y >= 0 else 32700 + zone}"


def _normalise(values: np.ndarray) -> np.ndarray:
    peak = float(np.max(values)) if values.size else 0.0
    return values.astype(np.float32) / peak if peak > 0 else values.astype(np.float32)


def _read_patch(src, bounds, padding_m: float):
    left, bottom, right, top = bounds
    wanted = (left - padding_m, bottom - padding_m, right + padding_m, top + padding_m)
    window = from_bounds(*wanted, transform=src.transform).round_offsets().round_lengths()
    clipped = window.intersection(Window(0, 0, src.width, src.height))
    if clipped.width < 8 or clipped.height < 8:
        return None
    rgb = src.read([1, 2, 3], window=clipped, boundless=True, fill_value=0)
    return np.moveaxis(rgb, 0, -1), src.window_transform(clipped), clipped


def _boundary_patch(source_or_path, bounds, height: int, width: int) -> np.ndarray | None:
    """Read hints from an already-open raster when processing a whole village.

    Reusing one file handle avoids opening `boundaries.tif` thousands of times.
    """
    if source_or_path is None:
        return None
    if hasattr(source_or_path, "read"):
        src = source_or_path
        window = from_bounds(*bounds, transform=src.transform)
        return src.read(1, window=window, out_shape=(height, width), boundless=True, fill_value=0)
    path = Path(source_or_path)
    if not path.exists():
        return None
    with rasterio.open(path) as src:
        window = from_bounds(*bounds, transform=src.transform)
        return src.read(1, window=window, out_shape=(height, width), boundless=True, fill_value=0)


def _edge_affinity(image: np.ndarray, boundary_hint: np.ndarray | None) -> np.ndarray:
    rgb = image.astype(np.float32)
    gray = (0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]) / 255.0
    gradient = _normalise(scharr(gray))
    outline = _normalise(gaussian_filter(canny(gray, sigma=1.6).astype(np.float32), sigma=1.0))
    edge = np.maximum(gradient, outline)
    if boundary_hint is not None and np.any(boundary_hint):
        edge = 0.72 * edge + 0.28 * _normalise(boundary_hint)
    return gaussian_filter(_normalise(edge), sigma=1.0)


def _pixel_geometry(geometry: BaseGeometry, src_crs, transform):
    project = Transformer.from_crs("EPSG:4326", src_crs, always_xy=True)
    inverse = ~transform
    return transform_geometry(
        lambda x, y, z=None: inverse * project.transform(x, y), geometry
    )


def _ring_mask(geometry: BaseGeometry, shape: tuple[int, int]) -> np.ndarray:
    # Rasterising a lightly buffered boundary keeps the template stable for coarse imagery.
    line = geometry.boundary.buffer(1.15, cap_style=2, join_style=2)
    return rasterize([(line, 1)], out_shape=shape, fill=0, default_value=1).astype(np.float32)


def _cross_correlation(edge: np.ndarray, ring: np.ndarray, radius_px: int):
    centred = edge - edge.mean()
    corr = np.fft.fftshift(np.fft.irfft2(np.fft.rfft2(centred) * np.conj(np.fft.rfft2(ring)), s=edge.shape))
    h, w = corr.shape
    cy, cx = h // 2, w // 2
    yy, xx = np.ogrid[:h, :w]
    allowed = (yy - cy) ** 2 + (xx - cx) ** 2 <= radius_px ** 2
    masked = np.where(allowed, corr, -np.inf)
    row, col = np.unravel_index(np.argmax(masked), corr.shape)
    peak = float(corr[row, col])
    sidelobe = allowed & ((yy - row) ** 2 + (xx - col) ** 2 > 16)
    noise = corr[sidelobe]
    psr = (peak - float(noise.mean())) / (float(noise.std()) + 1e-6)
    return row - cy, col - cx, float(psr)


def _match_one(src, hints, plot_number: str, geometry: BaseGeometry, area: float | None) -> LocalEvidence:
    to_image = Transformer.from_crs("EPSG:4326", src.crs, always_xy=True)
    projected = transform_geometry(lambda x, y, z=None: to_image.transform(x, y), geometry)
    search_m = float(np.clip(0.45 * np.sqrt(max(float(area or 0), 1)), 10, 28))
    patch_data = _read_patch(src, projected.bounds, search_m + 14)
    if patch_data is None:
        return LocalEvidence(plot_number, geometry, 0, 0, 0, 0, 0, False)
    image, transform, _ = patch_data
    height, width = image.shape[:2]
    hint = _boundary_patch(hints, rasterio.transform.array_bounds(height, width, transform), height, width)
    edge = _edge_affinity(image, hint)
    pixels = _pixel_geometry(geometry, src.crs, transform)
    ring = _ring_mask(pixels, edge.shape)
    if ring.sum() < 14 or image.std() < 4:
        return LocalEvidence(plot_number, geometry, 0, 0, 0, 0, 0, False)
    original_score = float((edge * ring).sum() / ring.sum())
    resolution = max(abs(transform.a), abs(transform.e))
    radius = int(np.clip(search_m / resolution, 3, min(height, width) // 2 - 2))
    if radius < 3:
        return LocalEvidence(plot_number, geometry, 0, 0, original_score, original_score, 0, False)
    drow, dcol, psr = _cross_correlation(edge, ring, radius)
    moved_ring = np.roll(np.roll(ring, drow, axis=0), dcol, axis=1)
    score = float((edge * moved_ring).sum() / max(moved_ring.sum(), 1))
    dx_img = transform.a * dcol + transform.b * drow
    dy_img = transform.d * dcol + transform.e * drow
    image_to_utm = Transformer.from_crs(src.crs, _utm_crs(geometry), always_xy=True)
    x0, y0 = image_to_utm.transform(projected.centroid.x, projected.centroid.y)
    x1, y1 = image_to_utm.transform(projected.centroid.x + dx_img, projected.centroid.y + dy_img)
    return LocalEvidence(plot_number, geometry, x1 - x0, y1 - y0, score, original_score, psr, True)


def _fit_drift(plots: gpd.GeoDataFrame, evidence: list[LocalEvidence], utm: str):
    anchors = [e for e in evidence if e.usable and e.psr >= 2.6 and e.score > e.original_score]
    if len(anchors) < 8:
        dx = float(np.median([e.dx for e in evidence if e.usable] or [0]))
        dy = float(np.median([e.dy for e in evidence if e.usable] or [0]))
        return DriftField(AffineTransform(translation=(dx, dy)), np.zeros(2), np.empty((0, 2)), np.empty((0, 2)), 0.0)
    metric = plots.to_crs(utm)
    xy = np.array([(metric.loc[e.plot_number].geometry.centroid.x, metric.loc[e.plot_number].geometry.centroid.y) for e in anchors])
    displacement = np.array([(e.dx, e.dy) for e in anchors])
    centre = xy.mean(axis=0)
    source = xy - centre
    target = source + displacement
    model, inliers = ransac((source, target), AffineTransform, min_samples=3, residual_threshold=6, max_trials=1000, rng=7)
    if model is None or inliers is None or inliers.sum() < 5:
        model = AffineTransform(translation=np.median(displacement, axis=0))
        residuals = displacement - (model(source) - source)
        return DriftField(model, centre, xy, residuals, 6.0)
    model = AffineTransform.from_estimate(source[inliers], target[inliers]) or model
    residual = np.linalg.norm(model(source[inliers]) - target[inliers], axis=1)
    local_residuals = displacement[inliers] - (model(source[inliers]) - source[inliers])
    limit = float(np.clip(2.5 * np.median(np.linalg.norm(local_residuals, axis=1)), 2.0, 10.0))
    return DriftField(model, centre, xy[inliers], local_residuals, limit)


def _warp_shift(field: DriftField, geometry: BaseGeometry, utm: str) -> tuple[float, float]:
    tf = Transformer.from_crs("EPSG:4326", utm, always_xy=True)
    x, y = tf.transform(geometry.centroid.x, geometry.centroid.y)
    return field.shift(x, y)


def _area_ratio(row) -> float | None:
    record = row.get("recorded_area_sqm")
    kharaba = row.get("pot_kharaba_ha")
    total = (float(record) if record is not None and np.isfinite(record) else 0.0) + (float(kharaba) * 10000 if kharaba is not None and np.isfinite(kharaba) else 0.0)
    drawn = row.get("map_area_sqm")
    return float(drawn) / total if drawn and total > 0 else None


def align(
    village_dir: Path,
    *,
    limit: int | None = None,
    ml_samples: int = 80,
    model_output: Path | None = None,
) -> gpd.GeoDataFrame:
    plots = gpd.read_file(village_dir / "input.geojson")
    plots["plot_number"] = plots["plot_number"].astype(str)
    plots = plots.set_index("plot_number", drop=False)
    if limit is not None:
        plots = plots.iloc[:limit].copy()
    imagery = village_dir / "imagery.tif"
    hints = village_dir / "boundaries.tif"
    hint_context = rasterio.open(hints) if hints.exists() else nullcontext(None)
    with rasterio.open(imagery) as source, hint_context as hint_source:
        evidence = [_match_one(source, hint_source, str(number), row.geometry, row.get("map_area_sqm")) for number, row in plots.iterrows()]
        # ML confidence is part of the standard pipeline. It learns expected recovery
        # quality from synthetic displacements and never trains on public truth examples.
        from .ml_confidence import train_synthetic_confidence
        confidence_model = train_synthetic_confidence(source, hint_source, plots, sample_size=ml_samples)
        model_path = model_output or village_dir / "ml_confidence_model.joblib"
        confidence_model.save(model_path)
        print(f"trained Random Forest confidence model on {confidence_model.training_rows} synthetic recovery examples: {model_path}")
    utm = _utm_crs(plots.geometry.iloc[0])
    field = _fit_drift(plots, evidence, utm)
    by_plot = {item.plot_number: item for item in evidence}
    records = []
    for number, row in plots.iterrows():
        item = by_plot[str(number)]
        wx, wy = _warp_shift(field, row.geometry, utm)
        agreement = float(np.hypot(item.dx - wx, item.dy - wy)) if item.usable else np.inf
        # A sharp local match can beat the smooth model; otherwise use the model as a conservative prior.
        if item.usable and item.psr >= 3.0:
            dx, dy, method = item.dx, item.dy, "local-edge"
        elif item.usable and item.psr >= 2.4 and agreement <= max(8, 2 * field.residual_limit):
            dx, dy, method = item.dx, item.dy, "local+village"
        else:
            dx, dy, method = wx, wy, "village-prior"
        area = _area_ratio(row)
        improvement = max(item.score - item.original_score, 0.0)
        heuristic_confidence = float(np.clip(0.12 + 0.10 * min(item.psr, 5) + 0.45 * item.score + 0.55 * improvement - 0.025 * min(agreement, 12), 0, 0.95))
        ml_confidence = confidence_model.predict(item, row.get("map_area_sqm"), area)
        confidence = float(0.5 * heuristic_confidence + 0.5 * ml_confidence)
        area_ok = area is None or 0.5 <= area <= 2.0
        is_aligned = item.usable and item.shift <= 3.0 and item.psr >= 2.6
        should_move = item.usable and area_ok and confidence >= 0.34 and np.hypot(dx, dy) <= 35 and not is_aligned
        if should_move:
            metric = gpd.GeoSeries([row.geometry], crs="EPSG:4326").to_crs(utm)
            geometry = translate(metric.iloc[0], xoff=dx, yoff=dy)
            geometry = gpd.GeoSeries([geometry], crs=utm).to_crs("EPSG:4326").iloc[0]
            status, note = "corrected", f"{method}; shift={np.hypot(dx, dy):.1f}m; confidence={confidence:.2f}; ml_iou={ml_confidence:.2f}"
        else:
            geometry, status, confidence = row.geometry, "flagged", None
            note = "flagged: insufficient or conflicting alignment evidence"
        records.append({"plot_number": str(number), "status": status, "confidence": confidence, "method_note": note, "geometry": geometry})
    result = gpd.GeoDataFrame(records, geometry="geometry", crs="EPSG:4326")
    # Preserve the conservative flagged decision while normalising rare invalid
    # source geometries so every exported feature is usable in GIS software.
    invalid = ~result.geometry.is_valid
    if invalid.any():
        result.loc[invalid, "geometry"] = result.loc[invalid, "geometry"].map(make_valid)
        result.loc[invalid, "method_note"] = (
            result.loc[invalid, "method_note"].fillna("flagged")
            + "; normalised invalid source geometry"
        )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Align cadastral plot boundaries to satellite-field edges.")
    parser.add_argument("village", type=Path, help="Village directory containing input.geojson and imagery.tif")
    parser.add_argument("--output", type=Path, help="Optional output path (defaults to <village>/predictions.geojson)")
    parser.add_argument("--limit", type=int, help="Process only the first N plots for a quick development smoke test")
    parser.add_argument("--ml-samples", type=int, default=80, help="Number of parcels used for synthetic ML confidence training")
    parser.add_argument("--model-output", type=Path, help="Where to save the trained Random Forest model")
    args = parser.parse_args()
    target = args.output or args.village / "predictions.geojson"
    model_target = args.model_output or target.with_name("ml_confidence_model.joblib")
    predictions = align(args.village, limit=args.limit, ml_samples=args.ml_samples, model_output=model_target)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(predictions.to_json())
    print(f"wrote {len(predictions)} predictions to {target}")

