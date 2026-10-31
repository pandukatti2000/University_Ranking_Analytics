import streamlit as st
import pandas as pd
from frontend.components.theme import (
    apply_custom_css,
    render_scale_warning,
    render_metric_card
)
from frontend.components.charts import (
    create_radar_chart,
    create_bar_chart
)
from frontend.components.api_client import (
    get_universities_list,
    get_ranking_systems_and_criteria,
    get_comparison_data
)

def render_comparison():
    apply_custom_css()
    st.title("⚖️ University Comparative Intelligence")
    st.markdown("Perform multi-institutional benchmarking across standardized criteria, demographic indicators, and ranking systems.")
    
    render_scale_warning()
    
    unis = get_universities_list(limit=1500)
    uni_name_to_id = {u["university_name"]: u["id"] for u in unis}
    uni_names = list(uni_name_to_id.keys())
    
    # Default selection: Harvard, MIT, Stanford, Oxford, Cambridge
    defaults = [name for name in ["Harvard University", "Massachusetts Institute of Technology (MIT)", "Stanford University", "University of Oxford", "University of Cambridge"] if name in uni_names]
    if not defaults:
        defaults = uni_names[:3] if len(uni_names) >= 3 else uni_names
        
    col_sel, col_sys, col_yr = st.columns([3, 2, 1])
    
    with col_sel:
        selected_unis = st.multiselect(
            "Select Universities to Compare (2–6 recommended):",
            options=uni_names,
            default=defaults
        )
        
    systems_data = get_ranking_systems_and_criteria()
    system_options = {s["system_name"]: s["id"] for s in systems_data}
    
    with col_sys:
        selected_sys_name = st.selectbox(
            "Ranking System:",
            options=list(system_options.keys()),
            index=0
        )
        selected_sys_id = system_options[selected_sys_name]
        
    # Available years based on ranking system
    year_map = {
        1: list(range(2011, 2017)), # THE: 2011-2016
        2: list(range(2005, 2016)), # Shanghai: 2005-2015
        3: list(range(2012, 2016)), # CWUR: 2012-2015
    }
    avail_years = year_map.get(selected_sys_id, [2015])
    
    with col_yr:
        selected_year = st.selectbox(
            "Year:",
            options=sorted(avail_years, reverse=True),
            index=0
        )
        
    if not selected_unis or len(selected_unis) < 2:
        st.info("💡 Please select at least 2 universities to enable comparative benchmarking.")
        return
        
    selected_ids = [uni_name_to_id[name] for name in selected_unis]
    
    # Fetch comparison data
    with st.spinner("Compiling multi-institutional telemetry..."):
        comp_data = get_comparison_data(
            university_ids=selected_ids,
            system_id=selected_sys_id
        )
        
    institutions = comp_data.get("universities", [])
    if not institutions:
        st.warning("No recorded observations found for the selected institutions under this system.")
        return
        
    # Scale explanation banner for active system
    if selected_sys_id == 3:
        st.info("ℹ️ **Active Metric: CWUR Ordinal Ranks (1–1,000)** — Lower numbers indicate higher global standing (except Criterion 21 'Total CWUR' which is a 43–100 score).")
    else:
        st.info("ℹ️ **Active Metric: Normalized Scores (0–100)** — Higher values indicate stronger relative performance.")
        
    # Prepare comparison dataframe for charts
    criteria_rows = []
    for inst in institutions:
        u_name = inst["university_name"]
        for score_point in inst.get("scores", []):
            if score_point.get("year") == selected_year and score_point.get("value") is not None:
                criteria_rows.append({
                    "university_name": u_name,
                    "criteria_name": score_point.get("criteria_name"),
                    "score": float(score_point.get("value"))
                })
                
    df_crit = pd.DataFrame(criteria_rows)
    
    tab_charts, tab_demographics, tab_matrix = st.tabs(["📊 Criteria Benchmarking", "👥 Demographic Profiles", "📋 Detailed Data Matrix"])
    
    with tab_charts:
        if not df_crit.empty:
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("Criteria Radar Benchmark")
                # For radar chart, THE and ARWU work best as normalized 0-100 scores
                if selected_sys_id in [1, 2]:
                    fig_radar = create_radar_chart(
                        df_crit,
                        categories_col="criteria_name",
                        value_col="score",
                        group_col="university_name",
                        title=f"{selected_sys_name} ({selected_year}) — Dimension Profiling"
                    )
                    st.plotly_chart(fig_radar, use_container_width=True)
                else:
                    st.markdown("*Radar polygon visualization is reserved for normalized 0–100 scores (THE & ARWU).*")
                    fig_bar_cwur = create_bar_chart(
                        df_crit,
                        x_col="criteria_name",
                        y_col="score",
                        color_col="university_name",
                        title=f"{selected_sys_name} ({selected_year}) — Criteria Rank/Score Comparison"
                    )
                    st.plotly_chart(fig_bar_cwur, use_container_width=True)
                    
            with c2:
                st.subheader("Side-by-Side Dimension Scores")
                fig_bar = create_bar_chart(
                    df_crit,
                    x_col="criteria_name",
                    y_col="score",
                    color_col="university_name",
                    title="Component Comparison",
                    barmode="group"
                )
                st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.warning(f"No criteria scores recorded for these universities in {selected_year}. Try another year or system.")
            
    with tab_demographics:
        st.subheader(f"Demographic Indicators ({selected_year})")
        demo_rows = []
        for inst in institutions:
            demos = inst.get("demographics") or []
            demo_yr = next((d for d in demos if d.get("year") == selected_year), None)
            if demo_yr:
                demo_rows.append({
                    "University": inst["university_name"],
                    "Country": inst["country_name"],
                    "Total Students": f"{demo_yr.get('num_students', 0):,}" if demo_yr.get('num_students') else "N/A",
                    "Student-to-Staff Ratio": f"{demo_yr.get('student_staff_ratio', 0):.1f}:1" if demo_yr.get('student_staff_ratio') else "N/A",
                    "International Students": f"{demo_yr.get('pct_international_students', 0):.1f}%" if demo_yr.get('pct_international_students') is not None else "N/A",
                    "Female Students": f"{demo_yr.get('pct_female_students', 0):.1f}%" if demo_yr.get('pct_female_students') is not None else "N/A"
                })
            else:
                demo_rows.append({
                    "University": inst["university_name"],
                    "Country": inst["country_name"],
                    "Total Students": "Missing (Not in THE demographic subset)",
                    "Student-to-Staff Ratio": "N/A",
                    "International Students": "N/A",
                    "Female Students": "N/A"
                })
                
        st.dataframe(pd.DataFrame(demo_rows), use_container_width=True)
        st.caption("📌 Note: Student demographic metrics are available exclusively for the 245 institutions surveyed by Times Higher Education (2011–2016).")
        
    with tab_matrix:
        st.subheader("Raw Metric Scorecard")
        if not df_crit.empty:
            pivot_df = df_crit.pivot(index="university_name", columns="criteria_name", values="score").reset_index()
            st.dataframe(pivot_df, use_container_width=True)
        else:
            st.info("No scorecard matrix records available.")

if __name__ == "__main__":
    render_comparison()
