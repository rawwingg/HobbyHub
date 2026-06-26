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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .main-header {
        background: linear-gradient(135deg, #00732F 0%, #1A1A2E 60%, #C5A572 100%);
        padding: 1.5rem 2rem; border-radius: 12px; color: white; margin-bottom: 1rem;
    }
    .main-header h1 { margin: 0; font-size: 2rem; }
    .main-header p { margin: 0.3rem 0 0; opacity: 0.9; }
    .kpi-card {
        background: #F5F0E6; border-left: 4px solid #00732F;
        padding: 1rem 1.2rem; border-radius: 8px;
    }
    .persona-btn { margin-bottom: 0.3rem; }
    div[data-testid="stMetricValue"] { color: #00732F; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .ethical-note {
        background: #FFF8E7; border: 1px solid #C5A572;
        padding: 0.8rem 1rem; border-radius: 8px; font-size: 0.9rem;
    }
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
    return {
        "communities": raw["communities"],
        "amenities": amenities,
        "listings": raw["listings"],
        "districts_ref": raw["districts"],
        "district_metrics": districts,
        "events": events,
    }


def render_header():
    st.markdown(
        """
        <div class="main-header">
            <h1>🌴 VibrantAD</h1>
            <p>AI for Social Connectivity &amp; Vibrant Living in Abu Dhabi</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption(
        "Powered by OSM amenity data · Community performance metrics · Simulated live events · "
        "Supporting Abu Dhabi's **Future Communities** vision: connected residents, "
        "data-driven investment, proactive city planning."
    )


def kpi_row(metrics: pd.DataFrame, events: pd.DataFrame):
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Districts Analysed", len(metrics))
    c2.metric("Avg Vibrancy Score", f"{metrics['vibrancy_score'].mean():.1f}")
    c3.metric("OSM Amenities", f"{metrics['total_amenities'].sum():,.0f}")
    c4.metric("Upcoming Events", len(events))
    c5.metric("Top District", metrics.iloc[0]["district"])


def copilot_answer(
    question: str,
    metrics: pd.DataFrame,
    events: pd.DataFrame,
    interests: list[str],
) -> str:
    """Keyword-based copilot — routes natural language to insights."""
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
        return f"**{len(filtered)} events** ({time_f}):\n" + "\n".join(lines)

    if any(w in q for w in ["family", "sport", "best district", "recommend", "where should"]):
        focus = interests or ["Football", "Family Activities"]
        if "family" in q:
            focus = ["Family Activities", "Swimming", "Football"]
        elif "sport" in q:
            focus = ["Football", "Tennis", "Running", "Swimming"]
        rec = recommend_districts_for_interests(metrics, events, focus, top_n=5)
        lines = [
            f"- **{r.district}** — vibrancy {r.vibrancy_score:.1f}, "
            f"{int(r.matching_events)} matching events"
            for r in rec.itertuples()
        ]
        return "**Top districts for your profile:**\n" + "\n".join(lines)

    if any(w in q for w in ["invest", "opportunity", "gap", "hub"]):
        top = metrics.nlargest(5, "optimization_score")
        lines = [
            f"- **{r.district}** — optimization {r.optimization_score:.1f}, "
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
        "I can help with events, district recommendations, investment opportunities, and vibrancy rankings. "
        f"Currently **{top.iloc[0]['district']}** leads with vibrancy **{top.iloc[0]['vibrancy_score']:.1f}**. "
        "Try: *Show me events for running enthusiasts this week* or *Best districts for families who love sports*."
    )


def export_csv(df: pd.DataFrame, filename: str) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


def main():
    render_header()

    # Session state for dynamic events refresh
    if "event_seed" not in st.session_state:
        st.session_state.event_seed = 42

    data = load_all(seed=st.session_state.event_seed)
    metrics = data["district_metrics"]
    amenities = data["amenities"]
    events = data["events"]

    # ── Sidebar ──────────────────────────────────────────────────────────────
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/commons/c/cb/Flag_of_the_United_Arab_Emirates.svg", width=80)
        st.header("Global Filters")
        st.markdown("---")

        st.subheader("👤 Demo Personas")
        persona = st.selectbox("Load persona", ["Custom"] + list(PERSONAS.keys()), label_visibility="collapsed")

        default_interests = PERSONAS.get(persona, [])
        selected_interests = st.multiselect(
            "Your interests",
            INTERESTS,
            default=default_interests,
            help="Used across Client Experience, maps, and Copilot",
        )

        time_filter = st.radio("Event time range", ["Today", "This Week", "All Upcoming"], index=1)

        map_color = st.selectbox(
            "District map colour by",
            ["vibrancy_score", "optimization_score", "service_demand_fulfillment"],
            format_func=lambda x: x.replace("_", " ").title(),
        )

        st.markdown("---")
        st.subheader("Map Layers")
        show_sports = st.checkbox("Sports Amenities", True)
        show_cultural = st.checkbox("Cultural Amenities", True)
        show_parks = st.checkbox("Parks & Playgrounds", True)

        st.markdown("---")
        audience = st.radio(
            "I am a…",
            ["🏠 Resident / Client", "🏗️ Planner / Investor"],
        )

        filtered_events = filter_events_by_interests(
            filter_events_by_time(events, time_filter),
            selected_interests if selected_interests else [],
        )
        if not selected_interests:
            filtered_events = filter_events_by_time(events, time_filter)

        st.success(f"{len(filtered_events)} events match filters")

    # ── Main tabs ────────────────────────────────────────────────────────────
    tab_overview, tab_map, tab_client, tab_investor, tab_explorer, tab_copilot = st.tabs(
        [
            "📊 Overview",
            "🗺️ Interactive Map",
            "🏠 Client Experience",
            "🏗️ Planner & Investor",
            "🔍 District Explorer",
            "💬 Copilot",
        ]
    )

    # ── Overview ─────────────────────────────────────────────────────────────
    with tab_overview:
        kpi_row(metrics, events)
        st.markdown("")

        col_l, col_r = st.columns(2)
        with col_l:
            st.subheader("Top Districts by Vibrancy")
            top_df = metrics.head(10)[["district", "vibrancy_score", "resident_experience_score"]]
            fig = px.bar(
                top_df,
                x="vibrancy_score",
                y="district",
                orientation="h",
                color="vibrancy_score",
                color_continuous_scale=["#C0392B", "#C5A572", "#00732F"],
                labels={"vibrancy_score": "Vibrancy Score", "district": ""},
            )
            fig.update_layout(
                yaxis={"categoryorder": "total ascending"},
                coloraxis_showscale=False,
                height=420,
                margin=dict(l=0, r=0, t=10, b=0),
            )
            st.plotly_chart(fig, use_container_width=True)

        with col_r:
            st.subheader("Sports Density vs Resident Experience")
            fig2 = px.scatter(
                metrics,
                x="sports_density",
                y="resident_experience_score",
                size="sports_amenity_count",
                color="vibrancy_score",
                hover_name="district",
                color_continuous_scale=["#C0392B", "#C5A572", "#00732F"],
                labels={
                    "sports_density": "Sports Amenity Density (norm.)",
                    "resident_experience_score": "Resident Experience Score",
                    "vibrancy_score": "Vibrancy",
                },
            )
            fig2.update_layout(height=420, margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig2, use_container_width=True)

        st.subheader("District Performance Heatmap")
        heat_cols = [
            "vibrancy_score",
            "resident_experience_score",
            "mobility_score",
            "service_demand_fulfillment",
            "optimization_score",
        ]
        heat = metrics.set_index("district")[heat_cols].head(12)
        fig3 = px.imshow(
            heat.T,
            color_continuous_scale=["#1A1A2E", "#C5A572", "#00732F"],
            aspect="auto",
            labels=dict(color="Score"),
        )
        fig3.update_layout(height=320, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig3, use_container_width=True)

        st.download_button(
            "📥 Export District Report (CSV)",
            export_csv(metrics, "vibrantad_districts.csv"),
            "vibrantad_district_report.csv",
            "text/csv",
        )

    # ── Interactive Map ──────────────────────────────────────────────────────
    with tab_map:
        st.subheader("City Intelligence Map — Abu Dhabi")
        map_col1, map_col2, map_col3 = st.columns([1, 1, 2])
        with map_col1:
            if st.button("🔄 Refresh Live Events", type="primary", use_container_width=True):
                st.session_state.event_seed = int(datetime.now().timestamp()) % 100000
                st.cache_data.clear()
                st.rerun()
        with map_col2:
            st.caption(f"Last refreshed: {datetime.now().strftime('%H:%M:%S')} · {len(filtered_events)} events")

        view_mode = st.radio(
            "Map view",
            ["District Vibrancy", "Amenity Layers", "Client Events (Live)"],
            horizontal=True,
        )

        if view_mode == "District Vibrancy":
            fmap = create_district_vibrancy_map(metrics, color_by=map_color)
        elif view_mode == "Amenity Layers":
            fmap = create_amenity_layers_map(
                amenities,
                metrics,
                show_sports=show_sports,
                show_cultural=show_cultural,
                show_parks=show_parks,
                color_by=map_color,
            )
        else:
            fmap = create_events_map(filtered_events, metrics, show_districts=True)

        st_folium(fmap, width=None, height=560, returned_objects=[])

        if view_mode == "Client Events (Live)":
            st.markdown("#### Upcoming Events")
            display_events = filtered_events.head(12)[
                ["title", "interest", "district", "start_time", "spots_available"]
            ].copy()
            display_events["start_time"] = display_events["start_time"].dt.strftime("%a %d %b, %H:%M")
            st.dataframe(display_events, use_container_width=True, hide_index=True)

    # ── Client Experience ────────────────────────────────────────────────────
    with tab_client:
        st.markdown("### 🏠 For Residents & Clients")
        st.info(
            "Discover districts and events tailored to **your interests**. "
            "VibrantAD connects you to sports, culture, and community life across Abu Dhabi."
        )

        rec = recommend_districts_for_interests(
            metrics, filter_events_by_time(events, "This Week"), selected_interests or INTERESTS[:3]
        )

        c1, c2 = st.columns([3, 2])
        with c1:
            client_events = filter_events_by_interests(
                filter_events_by_time(events, "This Week"),
                selected_interests if selected_interests else INTERESTS,
            )
            pmap = create_client_personalized_map(client_events, rec)
            st_folium(pmap, width=None, height=480, returned_objects=[])

        with c2:
            st.subheader("Areas That Might Interest You")
            for _, row in rec.iterrows():
                with st.container(border=True):
                    st.markdown(f"**{row['district']}** · Score {row.get('personalized_score', row['vibrancy_score']):.1f}")
                    st.caption(
                        f"Vibrancy {row['vibrancy_score']:.1f} · "
                        f"{int(row.get('matching_events', 0))} events this week"
                    )
                    st.write(row.get("event_highlights", "Explore local amenities"))

            st.subheader("Events Near You This Weekend")
            weekend = filter_events_by_time(events, "This Week")
            if selected_interests:
                weekend = filter_events_by_interests(weekend, selected_interests)
            for _, ev in weekend.head(6).iterrows():
                st.markdown(
                    f"**{ev['title']}** — _{ev['interest']}_  \n"
                    f"{ev['district']} · {ev['start_time'].strftime('%a %d %b, %H:%M')} · "
                    f"{ev['spots_available']} spots"
                )

        st.download_button(
            "📥 Export My Recommendations",
            export_csv(rec, "recommendations.csv"),
            "vibrantad_my_areas.csv",
            "text/csv",
        )

    # ── Planner & Investor ───────────────────────────────────────────────────
    with tab_investor:
        st.markdown("### 🏗️ For Planners & Investors")
        st.markdown(
            '<div class="ethical-note">🔒 <b>Ethical data use:</b> All insights are derived from '
            "aggregated public OSM amenity data and anonymised community performance indicators. "
            "No individual resident data is processed.</div>",
            unsafe_allow_html=True,
        )

        inv1, inv2 = st.columns(2)
        with inv1:
            st.subheader("Opportunity Ranking — New Community Hubs")
            opp = metrics.nlargest(10, "optimization_score")[
                [
                    "district",
                    "optimization_score",
                    "service_demand_index",
                    "service_demand_fulfillment",
                    "sports_amenity_count",
                    "cultural_amenity_count",
                ]
            ]
            fig = px.bar(
                opp,
                x="optimization_score",
                y="district",
                orientation="h",
                color="optimization_score",
                color_continuous_scale=["#00732F", "#C5A572", "#C0392B"],
            )
            fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=400, coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)

        with inv2:
            st.subheader("Gap Analysis — Demand vs Fulfillment")
            fig = go.Figure()
            fig.add_trace(
                go.Bar(
                    name="Service Demand",
                    x=metrics["district"],
                    y=metrics["service_demand_index"],
                    marker_color=UAE_COLORS["gold"],
                )
            )
            fig.add_trace(
                go.Bar(
                    name="Amenity Fulfillment",
                    x=metrics["district"],
                    y=metrics["service_demand_fulfillment"],
                    marker_color=UAE_COLORS["green"],
                )
            )
            fig.update_layout(barmode="group", height=400, xaxis_tickangle=-45, margin=dict(b=100))
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("Investment Simulator")
        sim_col1, sim_col2, sim_col3, sim_col4 = st.columns(4)
        with sim_col1:
            sim_district = st.selectbox("Target district", metrics["district"].tolist())
        with sim_col2:
            sim_facilities = st.slider("Facilities to add", 1, 20, 5)
        with sim_col3:
            sim_type = st.selectbox("Facility type", ["sports", "cultural", "parks", "mixed"])
        with sim_col4:
            st.write("")
            run_sim = st.button("Run Simulation", type="primary")

        if run_sim:
            row = metrics[metrics["district"] == sim_district].iloc[0]
            result = simulate_investment_uplift(row["vibrancy_score"], sim_facilities, sim_type)
            s1, s2, s3 = st.columns(3)
            s1.metric("Current Vibrancy", f"{result['current_vibrancy']}")
            s2.metric("Estimated Uplift", f"+{result['estimated_uplift']}")
            s3.metric("Projected Vibrancy", f"{result['projected_vibrancy']}")

        st.download_button(
            "📥 Export Investment Opportunities",
            export_csv(metrics.nlargest(20, "optimization_score"), "opportunities.csv"),
            "vibrantad_investment_opportunities.csv",
            "text/csv",
        )

    # ── District Explorer ────────────────────────────────────────────────────
    with tab_explorer:
        st.subheader("District Explorer")
        search = st.text_input("Search districts", placeholder="e.g. Yas Island, Corniche…")

        display = metrics.copy()
        if search:
            display = display[display["district"].str.contains(search, case=False, na=False)]

        st.dataframe(
            display[
                [
                    "district",
                    "vibrancy_score",
                    "resident_experience_score",
                    "mobility_score",
                    "sports_amenity_count",
                    "cultural_amenity_count",
                    "amenity_density",
                    "service_demand_fulfillment",
                    "optimization_score",
                    "intervention_suggestion",
                ]
            ].rename(columns=lambda c: c.replace("_", " ").title()),
            use_container_width=True,
            hide_index=True,
        )

        selected = st.selectbox("Detailed district view", display["district"].tolist())
        if selected:
            row = metrics[metrics["district"] == selected].iloc[0]
            st.markdown(get_intervention_text(row))
            d1, d2, d3, d4 = st.columns(4)
            d1.metric("Vibrancy", f"{row['vibrancy_score']:.1f}")
            d2.metric("Sports Amenities", int(row["sports_amenity_count"]))
            d3.metric("Cultural Amenities", int(row["cultural_amenity_count"]))
            d4.metric("Amenity Density", f"{row['amenity_density']:.2f}")

            district_events = events[events["district"] == selected].head(5)
            if not district_events.empty:
                st.markdown("**Upcoming events in this district:**")
                for _, ev in district_events.iterrows():
                    st.write(f"- {ev['title']} ({ev['interest']}) — {ev['start_time'].strftime('%a %d %b %H:%M')}")

    # ── Copilot ──────────────────────────────────────────────────────────────
    with tab_copilot:
        st.subheader("💬 VibrantAD Copilot")
        st.caption("Ask about events, districts, investment opportunities, or family-friendly areas.")

        samples = [
            "Show me events for running enthusiasts this week",
            "Best districts for families who love sports",
            "Which districts have the highest investment opportunity?",
            "Top vibrant districts in Abu Dhabi",
        ]
        sample = st.selectbox("Try a sample question", samples)
        question = st.text_area("Your question", value=sample, height=80)

        if st.button("Ask Copilot", type="primary"):
            answer = copilot_answer(question, metrics, events, selected_interests)
            st.markdown(answer)

        with st.expander("Conversation history"):
            st.write("Copilot uses keyword routing. Connect an LLM API for full natural-language power.")


if __name__ == "__main__":
    main()
