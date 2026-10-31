import streamlit as st
import pandas as pd
from frontend.components.theme import (
    apply_custom_css,
    render_scale_warning,
    render_non_causal_notice,
    render_metric_card
)
from frontend.components.charts import (
    create_bar_chart
)
from frontend.components.api_client import (
    get_ranking_systems_and_criteria,
    get_criteria_analytics
)

def render_criteria_analysis():
    apply_custom_css()
    st.title("🔬 Criteria Dynamics, Trade-offs & Distributions")
    st.markdown("Investigate structural distributions across ranking criteria (e.g., Teaching vs. Research vs. Citations) and evaluate score metrics.")
    
    render_scale_warning()
    render_non_causal_notice()
    
    systems_data = get_ranking_systems_and_criteria()
    system_map = {s["system_name"]: s["id"] for s in systems_data}
    
    col_sys, col_dummy = st.columns([2, 3])
    with col_sys:
        selected_sys = st.selectbox(
            "Select Ranking System for Criterion Exploration:",
            options=list(system_map.keys()),
            index=0
        )
        selected_sys_id = system_map[selected_sys]
        
    with st.spinner("Analyzing criteria distributions & metrics..."):
        crit_data = get_criteria_analytics(ranking_system_id=selected_sys_id)
        
    criteria_stats = pd.DataFrame(crit_data)
    
    st.subheader(f"Criterion Statistical Summary: {selected_sys}")
    if not criteria_stats.empty:
        if "std_dev" in criteria_stats.columns and "std" not in criteria_stats.columns:
            criteria_stats["std"] = criteria_stats["std_dev"]
        elif "std" in criteria_stats.columns and "std_dev" not in criteria_stats.columns:
            criteria_stats["std_dev"] = criteria_stats["std"]
            
        display_cols = [c for c in ["criteria_name", "count", "mean", "median", "std", "min", "q25", "q75", "max"] if c in criteria_stats.columns]
        st.dataframe(
            criteria_stats[display_cols].rename(columns={
                "criteria_name": "Ranking Criterion",
                "count": "Observations",
                "mean": "Mean",
                "median": "Median",
                "std": "Std Dev",
                "std_dev": "Std Dev",
                "min": "Min",
                "q25": "25th %tile",
                "q75": "75th %tile",
                "max": "Max"
            }),
            use_container_width=True
        )
        
        st.markdown("---")
        
        # Visualizations: Criteria Distributions
        st.subheader("Distribution & Variability Analysis")
        c1, c2 = st.columns(2)
        
        with c1:
            fig_bar = create_bar_chart(
                criteria_stats,
                x_col="criteria_name",
                y_col="mean",
                color_col="criteria_name",
                title=f"Mean Scores Across {selected_sys} Dimensions"
            )
            st.plotly_chart(fig_bar, use_container_width=True)
                
        with c2:
            std_col = "std" if "std" in criteria_stats.columns else "std_dev"
            fig_std = create_bar_chart(
                criteria_stats,
                x_col="criteria_name",
                y_col=std_col,
                color_col="criteria_name",
                title=f"Score Dispersion (Std Dev) by Dimension"
            )
            st.plotly_chart(fig_std, use_container_width=True)
    else:
        st.info("No criteria records found for this ranking authority.")

if __name__ == "__main__":
    render_criteria_analysis()
