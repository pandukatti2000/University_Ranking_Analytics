import streamlit as st
import pandas as pd
from frontend.components.theme import (
    apply_custom_css,
    render_scale_warning,
    render_metric_card
)
from frontend.components.charts import (
    create_trend_line_chart,
    create_bar_chart
)
from frontend.components.api_client import (
    get_universities_list,
    get_ranking_systems_and_criteria,
    get_historical_trends
)

def render_trends():
    apply_custom_css()
    st.title("📈 Longitudinal Ranking Trajectories & Momentum")
    st.markdown("Track institutional performance over 12 years (2005–2016), discover strongest gainers, and detect systemic score trends.")
    
    render_scale_warning()
    
    unis = get_universities_list(limit=1500)
    uni_name_to_id = {u["university_name"]: u["id"] for u in unis}
    uni_names = list(uni_name_to_id.keys())
    
    # Systems and Criteria
    systems_data = get_ranking_systems_and_criteria()
    crit_options = {}
    for sys_obj in systems_data:
        sys_name = sys_obj["system_name"]
        for c in sys_obj.get("criteria", []):
            crit_options[f"[{sys_name}] {c['criteria_name']}"] = c["id"]
            
    col_u, col_crit = st.columns([3, 2])
    
    with col_u:
        defaults = [n for n in ["Harvard University", "University of Oxford", "University of Cambridge", "Stanford University"] if n in uni_names]
        selected_unis = st.multiselect(
            "Select Universities for Longitudinal Tracking:",
            options=uni_names,
            default=defaults
        )
        
    with col_crit:
        crit_keys = list(crit_options.keys())
        if not crit_keys:
            st.warning("No ranking criteria found in catalog.")
            return
        default_crit_idx = 0
        for i, k in enumerate(crit_keys):
            if "Total Times" in k:
                default_crit_idx = i
                break
        selected_crit_label = st.selectbox(
            "Select Ranking Criterion:",
            options=crit_keys,
            index=default_crit_idx
        )
        if not selected_crit_label or selected_crit_label not in crit_options:
            st.warning("Please select a ranking criterion.")
            return
        selected_crit_id = crit_options[selected_crit_label]
        
    # Check if criterion is a CWUR rank (14 to 20) where lower is better
    is_rank = (14 <= selected_crit_id <= 20)
    if is_rank:
        st.info("ℹ️ **Ordinal Rank Metric:** Lower numerical rank positions represent higher global standing. Y-axis is inverted accordingly.")
    else:
        st.info("ℹ️ **Normalized Score Metric:** Higher scores (0–100) represent stronger performance.")
        
    if not selected_unis:
        st.info("💡 Please select at least one university to render longitudinal trajectories.")
        return
        
    selected_ids = [uni_name_to_id[name] for name in selected_unis]
    
    with st.spinner("Fetching historical time-series..."):
        trends_data = get_historical_trends(
            university_ids=selected_ids,
            ranking_criteria_id=selected_crit_id
        )
        
    # Multi-series line chart
    time_series = []
    for s in trends_data.get("trends", []):
        u_name = s["university_name"]
        for pt in s.get("data_points", []):
            if pt.get("score") is not None:
                time_series.append({
                    "university_name": u_name,
                    "year": pt.get("year"),
                    "score": float(pt.get("score"))
                })
                
    if time_series:
        df_ts = pd.DataFrame(time_series)
        fig_trend = create_trend_line_chart(
            df_ts,
            x_col="year",
            y_col="score",
            color_col="university_name",
            title=f"Historical Trajectory: {selected_crit_label}",
            y_label="Rank Position" if is_rank else "Score (0-100)",
            inverted_y=is_rank
        )
        st.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.warning("No historical observations recorded for the selected institutions and criterion.")
        
    st.markdown("---")
    
    # Top Movers Section
    st.subheader("🎯 Institutional Momentum: Top Movers & Decliners")
    st.markdown("Annual delta analysis identifying institutions with the greatest upward surge or downward drift under this criterion.")
    
    top_pos = trends_data.get("top_movers_positive", [])
    top_neg = trends_data.get("top_movers_negative", [])
    
    c_gainers, c_decliners = st.columns(2)
    with c_gainers:
        st.markdown("#### 🚀 Top Positive Momentum")
        if top_pos:
            df_gainers = pd.DataFrame(top_pos)
            st.dataframe(
                df_gainers[["university_name", "country_name", "start_year", "end_year", "absolute_change", "percent_change"]].rename(columns={
                    "university_name": "University",
                    "country_name": "Country",
                    "start_year": "Start Year",
                    "end_year": "End Year",
                    "absolute_change": "Delta",
                    "percent_change": "% Change"
                }),
                use_container_width=True
            )
        else:
            st.info("No positive movers recorded.")
            
    with c_decliners:
        st.markdown("#### 🔻 Top Negative Momentum")
        if top_neg:
            df_decliners = pd.DataFrame(top_neg)
            st.dataframe(
                df_decliners[["university_name", "country_name", "start_year", "end_year", "absolute_change", "percent_change"]].rename(columns={
                    "university_name": "University",
                    "country_name": "Country",
                    "start_year": "Start Year",
                    "end_year": "End Year",
                    "absolute_change": "Delta",
                    "percent_change": "% Change"
                }),
                use_container_width=True
            )
        else:
            st.info("No negative movers recorded.")

if __name__ == "__main__":
    render_trends()
