"""Planner / investor dashboard for VibrantAD."""

from __future__ import annotations

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from streamlit_folium import st_folium

from data_utils import get_intervention_text
from feedback_utils import (
    aggregate_by_district,
    aggregate_by_interest,
    build_investment_signals,
    feedback_to_dataframe,
    investor_recommend,
)
from map_utils import UAE_COLORS, create_amenity_layers_map, create_district_vibrancy_map
from scoring import simulate_investment_uplift
from ui_shared import export_csv, render_event_card, render_kpi_tiles, render_role_header


def render_planner_sidebar() -> tuple[str, bool, bool, bool]:
    with st.sidebar:
        st.markdown("### 🇦🇪 City Intelligence")
        if st.button("← Back to Home", use_container_width=True):
            st.session_state.user_role = None
            st.rerun()

        st.caption("Future Communities · Track 3")
        st.markdown("---")
        st.markdown('<div class="section-label">Map Settings</div>', unsafe_allow_html=True)

        map_color = st.selectbox(
            "District colour",
            ["vibrancy_score", "community_connectivity_score", "optimization_score"],
            format_func=lambda x: x.replace("_", " ").title(),
        )
        show_sports = st.checkbox("⚽ Sports", True)
        show_cultural = st.checkbox("🎭 Cultural", True)
        show_parks = st.checkbox("🌳 Parks", True)

        st.markdown("---")
        st.markdown(
            '<div class="ethical-note">🔒 <b>Ethical data:</b> Resident feedback is fully '
            "anonymized — investors see aggregates only, never identities.</div>",
            unsafe_allow_html=True,
        )

    return map_color, show_sports, show_cultural, show_parks


def render_feedback_insights(feedback_df):
    st.markdown("### 📊 Anonymized Resident Feedback")
    st.caption(f"{len(feedback_df)} anonymous responses — no user identities exposed")

    if feedback_df.empty:
        st.info("No feedback collected yet. Resident ratings will appear here as aggregates.")
        return

    m1, m2, m3 = st.columns(3)
    m1.metric("Total responses", len(feedback_df))
    m2.metric("Avg satisfaction", f"{feedback_df['rating'].mean():.1f} / 5")
    m3.metric("Want more events", int((feedback_df["preference"] == "More events like this").sum()))

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown('<div class="section-label">Demand by Interest</div>', unsafe_allow_html=True)
        by_interest = aggregate_by_interest(feedback_df)
        if not by_interest.empty:
            fig = px.bar(
                by_interest, x="interest", y="demand_signal",
                color="avg_rating", color_continuous_scale=["#C0392B", "#C5A572", "#00732F"],
                labels={"demand_signal": "Demand Signal", "interest": "", "avg_rating": "Avg Rating"},
            )
            fig.update_layout(height=320, margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.markdown('<div class="section-label">Satisfaction by District</div>', unsafe_allow_html=True)
        by_district = aggregate_by_district(feedback_df)
        if not by_district.empty:
            fig2 = px.scatter(
                by_district, x="responses", y="avg_rating", size="responses",
                color="satisfaction_pct", hover_name="district",
                color_continuous_scale=["#C0392B", "#C5A572", "#00732F"],
                labels={"responses": "Responses", "avg_rating": "Avg Rating"},
            )
            fig2.update_layout(height=320, margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig2, use_container_width=True)

    st.dataframe(
        by_interest.rename(columns=lambda c: c.replace("_", " ").title()) if not by_interest.empty else by_interest,
        use_container_width=True, hide_index=True,
    )


def render_planner_dashboard(data: dict):
    metrics = data["district_metrics"]
    amenities = data["amenities"]
    events = data["events"]
    pulse = data["pulse"]
    feedback_df = feedback_to_dataframe(st.session_state.event_feedback)

    map_color, show_sports, show_cultural, show_parks = render_planner_sidebar()

    render_role_header("planner")
    render_kpi_tiles(metrics, events, pulse, mode="planner")

    tab_overview, tab_map, tab_feedback, tab_invest, tab_explorer, tab_copilot = st.tabs(
        ["📊 Overview", "🗺️ Vibrancy Heatmap", "📊 Resident Feedback", "💰 Investment", "🔍 Districts", "🤖 AI Advisor"]
    )

    with tab_overview:
        col_l, col_r = st.columns(2)
        with col_l:
            st.markdown('<div class="section-label">Vibrancy Leaders</div>', unsafe_allow_html=True)
            top_df = metrics.head(10)[["district", "vibrancy_score", "community_connectivity_score"]]
            fig = px.bar(
                top_df, x="vibrancy_score", y="district", orientation="h",
                color="community_connectivity_score",
                color_continuous_scale=["#C0392B", "#C5A572", "#00732F"],
                labels={"vibrancy_score": "Vibrancy", "district": "", "community_connectivity_score": "Connectivity"},
            )
            fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=400, margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig, use_container_width=True)

        with col_r:
            st.markdown('<div class="section-label">Sports Supply vs Experience</div>', unsafe_allow_html=True)
            fig2 = px.scatter(
                metrics, x="sports_density", y="resident_experience_score",
                size="sports_amenity_count", color="community_connectivity_score",
                hover_name="district",
                color_continuous_scale=["#C0392B", "#C5A572", "#00732F"],
            )
            fig2.update_layout(height=400, margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig2, use_container_width=True)

        c1, c2 = st.columns(2)
        with c1:
            st.markdown('<div class="section-label">Connectivity Index</div>', unsafe_allow_html=True)
            conn_df = metrics.nlargest(12, "community_connectivity_score")[
                ["district", "community_connectivity_score", "mobility_score"]
            ].sort_values("community_connectivity_score")
            fig_conn = px.bar(
                conn_df, x="community_connectivity_score", y="district", orientation="h",
                color="mobility_score", color_continuous_scale=["#1A1A2E", "#00732F"],
            )
            fig_conn.update_layout(height=360, coloraxis_showscale=False, margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig_conn, use_container_width=True)

        with c2:
            st.markdown('<div class="section-label">Performance Matrix</div>', unsafe_allow_html=True)
            heat_cols = [
                "vibrancy_score", "community_connectivity_score", "resident_experience_score",
                "mobility_score", "service_demand_fulfillment",
            ]
            heat = metrics.set_index("district")[heat_cols].head(12)
            fig3 = px.imshow(heat.T, color_continuous_scale=["#1A1A2E", "#C5A572", "#00732F"], aspect="auto")
            fig3.update_layout(height=360, margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig3, use_container_width=True)

        st.download_button("📥 Export District Report", export_csv(metrics),
                           "vibrantad_district_report.csv", "text/csv", key="planner_export_report")

    with tab_map:
        st.markdown('<div class="section-label">District Vibrancy Heatmap</div>', unsafe_allow_html=True)
        st.caption("Red → Gold → Green intensity shows vibrancy, connectivity, or opportunity scores.")
        st.markdown(
            '<div class="map-legend"><span class="legend-swatch"></span> Stronger colour means stronger district performance on the selected score.</div>',
            unsafe_allow_html=True,
        )

        view_mode = st.segmented_control(
            "Map view", ["Vibrancy Heatmap", "Amenity Layers"], default="Vibrancy Heatmap",
        )
        if view_mode == "Vibrancy Heatmap":
            fmap = create_district_vibrancy_map(metrics, color_by=map_color)
        else:
            fmap = create_amenity_layers_map(
                amenities, metrics,
                show_sports=show_sports, show_cultural=show_cultural,
                show_parks=show_parks, color_by=map_color,
            )
        with st.container(border=True):
            st_folium(fmap, height=580, use_container_width=True, returned_objects=[])

    with tab_feedback:
        render_feedback_insights(feedback_df)
        signals = build_investment_signals(feedback_df, metrics)
        if not signals.empty and signals["responses"].sum() > 0:
            st.markdown('<div class="section-label">Feedback-Driven Opportunity Scores</div>', unsafe_allow_html=True)
            st.dataframe(
                signals[signals["responses"] > 0][
                    ["district", "responses", "avg_rating", "want_more", "feedback_opportunity", "optimization_score"]
                ].rename(columns=lambda c: c.replace("_", " ").title()),
                use_container_width=True, hide_index=True,
            )

    with tab_invest:
        st.markdown("### Investment & Planning Intelligence")
        inv1, inv2 = st.columns(2)
        with inv1:
            st.markdown('<div class="section-label">Hub Opportunity Ranking</div>', unsafe_allow_html=True)
            opp = metrics.nlargest(10, "optimization_score")
            fig = px.bar(
                opp, x="optimization_score", y="district", orientation="h",
                color="community_connectivity_score",
                color_continuous_scale=["#00732F", "#C5A572", "#C0392B"],
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
            sim_district = st.selectbox("Target district", metrics["district"].tolist(), key="sim_district")
        with sim_col2:
            sim_facilities = st.slider("Facilities to add", 1, 20, 5, key="sim_facilities")
        with sim_col3:
            sim_type = st.selectbox("Facility type", ["sports", "cultural", "parks", "mixed"], key="sim_type")
        with sim_col4:
            st.write("")
            run_sim = st.button("Simulate Impact", type="primary", use_container_width=True, key="sim_run")

        if run_sim:
            row = metrics[metrics["district"] == sim_district].iloc[0]
            result = simulate_investment_uplift(row["vibrancy_score"], sim_facilities, sim_type)
            s1, s2, s3 = st.columns(3)
            s1.metric("Current Vibrancy", f"{result['current_vibrancy']}")
            s2.metric("Community Uplift", f"+{result['estimated_uplift']}")
            s3.metric("Projected Score", f"{result['projected_vibrancy']}")
            st.info(
                f"Adding **{sim_facilities} {sim_type}** facilities in **{sim_district}** could "
                f"boost vibrancy by an estimated **+{result['estimated_uplift']}** points."
            )

        st.download_button("📥 Export Opportunities", export_csv(metrics.nlargest(20, "optimization_score")),
                           "vibrantad_investment_opportunities.csv", "text/csv", key="planner_export_opp")

    with tab_explorer:
        st.markdown('<div class="section-label">Search & Explore Districts</div>', unsafe_allow_html=True)
        search = st.text_input("Search", placeholder="Yas Island, Corniche, Khalifa City…",
                               label_visibility="collapsed", key="planner_search")

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

        selected = st.selectbox("Deep dive", display["district"].tolist(), key="planner_district_select")
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

    with tab_copilot:
        st.markdown("### 🤖 AI Investment Advisor")
        st.caption(
            "Powered by anonymized resident feedback + city intelligence. "
            "Recommendations reflect aggregate demand — never individual identities."
        )

        samples = [
            "Which districts have the highest investment opportunity?",
            "What do residents want more of based on feedback?",
            "Where is resident satisfaction lowest?",
            "Which interests should we expand programming for?",
            "Best districts for new sports hubs",
        ]
        sample = st.selectbox("Sample questions", samples, label_visibility="collapsed", key="pl_copilot_sample")
        question = st.text_area("Your question", value=sample, height=72, label_visibility="collapsed", key="pl_copilot_q")

        if st.button("Get AI Recommendation", type="primary", key="pl_copilot_btn"):
            with st.chat_message("assistant", avatar="🏗️"):
                answer = investor_recommend(question, feedback_df, metrics, events)
                st.markdown(answer)

        with st.expander("How the AI Advisor works"):
            st.markdown(
                "Combines **anonymized event ratings**, **preference signals** (more vs different events), "
                "and **planning metrics** (demand, fulfillment, optimization) to generate "
                "ethical, aggregate investment recommendations."
            )
