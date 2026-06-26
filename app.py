"""VibrantAD — AI for Social Connectivity & Vibrant Living in Abu Dhabi."""

from __future__ import annotations

from datetime import datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from streamlit_folium import st_folium

from data_utils import (
    INTERESTS,
    PERSONAS,
    enrich_amenities,
    filter_events_by_interests,
    filter_events_by_time,
    generate_community_pulse,
    generate_events,
    get_intervention_text,
    load_raw_data,
    compute_district_metrics,
    recommend_districts_for_interests,
)
from map_utils import (
    UAE_COLORS,
    create_amenity_layers_map,
    create_client_personalized_map,
    create_district_vibrancy_map,
    create_events_map,
)
from scoring import simulate_investment_uplift

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="VibrantAD | Future Communities Intelligence",
    page_icon="🌴",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom styling ───────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif; }

    .block-container { padding-top: 1.2rem; max-width: 1400px; }

    .hero-banner {
        background: linear-gradient(135deg, #004d26 0%, #1A1A2E 45%, #8B6914 100%);
        padding: 2rem 2.2rem; border-radius: 16px; color: white;
        margin-bottom: 1.2rem; position: relative; overflow: hidden;
    }
    .hero-banner::after {
        content: ''; position: absolute; top: -40%; right: -5%;
        width: 280px; height: 280px; border-radius: 50%;
        background: rgba(197,165,114,0.15);
    }
    .hero-banner h1 { margin: 0; font-size: 2.4rem; font-weight: 700; letter-spacing: -0.5px; }
    .hero-banner .tagline { margin: 0.4rem 0 0; opacity: 0.92; font-size: 1.05rem; }
    .hero-pillars { display: flex; gap: 1rem; margin-top: 1.2rem; flex-wrap: wrap; }
    .hero-pillar {
        background: rgba(255,255,255,0.12); backdrop-filter: blur(4px);
        padding: 0.6rem 1rem; border-radius: 10px; font-size: 0.85rem;
        border: 1px solid rgba(255,255,255,0.18);
    }

    .live-badge {
        display: inline-flex; align-items: center; gap: 6px;
        background: #E8F5E9; color: #00732F; padding: 4px 12px;
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
        background: linear-gradient(145deg, #FFFCF5 0%, #F5F0E6 100%);
        border: 1px solid #E8DFD0; border-radius: 12px;
        padding: 1rem 1.1rem; height: 100%;
    }
    .kpi-tile .label { font-size: 0.78rem; color: #666; text-transform: uppercase; letter-spacing: 0.5px; }
    .kpi-tile .value { font-size: 1.7rem; font-weight: 700; color: #00732F; line-height: 1.2; }
    .kpi-tile .sub { font-size: 0.75rem; color: #8B6914; margin-top: 2px; }

    .community-card {
        background: white; border: 1px solid #E8DFD0; border-radius: 12px;
        padding: 1rem 1.1rem; margin-bottom: 0.6rem;
        transition: box-shadow 0.2s;
    }
    .community-card:hover { box-shadow: 0 4px 16px rgba(0,115,47,0.1); }

    .event-chip {
        display: inline-block; background: #F0F7F2; color: #00732F;
        padding: 3px 10px; border-radius: 14px; font-size: 0.78rem;
        margin: 2px 4px 2px 0; border: 1px solid #C8E6C9;
    }

    .ethical-note {
        background: linear-gradient(90deg, #FFF8E7, #FFFCF5);
        border-left: 4px solid #C5A572; padding: 0.9rem 1.1rem;
        border-radius: 0 10px 10px 0; font-size: 0.9rem;
    }

    .section-label {
        font-size: 0.72rem; text-transform: uppercase; letter-spacing: 1px;
        color: #8B6914; font-weight: 600; margin-bottom: 0.3rem;
    }

    div[data-testid="stMetricValue"] { color: #00732F; font-weight: 700; }
    .stTabs [data-baseweb="tab-list"] { gap: 4px; background: #F5F0E6; padding: 6px; border-radius: 12px; }
    .stTabs [data-baseweb="tab"] { border-radius: 8px; font-weight: 500; }
    .stTabs [aria-selected="true"] { background: white !important; box-shadow: 0 1px 4px rgba(0,0,0,0.08); }

    #MainMenu, footer { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner="Loading Abu Dhabi intelligence data…")
def load_all(seed: int = 42):
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


def render_hero():
    st.markdown(
        """
        <div class="hero-banner">
            <h1>🌴 VibrantAD</h1>
            <p class="tagline">AI for Social Connectivity &amp; Vibrant Living in Abu Dhabi</p>
            <div class="hero-pillars">
                <span class="hero-pillar">🤝 Connected Communities</span>
                <span class="hero-pillar">📍 Live Event Discovery</span>
                <span class="hero-pillar">🏗️ Data-Driven Planning</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_kpi_tiles(metrics: pd.DataFrame, events: pd.DataFrame, pulse: dict):
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


def render_persona_pills():
    """Quick-load demo personas as horizontal buttons."""
    st.markdown('<div class="section-label">One-Click Demo Personas</div>', unsafe_allow_html=True)
    cols = st.columns(len(PERSONAS))
    for col, (name, interests) in zip(cols, PERSONAS.items()):
        with col:
            if st.button(f"👤 {name}", use_container_width=True, key=f"persona_{name}"):
                st.session_state.selected_interests = interests
                st.session_state.interest_multiselect = interests
                st.session_state.active_persona = name
                st.rerun()


def render_event_card(ev: pd.Series, compact: bool = False):
    time_str = ev["start_time"].strftime("%a %d %b · %H:%M")
    spots = ev["spots_available"]
    if compact:
        st.markdown(
            f"""<div class="community-card">
                <span class="event-chip">{ev['interest']}</span>
                <strong>{ev['title']}</strong><br>
                <small style="color:#666;">📍 {ev['district']} · {time_str} · 👥 {spots} joining</small>
            </div>""",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""<div class="community-card">
                <span class="live-badge"><span class="live-dot"></span> Upcoming</span>
                <span class="event-chip">{ev['interest']}</span>
                <h4 style="margin:8px 0 4px;">{ev['title']}</h4>
                <p style="margin:0;color:#555;font-size:0.9rem;">
                📍 {ev['district']} · {ev['amenity_name'][:30]}<br>
                🕐 {time_str} · 👥 {spots} neighbours interested</p>
            </div>""",
            unsafe_allow_html=True,
        )


def copilot_answer(
    question: str,
    metrics: pd.DataFrame,
    events: pd.DataFrame,
    interests: list[str],
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

    if any(w in q for w in ["invest", "opportunity", "gap", "hub"]):
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

    top = metrics.head(3)
    return (
        "I can help with community events, district recommendations, investment opportunities, and vibrancy rankings. "
        f"Currently **{top.iloc[0]['district']}** leads with vibrancy **{top.iloc[0]['vibrancy_score']:.1f}**. "
        "Try: *Show me events for running enthusiasts this week* or *Best districts for families who love sports*."
    )


def export_csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


def main():
    render_hero()

    if "event_seed" not in st.session_state:
        st.session_state.event_seed = 42
    if "selected_interests" not in st.session_state:
        st.session_state.selected_interests = []
    if "active_persona" not in st.session_state:
        st.session_state.active_persona = None

    data = load_all(seed=st.session_state.event_seed)
    metrics = data["district_metrics"]
    amenities = data["amenities"]
    events = data["events"]
    pulse = data["pulse"]

    # ── Sidebar ──────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("### 🇦🇪 Abu Dhabi")
        st.caption("Future Communities · Track 3")

        st.markdown('<div class="live-badge"><span class="live-dot"></span> Community Pulse Live</div>',
                    unsafe_allow_html=True)
        st.metric("Active today", f"{pulse['active_residents_today']:,}")
        st.metric("New connections", f"+{pulse['new_connections_week']}")
        st.caption(f"Hub: **{pulse['top_community_hub']}**")

        st.markdown("---")
        st.markdown('<div class="section-label">Your Profile</div>', unsafe_allow_html=True)

        persona_options = ["Custom"] + list(PERSONAS.keys())
        default_idx = 0
        if st.session_state.active_persona in PERSONAS:
            default_idx = persona_options.index(st.session_state.active_persona)

        persona = st.selectbox("Demo persona", persona_options, index=default_idx, label_visibility="collapsed")
        if persona != "Custom" and persona != st.session_state.active_persona:
            st.session_state.selected_interests = PERSONAS[persona]
            st.session_state.active_persona = persona
            st.session_state.interest_multiselect = PERSONAS[persona]

        if "interest_multiselect" not in st.session_state:
            st.session_state.interest_multiselect = (
                st.session_state.selected_interests or PERSONAS.get(persona, [])
            )

        selected_interests = st.multiselect(
            "Interests & hobbies",
            INTERESTS,
            key="interest_multiselect",
        )
        st.session_state.selected_interests = selected_interests

        time_filter = st.radio("Events", ["Today", "This Week", "All Upcoming"], index=1)

        map_color = st.selectbox(
            "District colour",
            ["vibrancy_score", "community_connectivity_score", "optimization_score"],
            format_func=lambda x: x.replace("_", " ").title(),
        )

        st.markdown("---")
        st.markdown('<div class="section-label">Map Layers</div>', unsafe_allow_html=True)
        show_sports = st.checkbox("⚽ Sports", True)
        show_cultural = st.checkbox("🎭 Cultural", True)
        show_parks = st.checkbox("🌳 Parks", True)

        st.markdown("---")
        audience = st.radio("Viewing as", ["🏠 Resident / Client", "🏗️ Planner / Investor"])

        filtered_events = filter_events_by_time(events, time_filter)
        if selected_interests:
            filtered_events = filter_events_by_interests(filtered_events, selected_interests)

        st.success(f"✓ {len(filtered_events)} events · {len(selected_interests) or 'all'} interests")

    # ── Persona quick buttons ────────────────────────────────────────────────
    render_persona_pills()
    if st.session_state.active_persona:
        chips = " ".join(f'<span class="event-chip">{i}</span>' for i in selected_interests)
        st.markdown(
            f'<div style="margin:0.5rem 0 1rem;">'
            f'<b>{st.session_state.active_persona}</b> profile loaded: {chips}</div>',
            unsafe_allow_html=True,
        )

    # ── Main tabs ────────────────────────────────────────────────────────────
    tab_overview, tab_map, tab_client, tab_investor, tab_explorer, tab_copilot = st.tabs(
        ["📊 Overview", "🗺️ Live Map", "🏠 My Community", "🏗️ Planner Insights", "🔍 Districts", "💬 Copilot"]
    )

    # ── Overview ─────────────────────────────────────────────────────────────
    with tab_overview:
        render_kpi_tiles(metrics, events, pulse)

        st.markdown("")
        col_l, col_r = st.columns(2)
        with col_l:
            st.markdown('<div class="section-label">Vibrancy Leaders</div>', unsafe_allow_html=True)
            top_df = metrics.head(10)[["district", "vibrancy_score", "community_connectivity_score"]]
            fig = px.bar(
                top_df,
                x="vibrancy_score",
                y="district",
                orientation="h",
                color="community_connectivity_score",
                color_continuous_scale=["#C0392B", "#C5A572", "#00732F"],
                labels={"vibrancy_score": "Vibrancy", "district": "", "community_connectivity_score": "Connectivity"},
            )
            fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=400, margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig, use_container_width=True)

        with col_r:
            st.markdown('<div class="section-label">Sports Supply vs Experience</div>', unsafe_allow_html=True)
            fig2 = px.scatter(
                metrics,
                x="sports_density",
                y="resident_experience_score",
                size="sports_amenity_count",
                color="community_connectivity_score",
                hover_name="district",
                color_continuous_scale=["#C0392B", "#C5A572", "#00732F"],
                labels={
                    "sports_density": "Sports Density",
                    "resident_experience_score": "Resident Experience",
                    "community_connectivity_score": "Connectivity",
                },
            )
            fig2.update_layout(height=400, margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig2, use_container_width=True)

        c1, c2 = st.columns(2)
        with c1:
            st.markdown('<div class="section-label">Community Connectivity Index</div>', unsafe_allow_html=True)
            conn_df = metrics.nlargest(12, "community_connectivity_score")[
                ["district", "community_connectivity_score", "mobility_score"]
            ].sort_values("community_connectivity_score")
            fig_conn = px.bar(
                conn_df, x="community_connectivity_score", y="district", orientation="h",
                color="mobility_score", color_continuous_scale=["#1A1A2E", "#00732F"],
                labels={"community_connectivity_score": "Connectivity Score", "district": ""},
            )
            fig_conn.update_layout(height=360, coloraxis_showscale=False, margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig_conn, use_container_width=True)

        with c2:
            st.markdown('<div class="section-label">District Performance Matrix</div>', unsafe_allow_html=True)
            heat_cols = ["vibrancy_score", "community_connectivity_score", "resident_experience_score",
                         "mobility_score", "service_demand_fulfillment"]
            heat = metrics.set_index("district")[heat_cols].head(12)
            fig3 = px.imshow(heat.T, color_continuous_scale=["#1A1A2E", "#C5A572", "#00732F"],
                             aspect="auto", labels=dict(color="Score"))
            fig3.update_layout(height=360, margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig3, use_container_width=True)

        st.download_button("📥 Export District Report", export_csv(metrics),
                           "vibrantad_district_report.csv", "text/csv")

    # ── Interactive Map ──────────────────────────────────────────────────────
    with tab_map:
        hdr_l, hdr_m, hdr_r = st.columns([2, 2, 3])
        with hdr_l:
            st.markdown(
                '<div class="live-badge"><span class="live-dot"></span> Live Events Map</div>',
                unsafe_allow_html=True,
            )
        with hdr_m:
            if st.button("🔄 Refresh Events", type="primary", use_container_width=True):
                st.session_state.event_seed = int(datetime.now().timestamp()) % 100000
                st.cache_data.clear()
                st.rerun()
        with hdr_r:
            st.caption(f"Updated {datetime.now().strftime('%H:%M:%S')} · {len(filtered_events)} events visible")

        view_mode = st.segmented_control(
            "Map view",
            ["District Vibrancy", "Amenity Layers", "Client Events (Live)"],
            default="Client Events (Live)",
        )

        if view_mode == "District Vibrancy":
            fmap = create_district_vibrancy_map(metrics, color_by=map_color)
        elif view_mode == "Amenity Layers":
            fmap = create_amenity_layers_map(
                amenities, metrics,
                show_sports=show_sports, show_cultural=show_cultural,
                show_parks=show_parks, color_by=map_color,
            )
        else:
            fmap = create_events_map(filtered_events, metrics, show_districts=True)

        st_folium(fmap, width=None, height=580, returned_objects=[])

        if view_mode == "Client Events (Live)" and not filtered_events.empty:
            st.markdown('<div class="section-label">Happening Near You</div>', unsafe_allow_html=True)
            ev_cols = st.columns(3)
            for i, (_, ev) in enumerate(filtered_events.head(9).iterrows()):
                with ev_cols[i % 3]:
                    render_event_card(ev, compact=True)

    # ── Client Experience ────────────────────────────────────────────────────
    with tab_client:
        st.markdown("### 🤝 Your Community, Your City")
        st.markdown(
            "Discover **neighbours, events, and vibrant districts** matched to your interests. "
            "VibrantAD connects Abu Dhabi residents to the sports, culture, and community life around them."
        )

        interests_for_rec = selected_interests or INTERESTS[:4]
        rec = recommend_districts_for_interests(
            metrics, filter_events_by_time(events, "This Week"), interests_for_rec
        )
        client_events = filter_events_by_interests(
            filter_events_by_time(events, "This Week"), interests_for_rec
        )

        top_c1, top_c2, top_c3, top_c4 = st.columns(4)
        top_c1.metric("Your interests", len(interests_for_rec))
        top_c2.metric("Matching events", len(client_events))
        top_c3.metric("Recommended areas", len(rec))
        top_c4.metric("Avg connectivity", f"{rec['community_connectivity_score'].mean():.0f}")

        map_col, side_col = st.columns([3, 2])
        with map_col:
            st.markdown('<div class="section-label">Personalised Community Map</div>', unsafe_allow_html=True)
            pmap = create_client_personalized_map(client_events, rec)
            st_folium(pmap, width=None, height=500, returned_objects=[])

        with side_col:
            st.markdown('<div class="section-label">Areas That Might Interest You</div>', unsafe_allow_html=True)
            for _, row in rec.iterrows():
                score = row.get("personalized_score", row["vibrancy_score"])
                conn = row.get("community_connectivity_score", 0)
                st.markdown(
                    f"""<div class="community-card">
                        <strong>{row['district']}</strong>
                        <span class="event-chip">Score {score:.0f}</span>
                        <div style="font-size:0.85rem;color:#555;margin-top:4px;">
                        Connectivity {conn:.0f} · {int(row.get('matching_events', 0))} events this week</div>
                        <div style="font-size:0.8rem;color:#00732F;margin-top:4px;">
                        {row.get('event_highlights', 'Explore local amenities')}</div>
                    </div>""",
                    unsafe_allow_html=True,
                )

            st.markdown('<div class="section-label">This Weekend Near You</div>', unsafe_allow_html=True)
            for _, ev in client_events.head(5).iterrows():
                render_event_card(ev, compact=True)

        st.download_button("📥 Export My Community Guide", export_csv(rec),
                           "vibrantad_my_community.csv", "text/csv")

    # ── Planner & Investor ───────────────────────────────────────────────────
    with tab_investor:
        st.markdown("### 🏗️ Planner & Investor Intelligence")
        st.markdown(
            '<div class="ethical-note">🔒 <b>Ethical data use:</b> Aggregated public OSM amenity data and '
            "anonymised community indicators only — no individual resident data.</div>",
            unsafe_allow_html=True,
        )
        st.markdown("")

        inv1, inv2 = st.columns(2)
        with inv1:
            st.markdown('<div class="section-label">Hub Opportunity Ranking</div>', unsafe_allow_html=True)
            opp = metrics.nlargest(10, "optimization_score")
            fig = px.bar(
                opp, x="optimization_score", y="district", orientation="h",
                color="community_connectivity_score",
                color_continuous_scale=["#00732F", "#C5A572", "#C0392B"],
                labels={"optimization_score": "Opportunity", "district": ""},
            )
            fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=380, coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)

        with inv2:
            st.markdown('<div class="section-label">Demand vs Fulfillment Gap</div>', unsafe_allow_html=True)
            fig = go.Figure()
            fig.add_trace(go.Bar(name="Service Demand", x=metrics["district"],
                                 y=metrics["service_demand_index"], marker_color=UAE_COLORS["gold"]))
            fig.add_trace(go.Bar(name="Amenity Fulfillment", x=metrics["district"],
                                 y=metrics["service_demand_fulfillment"], marker_color=UAE_COLORS["green"]))
            fig.update_layout(barmode="group", height=380, xaxis_tickangle=-45, margin=dict(b=100))
            st.plotly_chart(fig, use_container_width=True)

        st.markdown('<div class="section-label">Investment Simulator</div>', unsafe_allow_html=True)
        sim_col1, sim_col2, sim_col3, sim_col4 = st.columns(4)
        with sim_col1:
            sim_district = st.selectbox("Target district", metrics["district"].tolist())
        with sim_col2:
            sim_facilities = st.slider("Facilities to add", 1, 20, 5)
        with sim_col3:
            sim_type = st.selectbox("Facility type", ["sports", "cultural", "parks", "mixed"])
        with sim_col4:
            st.write("")
            run_sim = st.button("Simulate Impact", type="primary", use_container_width=True)

        if run_sim:
            row = metrics[metrics["district"] == sim_district].iloc[0]
            result = simulate_investment_uplift(row["vibrancy_score"], sim_facilities, sim_type)
            s1, s2, s3 = st.columns(3)
            s1.metric("Current Vibrancy", f"{result['current_vibrancy']}")
            s2.metric("Community Uplift", f"+{result['estimated_uplift']}")
            s3.metric("Projected Score", f"{result['projected_vibrancy']}")
            st.info(
                f"Adding **{sim_facilities} {sim_type}** facilities in **{sim_district}** could "
                f"boost social connectivity and resident vibrancy by an estimated **+{result['estimated_uplift']}** points."
            )

        st.download_button("📥 Export Opportunities", export_csv(metrics.nlargest(20, "optimization_score")),
                           "vibrantad_investment_opportunities.csv", "text/csv")

    # ── District Explorer ────────────────────────────────────────────────────
    with tab_explorer:
        st.markdown('<div class="section-label">Search & Explore Districts</div>', unsafe_allow_html=True)
        search = st.text_input("Search", placeholder="Yas Island, Corniche, Khalifa City…", label_visibility="collapsed")

        display = metrics.copy()
        if search:
            display = display[display["district"].str.contains(search, case=False, na=False)]

        st.dataframe(
            display[[
                "district", "vibrancy_score", "community_connectivity_score",
                "resident_experience_score", "mobility_score",
                "sports_amenity_count", "cultural_amenity_count",
                "amenity_density", "service_demand_fulfillment",
                "optimization_score", "intervention_suggestion",
            ]].rename(columns=lambda c: c.replace("_", " ").title()),
            use_container_width=True, hide_index=True,
        )

        selected = st.selectbox("Deep dive", display["district"].tolist())
        if selected:
            row = metrics[metrics["district"] == selected].iloc[0]
            st.markdown(get_intervention_text(row))

            d1, d2, d3, d4, d5 = st.columns(5)
            d1.metric("Vibrancy", f"{row['vibrancy_score']:.1f}")
            d2.metric("Connectivity", f"{row['community_connectivity_score']:.1f}")
            d3.metric("Sports", int(row["sports_amenity_count"]))
            d4.metric("Cultural", int(row["cultural_amenity_count"]))
            d5.metric("Density", f"{row['amenity_density']:.2f}")

            district_events = events[events["district"] == selected].head(6)
            if not district_events.empty:
                st.markdown('<div class="section-label">Community Events Here</div>', unsafe_allow_html=True)
                ev_cols = st.columns(2)
                for i, (_, ev) in enumerate(district_events.iterrows()):
                    with ev_cols[i % 2]:
                        render_event_card(ev, compact=True)

    # ── Copilot ──────────────────────────────────────────────────────────────
    with tab_copilot:
        st.markdown("### 💬 VibrantAD Community Copilot")
        st.caption("Ask about events, neighbourhoods, families, or investment — in plain language.")

        samples = [
            "Show me events for running enthusiasts this week",
            "Best districts for families who love sports",
            "Which districts have the highest investment opportunity?",
            "Top vibrant communities in Abu Dhabi",
        ]
        sample = st.selectbox("Sample questions", samples, label_visibility="collapsed")
        question = st.text_area("Your question", value=sample, height=72, label_visibility="collapsed")

        if st.button("Ask Copilot", type="primary"):
            with st.chat_message("assistant", avatar="🌴"):
                answer = copilot_answer(question, metrics, events, selected_interests)
                st.markdown(answer)

        with st.expander("How Copilot works"):
            st.write(
                "Keyword routing maps your question to live event data, district scores, and investment gaps. "
                "Connect an LLM API for full conversational AI in production."
            )


if __name__ == "__main__":
    main()
