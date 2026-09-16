<div align="center">

# 🌏 BhoomiNiti AI

### National Digital Platform for Research, Policy Innovation & Evidence-Based Land Governance

**Prototype for SIH26019 · Ministry of Rural Development · Department of Land Resources**

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-App-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![SQLite](https://img.shields.io/badge/Database-SQLite-07405E?logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Claude](https://img.shields.io/badge/AI-Claude-D4A574?logo=anthropic&logoColor=white)](https://www.anthropic.com/)
[![Status](https://img.shields.io/badge/Status-Prototype-yellow)]()
[![License](https://img.shields.io/badge/License-None-lightgrey)]()

</div>

---

## Overview

Land governance in India generates enormous volumes of data — cadastral records, GIS layers, satellite imagery, policy documents — but there's no unified platform to turn that data into research, evidence, and coordinated policy action.

**BhoomiNiti AI** is a working prototype of that platform: a single application that brings together GIS-based spatial intelligence, an AI-powered research repository, policy scenario simulation, and an innovation portal for hackathons and grants, all backed by a real (if lightweight) database with role-based access.

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Quick Start](#quick-start)
- [Logging In](#logging-in)
- [Enabling Claude AI Synthesis](#enabling-claude-ai-synthesis)
- [Project Structure](#project-structure)
- [Roadmap](#roadmap)
- [Data Notice](#data-notice)

## Features

| Module | What it does |
|---|---|
| 📊 **Dashboard** | National governance metrics, risk distribution, state-by-state ranking |
| 🗺️ **GIS Intelligence** | Interactive choropleth map with drill-down, multiple base layers, per-state risk profiles |
| 📚 **Research Hub** | Centralized, searchable repository of land governance research and policy papers |
| 🤖 **AI Intelligence** | TF-IDF evidence retrieval, ranked results, and optional Claude-powered synthesis and follow-up Q&A |
| 📈 **Analytics** | Correlation matrices, scatter analysis, and dominant risk-driver breakdowns |
| ⚖️ **Policy Lab** | Adjustable-weight scenario simulation for testing policy trade-offs |
| 🚀 **Innovation Portal** | Hackathons, grants, and pilot projects — post, browse, submit, and review proposals |
| 📄 **Reports** | One-click, downloadable per-state intelligence briefs |
| 🔐 **Role-Based Access** | Public guest / Researcher / Official tiers with gated features |

## Tech Stack

<div align="center">

| Layer | Technology |
|---|---|
| Frontend / App | Streamlit |
| Database | SQLite |
| Mapping | GeoPandas, Folium |
| Charts | Plotly |
| Search & Retrieval | scikit-learn (TF-IDF, cosine similarity) |
| Optional LLM Layer | Anthropic Claude API |
| Auth | PBKDF2-hashed credentials, session-based roles |

</div>

## Quick Start

```bash
git clone https://github.com/saiswarooppatnala/bhoominiti-ai.git
cd bhoominiti-ai

python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

The app opens at `http://localhost:8501`. A SQLite database (`bhoominiti.db`) is created and seeded automatically on first run — no manual setup required.

> **Windows note:** `geopandas` can be the trickiest install (it needs GDAL/Fiona/pyproj). If `pip install geopandas` fails, use `conda install -c conda-forge geopandas` instead, then install the rest of `requirements.txt` in that same environment.

## Logging In

Two demo accounts are seeded automatically so you can explore every role immediately:

| Role | Username | Password |
|---|---|---|
| 👤 Official | `official_demo` | `Demo@1234` |
| 🔬 Researcher | `researcher_demo` | `Demo@1234` |

You can also sign up your own account, or continue as a **Guest** for read-only access to the Dashboard, GIS Intelligence, Research Hub, AI Intelligence, Analytics, and the public Innovation Portal listing. Logging in unlocks the Policy Lab, contributing research records, and submitting or reviewing Innovation Portal proposals. Officials can additionally post new opportunities and manage their status.

> This is a prototype auth system — solid for a demo or internal pilot, but it would need HTTPS, rate-limiting, and a production session store before any real deployment.

## Enabling Claude AI Synthesis

Evidence retrieval always works fully offline (TF-IDF + cosine similarity, no API key required). To enable natural-language synthesis and follow-up Q&A on the **AI Intelligence** page:

1. Get an API key from [console.anthropic.com](https://console.anthropic.com)
2. Paste it into the **AI Settings** panel in the sidebar (kept only in that browser session — never written to disk)
3. Run a search — synthesis and follow-up answers will now be generated by Claude, grounded strictly in the retrieved evidence

Without a key, everything falls back automatically to the offline rule-based summary.

## Project Structure

```
bhoominiti-ai/
├── app.py                     # Streamlit app — pages, UI, routing
├── db.py                      # SQLite schema, seeding, CRUD
├── auth.py                    # Login, signup, role gating
├── ai_engine.py                # TF-IDF retrieval + Claude synthesis
├── requirements.txt
├── data/
│   ├── land_data.csv           # Synthetic state-level indicators (36 states/UTs)
│   ├── research_data.csv       # Synthetic research corpus
│   └── india_states.geojson    # Simplified state boundary shapes
└── bhoominiti.db               # Created automatically on first run
```

## Roadmap

Built in this prototype:

- ✅ Centralized research repository with AI-powered search
- ✅ Interactive GIS visualization with spatial risk layers
- ✅ Policy simulation and decision-support analytics
- ✅ Role-based access (Public / Researcher / Official)
- ✅ Innovation portal for hackathons, grants, and pilot projects

Not yet built, and why:

- **Satellite / remote-sensing imagery** — needs a licensed data feed (Bhuvan/ISRO, Sentinel Hub), out of scope for a local prototype
- **External REST APIs** — the app is currently the interface itself; exposing `db.py` behind FastAPI endpoints is a natural next step
- **Collaborative workspaces** — deprioritized in favor of AI synthesis, auth, and the Innovation Portal; the schema already supports adding this later
- **Survey-accurate state boundaries** — `india_states.geojson` uses simplified, hand-plotted outlines rather than official cadastral boundaries

## Data Notice

All data in this repository (`land_data.csv`, `research_data.csv`, `india_states.geojson`) is **synthetic demo data** created for this prototype. None of it is sourced from an official government dataset, and it should not be presented or cited as real statistics.

---

<div align="center">
Built for Smart India Hackathon 2026 · SIH26019 · Dept. of Land Resources
</div>
