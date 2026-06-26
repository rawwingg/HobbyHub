# VibrantAD

**AI for Social Connectivity & Vibrant Living in Abu Dhabi**

VibrantAD is a Streamlit city-intelligence prototype for the Abu Dhabi AI PropTech Challenge — **Track 3: Future Communities**. It helps residents discover community events and helps planners/investors identify where to invest in sports, culture, and social infrastructure — powered by real OSM amenity data and community performance metrics.

---

## Setup

**Requirements:** Python 3.10+

**One command:**

```bash
git clone https://github.com/rawwingg/HobbyHub.git
cd HobbyHub
./quickstart.sh
```

**Or manually:**

```bash
git clone https://github.com/rawwingg/HobbyHub.git
cd HobbyHub

python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

streamlit run app.py
```

Open **http://localhost:8501** in your browser.

That's it — no API keys required. All data ships in the `data/` folder.

---

## How to use the app

1. **Homepage** — choose your role:
   - **Resident / Client** — events, personalised districts, feedback
   - **Planner / Investor** — vibrancy analytics, heatmaps, AI investment advisor

2. **Residents** can browse live events on a map, get area recommendations based on interests, and **rate events anonymously** (satisfaction + whether they want more or different programming).

3. **Planners** can explore a **vibrancy heatmap**, run gap analysis, simulate facility investments, and use the **AI Investment Advisor** — which combines anonymized resident feedback with city planning metrics. Individual identities are never exposed.

Use the **← Back to Home** button in the sidebar to switch roles.

---

## Features

| Area | What it does |
|------|----------------|
| **Vibrancy scoring** | Composite score from resident experience, mobility, amenity fulfillment, and optimization opportunity |
| **District heatmap** | Folium heatmap coloured by vibrancy, connectivity, or investment opportunity |
| **Live events map** | Simulated community events pinned to real OSM sports/cultural venues |
| **Resident hub** | Personas, interest filters, personalised maps, weekend event discovery |
| **Event feedback** | Anonymous ratings and preference signals (more / variety / different) |
| **Planner intelligence** | Opportunity ranking, demand vs fulfillment gaps, investment simulator |
| **AI Investment Advisor** | Feedback-driven recommendations for hubs, interests, and districts |
| **Copilot** | Natural-language Q&A for both residents and planners |

---

## Project structure

```
app.py                  Entry point — homepage + role routing
resident_dashboard.py   Resident / client experience
planner_dashboard.py    Planner / investor analytics
ui_shared.py            Shared styles, data loading, helpers
data_utils.py           CSV loading, spatial enrichment, events
map_utils.py            Folium maps (heatmap, amenities, events)
scoring.py              Vibrancy formula + investment simulator
feedback_utils.py       Anonymous feedback + AI investor recommendations
data/                   CSV datasets (communities, amenities, districts, listings)
```

---

## Data

| File | Description |
|------|-------------|
| `data/sample_communities.csv` | District-level service demand, mobility, experience scores |
| `data/osm_amenities.csv` | 3,155 real OpenStreetMap sports/cultural/park points |
| `data/districts.csv` | 20 Abu Dhabi district reference with centroids |
| `data/sample_listings.csv` | Property coordinates for map context |

Amenities are spatially joined to districts. Events are generated dynamically from amenity locations.

---

## Ethical data use

- Resident feedback is **fully anonymized** — no names, accounts, or identifiers
- Planners see **aggregated** satisfaction and demand signals only
- City metrics use public OSM data and synthetic community indicators

---

## Challenge context

Built for the **Abu Dhabi AI PropTech Challenge** (Cursor × eVoost AI, Hub71) — supporting Abu Dhabi's Future Communities vision: connected residents, data-driven investment, proactive city planning.

---

Licensed under the [MIT License](LICENSE).
