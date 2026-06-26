"""Anonymized event feedback collection and aggregation for VibrantAD."""

from __future__ import annotations

import random
from datetime import datetime

import pandas as pd

WANT_MORE = "More events like this"
WANT_DIFFERENT = "Different types of events"
WANT_VARIETY = "A mix of both"


def init_feedback_state():
    import streamlit as st

    if "event_feedback" not in st.session_state:
        st.session_state.event_feedback = []
    if "attended_events" not in st.session_state:
        st.session_state.attended_events = set()


def seed_demo_feedback(events: pd.DataFrame, seed: int = 42) -> list[dict]:
    """Seed anonymized demo feedback so investor views are populated."""
    rng = random.Random(seed)
    records = []
    sample = events.sample(n=min(28, len(events)), random_state=seed)
    for i, row in sample.iterrows():
        rating = rng.choices([3, 4, 4, 5, 5, 2], weights=[1, 2, 3, 4, 3, 1])[0]
        preference = rng.choices(
            [WANT_MORE, WANT_VARIETY, WANT_DIFFERENT],
            weights=[5, 3, 2],
        )[0]
        records.append(
            {
                "feedback_id": f"FB-DEMO-{len(records)+1:03d}",
                "event_id": row["event_id"],
                "interest": row["interest"],
                "event_type": row["event_type"],
                "district": row["district"],
                "rating": rating,
                "preference": preference,
                "submitted_at": datetime.now().isoformat(),
            }
        )
    return records


def submit_feedback(
    event_row: pd.Series,
    rating: int,
    preference: str,
) -> dict:
    """Record anonymized feedback — no user identity stored."""
    return {
        "feedback_id": f"FB-{datetime.now().strftime('%H%M%S%f')}",
        "event_id": event_row["event_id"],
        "interest": event_row["interest"],
        "event_type": event_row["event_type"],
        "district": event_row["district"],
        "rating": rating,
        "preference": preference,
        "submitted_at": datetime.now().isoformat(),
    }


def feedback_to_dataframe(records: list[dict]) -> pd.DataFrame:
    if not records:
        return pd.DataFrame(
            columns=["feedback_id", "event_id", "interest", "event_type", "district", "rating", "preference"]
        )
    return pd.DataFrame(records)


def aggregate_by_interest(feedback_df: pd.DataFrame) -> pd.DataFrame:
    if feedback_df.empty:
        return pd.DataFrame()
    agg = (
        feedback_df.groupby("interest")
        .agg(
            responses=("rating", "count"),
            avg_rating=("rating", "mean"),
            want_more=("preference", lambda x: (x == WANT_MORE).sum()),
            want_different=("preference", lambda x: (x == WANT_DIFFERENT).sum()),
        )
        .reset_index()
    )
    agg["avg_rating"] = agg["avg_rating"].round(2)
    agg["demand_signal"] = (agg["want_more"] - agg["want_different"]).astype(int)
    return agg.sort_values("demand_signal", ascending=False)


def aggregate_by_district(feedback_df: pd.DataFrame) -> pd.DataFrame:
    if feedback_df.empty:
        return pd.DataFrame()
    agg = (
        feedback_df.groupby("district")
        .agg(
            responses=("rating", "count"),
            avg_rating=("rating", "mean"),
            want_more=("preference", lambda x: (x == WANT_MORE).sum()),
            top_interest=("interest", lambda x: x.mode().iloc[0] if len(x) else ""),
        )
        .reset_index()
    )
    agg["avg_rating"] = agg["avg_rating"].round(2)
    agg["satisfaction_pct"] = (agg["avg_rating"] / 5 * 100).round(1)
    return agg.sort_values("responses", ascending=False)


def aggregate_by_event_type(feedback_df: pd.DataFrame) -> pd.DataFrame:
    if feedback_df.empty:
        return pd.DataFrame()
    return (
        feedback_df.groupby("event_type")
        .agg(responses=("rating", "count"), avg_rating=("rating", "mean"))
        .reset_index()
        .assign(avg_rating=lambda d: d["avg_rating"].round(2))
    )


def build_investment_signals(
    feedback_df: pd.DataFrame,
    district_metrics: pd.DataFrame,
) -> pd.DataFrame:
    """Merge resident feedback demand with planning metrics — fully anonymized."""
    if feedback_df.empty:
        return pd.DataFrame()

    by_district = aggregate_by_district(feedback_df)
    merged = district_metrics.merge(by_district, on="district", how="left")
    merged["responses"] = merged["responses"].fillna(0).astype(int)
    merged["avg_rating"] = merged["avg_rating"].fillna(0)
    merged["want_more"] = merged["want_more"].fillna(0).astype(int)

    merged["feedback_opportunity"] = (
        merged["want_more"] * 8
        + (5 - merged["avg_rating"].clip(0, 5)) * 6
        + merged["optimization_score"] * 0.4
    ).round(1)

    return merged.sort_values("feedback_opportunity", ascending=False)


def investor_recommend(
    question: str,
    feedback_df: pd.DataFrame,
    district_metrics: pd.DataFrame,
    events: pd.DataFrame,
) -> str:
    """AI-style investment recommendations driven by anonymized resident feedback."""
    q = question.lower()
    signals = build_investment_signals(feedback_df, district_metrics)
    by_interest = aggregate_by_interest(feedback_df)
    total = len(feedback_df)

    if total == 0:
        top = district_metrics.nlargest(3, "optimization_score")
        lines = [
            f"- **{r.district}** — optimization {r.optimization_score:.1f}"
            for r in top.itertuples()
        ]
        return (
            "**No resident feedback yet** — recommendations based on supply/demand metrics only:\n"
            + "\n".join(lines)
            + "\n\n_Residents can rate events to unlock demand-driven insights._"
        )

    if any(w in q for w in ["feedback", "resident", "satisfaction", "rating", "attend"]):
        low = signals[signals["avg_rating"] > 0].nsmallest(3, "avg_rating")
        high = signals[signals["avg_rating"] > 0].nlargest(3, "avg_rating")
        lines_low = [
            f"- **{r.district}** — avg {r.avg_rating:.1f}/5 ({int(r.responses)} responses), "
            f"residents want more **{r.top_interest}**"
            for r in low.itertuples()
        ]
        lines_high = [
            f"- **{r.district}** — avg {r.avg_rating:.1f}/5, strong satisfaction"
            for r in high.itertuples()
        ]
        return (
            f"**Anonymized feedback analysis** ({total} responses, no identities):\n\n"
            "**Needs attention:**\n" + ("\n".join(lines_low) if lines_low else "- None flagged")
            + "\n\n**High satisfaction hubs:**\n" + ("\n".join(lines_high) if lines_high else "- Collecting data")
        )

    if any(w in q for w in ["interest", "yoga", "football", "heritage", "sport", "cultural", "music"]):
        if by_interest.empty:
            return "No interest-level feedback available yet."
        top_demand = by_interest.nlargest(5, "demand_signal")
        lines = []
        for r in top_demand.itertuples():
            action = "expand programming" if r.demand_signal > 0 else "introduce variety"
            lines.append(
                f"- **{r.interest}** — {int(r.responses)} ratings, avg {r.avg_rating:.1f}/5, "
                f"{int(r.want_more)} want more → _{action}_"
            )
        underserved = by_interest[by_interest["avg_rating"] < 3.5]
        extra = ""
        if not underserved.empty:
            extra = "\n\n**Underperforming categories:** " + ", ".join(underserved["interest"].tolist())
        return "**Demand signals by interest:**\n" + "\n".join(lines) + extra

    if any(w in q for w in ["invest", "opportunity", "hub", "gap", "where", "build", "facility"]):
        top = signals.head(5)
        lines = []
        for r in top.itertuples():
            if r.responses > 0:
                lines.append(
                    f"- **{r.district}** — feedback opportunity {r.feedback_opportunity:.0f}, "
                    f"{int(r.want_more)} residents want more events, "
                    f"planning score {r.optimization_score:.1f}"
                )
            else:
                lines.append(
                    f"- **{r.district}** — high planning gap (score {r.optimization_score:.1f}), "
                    f"limited feedback so far"
                )
        top_interest = by_interest.iloc[0] if not by_interest.empty else None
        rec_type = top_interest.interest if top_interest is not None else "mixed community"
        return (
            "**AI Investment Recommendations** (feedback + planning data, anonymized):\n\n"
            + "\n".join(lines)
            + f"\n\n**Suggested focus:** Expand **{rec_type}** programming in top-opportunity districts."
        )

    if any(w in q for w in ["vibrant", "score", "top", "rank", "best"]):
        top = district_metrics.head(5)
        lines = [f"- **{r.district}**: vibrancy {r.vibrancy_score:.1f}/100" for r in top.itertuples()]
        avg_sat = feedback_df["rating"].mean() if not feedback_df.empty else 0
        return (
            f"**Top districts by vibrancy** (city avg satisfaction: {avg_sat:.1f}/5 from {total} reviews):\n"
            + "\n".join(lines)
        )

    # Default intelligent summary
    top_sig = signals.head(3)
    top_int = by_interest.head(3) if not by_interest.empty else pd.DataFrame()
    lines = [
        f"- **{r.district}**: {int(r.want_more)} residents want more events, "
        f"opportunity {r.feedback_opportunity:.0f}"
        for r in top_sig.itertuples() if r.responses > 0
    ]
    int_lines = [
        f"- **{r.interest}**: demand signal +{r.demand_signal}, avg {r.avg_rating:.1f}/5"
        for r in top_int.itertuples()
    ] if not top_int.empty else []

    return (
        f"**Intelligent summary** from {total} anonymized resident reviews:\n\n"
        "**Priority districts:**\n" + ("\n".join(lines) if lines else "- Awaiting more feedback")
        + "\n\n**Hot interests:**\n" + ("\n".join(int_lines) if int_lines else "- Awaiting more feedback")
        + "\n\nAsk about *investment opportunities*, *resident satisfaction*, or *which interests to expand*."
    )
