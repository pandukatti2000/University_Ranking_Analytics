import streamlit as st
import pandas as pd
from frontend.components.theme import (
    apply_custom_css,
    render_non_causal_notice,
    render_metric_card
)
from frontend.components.charts import (
    create_bar_chart
)
from frontend.components.api_client import get_demographics_analytics

def render_demographics():
    apply_custom_css()
    st.title("👥 Institutional Demographics & Non-Causal Patterns")
    st.markdown("Investigate structural student demographics — student enrollments, faculty ratios, internationalization, and gender parity.")
    
    render_non_causal_notice()
    
    with st.spinner("Compiling demographic telemetry..."):
        demo_data = get_demographics_analytics()
        
    c1, c2, c3 = st.columns(3)
    with c1:
        render_metric_card("Total Demographic Records", f"{demo_data.get('total_observations', 0):,}", "Longitudinal observations", "📊")
    with c2:
        render_metric_card("Surveyed Institutions", f"{demo_data.get('unique_universities', 0):,}", "Distinct universities in THE subset", "🏛️")
    with c3:
        years = demo_data.get("years_covered", [2011, 2016])
        yr_str = f"{min(years)} – {max(years)}" if years else "2011 – 2016"
        render_metric_card("Surveyed Period", yr_str, "Annual cohort reporting", "📅")
        
    st.markdown("""
    <div class="callout-box callout-info">
        ℹ️ <strong>Demographic Coverage Scope:</strong> Demographics are recorded exclusively for institutions surveyed in the Times Higher Education survey (2011–2016), covering 245 distinct universities. 1,002 universities in the catalog have no demographic records.
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Distributions table
    st.subheader("Demographic Indicator Distributions")
    dists = demo_data.get("distributions", [])
    if dists:
        df_dist = pd.DataFrame(dists)
        st.dataframe(
            df_dist.rename(columns={
                "metric_name": "Indicator",
                "count": "Observations",
                "mean": "Mean",
                "median": "Median",
                "min": "Min",
                "max": "Max",
                "unit": "Unit"
            }),
            use_container_width=True
        )
        
        fig_bar = create_bar_chart(
            df_dist,
            x_col="metric_name",
            y_col="mean",
            color_col="metric_name",
            title="Mean Values Across Demographic Indicators"
        )
        st.plotly_chart(fig_bar, use_container_width=True)
        
    st.markdown("---")
    
    # Non-Causal Associations Section
    st.subheader("Non-Causal Associations with Ranking Indicators")
    st.markdown("Empirical Pearson correlation coefficients between demographic metrics and performance criteria.")
    
    corrs = demo_data.get("correlations", [])
    if corrs:
        df_corr = pd.DataFrame(corrs)
        st.dataframe(
            df_corr[[
                "demographic_field", "criteria_name", "sample_size", "pearson_r", "interpretation"
            ]].rename(columns={
                "demographic_field": "Demographic Field",
                "criteria_name": "Ranking Criterion",
                "sample_size": "Sample Size",
                "pearson_r": "Pearson r",
                "interpretation": "Interpretation"
            }),
            use_container_width=True
        )
    else:
        st.info("No correlation pairs computed.")

if __name__ == "__main__":
    render_demographics()
