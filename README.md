# BhoomiNiti AI — National Land Governance Intelligence Platform

Prototype for SIH26019 (Ministry of Rural Development, Dept. of Land Resources):
*National Digital Platform for Research, Policy Innovation, and Evidence-Based
Land Governance.*

## What's implemented

| Problem statement bullet | Status |
|---|---|
| Centralized repository for research, policy papers, datasets | ✅ Research Hub (SQLite-backed) |
| AI-powered search / recommendation engine | ✅ TF-IDF retrieval + optional Claude synthesis |
| Interactive GIS visualization | ✅ GIS Intelligence (choropleth + drill-down) |
| Analytics & decision-support tools | ✅ Analytics page (correlations, scatter, drivers) |
| Policy simulation modules | ✅ Policy Lab (weight-adjustable scenario risk) |
| Secure role-based access | ✅ Login/signup, Public / Researcher / Official roles |
| Innovation portal (hackathons, grants, pilots) | ✅ Innovation Portal (post, browse, submit, review) |
| Dashboards | ✅ Dashboard + per-state profiles |
| AI-assisted trend analysis / literature synthesis | ✅ AI Intelligence page (Claude-powered, optional) |
| APIs for external integration | ⚠️ Not built — see "What's not implemented" |
| Satellite imagery / remote sensing integration | ⚠️ Not built — see "What's not implemented" |
| Collaborative workspaces | ⚠️ Not built in this pass |

## What's not implemented (and why)

- **Real satellite/remote-sensing imagery** — needs a licensed data feed
  (Bhuvan/ISRO, Sentinel Hub, etc.); out of scope for a local prototype.
- **External REST APIs** — the app currently *is* the interface. Exposing
  `db.py`'s functions behind FastAPI endpoints is the natural next step if
  you want other systems to integrate; ask and I'll build that layer.
- **Collaborative workspaces** — you deprioritized this in favor of AI,
  login, and the Innovation Portal. The DB schema and role system are
  already structured so this can be added later without a rewrite.
- **India state boundaries are placeholder rectangles**, not survey-accurate
  polygons — see "Important: swap in a real GeoJSON" below.

## Setup

```bash
cd bhoominiti_platform
python -m venv venv
source venv/bin/activate        
pip install -r requirements.txt
streamlit run app.py
```

`geopandas` can be the trickiest install on Windows (it needs GDAL/Fiona/
pyproj). If `pip install geopandas` fails, the easiest fix is:
```bash
conda install -c conda-forge geopandas
```
then `pip install` the rest of `requirements.txt` inside that same
environment.

The app creates `bhoominiti.db` (SQLite) on first run and seeds it from the
CSVs in `data/`. Delete `bhoominiti.db` any time to reset to fresh demo data.

## Logging in

Two demo accounts are seeded automatically:

| Role | Username | Password |
|---|---|---|
| Official | `official_demo` | `Demo@1234` |
| Researcher | `researcher_demo` | `Demo@1234` |

You can also sign up your own account, or continue as a **Guest** for
read-only browsing (Dashboard, GIS, Research Hub, AI Intelligence,
Analytics, and viewing the Innovation Portal). Logging in unlocks the
Policy Lab, contributing research records, and submitting/reviewing
Innovation Portal proposals. **Officials** can additionally post new
opportunities and change their status.

⚠️ This is a prototype auth system (PBKDF2-hashed passwords in SQLite,
session held in Streamlit's session state). It's fine for a demo or an
internal pilot but would need HTTPS, rate-limiting, and a proper session
store before any real deployment.

## Enabling Claude-powered AI synthesis

The Research Hub search always works offline (TF-IDF + cosine similarity —
no API key needed). For richer, natural-language synthesis and follow-up
Q&A on the **AI Intelligence** page:

1. Get an API key from https://console.anthropic.com
2. Paste it into the "🔑 AI Settings" box in the sidebar (kept only in that
   browser session — nothing is written to disk).
3. Run a search on the AI Intelligence page — the synthesis and the
   follow-up question box will now use Claude, grounded strictly in the
   retrieved evidence records (the prompt instructs it not to invent facts).

If no key is set, or the `anthropic` package isn't installed, everything
falls back to the offline rule-based summary automatically — the app never
breaks because of this.

## Important: swap in a real India states GeoJSON

`data/india_states.geojson` in this prototype is a **placeholder** —
simplified rectangular boxes around each state's approximate centroid, just
so the choropleth map renders and the demo runs end-to-end without needing
internet access to fetch a real boundary file. It is *not* survey-accurate
and shouldn't be used beyond this demo.

To get accurate boundaries:
1. Search for an open India states GeoJSON (a commonly used one is the
   `india_states.geojson` file circulated in several public GitHub repos
   for Indian choropleth maps — search "India states GeoJSON st_nm" to find
   a current, actively maintained source).
2. Replace `data/india_states.geojson` with the downloaded file.
3. Make sure it has a property holding the state name — if it isn't called
   `st_nm`, update the field name check near the top of `load_states()` in
   `app.py`.
4. Delete `bhoominiti.db` if you also change `land_data.csv` state names,
   so the seed data re-syncs.

## Project structure

```
bhoominiti_platform/
├── app.py              # Main Streamlit app — all pages, UI, routing
├── db.py                # SQLite schema, seeding, CRUD helpers
├── auth.py               # Login/signup/role-gating logic
├── ai_engine.py          # TF-IDF retrieval + optional Claude synthesis
├── requirements.txt
├── data/
│   ├── land_data.csv         # Synthetic state-level indicators (36 states/UTs)
│   ├── research_data.csv     # Synthetic research corpus (36 records)
│   └── india_states.geojson  # Placeholder boundaries — replace before real use
└── bhoominiti.db        # Created automatically on first run
```

## Data notice

All data (`land_data.csv`, `research_data.csv`) is **synthetic demo data**
generated for this prototype. It is not sourced from any official
government dataset and should not be presented as real statistics.
