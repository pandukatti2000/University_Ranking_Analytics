import streamlit as st
import pandas as pd
from frontend.components.theme import (
    apply_custom_css,
    render_metric_card,
    render_scale_warning
)
from frontend.components.charts import (
    create_bar_chart,
    create_treemap,
    create_choropleth_map
)
from frontend.components.api_client import get_overview_data, get_universities_list

def render_overview():
    apply_custom_css()
    
    st.title("🏛️ Executive Overview & Global Footprint")
    st.markdown("Macro-level analytical synthesis across 3 premier global university ranking systems.")
    
    render_scale_warning()
    
    overview = get_overview_data()
    
    # 5 KPI Metric Cards
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        render_metric_card("Total Universities", f"{overview.get('total_universities', 0):,}", "Catalog institutions", "🏛️")
    with col2:
        render_metric_card("Countries", f"{overview.get('total_countries', 0):,}", "Global coverage", "🌍")
    with col3:
        render_metric_card("Years Covered", f"{overview.get('min_year', 2005)} – {overview.get('max_year', 2016)}", "12-year longitudinal span", "📅")
    with col4:
        render_metric_card("Ranking Records", f"{overview.get('total_ranking_records', 0):,}", "Empirical observations", "📊")
    with col5:
        render_metric_card("Triple-Ranked", f"{overview.get('universities_in_all_systems', 0):,}", "Present in THE, ARWU & CWUR", "🎯")
        
    st.markdown("---")
    
    # Visualizations Row 1: Global Map & Treemap
    col_map, col_tree = st.columns([3, 2])
    
    country_dist = pd.DataFrame(overview.get("top_countries", []))
    
    with col_map:
        st.subheader("Global University Distribution")
        if not country_dist.empty:
            fig_map = create_choropleth_map(
                country_dist,
                locations_col="country_name",
                color_col="university_count",
                title="Institutional Density by Nation"
            )
            st.plotly_chart(fig_map, use_container_width=True)
            
    with col_tree:
        st.subheader("Top Contributing Nations")
        if not country_dist.empty:
            fig_tree = create_treemap(
                country_dist.head(25),
                path=["country_name"],
                values_col="university_count",
                title="Top Nations by University Count"
            )
            st.plotly_chart(fig_tree, use_container_width=True)
            
    # Visualizations Row 2: Ranking Systems Coverage & Multi-System Overlap
    st.subheader("Ranking System Methodological Profiles")
    sys_col1, sys_col2 = st.columns([3, 2])
    
    with sys_col1:
        sys_coverage = pd.DataFrame(overview.get("ranking_systems", []))
        if not sys_coverage.empty:
            fig_bar = create_bar_chart(
                sys_coverage,
                x_col="system_name",
                y_col="total_institutions",
                color_col="system_name",
                title="Total Ranked Institutions per System"
            )
            st.plotly_chart(fig_bar, use_container_width=True)
            
    with sys_col2:
        st.markdown("""
        ### System Comparison Matrix
        | Ranking System | Metric Basis | Scale | Coverage |
        | :--- | :--- | :--- | :--- |
        | **Times Higher Education (THE)** | Criteria Scores | 0–100 (Higher is Better) | 2011–2016 (245 unis) |
        | **Shanghai Ranking (ARWU)** | Criteria Scores | 0–100 (Right-Skewed) | 2005–2015 (658 unis) |
        | **CWUR** | Rank Ordinals (14-20) & Score (21) | 1–1,000 (Lower is Better) | 2012–2015 (1,024 unis) |
        
        > **Data Integrity Rule:** Scores and rank positions are held in strict isolation and are never combined into invalid compound averages.
        """)
        
    st.markdown("---")
    
    # Institution Catalog Explorer
    st.subheader("Institutional Directory Explorer")
    unis = get_universities_list(limit=1500)
    if unis:
        df_unis = pd.DataFrame(unis)
        search_query = st.text_input("🔍 Search Universities or Countries:", placeholder="Type 'Harvard', 'United Kingdom', etc.")
        if search_query:
            df_filtered = df_unis[
                df_unis["university_name"].str.contains(search_query, case=False, na=False) |
                df_unis["country_name"].str.contains(search_query, case=False, na=False)
            ]
        else:
            df_filtered = df_unis
            
        st.dataframe(
            df_filtered.rename(columns={"id": "ID", "university_name": "University Name", "country_name": "Country"}),
            use_container_width=True,
            height=300
        )
        
        csv_data = df_filtered.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Directory CSV",
            data=csv_data,
            file_name="university_directory.csv",
            mime="text/csv"
        )

if __name__ == "__main__":
    render_overview()
