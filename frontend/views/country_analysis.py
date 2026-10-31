import streamlit as st
import pandas as pd
from frontend.components.theme import (
    apply_custom_css,
    render_scale_warning,
    render_metric_card
)
from frontend.components.charts import (
    create_bar_chart,
    create_choropleth_map
)
from frontend.components.api_client import (
    get_countries_list,
    get_country_analytics
)

def render_country_analysis():
    apply_custom_css()
    st.title("🌍 Country Institutional Intelligence")
    st.markdown("Examine geographic concentration, national representation across ranking systems, and cross-border distributions.")
    
    render_scale_warning()
    
    countries = get_countries_list()
    country_map = {c["country_name"]: (c.get("country_id") or c.get("id")) for c in countries if "country_name" in c}
    country_names = ["All Countries (Global Benchmark)"] + sorted(list(country_map.keys()))
    
    col_c, col_info = st.columns([2, 3])
    with col_c:
        selected_c_name = st.selectbox(
            "Select Target Nation:",
            options=country_names,
            index=0
        )
        
    selected_c_id = None if selected_c_name.startswith("All") else country_map[selected_c_name]
    
    data = get_country_analytics(country_id=selected_c_id)
    
    if selected_c_id is None:
        # Global view: data is list of CountryCount dicts
        benchmarks = pd.DataFrame(data)
        
        st.subheader("Global Institutional Density by Nation")
        if not benchmarks.empty:
            c1, c2 = st.columns(2)
            with c1:
                fig_top = create_bar_chart(
                    benchmarks.head(15),
                    x_col="country_name",
                    y_col="university_count",
                    color_col="country_name",
                    title="Top 15 Nations by Total Ranked Institutions",
                    orientation="v"
                )
                st.plotly_chart(fig_top, use_container_width=True)
                
            with c2:
                fig_map = create_choropleth_map(
                    benchmarks,
                    locations_col="country_name",
                    color_col="university_count",
                    title="Global Institutional Distribution"
                )
                st.plotly_chart(fig_map, use_container_width=True)
                
            st.markdown("---")
            st.subheader("National Benchmarking Data Matrix")
            st.dataframe(
                benchmarks.rename(columns={
                    "country_id": "Country ID",
                    "country_name": "Country",
                    "university_count": "Total Universities"
                }),
                use_container_width=True
            )
    else:
        # Specific country deep-dive: data is CountryDetailResponse dict
        detail = data if isinstance(data, dict) else {}
        st.subheader(f"National Profile: {detail.get('country_name', selected_c_name)}")
        
        c1, c2 = st.columns(2)
        with c1:
            render_metric_card("Total Universities", str(detail.get("total_universities", 0)), "National catalogue", "🏛️")
        with c2:
            sys_reps = detail.get("system_representation", [])
            the_unis = next((s["institution_count"] for s in sys_reps if "Times" in s.get("system_name", "")), 0)
            render_metric_card("THE Coverage", str(the_unis), "Times Higher Education surveyed", "📘")
            
        st.markdown("---")
        
        # System Representation breakdown
        if sys_reps:
            st.subheader("Representation Across Ranking Systems")
            df_sys = pd.DataFrame(sys_reps)
            fig_sys = create_bar_chart(
                df_sys,
                x_col="system_name",
                y_col="institution_count",
                color_col="system_name",
                title=f"{detail.get('country_name')} Institutions Present in Each System"
            )
            st.plotly_chart(fig_sys, use_container_width=True)
            
        # Universities list
        st.subheader(f"Institutions in {detail.get('country_name')}")
        unis = detail.get("universities", [])
        if unis:
            df_unis = pd.DataFrame(unis)
            st.dataframe(
                df_unis.rename(columns={"university_id": "ID", "university_name": "University Name"}),
                use_container_width=True,
                height=350
            )
        else:
            st.info("No individual institutions listed for this nation.")

if __name__ == "__main__":
    render_country_analysis()
