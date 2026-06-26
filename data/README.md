# VibrantAD data

CSV files used by the app. All paths are loaded from `data_utils.py`.

| File | Rows | Used for |
|------|------|----------|
| `districts.csv` | 20 | District centroids and reference |
| `sample_communities.csv` | 90 | Service demand, mobility, resident experience |
| `osm_amenities.csv` | 3,155 | Real OSM sports, culture, parks (lat/long) |
| `sample_listings.csv` | 6,000 | Property coordinates for map context |

`osm_amenities.csv` is real OpenStreetMap data (© OSM contributors, ODbL). Other files are synthetic challenge datasets keyed on `district`.
