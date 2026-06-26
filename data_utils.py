"""Data loading, spatial enrichment, and simulated events for VibrantAD."""

from __future__ import annotations

import math
import random
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

from scoring import (
    compute_optimization_score,
    compute_service_demand_fulfillment,
    compute_vibrancy_score,
    normalize_series,
)

DATA_DIR = Path(__file__).resolve().parent / "data"

SPORTS_SUBTYPES = {"playground", "community_centre", "park"}
CULTURAL_SUBTYPES = {
    "place_of_worship",
    "community_centre",
    "university",
    "college",
    "mall",
}
PARK_SUBTYPES = {"park", "playground"}

INTERESTS = [
    "Football",
    "Tennis",
    "Swimming",
    "Yoga",
    "Running",
    "Arts & Crafts",
    "Heritage",
    "Music",
    "Family Activities",
    "Community Meetups",
]

INTEREST_TO_SUBTYPES: dict[str, set[str]] = {
    "Football": {"playground", "park", "community_centre"},
    "Tennis": {"playground", "park", "community_centre"},
    "Swimming": {"community_centre", "park"},
    "Yoga": {"park", "community_centre"},
    "Running": {"park", "playground"},
    "Arts & Crafts": {"community_centre", "mall"},
    "Heritage": {"place_of_worship", "university", "college"},
    "Music": {"community_centre", "mall", "university"},
    "Family Activities": {"playground", "park", "community_centre"},
    "Community Meetups": {"community_centre", "park"},
}

EVENT_TEMPLATES: dict[str, list[str]] = {
    "Football": ["Football Night", "5-a-Side Tournament", "Youth Football Clinic"],
    "Tennis": ["Tennis Social", "Beginner Tennis Hour", "Community Tennis Cup"],
    "Swimming": ["Aqua Fitness", "Family Swim Session", "Lane Swimming Meetup"],
    "Yoga": ["Sunrise Yoga", "Park Yoga Flow", "Mindful Movement Session"],
    "Running": ["Morning Run Club", "5K Community Run", "Sunset Jogging Group"],
    "Arts & Crafts": ["Creative Workshop", "Art in the Park", "Craft & Connect"],
    "Heritage": ["Cultural Heritage Walk", "Emirati Storytelling", "Heritage Craft Demo"],
    "Music": ["Live Acoustic Session", "Community Choir", "Open Mic Night"],
    "Family Activities": ["Family Fun Day", "Kids Activity Hour", "Weekend Family Picnic"],
    "Community Meetups": ["Neighbourhood Meetup", "Community Coffee Chat", "New Residents Welcome"],
}

PERSONAS: dict[str, list[str]] = {
    "Active Family": ["Football", "Swimming", "Family Activities", "Running"],
    "Young Professional": ["Yoga", "Running", "Music", "Community Meetups"],
    "Cultural Enthusiast": ["Heritage", "Arts & Crafts", "Music", "Community Meetups"],
}

OPTIMIZATION_LABELS: dict[str, str] = {
    "expand_retail_offering": "Expand retail & dining to boost walkability",
    "improve_cycle_paths": "Invest in cycling infrastructure & green corridors",
    "add_clinic_capacity": "Add healthcare & wellness facilities",
    "accelerate_transit_link": "Accelerate transit links & last-mile mobility",
    "add_nursery_capacity": "Expand nurseries & family services",
    "add_community_events": "Fund community events & cultural programming",
    "increase_sports_facilities": "Build sports hubs & active recreation",
    "enhance_park_access": "Upgrade parks & public realm quality",
}


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in kilometres."""
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlon / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def assign_nearest_district(
    points: pd.DataFrame,
    districts: pd.DataFrame,
    lat_col: str = "latitude",
    lon_col: str = "longitude",
) -> pd.Series:
    """Assign each point to the nearest district centroid."""
    district_names = districts["district"].tolist()
    centroids = districts[["latitude", "longitude"]].values

    assignments = []
    for _, row in points.iterrows():
        lat, lon = row[lat_col], row[lon_col]
        distances = [
            haversine_km(lat, lon, c[0], c[1]) for c in centroids
        ]
        assignments.append(district_names[int(min(range(len(distances)), key=lambda i: distances[i]))])
    return pd.Series(assignments, index=points.index)


def classify_amenity(row: pd.Series) -> dict[str, bool]:
    """Tag amenity as sports, cultural, or park."""
    subtype = row.get("subtype", "")
    return {
        "is_sports": subtype in SPORTS_SUBTYPES,
        "is_cultural": subtype in CULTURAL_SUBTYPES,
        "is_park": subtype in PARK_SUBTYPES,
    }


def load_raw_data() -> dict[str, pd.DataFrame]:
    """Load all CSV datasets from the data directory."""
    return {
        "communities": pd.read_csv(DATA_DIR / "sample_communities.csv"),
        "amenities": pd.read_csv(DATA_DIR / "osm_amenities.csv"),
        "listings": pd.read_csv(DATA_DIR / "sample_listings.csv"),
        "districts": pd.read_csv(DATA_DIR / "districts.csv"),
    }


def enrich_amenities(amenities: pd.DataFrame, districts: pd.DataFrame) -> pd.DataFrame:
    """Validate / fill district assignments and add classification flags."""
    df = amenities.copy()
    missing = df["district"].isna() | (df["district"].astype(str).str.strip() == "")
    if missing.any():
        df.loc[missing, "district"] = assign_nearest_district(
            df.loc[missing], districts
        )

    flags = df.apply(classify_amenity, axis=1, result_type="expand")
    return pd.concat([df, flags], axis=1)


def aggregate_community_metrics(communities: pd.DataFrame) -> pd.DataFrame:
    """Roll community-level data up to district averages."""
    agg = (
        communities.groupby("district")
        .agg(
            population_estimate=("population_estimate", "sum"),
            avg_occupancy=("occupancy_rate", "mean"),
            service_demand_index=("service_demand_index", "mean"),
            mobility_score=("mobility_score", "mean"),
            resident_experience_score=("resident_experience_score", "mean"),
            community_count=("community_id", "count"),
            top_optimization=("optimization_opportunity", lambda x: x.mode().iloc[0]),
        )
        .reset_index()
    )
    for col in ["service_demand_index", "mobility_score", "resident_experience_score"]:
        agg[col] = agg[col].round(1)
    agg["avg_occupancy"] = agg["avg_occupancy"].round(2)
    return agg


def compute_district_metrics(
    communities: pd.DataFrame,
    amenities: pd.DataFrame,
    districts: pd.DataFrame,
) -> pd.DataFrame:
    """Build enriched district-level dataset with vibrancy metrics."""
    community_agg = aggregate_community_metrics(communities)

    amenity_counts = (
        amenities.groupby("district")
        .agg(
            sports_amenity_count=("is_sports", "sum"),
            cultural_amenity_count=("is_cultural", "sum"),
            park_count=("is_park", "sum"),
            total_amenities=("amenity_id", "count"),
        )
        .reset_index()
    )

    df = districts.merge(community_agg, on="district", how="left")
    df = df.merge(amenity_counts, on="district", how="left")
    df = df.fillna(
        {
            "sports_amenity_count": 0,
            "cultural_amenity_count": 0,
            "park_count": 0,
            "total_amenities": 0,
            "population_estimate": 1,
        }
    )

    df["amenity_density"] = (
        (df["sports_amenity_count"] + df["cultural_amenity_count"] + df["park_count"])
        / df["population_estimate"].clip(lower=1000)
        * 10_000
    ).round(2)

    supply_index = (
        df["sports_amenity_count"] * 1.5
        + df["cultural_amenity_count"] * 2.0
        + df["park_count"] * 0.8
    )

    df["service_demand_fulfillment"] = compute_service_demand_fulfillment(
        df["service_demand_index"],
        supply_index,
    )
    df["optimization_score"] = compute_optimization_score(
        df["service_demand_index"],
        df["service_demand_fulfillment"],
        df["amenity_density"],
    )
    df["vibrancy_score"] = compute_vibrancy_score(
        df["resident_experience_score"],
        df["mobility_score"],
        df["service_demand_fulfillment"],
        df["optimization_score"],
    )
    df["sports_density"] = normalize_series(df["sports_amenity_count"])
    df["community_connectivity_score"] = (
        0.35 * df["service_demand_fulfillment"]
        + 0.35 * df["mobility_score"]
        + 0.30 * normalize_series(df["total_amenities"])
    ).round(1)
    df["intervention_suggestion"] = df["top_optimization"].map(
        lambda x: OPTIMIZATION_LABELS.get(x, str(x).replace("_", " ").title())
    )
    return df.sort_values("vibrancy_score", ascending=False).reset_index(drop=True)


def generate_community_pulse(
    events: pd.DataFrame,
    district_metrics: pd.DataFrame,
    seed: int = 42,
) -> dict:
    """Simulated live community engagement stats for demo storytelling."""
    rng = random.Random(seed)
    week_events = filter_events_by_time(events, "This Week")
    top_district = district_metrics.iloc[0]["district"]
    return {
        "active_residents_today": rng.randint(840, 2100),
        "events_this_week": len(week_events),
        "districts_with_events": int(week_events["district"].nunique()) if not week_events.empty else 0,
        "new_connections_week": rng.randint(120, 480),
        "top_community_hub": top_district,
        "avg_connectivity": round(district_metrics["community_connectivity_score"].mean(), 1),
        "meetups_today": len(filter_events_by_time(events, "Today")),
    }


def generate_events(
    amenities: pd.DataFrame,
    seed: int | None = None,
    n_events: int = 45,
) -> pd.DataFrame:
    """Generate simulated upcoming events tied to sports/cultural amenities."""
    rng = random.Random(seed)
    event_amenities = amenities[
        amenities["is_sports"] | amenities["is_cultural"]
    ].copy()

    if event_amenities.empty:
        return pd.DataFrame(
            columns=[
                "event_id",
                "title",
                "interest",
                "event_type",
                "district",
                "latitude",
                "longitude",
                "amenity_name",
                "amenity_subtype",
                "start_time",
                "end_time",
                "spots_available",
            ]
        )

    sample_size = min(n_events, len(event_amenities))
    chosen = event_amenities.sample(n=sample_size, random_state=seed).reset_index(drop=True)

    now = datetime.now().replace(minute=0, second=0, microsecond=0)
    events = []

    for i, row in chosen.iterrows():
        eligible_interests = [
            interest
            for interest, subtypes in INTEREST_TO_SUBTYPES.items()
            if row["subtype"] in subtypes
        ]
        if not eligible_interests:
            eligible_interests = list(INTEREST_TO_SUBTYPES.keys())

        interest = rng.choice(eligible_interests)
        title = rng.choice(EVENT_TEMPLATES[interest])
        days_ahead = rng.randint(0, 14)
        hour = rng.choice([7, 8, 9, 17, 18, 19, 20])
        start = (now + timedelta(days=days_ahead)).replace(hour=hour, minute=0, second=0, microsecond=0)
        duration = rng.choice([1, 1.5, 2, 3])

        events.append(
            {
                "event_id": f"EVT-{i + 1:04d}",
                "title": title,
                "interest": interest,
                "event_type": "Sports" if interest in {"Football", "Tennis", "Swimming", "Yoga", "Running"} else "Cultural",
                "district": row["district"],
                "latitude": row["latitude"],
                "longitude": row["longitude"],
                "amenity_name": row["name"],
                "amenity_subtype": row["subtype"],
                "start_time": start,
                "end_time": start + timedelta(hours=duration),
                "spots_available": rng.randint(5, 40),
            }
        )

    df = pd.DataFrame(events)
    df["start_time"] = pd.to_datetime(df["start_time"])
    df["end_time"] = pd.to_datetime(df["end_time"])
    return df.sort_values("start_time").reset_index(drop=True)


def filter_events_by_time(events: pd.DataFrame, time_filter: str) -> pd.DataFrame:
    """Filter events by Today / This Week / All Upcoming."""
    if events.empty:
        return events
    now = datetime.now()
    today_end = now.replace(hour=23, minute=59, second=59)
    week_end = now + timedelta(days=7)

    if time_filter == "Today":
        mask = (events["start_time"] >= now.replace(hour=0, minute=0, second=0)) & (
            events["start_time"] <= today_end
        )
    elif time_filter == "This Week":
        mask = (events["start_time"] >= now) & (events["start_time"] <= week_end)
    else:
        mask = events["start_time"] >= now.replace(hour=0, minute=0, second=0)

    return events[mask].copy()


def filter_events_by_interests(
    events: pd.DataFrame,
    interests: list[str],
) -> pd.DataFrame:
    """Filter events matching user interests."""
    if not interests or events.empty:
        return events
    return events[events["interest"].isin(interests)].copy()


def recommend_districts_for_interests(
    district_metrics: pd.DataFrame,
    events: pd.DataFrame,
    interests: list[str],
    top_n: int = 5,
) -> pd.DataFrame:
    """Rank districts by vibrancy and matching upcoming events."""
    if not interests:
        base = district_metrics.nlargest(top_n, "vibrancy_score").copy()
        base["matching_events"] = 0
        base["event_highlights"] = ""
        return base

    matched = events[events["interest"].isin(interests)]
    event_counts = matched.groupby("district").size().rename("matching_events")
    highlights = (
        matched.groupby("district")["title"]
        .apply(lambda x: " · ".join(x.head(3).tolist()))
        .rename("event_highlights")
    )

    scored = district_metrics.copy()
    scored = scored.merge(event_counts, on="district", how="left")
    scored = scored.merge(highlights, on="district", how="left")
    scored["matching_events"] = scored["matching_events"].fillna(0).astype(int)
    scored["event_highlights"] = scored["event_highlights"].fillna("No upcoming matches")
    scored["personalized_score"] = (
        scored["vibrancy_score"] * 0.6 + scored["matching_events"] * 5
    ).round(1)
    return scored.nlargest(top_n, "personalized_score")


def get_intervention_text(row: pd.Series) -> str:
    """Human-readable district insight."""
    return (
        f"**{row['district']}** scores **{row['vibrancy_score']:.1f}/100** on vibrancy. "
        f"Resident experience is {row['resident_experience_score']:.0f}/100 with "
        f"{int(row['sports_amenity_count'])} sports and {int(row['cultural_amenity_count'])} "
        f"cultural amenities. **Suggested intervention:** {row['intervention_suggestion']}."
    )
