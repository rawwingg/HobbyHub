"""Vibrancy scoring and investment simulation for VibrantAD."""

from __future__ import annotations

import pandas as pd


def normalize_series(series: pd.Series, invert: bool = False) -> pd.Series:
    """Scale a series to 0–100 across districts."""
    mn, mx = series.min(), series.max()
    if mx == mn:
        scaled = pd.Series(50.0, index=series.index)
    else:
        scaled = (series - mn) / (mx - mn) * 100
    if invert:
        scaled = 100 - scaled
    return scaled.round(1)


def compute_service_demand_fulfillment(
    demand_index: pd.Series,
    supply_index: pd.Series,
) -> pd.Series:
    """
    How well amenity supply meets service demand (0–100).
    Higher when supply aligns with or exceeds normalized demand.
    """
    demand_norm = normalize_series(demand_index)
    supply_norm = normalize_series(supply_index)
    gap = (demand_norm - supply_norm).abs()
    fulfillment = (100 - gap * 0.75).clip(0, 100)
    bonus = (supply_norm - demand_norm).clip(0, None) * 0.15
    return (fulfillment + bonus).clip(0, 100).round(1)


def compute_optimization_score(
    demand_index: pd.Series,
    fulfillment: pd.Series,
    amenity_density: pd.Series,
) -> pd.Series:
    """Investment / planning opportunity score (0–100)."""
    unmet = (100 - fulfillment) * 0.5
    demand_factor = normalize_series(demand_index) * 0.35
    density_gap = normalize_series(amenity_density, invert=True) * 0.15
    return (unmet + demand_factor + density_gap).clip(0, 100).round(1)


def compute_vibrancy_score(
    resident_experience: pd.Series,
    mobility: pd.Series,
    fulfillment: pd.Series,
    optimization: pd.Series,
) -> pd.Series:
    """Composite Vibrancy Score per specification."""
    score = (
        0.35 * resident_experience
        + 0.25 * mobility
        + 0.25 * fulfillment
        + 0.15 * optimization
    )
    return score.round(1)


def simulate_investment_uplift(
    current_vibrancy: float,
    facilities_added: int,
    facility_type: str = "sports",
) -> dict:
    """Estimate vibrancy uplift from adding facilities."""
    weights = {"sports": 1.2, "cultural": 1.0, "parks": 0.8, "mixed": 1.1}
    weight = weights.get(facility_type, 1.0)
    uplift_per = 0.35 * weight
    raw_uplift = facilities_added * uplift_per
    diminishing = raw_uplift * (1 - current_vibrancy / 200)
    new_score = min(100, current_vibrancy + diminishing)
    return {
        "current_vibrancy": round(current_vibrancy, 1),
        "facilities_added": facilities_added,
        "facility_type": facility_type,
        "estimated_uplift": round(new_score - current_vibrancy, 1),
        "projected_vibrancy": round(new_score, 1),
    }


def rank_districts(df: pd.DataFrame, column: str = "vibrancy_score") -> pd.DataFrame:
    """Return districts sorted by score descending."""
    return df.sort_values(column, ascending=False).reset_index(drop=True)
