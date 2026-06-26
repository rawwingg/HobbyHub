"""Folium map builders for VibrantAD."""

from __future__ import annotations

import branca.colormap as cm
import folium
import pandas as pd
from folium.plugins import MarkerCluster

ABU_DHABI_CENTER = [24.4539, 54.3773]
UAE_COLORS = {
    "green": "#00732F",
    "gold": "#C5A572",
    "sand": "#F5F0E6",
    "dark": "#1A1A2E",
    "red": "#C0392B",
    "blue": "#2980B9",
}


def _score_color(value: float, low: float = 40, high: float = 85) -> str:
    """Green–gold–red gradient for scores."""
    if value >= high:
        return UAE_COLORS["green"]
    if value >= (low + high) / 2:
        return UAE_COLORS["gold"]
    return UAE_COLORS["red"]


def _popup_html(title: str, rows: list[tuple[str, str]]) -> str:
    body = "".join(
        f"<tr><td style='padding:2px 8px;color:#666;'>{k}</td>"
        f"<td style='padding:2px 8px;'><b>{v}</b></td></tr>"
        for k, v in rows
    )
    return (
        f"<div style='font-family:Arial;min-width:180px;'>"
        f"<h4 style='margin:0 0 6px;color:{UAE_COLORS['green']};'>{title}</h4>"
        f"<table>{body}</table></div>"
    )


def create_district_vibrancy_map(
    district_metrics: pd.DataFrame,
    color_by: str = "vibrancy_score",
    zoom: int = 11,
) -> folium.Map:
    """District centroids colored by vibrancy or optimization score."""
    fmap = folium.Map(location=ABU_DHABI_CENTER, zoom_start=zoom, tiles="CartoDB positron")

    colormap = cm.LinearColormap(
        colors=[UAE_COLORS["red"], UAE_COLORS["gold"], UAE_COLORS["green"]],
        vmin=district_metrics[color_by].min(),
        vmax=district_metrics[color_by].max(),
        caption=color_by.replace("_", " ").title(),
    )
    colormap.add_to(fmap)

    for _, row in district_metrics.iterrows():
        score = row[color_by]
        popup = _popup_html(
            row["district"],
            [
                ("Vibrancy", f"{row['vibrancy_score']:.1f}"),
                ("Experience", f"{row['resident_experience_score']:.0f}"),
                ("Mobility", f"{row['mobility_score']:.0f}"),
                ("Sports amenities", str(int(row["sports_amenity_count"]))),
                ("Cultural amenities", str(int(row["cultural_amenity_count"]))),
                ("Optimization", f"{row['optimization_score']:.1f}"),
            ],
        )
        folium.CircleMarker(
            location=[row["latitude"], row["longitude"]],
            radius=8 + score / 12,
            color=_score_color(score),
            fill=True,
            fill_color=colormap(score),
            fill_opacity=0.75,
            weight=2,
            popup=folium.Popup(popup, max_width=280),
            tooltip=f"{row['district']}: {score:.1f}",
        ).add_to(fmap)

    return fmap


def create_amenity_layers_map(
    amenities: pd.DataFrame,
    district_metrics: pd.DataFrame,
    show_sports: bool = True,
    show_cultural: bool = True,
    show_parks: bool = True,
    color_by: str = "vibrancy_score",
    zoom: int = 11,
) -> folium.Map:
    """Interactive map with toggleable amenity layers and district overlay."""
    fmap = create_district_vibrancy_map(district_metrics, color_by=color_by, zoom=zoom)

    layer_config = [
        ("Sports Amenities", "is_sports", "green"),
        ("Cultural Amenities", "is_cultural", "purple"),
        ("Parks & Playgrounds", "is_park", "darkgreen"),
    ]

    for layer_name, flag_col, color in layer_config:
        show = {"is_sports": show_sports, "is_cultural": show_cultural, "is_park": show_parks}[
            flag_col
        ]
        if not show:
            continue

        cluster = MarkerCluster(name=layer_name)
        subset = amenities[amenities[flag_col]]
        for _, row in subset.iterrows():
            name = row["name"] if row["name"] and "(unnamed" not in str(row["name"]) else row["subtype"]
            popup = _popup_html(
                name,
                [
                    ("Type", row["subtype"]),
                    ("District", row["district"]),
                    ("Category", row["category"]),
                ],
            )
            folium.CircleMarker(
                location=[row["latitude"], row["longitude"]],
                radius=5,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.7,
                popup=folium.Popup(popup, max_width=260),
                tooltip=name,
            ).add_to(cluster)
        cluster.add_to(fmap)

    folium.LayerControl(collapsed=False).add_to(fmap)
    return fmap


def create_events_map(
    events: pd.DataFrame,
    district_metrics: pd.DataFrame | None = None,
    show_districts: bool = True,
    zoom: int = 11,
) -> folium.Map:
    """Client events layer with live-style pins."""
    fmap = folium.Map(location=ABU_DHABI_CENTER, zoom_start=zoom, tiles="CartoDB positron")

    if show_districts and district_metrics is not None:
        for _, row in district_metrics.iterrows():
            folium.CircleMarker(
                location=[row["latitude"], row["longitude"]],
                radius=6,
                color=UAE_COLORS["gold"],
                fill=True,
                fill_color=UAE_COLORS["gold"],
                fill_opacity=0.25,
                weight=1,
                tooltip=f"{row['district']} · Vibrancy {row['vibrancy_score']:.0f}",
            ).add_to(fmap)

    if events.empty:
        folium.Marker(
            ABU_DHABI_CENTER,
            popup="No events match your filters",
            icon=folium.Icon(color="gray", icon="info-sign"),
        ).add_to(fmap)
        return fmap

    sports_cluster = MarkerCluster(name="Sports Events")
    cultural_cluster = MarkerCluster(name="Cultural Events")

    for _, ev in events.iterrows():
        start_str = ev["start_time"].strftime("%a %d %b, %H:%M")
        popup = _popup_html(
            ev["title"],
            [
                ("When", start_str),
                ("Interest", ev["interest"]),
                ("Type", ev["event_type"]),
                ("District", ev["district"]),
                ("Venue", ev["amenity_name"][:40]),
                ("Spots left", str(ev["spots_available"])),
            ],
        )
        icon_color = "green" if ev["event_type"] == "Sports" else "purple"
        marker = folium.Marker(
            location=[ev["latitude"], ev["longitude"]],
            popup=folium.Popup(popup, max_width=300),
            tooltip=f"LIVE · {ev['title']} · {start_str}",
            icon=folium.Icon(color=icon_color, icon="calendar"),
        )
        target = sports_cluster if ev["event_type"] == "Sports" else cultural_cluster
        marker.add_to(target)

    sports_cluster.add_to(fmap)
    cultural_cluster.add_to(fmap)
    folium.LayerControl(collapsed=False).add_to(fmap)
    return fmap


def create_client_personalized_map(
    events: pd.DataFrame,
    recommended_districts: pd.DataFrame,
    zoom: int = 11,
) -> folium.Map:
    """Personalized client map highlighting recommended districts and matching events."""
    fmap = folium.Map(location=ABU_DHABI_CENTER, zoom_start=zoom, tiles="CartoDB positron")

    for _, row in recommended_districts.iterrows():
        folium.Circle(
            location=[row["latitude"], row["longitude"]],
            radius=2500,
            color=UAE_COLORS["green"],
            fill=True,
            fill_color=UAE_COLORS["green"],
            fill_opacity=0.12,
            weight=2,
            popup=folium.Popup(
                _popup_html(
                    f"⭐ {row['district']}",
                    [
                        ("Personalized score", f"{row.get('personalized_score', row['vibrancy_score']):.1f}"),
                        ("Matching events", str(int(row.get("matching_events", 0)))),
                        ("Vibrancy", f"{row['vibrancy_score']:.1f}"),
                    ],
                ),
                max_width=280,
            ),
            tooltip=f"Recommended: {row['district']}",
        ).add_to(fmap)

    event_cluster = MarkerCluster(name="Events For You")
    for _, ev in events.iterrows():
        start_str = ev["start_time"].strftime("%a %d %b, %H:%M")
        folium.Marker(
            location=[ev["latitude"], ev["longitude"]],
            popup=folium.Popup(
                _popup_html(ev["title"], [("When", start_str), ("Interest", ev["interest"])]),
                max_width=260,
            ),
            tooltip=f"{ev['title']} · {ev['interest']}",
            icon=folium.Icon(color="green", icon="heart"),
        ).add_to(event_cluster)

    event_cluster.add_to(fmap)
    folium.LayerControl(collapsed=False).add_to(fmap)
    return fmap
