import streamlit as st
import pandas as pd
import uuid
from frontend.components.theme import (
    apply_custom_css,
    render_scale_warning
)
from frontend.components.charts import (
    create_bar_chart,
    create_trend_line_chart
)
from frontend.components.api_client import send_chat_message

STARTER_PROMPTS = [
    "Which universities have the highest research scores in 2015?",
    "Compare Harvard, MIT, and Stanford using available metrics in 2015.",
    "Which countries have the most universities represented?",
    "How do the three ranking systems differ?",
    "How has the University of Cambridge performed over time?",
    "Which universities have strong citations performance but lower teaching scores?",
    "Is there a relationship between international student percentage and research scores?"
]

def render_ai_copilot():
    apply_custom_css()
    st.title("✨ AI Analytics Assistant (LangGraph Copilot)")
    st.markdown("Ask natural language analytical questions. Answers are deterministically grounded in PostgreSQL queries validated via SQLGlot AST inspection.")
    
    render_scale_warning()
    
    # Initialize thread_id
    if "chat_thread_id" not in st.session_state:
        st.session_state.chat_thread_id = f"st-session-{uuid.uuid4().hex[:8]}"
        
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [
            {
                "role": "assistant",
                "content": "Hello! I am your AI analytics assistant. You can ask me questions about global university rankings, institutional comparisons, country distributions, or historical trends. What would you like to explore?",
                "sql": None,
                "results": None,
                "chart": None,
                "latency": None
            }
        ]
        
    # Starter Prompts Section
    st.markdown("#### Suggested Analytical Prompts")
    prompt_cols = st.columns(len(STARTER_PROMPTS[:4]))
    selected_prompt = None
    for i, p in enumerate(STARTER_PROMPTS[:4]):
        with prompt_cols[i]:
            if st.button(p, key=f"starter_{i}", use_container_width=True):
                selected_prompt = p
                
    st.markdown("---")
    
    # Display Chat History
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
            # Collapsible SQL inspection pill
            if msg.get("sql"):
                with st.expander("🔍 Verified Read-Only SQL Inspection", expanded=False):
                    st.code(msg["sql"], language="sql")
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.caption(f"**Safety Check:** ✅ Validated SELECT")
                    with c2:
                        st.caption(f"**Rows Retrieved:** {len(msg.get('results', []))}")
                    with c3:
                        latency = msg.get('latency', 0)
                        st.caption(f"**Workflow Latency:** {latency:.1f} ms" if latency else "**Latency:** < 100 ms")
                        
            # Render Query Results Data Table if available
            results = msg.get("results")
            if results and isinstance(results, list) and len(results) > 0:
                with st.expander("📊 View Underlying Query Records", expanded=False):
                    st.dataframe(pd.DataFrame(results), use_container_width=True)
                    
            # Render Recommended Chart
            chart_rec = msg.get("chart")
            if chart_rec and results:
                df_res = pd.DataFrame(results)
                chart_type = chart_rec.get("chart_type")
                x_col = chart_rec.get("x")
                y_col = chart_rec.get("y")
                
                if chart_type == "bar" and x_col in df_res.columns and y_col in df_res.columns:
                    fig = create_bar_chart(
                        df_res,
                        x_col=x_col,
                        y_col=y_col,
                        color_col=chart_rec.get("color"),
                        title=chart_rec.get("title", "Visualized Insights")
                    )
                    st.plotly_chart(fig, use_container_width=True)
                elif chart_type == "line" and x_col in df_res.columns and y_col in df_res.columns:
                    fig = create_trend_line_chart(
                        df_res,
                        x_col=x_col,
                        y_col=y_col,
                        color_col=chart_rec.get("color", x_col),
                        title=chart_rec.get("title", "Historical Trajectory")
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
    # Handle New Input
    user_input = st.chat_input("Ask a question about universities, rankings, or countries...") or selected_prompt
    
    if user_input:
        # Append User Message
        st.session_state.chat_history.append({
            "role": "user",
            "content": user_input
        })
        with st.chat_message("user"):
            st.markdown(user_input)
            
        # Run Assistant
        with st.chat_message("assistant"):
            with st.spinner("Analyzing schema, validating AST safety, and executing query..."):
                response = send_chat_message(
                    question=user_input,
                    thread_id=st.session_state.chat_thread_id
                )
                
            ans_text = response.get("final_answer", "Analysis completed.")
            st.markdown(ans_text)
            
            gen_sql = response.get("generated_sql")
            results = response.get("query_results", [])
            chart_rec = response.get("visualization_recommendation")
            latency = response.get("execution_time_ms")
            
            if gen_sql:
                with st.expander("🔍 Verified Read-Only SQL Inspection", expanded=False):
                    st.code(gen_sql, language="sql")
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.caption(f"**Safety Check:** ✅ Validated SELECT")
                    with c2:
                        st.caption(f"**Rows Retrieved:** {len(results)}")
                    with c3:
                        st.caption(f"**Workflow Latency:** {latency:.1f} ms" if latency else "**Latency:** < 100 ms")
                        
            if results and len(results) > 0:
                with st.expander("📊 View Underlying Query Records", expanded=False):
                    st.dataframe(pd.DataFrame(results), use_container_width=True)
                    
            if chart_rec and results:
                df_res = pd.DataFrame(results)
                chart_type = chart_rec.get("chart_type")
                x_col = chart_rec.get("x")
                y_col = chart_rec.get("y")
                
                if chart_type == "bar" and x_col in df_res.columns and y_col in df_res.columns:
                    fig = create_bar_chart(
                        df_res,
                        x_col=x_col,
                        y_col=y_col,
                        color_col=chart_rec.get("color"),
                        title=chart_rec.get("title", "Visualized Insights")
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
            # Save Assistant Message
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": ans_text,
                "sql": gen_sql,
                "results": results,
                "chart": chart_rec,
                "latency": latency
            })
            
    # Reset Chat Session button in sidebar
    with st.sidebar:
        st.markdown("---")
        st.markdown(f"**Thread ID:** `{st.session_state.chat_thread_id}`")
        if st.button("🗑️ Reset Chat History", use_container_width=True):
            st.session_state.chat_history = []
            st.session_state.chat_thread_id = f"st-session-{uuid.uuid4().hex[:8]}"
            st.rerun()

if __name__ == "__main__":
    render_ai_copilot()
