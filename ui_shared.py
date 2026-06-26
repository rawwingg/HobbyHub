"""Shared UI styles, data loading, and helpers for VibrantAD."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from data_utils import (
    filter_events_by_interests,
    filter_events_by_time,
    generate_community_pulse,
    generate_events,
    enrich_amenities,
    load_raw_data,
    compute_district_metrics,
    recommend_districts_for_interests,
)

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

:root {
    --vibrant-bg: #F7F4EE;
    --vibrant-surface: #FFFFFF;
    --vibrant-surface-alt: #FBF8F1;
    --vibrant-border: #E6DAC7;
    --vibrant-ink: #182033;
    --vibrant-muted: #5D6475;
    --vibrant-green: #0A7A3C;
    --vibrant-gold: #A97D2F;
    --vibrant-shadow: 0 12px 30px rgba(24, 32, 51, 0.08);
}

html, body, [class*="css"], .stApp {
    font-family: 'Plus Jakarta Sans', sans-serif;
    color: var(--vibrant-ink) !important;
    background:
        radial-gradient(circle at top left, rgba(169,125,47,0.10), transparent 28%),
        radial-gradient(circle at top right, rgba(10,122,60,0.08), transparent 24%),
        linear-gradient(180deg, #FCFBF7 0%, var(--vibrant-bg) 100%) !important;
}
.block-container { padding-top: 1.2rem; max-width: 1400px; }
p, li, label, span, div, h1, h2, h3, h4, h5, h6 { color: var(--vibrant-ink); }
h1 { color: #334155 !important; }
.stMarkdown, .stCaption { color: var(--vibrant-muted) !important; }
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #F8F3E8 0%, #F3EEDF 100%) !important;
    border-right: 1px solid var(--vibrant-border);
}
[data-testid="stSidebar"] * { color: var(--vibrant-ink) !important; }

.hero-banner {
    background: linear-gradient(135deg, #083B22 0%, #1A2438 48%, #8B6914 100%);
    padding: 2rem 2.2rem; border-radius: 22px;
    margin-bottom: 1.2rem; position: relative; overflow: hidden;
    box-shadow: var(--vibrant-shadow);
    border: 1px solid rgba(255,255,255,0.12);
}
.hero-banner, .hero-banner h1, .hero-banner p, .hero-banner .tagline { color: #FFFFFF !important; }
.hero-banner::after {
    content: ''; position: absolute; top: -40%; right: -5%;
    width: 280px; height: 280px; border-radius: 50%;
    background: rgba(197,165,114,0.15);
}
.hero-banner h1 { margin: 0; font-size: 2.5rem; font-weight: 800; letter-spacing: -0.7px; }
.hero-banner .tagline { margin: 0.4rem 0 0; opacity: 0.96; font-size: 1.05rem; }
.hero-pillars { display: flex; gap: 1rem; margin-top: 1.2rem; flex-wrap: wrap; }
.hero-pillar {
    background: rgba(255,255,255,0.15); backdrop-filter: blur(4px);
    padding: 0.6rem 1rem; border-radius: 10px; font-size: 0.85rem;
    border: 1px solid rgba(255,255,255,0.25); color: #FFFFFF !important;
}

.role-card {
    background: linear-gradient(180deg, var(--vibrant-surface) 0%, var(--vibrant-surface-alt) 100%);
    border: 1px solid var(--vibrant-border); border-radius: 18px;
    padding: 2rem 1.5rem; text-align: center; height: 100%;
    box-shadow: var(--vibrant-shadow);
}
.role-card .icon { font-size: 3rem; margin-bottom: 0.5rem; }
.role-card h3 { color: var(--vibrant-ink) !important; margin: 0 0 0.5rem; }
.role-card p { color: var(--vibrant-muted) !important; font-size: 0.92rem; margin: 0; line-height: 1.55; }

.live-badge {
    display: inline-flex; align-items: center; gap: 6px;
    background: #E8F5E9; color: #00732F !important; padding: 4px 12px;
    border-radius: 20px; font-size: 0.8rem; font-weight: 600;
}
.live-dot {
    width: 8px; height: 8px; background: #00C853; border-radius: 50%;
    animation: pulse 1.5s ease-in-out infinite;
}
@keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.5; transform: scale(1.3); }
}

.kpi-tile {
    background: linear-gradient(145deg, #FFFCF5 0%, #F4EEE1 100%);
    border: 1px solid var(--vibrant-border); border-radius: 16px;
    padding: 1rem 1.1rem; height: 100%;
    box-shadow: 0 8px 18px rgba(24, 32, 51, 0.06);
}
.kpi-tile .label { font-size: 0.78rem; color: var(--vibrant-muted) !important; text-transform: uppercase; letter-spacing: 0.7px; }
.kpi-tile .value { font-size: 1.75rem; font-weight: 800; color: var(--vibrant-green) !important; line-height: 1.2; }
.kpi-tile .sub { font-size: 0.75rem; color: var(--vibrant-gold) !important; margin-top: 2px; }

.community-card {
    background: linear-gradient(180deg, #FFFFFF 0%, #FBF8F1 100%);
    border: 1px solid var(--vibrant-border); border-radius: 14px;
    padding: 1rem 1.1rem; margin-bottom: 0.75rem; color: var(--vibrant-ink);
    box-shadow: 0 8px 18px rgba(24, 32, 51, 0.05);
}
.community-card strong, .community-card h4 { color: var(--vibrant-ink) !important; }
.surface-copy { color: var(--vibrant-ink) !important; }
.surface-meta { color: var(--vibrant-muted) !important; }
.surface-emphasis { color: var(--vibrant-green) !important; }
.event-chip {
    display: inline-block; background: #F0F7F2; color: var(--vibrant-green) !important;
    padding: 3px 10px; border-radius: 14px; font-size: 0.78rem;
    margin: 2px 4px 2px 0; border: 1px solid #C8E6C9;
}
.ethical-note {
    background: linear-gradient(90deg, #FFF8E7, #FFFCF5);
    border-left: 4px solid #C5A572; padding: 0.9rem 1.1rem;
    border-radius: 0 10px 10px 0; font-size: 0.9rem; color: var(--vibrant-muted) !important;
}
.section-label {
    font-size: 0.74rem; text-transform: uppercase; letter-spacing: 1.2px;
    color: var(--vibrant-gold) !important; font-weight: 700; margin-bottom: 0.45rem;
}
div[data-testid="stMetricValue"] { color: var(--vibrant-green) !important; font-weight: 800; }
div[data-testid="stMetricLabel"] { color: var(--vibrant-muted) !important; }

div[data-testid="stMetric"] {
    background: rgba(255,255,255,0.82);
    border: 1px solid var(--vibrant-border);
    border-radius: 16px;
    padding: 0.9rem 1rem;
    box-shadow: 0 8px 18px rgba(24, 32, 51, 0.04);
}

.stTabs [data-baseweb="tab-list"] { gap: 4px; background: rgba(237, 232, 223, 0.9) !important; padding: 6px; border-radius: 14px; }
.stTabs [data-baseweb="tab"] {
    border-radius: 8px; font-weight: 500;
    color: #444 !important; background: transparent !important;
}
.stTabs [aria-selected="true"] {
    background: #FFFFFF !important; color: #00732F !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08);
}

.feedback-box {
    background: #F8FBF8; border: 1px solid #C8E6C9; border-radius: 12px;
    padding: 1.2rem; color: #1A1A2E;
}

#MainMenu, footer { visibility: hidden; }

.stButton > button,
.stSelectbox > div > div,
.stTextInput > div > div,
.stTextArea > div > div,
.stMultiSelect > div > div,
.stRadio [role="radiogroup"] {
    border-radius: 14px !important;
}

.stButton > button {
    border: 1px solid rgba(10,122,60,0.18) !important;
    box-shadow: 0 10px 20px rgba(10,122,60,0.08);
}

.stButton > button:hover {
    border-color: rgba(10,122,60,0.35) !important;
    box-shadow: 0 12px 24px rgba(10,122,60,0.12);
}

.map-shell {
    background: linear-gradient(180deg, #FFFFFF 0%, #FBF8F1 100%);
    border: 1px solid var(--vibrant-border);
    border-radius: 18px;
    padding: 1rem 1rem 0.75rem;
    box-shadow: var(--vibrant-shadow);
}

.map-shell iframe {
    border-radius: 14px;
}

.map-legend {
    display: inline-flex; align-items: center; gap: 8px;
    background: rgba(255,255,255,0.9); border: 1px solid var(--vibrant-border);
    border-radius: 999px; padding: 0.35rem 0.7rem; margin-top: 0.2rem;
    color: var(--vibrant-muted) !important; font-size: 0.82rem;
}

.legend-swatch {
    width: 12px; height: 12px; border-radius: 999px;
    background: linear-gradient(90deg, #C0392B 0%, #C5A572 50%, #00732F 100%);
    border: 1px solid rgba(0,0,0,0.08);
}
</style>
"""


def inject_styles():
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


@st.cache_data(show_spinner="Loading Abu Dhabi intelligence data…")
def load_all(seed: int = 42) -> dict:
    raw = load_raw_data()
    amenities = enrich_amenities(raw["amenities"], raw["districts"])
    districts = compute_district_metrics(raw["communities"], amenities, raw["districts"])
    events = generate_events(amenities, seed=seed)
    pulse = generate_community_pulse(events, districts, seed=seed)
    return {
        "communities": raw["communities"],
        "amenities": amenities,
        "listings": raw["listings"],
        "districts_ref": raw["districts"],
        "district_metrics": districts,
        "events": events,
        "pulse": pulse,
    }


def init_session_state():
    from feedback_utils import init_feedback_state

    defaults = {
        "user_role": None,
        "event_seed": 42,
        "selected_interests": [],
        "active_persona": None,
        "interest_multiselect": [],
        "feedback_seeded": False,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

    init_feedback_state()


def render_role_header(role: str):
    labels = {
        "resident": ("🏠 Resident & Community Hub", "Discover events, neighbours, and vibrant districts"),
        "planner": ("🏗️ Planner & Investor Intelligence", "City-wide analytics, gaps, and investment simulation"),
    }
    title, subtitle = labels.get(role, ("VibrantAD", ""))
    st.markdown(
        f"""<div class="hero-banner" style="padding:1.2rem 1.8rem;">
            <h1 style="font-size:1.6rem;">{title}</h1>
            <p class="tagline">{subtitle}</p>
        </div>""",
        unsafe_allow_html=True,
    )


def render_kpi_tiles(metrics: pd.DataFrame, events: pd.DataFrame, pulse: dict, mode: str = "all"):
    if mode == "resident":
        tiles = [
            ("Events", str(len(events)), f"{pulse['meetups_today']} today"),
            ("Districts", str(len(metrics)), "across Abu Dhabi"),
            ("Connected", f"{pulse['active_residents_today']:,}", "active today"),
            ("Hub", pulse["top_community_hub"], "top community"),
        ]
    elif mode == "planner":
        tiles = [
            ("Districts", str(len(metrics)), "analysed city-wide"),
            ("Vibrancy", f"{metrics['vibrancy_score'].mean():.1f}", "avg composite score"),
            ("Amenities", f"{metrics['total_amenities'].sum():,.0f}", "OSM sports & culture"),
            ("Opportunity", f"{metrics['optimization_score'].max():.0f}", "peak district score"),
        ]
    else:
        tiles = [
            ("Districts", str(len(metrics)), "analysed city-wide"),
            ("Vibrancy", f"{metrics['vibrancy_score'].mean():.1f}", "avg composite score"),
            ("Amenities", f"{metrics['total_amenities'].sum():,.0f}", "OSM sports & culture"),
            ("Events", str(len(events)), f"{pulse['meetups_today']} today"),
            ("Connected", f"{pulse['active_residents_today']:,}", "residents active today"),
        ]
    cols = st.columns(len(tiles))
    for col, (label, value, sub) in zip(cols, tiles):
        with col:
            st.markdown(
                f"""<div class="kpi-tile">
                    <div class="label">{label}</div>
                    <div class="value">{value}</div>
                    <div class="sub">{sub}</div>
                </div>""",
                unsafe_allow_html=True,
            )


def render_event_card(ev: pd.Series, compact: bool = False):
    time_str = ev["start_time"].strftime("%a %d %b · %H:%M")
    spots = ev["spots_available"]
    if compact:
        st.markdown(
            f"""<div class="community-card">
                <span class="event-chip">{ev['interest']}</span>
                <strong>{ev['title']}</strong><br>
                <small class="surface-meta">📍 {ev['district']} · {time_str} · 👥 {spots} joining</small>
            </div>""",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""<div class="community-card">
                <span class="live-badge"><span class="live-dot"></span> Upcoming</span>
                <span class="event-chip">{ev['interest']}</span>
                <h4 style="margin:8px 0 4px;">{ev['title']}</h4>
                <p class="surface-meta" style="margin:0;font-size:0.9rem;">
                📍 {ev['district']} · {ev['amenity_name'][:30]}<br>
                🕐 {time_str} · 👥 {spots} neighbours interested</p>
            </div>""",
            unsafe_allow_html=True,
        )


def ensure_demo_feedback(events):
    """Seed anonymized demo feedback once for investor dashboards."""
    if not st.session_state.feedback_seeded and not st.session_state.event_feedback:
        from feedback_utils import seed_demo_feedback
        st.session_state.event_feedback = seed_demo_feedback(events, seed=st.session_state.event_seed)
        st.session_state.feedback_seeded = True


def export_csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


def copilot_answer(
    question: str,
    metrics: pd.DataFrame,
    events: pd.DataFrame,
    interests: list[str],
    role: str = "resident",
) -> str:
    q = question.lower()

    if any(w in q for w in ["event", "happening", "weekend", "today", "this week"]):
        time_f = "This Week" if "week" in q or "weekend" in q else "Today" if "today" in q else "All Upcoming"
        filtered = filter_events_by_time(events, time_f)
        if any(w in q for w in ["run", "running", "jog"]):
            filtered = filtered[filtered["interest"] == "Running"]
        elif "yoga" in q:
            filtered = filtered[filtered["interest"] == "Yoga"]
        elif "football" in q or "soccer" in q:
            filtered = filtered[filtered["interest"] == "Football"]
        elif "heritage" in q or "cultural" in q:
            filtered = filtered[filtered["event_type"] == "Cultural"]
        elif interests:
            filtered = filter_events_by_interests(filtered, interests)

        if filtered.empty:
            return f"No events found for **{time_f}** with your filters. Try broadening interests or time range."
        lines = [
            f"- **{r.title}** ({r.interest}) — {r.district}, {r.start_time.strftime('%a %d %b %H:%M')}"
            for r in filtered.head(8).itertuples()
        ]
        return f"**{len(filtered)} community events** ({time_f}):\n" + "\n".join(lines)

    if any(w in q for w in ["family", "sport", "best district", "recommend", "where should", "community"]):
        focus = interests or ["Football", "Family Activities"]
        if "family" in q:
            focus = ["Family Activities", "Swimming", "Football"]
        elif "sport" in q:
            focus = ["Football", "Tennis", "Running", "Swimming"]
        rec = recommend_districts_for_interests(metrics, events, focus, top_n=5)
        lines = [
            f"- **{r.district}** — connectivity {getattr(r, 'community_connectivity_score', r.vibrancy_score):.0f}, "
            f"{int(r.matching_events)} matching events"
            for r in rec.itertuples()
        ]
        return "**Top communities for your profile:**\n" + "\n".join(lines)

    if role == "planner" and any(w in q for w in ["invest", "opportunity", "gap", "hub"]):
        top = metrics.nlargest(5, "optimization_score")
        lines = [
            f"- **{r.district}** — opportunity {r.optimization_score:.1f}, "
            f"demand {r.service_demand_index:.0f}, fulfillment {r.service_demand_fulfillment:.1f}"
            for r in top.itertuples()
        ]
        return "**Highest investment opportunity districts:**\n" + "\n".join(lines)

    if any(w in q for w in ["vibrant", "score", "top", "rank"]):
        top = metrics.head(5)
        lines = [f"- **{r.district}**: {r.vibrancy_score:.1f}/100" for r in top.itertuples()]
        return "**Top districts by Vibrancy Score:**\n" + "\n".join(lines)

    if role == "planner":
        top = metrics.nlargest(3, "optimization_score")
        return (
            "I can help with investment gaps, hub opportunities, and vibrancy rankings. "
            f"**{top.iloc[0]['district']}** has the highest optimization score at "
            f"**{top.iloc[0]['optimization_score']:.1f}**. "
            "Try: *Which districts have the highest investment opportunity?*"
        )

    top = metrics.head(3)
    return (
        "I can help with community events, district recommendations, and vibrant neighbourhoods. "
        f"Currently **{top.iloc[0]['district']}** leads with vibrancy **{top.iloc[0]['vibrancy_score']:.1f}**. "
        "Try: *Show me events for running enthusiasts this week*."
    )
