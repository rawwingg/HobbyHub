"""Resident / client dashboard for VibrantAD."""

from __future__ import annotations

from datetime import datetime

import streamlit as st
from streamlit_folium import st_folium

from data_utils import INTERESTS, PERSONAS, filter_events_by_interests, filter_events_by_time, recommend_districts_for_interests
from feedback_utils import WANT_DIFFERENT, WANT_MORE, WANT_VARIETY, submit_feedback
from map_utils import create_client_personalized_map, create_events_map
from ui_shared import copilot_answer, export_csv, render_event_card, render_kpi_tiles, render_role_header


def render_persona_pills():
    st.markdown('<div class="section-label">One-Click Demo Personas</div>', unsafe_allow_html=True)
    cols = st.columns(len(PERSONAS))
    for col, (name, interests) in zip(cols, PERSONAS.items()):
        with col:
            if st.button(f"👤 {name}", use_container_width=True, key=f"res_persona_{name}"):
                st.session_state.selected_interests = interests
                st.session_state.interest_multiselect = interests
                st.session_state.active_persona = name
                st.rerun()


def render_resident_sidebar(events, pulse) -> tuple[list[str], str, list]:
    with st.sidebar:
        st.markdown("### 🇦🇪 My Community")
        if st.button("← Back to Home", use_container_width=True):
            st.session_state.user_role = None
            st.rerun()

        st.markdown('<div class="live-badge"><span class="live-dot"></span> Community Pulse</div>',
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

        selected_interests = st.multiselect("Interests & hobbies", INTERESTS, key="interest_multiselect")
        st.session_state.selected_interests = selected_interests
        time_filter = st.radio("Events", ["Today", "This Week", "All Upcoming"], index=1)

        filtered_events = filter_events_by_time(events, time_filter)
        if selected_interests:
            filtered_events = filter_events_by_interests(filtered_events, selected_interests)
        st.success(f"✓ {len(filtered_events)} events for you")

    return selected_interests, time_filter, filtered_events


def render_feedback_section(events):
    """Let residents rate attended events — stored anonymously."""
    st.markdown("### ⭐ Rate Your Experience")
    st.markdown(
        "Attended an event? Your feedback helps improve community programming. "
        "**No personal data is collected** — only ratings and preferences."
    )

    rated_ids = {r["event_id"] for r in st.session_state.event_feedback}
    rateable = events[~events["event_id"].isin(rated_ids)].head(20)

    if rateable.empty:
        st.info("You've rated all available events — check back after new events are published!")
        return

    event_labels = {
        row["event_id"]: f"{row['title']} · {row['district']} · {row['start_time'].strftime('%a %d %b')}"
        for _, row in rateable.iterrows()
    }
    chosen_id = st.selectbox(
        "Which event did you attend?",
        options=list(event_labels.keys()),
        format_func=lambda eid: event_labels[eid],
        key="feedback_event_select",
    )
    chosen = rateable[rateable["event_id"] == chosen_id].iloc[0]

    st.markdown('<div class="feedback-box">', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        rating = st.slider("How was it?", 1, 5, 4, key="feedback_rating")
        st.caption("1 = Poor · 5 = Excellent")
    with col2:
        preference = st.radio(
            "What would you like next?",
            [WANT_MORE, WANT_VARIETY, WANT_DIFFERENT],
            key="feedback_preference",
        )

    if st.button("Submit Feedback", type="primary", key="submit_feedback_btn"):
        record = submit_feedback(chosen, rating, preference)
        st.session_state.event_feedback.append(record)
        st.session_state.feedback_seeded = True
        st.success(f"Thanks! Your anonymous feedback helps shape **{chosen['district']}** community events.")
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


def render_resident_dashboard(data: dict):
    metrics = data["district_metrics"]
    events = data["events"]
    pulse = data["pulse"]

    selected_interests, time_filter, filtered_events = render_resident_sidebar(events, pulse)

    render_role_header("resident")
    render_kpi_tiles(metrics, events, pulse, mode="resident")
    render_persona_pills()

    if st.session_state.active_persona:
        chips = " ".join(f'<span class="event-chip">{i}</span>' for i in selected_interests)
        st.markdown(
            f'<div class="surface-copy" style="margin:0.5rem 0 1rem;">'
            f'<b>{st.session_state.active_persona}</b> profile: {chips}</div>',
            unsafe_allow_html=True,
        )

    tab_community, tab_map, tab_feedback, tab_copilot = st.tabs(
        ["🏠 My Community", "🗺️ Live Events Map", "⭐ Rate Events", "💬 Copilot"]
    )

    with tab_community:
        st.markdown("### 🤝 Your Community, Your City")
        st.markdown("Discover **neighbours, events, and vibrant districts** matched to your interests.")

        interests_for_rec = selected_interests or INTERESTS[:4]
        rec = recommend_districts_for_interests(
            metrics, filter_events_by_time(events, "This Week"), interests_for_rec
        )
        client_events = filter_events_by_interests(
            filter_events_by_time(events, "This Week"), interests_for_rec
        )

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Your interests", len(interests_for_rec))
        c2.metric("Matching events", len(client_events))
        c3.metric("Recommended areas", len(rec))
        c4.metric("Avg connectivity", f"{rec['community_connectivity_score'].mean():.0f}")

        map_col, side_col = st.columns([3, 2])
        with map_col:
            st.markdown('<div class="section-label">Personalised Community Map</div>', unsafe_allow_html=True)
            with st.container(border=True):
                st_folium(create_client_personalized_map(client_events, rec), height=500, use_container_width=True, returned_objects=[])

        with side_col:
            st.markdown('<div class="section-label">Areas That Might Interest You</div>', unsafe_allow_html=True)
            for _, row in rec.iterrows():
                score = row.get("personalized_score", row["vibrancy_score"])
                conn = row.get("community_connectivity_score", 0)
                st.markdown(
                    f"""<div class="community-card">
                        <strong>{row['district']}</strong>
                        <span class="event-chip">Score {score:.0f}</span>
                        <div class="surface-meta" style="font-size:0.85rem;margin-top:4px;">
                        Connectivity {conn:.0f} · {int(row.get('matching_events', 0))} events this week</div>
                        <div class="surface-emphasis" style="font-size:0.8rem;margin-top:4px;">
                        {row.get('event_highlights', 'Explore local amenities')}</div>
                    </div>""",
                    unsafe_allow_html=True,
                )

            st.markdown('<div class="section-label">This Weekend Near You</div>', unsafe_allow_html=True)
            for _, ev in client_events.head(5).iterrows():
                render_event_card(ev, compact=True)
                if st.button(f"I attended · {ev['title'][:24]}", key=f"attend_{ev['event_id']}"):
                    st.session_state.attended_events.add(ev["event_id"])
                    st.info("Head to the **Rate Events** tab to share your experience!")

        st.download_button("📥 Export My Community Guide", export_csv(rec),
                           "vibrantad_my_community.csv", "text/csv")

    with tab_map:
        hdr_l, hdr_m, hdr_r = st.columns([2, 2, 3])
        with hdr_l:
            st.markdown('<div class="live-badge"><span class="live-dot"></span> Live Events Map</div>',
                        unsafe_allow_html=True)
        with hdr_m:
            if st.button("🔄 Refresh Events", type="primary", use_container_width=True, key="res_refresh"):
                st.session_state.event_seed = int(datetime.now().timestamp()) % 100000
                st.cache_data.clear()
                st.rerun()
        with hdr_r:
            st.caption(f"Updated {datetime.now().strftime('%H:%M:%S')} · {len(filtered_events)} events")

        with st.container(border=True):
            st_folium(create_events_map(filtered_events, metrics, show_districts=True),
                      height=580, use_container_width=True, returned_objects=[])

        if not filtered_events.empty:
            st.markdown('<div class="section-label">Happening Near You</div>', unsafe_allow_html=True)
            ev_cols = st.columns(3)
            for i, (_, ev) in enumerate(filtered_events.head(9).iterrows()):
                with ev_cols[i % 3]:
                    render_event_card(ev, compact=True)

    with tab_feedback:
        render_feedback_section(events)

    with tab_copilot:
        st.markdown("### 💬 Community Copilot")
        st.caption("Ask about events, neighbourhoods, and family-friendly areas.")

        samples = [
            "Show me events for running enthusiasts this week",
            "Best districts for families who love sports",
            "What events are happening today?",
            "Top vibrant communities in Abu Dhabi",
        ]
        sample = st.selectbox("Sample questions", samples, label_visibility="collapsed", key="res_copilot_sample")
        question = st.text_area("Your question", value=sample, height=72, label_visibility="collapsed", key="res_copilot_q")

        if st.button("Ask Copilot", type="primary", key="res_copilot_btn"):
            with st.chat_message("assistant", avatar="🌴"):
                st.markdown(copilot_answer(question, metrics, events, selected_interests, role="resident"))
