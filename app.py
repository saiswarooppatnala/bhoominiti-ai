import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
import plotly.express as px
from streamlit_folium import st_folium
from folium.plugins import Fullscreen, MousePosition

import db
import auth
import ai_engine

st.set_page_config(
    page_title="BhoomiNiti AI",
    page_icon="🌏",
    layout="wide",
    initial_sidebar_state="expanded",
)

db.init_db()

if "user" not in st.session_state:
    st.session_state["user"] = None
if "guest_mode" not in st.session_state:
    st.session_state["guest_mode"] = False
if "claude_api_key" not in st.session_state:
    st.session_state["claude_api_key"] = ""
if "ai_chat_history" not in st.session_state:
    st.session_state["ai_chat_history"] = []


def calculate_risk_score(df):
    governance_risk = 100 - df["Land_Governance_Index"]
    return (
        governance_risk * 0.25
        + df["Urban_Expansion"] * 0.20
        + df["Climate_Vulnerability"] * 0.25
        + df["Dispute_Density"] * 0.15
        + df["Infrastructure_Pressure"] * 0.15
    ).round(2)


def risk_level(score):
    if score >= 65:
        return "High"
    if score >= 40:
        return "Medium"
    return "Low"


def risk_label(score):
    if score >= 65:
        return "🔴 High"
    if score >= 40:
        return "🟠 Medium"
    return "🟢 Low"


def dominant_driver(row):
    drivers = {
        "Climate Vulnerability": row["Climate_Vulnerability"],
        "Urban Expansion": row["Urban_Expansion"],
        "Land Disputes": row["Dispute_Density"],
        "Infrastructure Pressure": row["Infrastructure_Pressure"],
        "Governance": 100 - row["Land_Governance_Index"],
    }
    return max(drivers, key=drivers.get)


def intervention_for_driver(driver):
    actions = {
        "Climate Vulnerability": "Prioritize climate-resilient land-use planning, watershed protection and adaptation investments.",
        "Urban Expansion": "Strengthen urban growth management, land-use zoning and agricultural land protection.",
        "Land Disputes": "Improve record modernization, dispute-resolution workflows and legal-service access.",
        "Infrastructure Pressure": "Coordinate infrastructure corridors with land-use plans and social-environmental safeguards.",
        "Governance": "Prioritize institutional capacity, digital records, transparency and evidence-based monitoring.",
    }
    return actions.get(driver, "Strengthen integrated land governance and evidence-based planning.")


@st.cache_data
def load_land_df():
    df = db.load_land_df()
    numeric_cols = [
        "Land_Governance_Index", "Urban_Expansion", "Agri_Land_Percent",
        "Climate_Vulnerability", "Dispute_Density", "Infrastructure_Pressure",
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["Composite_Risk"] = calculate_risk_score(df)
    df["Risk_Level"] = df["Composite_Risk"].apply(risk_level)
    df["Priority"] = df["Composite_Risk"].rank(ascending=False, method="min").astype(int)
    return df


@st.cache_data
def load_research_df():
    df = db.load_research_df()
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    return df


@st.cache_data
def load_states():
    india = gpd.read_file(db.DATA_DIR / "india_states.geojson")
    if "st_nm" not in india.columns:
        raise ValueError("GeoJSON missing 'st_nm' field.")
    india["st_nm"] = india["st_nm"].replace({
        "Orissa": "Odisha", "Uttaranchal": "Uttarakhand",
        "Telengana": "Telangana", "Pondicherry": "Puducherry",
    })
    india = india[["st_nm", "geometry"]].copy()
    return india.dissolve(by="st_nm", as_index=False)


INDICATORS = {
    "Land Governance Index": "Land_Governance_Index",
    "Urban Expansion": "Urban_Expansion",
    "Agricultural Land %": "Agri_Land_Percent",
    "Climate Vulnerability": "Climate_Vulnerability",
    "Land Dispute Density": "Dispute_Density",
    "Infrastructure Pressure": "Infrastructure_Pressure",
    "Composite Governance Risk": "Composite_Risk",
}

if st.session_state["user"] is None and not st.session_state["guest_mode"]:
    auth.auth_gate()
    st.stop()

land_df = load_land_df()
research_df = load_research_df()
india_states = load_states()

india_states = india_states.rename(columns={"st_nm": "State"})
map_df = india_states.merge(land_df, on="State", how="left", suffixes=("", "_data"))

with st.sidebar:
    st.markdown("# 🌏 BhoomiNiti AI")
    st.caption("National Land Governance Intelligence Platform")

    user = auth.current_user()
    if user:
        st.success(f"Signed in as **{user['full_name']}** ({user['role']})")
        if st.button("Log out", use_container_width=True):
            auth.logout()
            st.rerun()
    else:
        st.info("Browsing as **Guest** (read-only)")
        if st.button("Log in / Sign up", use_container_width=True):
            st.session_state["guest_mode"] = False
            st.rerun()

    st.divider()

    pages = [
        "Dashboard", "GIS Intelligence", "Research Hub", "AI Intelligence",
        "Analytics", "Policy Lab", "Innovation Portal", "Reports",
    ]
    page = st.radio("Navigation", pages)

    st.divider()
    with st.expander("🔑 AI Settings (optional)"):
        st.caption(
            "Add an Anthropic API key to enable Claude-powered synthesis and follow-up "
            "Q&A in AI Intelligence. Without a key, search still works fully offline."
        )
        st.session_state["claude_api_key"] = st.text_input(
            "Anthropic API key", type="password",
            value=st.session_state["claude_api_key"],
            placeholder="sk-ant-...",
        )

    st.divider()
    st.markdown("### Platform Status")
    st.success("AI Research Engine: Active")
    st.success("GIS Engine: Active")
    st.success("Policy Simulation: Active")
    st.success(f"LLM Synthesis: {'Enabled' if st.session_state['claude_api_key'] else 'Offline mode'}")

    st.divider()
    st.caption(
        "Prototype data is synthetic/demo data built for this SIH submission and is not "
        "an official government dataset."
    )


if page == "Dashboard":
    st.title("National Land Governance Intelligence Dashboard")
    st.caption("A unified decision-support view for land governance, spatial pressure and policy research.")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("States / Regions", land_df["State"].nunique())
    c2.metric("Avg Governance Index", f"{land_df['Land_Governance_Index'].mean():.1f}")
    c3.metric("Avg Composite Risk", f"{land_df['Composite_Risk'].mean():.1f}")
    c4.metric("High-Risk States", int((land_df["Risk_Level"] == "High").sum()))

    st.divider()
    left, right = st.columns(2)

    with left:
        governance = land_df.sort_values("Land_Governance_Index", ascending=False)
        fig = px.bar(governance, x="Land_Governance_Index", y="State", orientation="h",
                     title="Land Governance Index by State",
                     labels={"Land_Governance_Index": "Governance Index"})
        fig.update_layout(height=650)
        st.plotly_chart(fig, use_container_width=True)

    with right:
        risk_counts = land_df["Risk_Level"].value_counts().reindex(["Low", "Medium", "High"], fill_value=0)
        fig = px.pie(values=risk_counts.values, names=risk_counts.index,
                     title="Composite Governance Risk Distribution", hole=0.45)
        fig.update_layout(height=650)
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("National State Ranking")
    ranking = land_df[["State", "Land_Governance_Index", "Composite_Risk", "Risk_Level", "Priority"]] \
        .sort_values("Composite_Risk", ascending=False).reset_index(drop=True)
    ranking["Risk"] = ranking["Composite_Risk"].apply(risk_label)
    st.dataframe(
        ranking[["Priority", "State", "Land_Governance_Index", "Composite_Risk", "Risk"]],
        use_container_width=True, hide_index=True,
    )


elif page == "GIS Intelligence":
    st.title("GIS Intelligence")
    st.caption("Interactive state-level land governance intelligence with spatial risk layers and drill-down.")

    c_left, c_mid, c_right = st.columns([1.4, 1.2, 1.2])
    with c_left:
        selected_indicator = st.selectbox("Map Indicator", list(INDICATORS.keys()))
    with c_mid:
        selected_state = st.selectbox("Focus State", ["All States"] + sorted(land_df["State"].tolist()))
    with c_right:
        map_style = st.selectbox("Base Map", ["OpenStreetMap", "Esri World Street Map", "Esri Satellite"])

    indicator_column = INDICATORS[selected_indicator]

    if selected_state == "All States":
        map_center, zoom = [22.5, 80.0], 4.5
    else:
        geom = map_df.loc[map_df["State"] == selected_state, "geometry"].iloc[0]
        bounds = geom.bounds
        map_center = [(bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2]
        zoom = 5.7

    m = folium.Map(location=map_center, zoom_start=zoom, tiles=None, control_scale=True)

    folium.TileLayer(tiles="OpenStreetMap", name="OpenStreetMap", overlay=False, control=True,
                      show=map_style == "OpenStreetMap").add_to(m)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",
        attr="Esri", name="Esri World Street Map", overlay=False, control=True,
        show=map_style == "Esri World Street Map",
    ).add_to(m)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri", name="Esri Satellite", overlay=False, control=True,
        show=map_style == "Esri Satellite",
    ).add_to(m)

    Fullscreen(position="topleft", title="Open full screen", title_cancel="Exit full screen").add_to(m)
    MousePosition(position="bottomright", separator=" | ", prefix="Coordinates:").add_to(m)

    tooltip = folium.GeoJsonTooltip(
        fields=["State", "Land_Governance_Index", "Urban_Expansion", "Agri_Land_Percent",
                "Climate_Vulnerability", "Dispute_Density", "Infrastructure_Pressure",
                "Composite_Risk", "Risk_Level"],
        aliases=["State", "Governance Index", "Urban Expansion", "Agricultural Land %",
                 "Climate Vulnerability", "Dispute Density", "Infrastructure Pressure",
                 "Composite Risk", "Risk Level"],
        localize=True, sticky=True, labels=True,
        style="background-color: white; color: #222; font-family: arial; font-size: 12px; padding: 8px;",
    )

    folium.Choropleth(
        geo_data=map_df.__geo_interface__, data=map_df,
        columns=["State", indicator_column], key_on="feature.properties.State",
        fill_color="YlOrRd", fill_opacity=0.70, line_opacity=0.55, line_color="#555555",
        nan_fill_color="#d9d9d9", nan_fill_opacity=0.45, legend_name=selected_indicator, highlight=True,
    ).add_to(m)

    folium.GeoJson(
        map_df.__geo_interface__, name="State Boundaries",
        style_function=lambda f: {"fillColor": "transparent", "color": "#333333", "weight": 0.65, "fillOpacity": 0},
        highlight_function=lambda f: {"weight": 2.2, "color": "#111111", "fillOpacity": 0.08},
        tooltip=tooltip, show=True,
    ).add_to(m)

    if selected_state != "All States":
        selected_geo = map_df[map_df["State"] == selected_state]
        folium.GeoJson(
            selected_geo.__geo_interface__, name=f"Focus: {selected_state}",
            style_function=lambda f: {"fillColor": "transparent", "color": "#111111", "weight": 3.5, "fillOpacity": 0.02},
            show=True,
        ).add_to(m)
        minx, miny, maxx, maxy = selected_geo.total_bounds
        m.fit_bounds([[miny, minx], [maxy, maxx]], padding=(28, 28))
    else:
        minx, miny, maxx, maxy = map_df.total_bounds
        m.fit_bounds([[miny, minx], [maxy, maxx]], padding=(18, 18))

    folium.LayerControl(collapsed=False, position="topright").add_to(m)
    st_folium(m, use_container_width=True, height=720, returned_objects=[])

    st.divider()

    if selected_state != "All States":
        state_row = land_df[land_df["State"] == selected_state].iloc[0]
        driver = dominant_driver(state_row)

        st.subheader(f"{selected_state} — Intelligence Profile")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Governance Index", f"{state_row['Land_Governance_Index']:.1f}")
        c2.metric("Composite Risk", f"{state_row['Composite_Risk']:.1f}")
        c3.metric("Risk Level", state_row["Risk_Level"])
        c4.metric("Priority Rank", f"#{int(state_row['Priority'])}")

        st.info(f"Dominant intervention driver: **{driver}**. " + intervention_for_driver(driver))

        state_metrics = pd.DataFrame({
            "Indicator": ["Governance Risk", "Urban Expansion", "Climate Vulnerability", "Land Disputes", "Infrastructure Pressure"],
            "Value": [100 - state_row["Land_Governance_Index"], state_row["Urban_Expansion"],
                      state_row["Climate_Vulnerability"], state_row["Dispute_Density"], state_row["Infrastructure_Pressure"]],
        })

        gl, gr = st.columns([1.4, 1])
        with gl:
            fig = px.bar(state_metrics, x="Value", y="Indicator", orientation="h", title="Risk Driver Profile")
            fig.update_layout(height=420)
            st.plotly_chart(fig, use_container_width=True)
        with gr:
            profile = pd.DataFrame({
                "Indicator": ["Governance Index", "Agricultural Land %", "Urban Expansion"],
                "Value": [state_row["Land_Governance_Index"], state_row["Agri_Land_Percent"], state_row["Urban_Expansion"]],
            })
            fig = px.bar(profile, x="Indicator", y="Value", title="State Land Profile")
            fig.update_layout(height=420)
            st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.subheader("National Spatial Ranking")
    ranking_columns = ["State", indicator_column, "Risk_Level", "Priority"]
    if indicator_column != "Composite_Risk":
        ranking_columns.insert(2, "Composite_Risk")
    ranking = land_df[ranking_columns].copy().sort_values(indicator_column, ascending=False).reset_index(drop=True)
    st.dataframe(ranking, use_container_width=True, hide_index=True)


elif page == "Research Hub":
    st.title("Research Hub")
    st.caption("Centralized discovery and evidence management for land-governance research.")

    corpus = ai_engine.build_corpus(research_df)
    vectorizer, matrix = ai_engine.build_engine(tuple(corpus.tolist()))

    st.info(
        "Research records in this prototype are synthetic/demo evidence. Logged-in "
        "Researchers/Officials can contribute new records below."
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Evidence Records", len(research_df))
    c2.metric("Research Themes", research_df["Theme"].nunique())
    c3.metric("Evidence Types", research_df["Type"].nunique())
    c4.metric("Regions Covered", research_df["Region"].nunique())

    if auth.is_logged_in():
        with st.expander("➕ Contribute a research record"):
            with st.form("add_research"):
                t_title = st.text_input("Title")
                t_type = st.selectbox("Type", ["Research Paper", "Policy Paper", "Case Study", "Technical Report"])
                t_theme = st.text_input("Theme")
                t_region = st.text_input("Region (state name or 'National')")
                t_year = st.number_input("Year", min_value=1990, max_value=2030, value=2026)
                t_summary = st.text_area("Summary")
                if st.form_submit_button("Submit record"):
                    if t_title and t_summary:
                        db.add_research_record(t_title, t_type, t_theme, t_region, int(t_year),
                                                t_summary, auth.current_user()["username"])
                        st.success("Record added. Refresh search to see it indexed.")
                        st.cache_data.clear()
                    else:
                        st.error("Title and summary are required.")
    else:
        st.caption("Log in as a Researcher or Official to contribute new research records.")

    st.divider()
    query = st.text_input("Search research evidence", placeholder="Try: climate resilient land use planning")

    f1, f2, f3 = st.columns(3)
    with f1:
        theme_filter = st.selectbox("Theme", ["All"] + sorted(research_df["Theme"].dropna().astype(str).unique().tolist()))
    with f2:
        type_filter = st.selectbox("Evidence Type", ["All"] + sorted(research_df["Type"].dropna().astype(str).unique().tolist()))
    with f3:
        region_filter = st.selectbox("Region", ["All"] + sorted(research_df["Region"].dropna().astype(str).unique().tolist()))

    valid_years = pd.to_numeric(research_df["Year"], errors="coerce").dropna()
    min_year = int(valid_years.min()) if not valid_years.empty else 2000
    max_year = int(valid_years.max()) if not valid_years.empty else 2026
    year_range = st.slider("Publication Year", min_value=min_year, max_value=max_year, value=(min_year, max_year))

    filtered = research_df.copy()
    filtered["Year"] = pd.to_numeric(filtered["Year"], errors="coerce")
    filtered = filtered[filtered["Year"].between(year_range[0], year_range[1])]
    if theme_filter != "All":
        filtered = filtered[filtered["Theme"] == theme_filter]
    if type_filter != "All":
        filtered = filtered[filtered["Type"] == type_filter]
    if region_filter != "All":
        filtered = filtered[filtered["Region"] == region_filter]

    if query.strip():
        all_results = ai_engine.search(query, research_df, vectorizer, matrix)
        filtered = filtered.merge(
            all_results[["Title", "Similarity", "Title_Boost", "Theme_Boost", "AI_Relevance", "Rank", "Relevance_Percent"]],
            on="Title", how="left",
        )
        filtered["AI_Relevance"] = filtered["AI_Relevance"].fillna(0)
        filtered["Relevance_Percent"] = filtered["Relevance_Percent"].fillna(0)
        filtered = filtered.sort_values(["AI_Relevance", "Year"], ascending=[False, False])
    else:
        filtered = filtered.sort_values(["Year"], ascending=False)

    filtered = filtered.head(25).reset_index(drop=True)

    st.divider()
    st.write(f"**{len(filtered)} evidence records displayed**")

    if filtered.empty:
        st.warning("No evidence records match the selected search and filters.")
    else:
        for _, row in filtered.iterrows():
            with st.container(border=True):
                hl, hr = st.columns([5, 1])
                with hl:
                    st.markdown(f"### {row['Title']}")
                    year_display = int(row["Year"]) if pd.notna(row["Year"]) else "N/A"
                    st.caption(f"{row['Type']} • {year_display} • {row['Theme']} • {row['Region']}")
                with hr:
                    if query.strip():
                        st.metric("Relevance", f"{row.get('Relevance_Percent', 0):.1f}%")
                st.write(row["Summary"])


elif page == "AI Intelligence":
    st.title("AI Research Intelligence Engine")
    st.caption("AI-assisted evidence retrieval, relevance ranking, and research synthesis.")

    corpus = ai_engine.build_corpus(research_df)
    vectorizer, matrix = ai_engine.build_engine(tuple(corpus.tolist()))

    api_key = st.session_state["claude_api_key"]
    if api_key:
        st.success("Claude synthesis is active — summaries below are LLM-generated and grounded in retrieved evidence.")
    else:
        st.info("Running in offline mode (TF-IDF + rule-based summary). Add an Anthropic API key in the sidebar for LLM-powered synthesis and follow-up Q&A.")

    query = st.text_area("Ask a research question",
                          placeholder="Example: How can climate vulnerability influence sustainable land-use planning?",
                          height=110)

    top_k = st.slider("Evidence records", min_value=3, max_value=min(10, len(research_df)),
                       value=min(6, len(research_df)))

    if query.strip():
        results = ai_engine.search(query, research_df, vectorizer, matrix, top_k=top_k)
        st.session_state["last_ai_results"] = results
        st.session_state["ai_chat_history"] = []

        st.divider()
        if results.empty:
            st.warning("No evidence could be retrieved.")
        else:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Records Retrieved", len(results))
            c2.metric("Top Relevance", f"{results.iloc[0]['Relevance_Percent']:.1f}%")
            c3.metric("Top Theme", results["Theme"].mode().iloc[0])
            c4.metric("Regions Covered", results["Region"].nunique())

            st.subheader("Ranked Evidence")
            for _, row in results.iterrows():
                with st.container(border=True):
                    left, right = st.columns([4, 1])
                    with left:
                        st.markdown(f"### #{int(row['Rank'])} — {row['Title']}")
                        st.caption(f"{row['Type']} • {row['Year']} • {row['Theme']} • {row['Region']}")
                        st.write(row["Summary"])
                        st.caption("Matching signals: " + ai_engine.matching_explanation(row))
                    with right:
                        st.metric("AI Relevance", f"{row['Relevance_Percent']:.1f}%")

            st.divider()
            st.subheader("Research Synthesis")
            with st.spinner("Synthesizing evidence..."):
                synthesis = ai_engine.claude_synthesis(query, results, api_key) if api_key else ai_engine.rule_based_synthesis(results)
            st.write(synthesis)

            if api_key:
                st.subheader("Ask a follow-up question")
                followup = st.text_input("Ask about the retrieved evidence", key="followup_q")
                if st.button("Ask Claude"):
                    with st.spinner("Thinking..."):
                        answer = ai_engine.claude_answer_followup(followup, results, api_key)
                    st.session_state["ai_chat_history"].append({"role": "user", "content": followup})
                    st.session_state["ai_chat_history"].append({"role": "assistant", "content": answer})

                for turn in st.session_state["ai_chat_history"]:
                    role_label = "🧑 You" if turn["role"] == "user" else "🤖 Claude"
                    st.markdown(f"**{role_label}:** {turn['content']}")

            st.subheader("Evidence Themes")
            theme_counts = results["Theme"].value_counts().rename_axis("Theme").reset_index(name="Evidence Records")
            fig = px.bar(theme_counts, x="Evidence Records", y="Theme", orientation="h", title="Themes Represented")
            st.plotly_chart(fig, use_container_width=True)

            st.subheader("Potentially Relevant States")
            result_regions = set(results["Region"].astype(str))
            relevant_states = land_df[land_df["State"].isin(result_regions)][
                ["State", "Composite_Risk", "Risk_Level", "Priority"]
            ].sort_values("Composite_Risk", ascending=False)
            if not relevant_states.empty:
                st.dataframe(relevant_states, use_container_width=True, hide_index=True)
            else:
                st.info("No direct state match found between retrieved research regions and the land dataset.")
    else:
        st.subheader("Try the Research Engine")
        for example in [
            "climate resilient land use planning", "digital land records governance",
            "urban expansion agricultural land", "land dispute resolution",
            "remote sensing land monitoring", "infrastructure and land pressure",
        ]:
            st.markdown(f"- `{example}`")


elif page == "Analytics":
    st.title("Policy Impact Analytics")
    st.caption("Explore relationships among land governance, climate vulnerability, urbanization and infrastructure pressure.")

    x_axis = st.selectbox("X-axis", list(INDICATORS.keys())[:-1])
    y_axis = st.selectbox("Y-axis", list(INDICATORS.keys())[:-1], index=2)

    fig = px.scatter(land_df, x=INDICATORS[x_axis], y=INDICATORS[y_axis], hover_name="State",
                      size="Composite_Risk", color="Risk_Level", trendline="ols",
                      title=f"{x_axis} vs {y_axis}")
    st.plotly_chart(fig, use_container_width=True)

    correlation = land_df[[
        "Land_Governance_Index", "Urban_Expansion", "Agri_Land_Percent",
        "Climate_Vulnerability", "Dispute_Density", "Infrastructure_Pressure", "Composite_Risk",
    ]].corr()

    st.subheader("Indicator Correlation Matrix")
    fig = px.imshow(correlation, text_auto=".2f", aspect="auto", title="Land Governance Indicator Correlations")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Priority Intervention Drivers")
    driver_data = [{"State": r["State"], "Dominant Driver": dominant_driver(r), "Composite Risk": r["Composite_Risk"]}
                   for _, r in land_df.iterrows()]
    driver_summary = pd.DataFrame(driver_data)["Dominant Driver"].value_counts().rename_axis("Driver").reset_index(name="States")
    fig = px.bar(driver_summary, x="Driver", y="States", title="Dominant Intervention Driver Across States")
    st.plotly_chart(fig, use_container_width=True)


elif page == "Policy Lab":
    st.title("Policy Simulation Lab")
    auth.require_role("Researcher", "Official")

    st.caption("Run transparent scenario simulations by changing the relative importance of major land-governance pressures.")
    st.info("This simulator changes the weighting of existing indicators; it does not predict real-world policy outcomes.")

    c1, c2 = st.columns(2)
    with c1:
        governance_weight = st.slider("Governance Risk Weight", 0.0, 1.0, 0.25, 0.05)
        climate_weight = st.slider("Climate Vulnerability Weight", 0.0, 1.0, 0.25, 0.05)
        urban_weight = st.slider("Urban Expansion Weight", 0.0, 1.0, 0.20, 0.05)
    with c2:
        dispute_weight = st.slider("Land Dispute Weight", 0.0, 1.0, 0.15, 0.05)
        infrastructure_weight = st.slider("Infrastructure Pressure Weight", 0.0, 1.0, 0.15, 0.05)

    total_weight = governance_weight + climate_weight + urban_weight + dispute_weight + infrastructure_weight

    if total_weight == 0:
        st.error("At least one policy weight must be greater than zero.")
    else:
        simulated = land_df[["State", "Land_Governance_Index", "Climate_Vulnerability",
                              "Urban_Expansion", "Dispute_Density", "Infrastructure_Pressure"]].copy()
        simulated["Scenario_Risk"] = (
            (100 - simulated["Land_Governance_Index"]) * governance_weight
            + simulated["Climate_Vulnerability"] * climate_weight
            + simulated["Urban_Expansion"] * urban_weight
            + simulated["Dispute_Density"] * dispute_weight
            + simulated["Infrastructure_Pressure"] * infrastructure_weight
        ) / total_weight
        simulated["Scenario_Risk"] = simulated["Scenario_Risk"].round(2)
        simulated["Scenario_Level"] = simulated["Scenario_Risk"].apply(risk_level)

        st.divider()
        top_state = simulated.sort_values("Scenario_Risk", ascending=False).iloc[0]
        low_state = simulated.sort_values("Scenario_Risk", ascending=True).iloc[0]

        c1, c2, c3 = st.columns(3)
        c1.metric("Scenario Avg Risk", f"{simulated['Scenario_Risk'].mean():.1f}")
        c2.metric("Highest Scenario Risk", top_state["State"])
        c3.metric("Lowest Scenario Risk", low_state["State"])

        fig = px.bar(simulated.sort_values("Scenario_Risk", ascending=False), x="Scenario_Risk", y="State",
                     color="Scenario_Level", orientation="h", title="Simulated State Risk Under Current Policy Weights")
        fig.update_layout(height=700)
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(simulated.sort_values("Scenario_Risk", ascending=False), use_container_width=True, hide_index=True)


elif page == "Innovation Portal":
    st.title("Innovation Portal")
    st.caption("Hackathons, research grants, pilot projects and knowledge competitions supporting land governance innovation.")

    items = db.load_innovation_items()

    if auth.has_role("Official"):
        with st.expander("➕ Post a new opportunity (Official)"):
            with st.form("add_item"):
                i_category = st.selectbox("Category", ["Hackathon", "Grant", "Pilot Project", "Knowledge Competition"])
                i_title = st.text_input("Title")
                i_org = st.text_input("Organization")
                i_deadline = st.date_input("Deadline")
                i_desc = st.text_area("Description")
                if st.form_submit_button("Publish"):
                    if i_title and i_desc:
                        db.add_innovation_item(i_category, i_title, i_desc, i_org, str(i_deadline),
                                                auth.current_user()["username"])
                        st.success("Opportunity published.")
                        st.rerun()
                    else:
                        st.error("Title and description are required.")

    st.divider()

    if items.empty:
        st.info("No opportunities posted yet.")
    else:
        cat_filter = st.selectbox("Filter by category", ["All"] + sorted(items["category"].unique().tolist()))
        view = items if cat_filter == "All" else items[items["category"] == cat_filter]

        for _, item in view.iterrows():
            with st.container(border=True):
                hl, hr = st.columns([4, 1])
                with hl:
                    st.markdown(f"### {item['title']}")
                    st.caption(f"{item['category']} • {item['organization']} • Deadline: {item['deadline']}")
                    st.write(item["description"])
                with hr:
                    status_color = {"Open": "🟢", "Ongoing": "🟠", "Closed": "🔴"}.get(item["status"], "⚪")
                    st.metric("Status", f"{status_color} {item['status']}")

                if auth.has_role("Official"):
                    new_status = st.selectbox(
                        "Update status", ["Open", "Ongoing", "Closed"],
                        index=["Open", "Ongoing", "Closed"].index(item["status"]),
                        key=f"status_{item['id']}",
                    )
                    if new_status != item["status"]:
                        if st.button("Save status", key=f"save_status_{item['id']}"):
                            db.update_innovation_item_status(item["id"], new_status)
                            st.rerun()

                if auth.is_logged_in():
                    with st.expander("Submit a proposal for this opportunity"):
                        with st.form(f"submit_{item['id']}"):
                            s_title = st.text_input("Proposal title", key=f"s_title_{item['id']}")
                            s_desc = st.text_area("Proposal description", key=f"s_desc_{item['id']}")
                            if st.form_submit_button("Submit proposal"):
                                if s_title and s_desc:
                                    db.add_innovation_submission(
                                        item["id"], s_title, s_desc, item["category"],
                                        auth.current_user()["username"],
                                    )
                                    st.success("Proposal submitted.")
                                else:
                                    st.error("Both fields are required.")

    if auth.is_logged_in():
        st.divider()
        st.subheader("My submissions")
        all_subs = db.load_innovation_submissions()
        my_subs = all_subs[all_subs["submitted_by"] == auth.current_user()["username"]]
        if my_subs.empty:
            st.caption("You haven't submitted any proposals yet.")
        else:
            st.dataframe(my_subs[["title", "category", "status", "created_at"]], use_container_width=True, hide_index=True)

    if auth.has_role("Official"):
        st.divider()
        st.subheader("Review all submissions (Official)")
        all_subs = db.load_innovation_submissions()
        if all_subs.empty:
            st.caption("No submissions yet.")
        else:
            for _, sub in all_subs.iterrows():
                with st.container(border=True):
                    st.markdown(f"**{sub['title']}** — submitted by `{sub['submitted_by']}`")
                    st.write(sub["description"])
                    new_sub_status = st.selectbox(
                        "Review status", ["Submitted", "Under Review", "Accepted", "Rejected"],
                        index=["Submitted", "Under Review", "Accepted", "Rejected"].index(sub["status"]),
                        key=f"sub_status_{sub['id']}",
                    )
                    if new_sub_status != sub["status"]:
                        if st.button("Save review", key=f"save_sub_{sub['id']}"):
                            db.update_submission_status(sub["id"], new_sub_status)
                            st.rerun()


elif page == "Reports":
    st.title("Decision Reports")
    st.caption("Generate a concise intelligence brief from the current prototype dataset.")

    selected_state = st.selectbox("Select state", sorted(land_df["State"].tolist()))
    row = land_df[land_df["State"] == selected_state].iloc[0]
    driver = dominant_driver(row)

    report_text = f"""BHOOMINITI AI — LAND GOVERNANCE INTELLIGENCE BRIEF

State: {selected_state}

Governance Index: {row['Land_Governance_Index']:.1f}
Composite Risk: {row['Composite_Risk']:.1f}
Risk Level: {row['Risk_Level']}
Priority Rank: #{int(row['Priority'])}

INDICATOR PROFILE
Urban Expansion: {row['Urban_Expansion']:.1f}
Agricultural Land %: {row['Agri_Land_Percent']:.1f}
Climate Vulnerability: {row['Climate_Vulnerability']:.1f}
Land Dispute Density: {row['Dispute_Density']:.1f}
Infrastructure Pressure: {row['Infrastructure_Pressure']:.1f}

DOMINANT DRIVER
{driver}

POLICY DIRECTION
{intervention_for_driver(driver)}

DATA NOTICE
This brief is generated from synthetic/demo data created for the BhoomiNiti AI prototype.
It does not represent official government statistics.
Generated by: {auth.current_user()['full_name'] if auth.is_logged_in() else 'Guest'}
"""

    st.text_area("Generated Intelligence Brief", report_text, height=480)
    st.download_button(
        "Download Intelligence Brief", data=report_text,
        file_name=f"{selected_state.replace(' ', '_')}_BhoomiNiti_Intelligence_Brief.txt",
        mime="text/plain",
    )
