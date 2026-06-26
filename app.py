"""VibrantAD — Homepage and role-based routing."""

from __future__ import annotations

import streamlit as st

from planner_dashboard import render_planner_dashboard
from resident_dashboard import render_resident_dashboard
from ui_shared import init_session_state, inject_styles, load_all, render_kpi_tiles, ensure_demo_feedback

st.set_page_config(
    page_title="VibrantAD | Future Communities Intelligence",
    page_icon="🌴",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_styles()
init_session_state()


def render_homepage():
    st.markdown(
        """
        <style>[data-testid="stSidebar"] { display: none; }</style>
        <div class="hero-banner" style="padding:3rem 2.5rem;text-align:center;">
            <h1 style="font-size:3 color: white;">🌴 VibrantAD</h1>
            <p class="tagline" style="font-size:1.15rem;">
                AI for Social Connectivity &amp; Vibrant Living in Abu Dhabi
            </p>
            <div class="hero-pillars" style="justify-content:center;margin-top:1.5rem;">
                <span class="hero-pillar">🤝 Connected Communities</span>
                <span class="hero-pillar">📍 Live Event Discovery</span>
                <span class="hero-pillar">🏗️ Data-Driven Planning</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        Supporting Abu Dhabi's **Future Communities** vision — better connected residents,
        data-driven investment, and proactive city planning powered by OSM amenity data
        and community performance metrics.
        """
    )

    data = load_all(seed=st.session_state.event_seed)
    render_kpi_tiles(data["district_metrics"], data["events"], data["pulse"], mode="all")

    st.markdown("")
    st.markdown("### Who are you?")
    st.caption("Select your role to enter a tailored dashboard experience.")

    col_res, col_plan = st.columns(2, gap="large")

    with col_res:
        st.markdown(
            """
            <div class="role-card">
                <div class="icon">🏠</div>
                <h3>Resident / Client</h3>
                <p>Discover events, find your community, explore districts matched to your interests,
                and connect with neighbours across Abu Dhabi.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Enter Resident Hub →", type="primary", use_container_width=True, key="btn_resident"):
            st.session_state.user_role = "resident"
            st.rerun()

    with col_plan:
        st.markdown(
            """
            <div class="role-card">
                <div class="icon">🏗️</div>
                <h3>Planner / Investor</h3>
                <p>Analyse district vibrancy, identify investment gaps, simulate facility impact,
                and plan the next generation of community hubs.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Enter Planner Intelligence →", use_container_width=True, key="btn_planner"):
            st.session_state.user_role = "planner"
            st.rerun()

    st.markdown("---")
    st.caption(
        "Abu Dhabi AI PropTech Challenge · Track 3: Future Communities · "
        "Aggregated public data only"
    )


def main():
    role = st.session_state.user_role
    data = load_all(seed=st.session_state.event_seed)
    ensure_demo_feedback(data["events"])

    if role == "resident":
        render_resident_dashboard(data)
    elif role == "planner":
        render_planner_dashboard(data)
    else:
        render_homepage()


if __name__ == "__main__":
    main()
