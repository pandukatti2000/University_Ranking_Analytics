import sys
if sys.platform == "win32":
    sys.modules["xarray"] = None
    sys.modules["statsmodels"] = None

import plotly.graph_objects as go
import plotly.express as px
import plotly.io as pio
pio.json.config.default_engine = "json"
import pandas as pd
import numpy as np
from typing import List, Optional

DARK_LAYOUT = dict(
    paper_bgcolor="rgba(15, 23, 42, 0.0)",
    plot_bgcolor="rgba(30, 41, 59, 0.5)",
    font=dict(family="Inter, sans-serif", color="#F8FAFC", size=12),
    margin=dict(l=40, r=40, t=50, b=40),
    xaxis=dict(
        gridcolor="#334155",
        zerolinecolor="#475569",
        showgrid=True,
        linecolor="#475569"
    ),
    yaxis=dict(
        gridcolor="#334155",
        zerolinecolor="#475569",
        showgrid=True,
        linecolor="#475569"
    ),
    legend=dict(
        bgcolor="rgba(15, 23, 42, 0.8)",
        bordercolor="#334155",
        borderwidth=1,
        font=dict(color="#CBD5E1")
    )
)

COLOR_PALETTE = [
    "#6366F1", "#06B6D4", "#10B981", "#F59E0B",
    "#EC4899", "#8B5CF6", "#14B8A6", "#F97316"
]

def create_radar_chart(df: pd.DataFrame, categories_col: str, value_col: str, group_col: str, title: str = "") -> go.Figure:
    """Create radar chart comparing multiple entities across numerical criteria."""
    fig = go.Figure()
    groups = df[group_col].unique()

    for idx, group in enumerate(groups):
        sub_df = df[df[group_col] == group]
        r_vals = sub_df[value_col].tolist()
        theta_vals = sub_df[categories_col].tolist()

        # Close the loop
        if r_vals:
            r_vals.append(r_vals[0])
            theta_vals.append(theta_vals[0])

        color = COLOR_PALETTE[idx % len(COLOR_PALETTE)]
        fig.add_trace(go.Scatterpolar(
            r=r_vals,
            theta=theta_vals,
            fill='toself',
            name=str(group),
            line=dict(color=color, width=2),
            opacity=0.65
        ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                gridcolor="#334155",
                linecolor="#475569",
                tickfont=dict(color="#94A3B8")
            ),
            angularaxis=dict(
                gridcolor="#334155",
                linecolor="#475569",
                tickfont=dict(color="#F8FAFC", size=11)
            ),
            bgcolor="rgba(30, 41, 59, 0.4)"
        ),
        showlegend=True,
        title=dict(text=title, font=dict(color="#F8FAFC", size=15)),
        **DARK_LAYOUT
    )
    return fig

def create_trend_line_chart(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    color_col: str,
    title: str = "",
    y_label: str = "Score",
    inverted_y: bool = False
) -> go.Figure:
    """Create multi-series historical trend line chart with markers."""
    fig = px.line(
        df,
        x=x_col,
        y=y_col,
        color=color_col,
        markers=True,
        title=title,
        color_discrete_sequence=COLOR_PALETTE
    )
    layout = DARK_LAYOUT.copy()
    if inverted_y:
        layout["yaxis"] = dict(
            autorange="reversed",
            gridcolor="#334155",
            zerolinecolor="#475569",
            title=dict(text=f"{y_label} (Lower is Better)")
        )
    else:
        layout["yaxis"] = dict(
            gridcolor="#334155",
            zerolinecolor="#475569",
            title=dict(text=y_label)
        )

    fig.update_layout(title=dict(text=title, font=dict(color="#F8FAFC", size=15)), **layout)
    fig.update_traces(line=dict(width=2.5), marker=dict(size=7))
    return fig

def create_bar_chart(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    color_col: Optional[str] = None,
    title: str = "",
    orientation: str = "v",
    barmode: str = "group"
) -> go.Figure:
    """Create styled grouped or stacked bar chart."""
    fig = px.bar(
        df,
        x=x_col,
        y=y_col,
        color=color_col,
        title=title,
        orientation=orientation,
        barmode=barmode,
        color_discrete_sequence=COLOR_PALETTE
    )
    fig.update_layout(title=dict(text=title, font=dict(color="#F8FAFC", size=15)), **DARK_LAYOUT)
    return fig

def create_scatter_plot(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    color_col: Optional[str] = None,
    size_col: Optional[str] = None,
    hover_name: Optional[str] = None,
    title: str = "",
    trendline: Optional[str] = None
) -> go.Figure:
    """Create correlation-safe scatter plot with optional pure-numpy OLS trendline."""
    fig = px.scatter(
        df,
        x=x_col,
        y=y_col,
        color=color_col,
        size=size_col,
        hover_name=hover_name,
        title=title,
        color_discrete_sequence=COLOR_PALETTE
    )
    if trendline and len(df) > 1 and x_col in df.columns and y_col in df.columns:
        try:
            valid_df = df[[x_col, y_col]].dropna()
            if len(valid_df) > 1:
                x_vals = valid_df[x_col].values.astype(float)
                y_vals = valid_df[y_col].values.astype(float)
                if len(np.unique(x_vals)) > 1:
                    slope, intercept = np.polyfit(x_vals, y_vals, 1)
                    x_line = np.linspace(x_vals.min(), x_vals.max(), 50)
                    y_line = slope * x_line + intercept
                    fig.add_trace(go.Scatter(
                        x=x_line,
                        y=y_line,
                        mode="lines",
                        name="Linear Trend (OLS)",
                        line=dict(color="#F59E0B", width=2, dash="dash")
                    ))
        except Exception:
            pass

    fig.update_layout(title=dict(text=title, font=dict(color="#F8FAFC", size=15)), **DARK_LAYOUT)
    fig.update_traces(marker=dict(opacity=0.8, line=dict(width=1, color="#1E293B")))
    return fig

def create_box_plot(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    color_col: Optional[str] = None,
    title: str = ""
) -> go.Figure:
    """Create distribution box plot."""
    fig = px.box(
        df,
        x=x_col,
        y=y_col,
        color=color_col or x_col,
        title=title,
        color_discrete_sequence=COLOR_PALETTE
    )
    fig.update_layout(title=dict(text=title, font=dict(color="#F8FAFC", size=15)), **DARK_LAYOUT)
    return fig

def create_treemap(
    df: pd.DataFrame,
    path: List[str],
    values_col: str,
    title: str = ""
) -> go.Figure:
    """Create hierarchical treemap."""
    fig = px.treemap(
        df,
        path=path,
        values=values_col,
        title=title,
        color_discrete_sequence=COLOR_PALETTE
    )
    fig.update_layout(
        title=dict(text=title, font=dict(color="#F8FAFC", size=15)),
        paper_bgcolor="rgba(15, 23, 42, 0.0)",
        font=dict(family="Inter, sans-serif", color="#F8FAFC")
    )
    return fig

def create_choropleth_map(
    df: pd.DataFrame,
    locations_col: str,
    color_col: str,
    title: str = "",
    location_mode: str = "country names"
) -> go.Figure:
    """Create global choropleth map."""
    fig = px.choropleth(
        df,
        locations=locations_col,
        locationmode=location_mode,
        color=color_col,
        title=title,
        color_continuous_scale="Viridis"
    )
    fig.update_layout(
        title=dict(text=title, font=dict(color="#F8FAFC", size=15)),
        paper_bgcolor="rgba(15, 23, 42, 0.0)",
        geo=dict(
            bgcolor="rgba(15, 23, 42, 0.0)",
            lakecolor="#1E293B",
            landcolor="#1E293B",
            showocean=True,
            oceancolor="#0F172A",
            showcoastlines=True,
            coastlinecolor="#334155"
        ),
        font=dict(family="Inter, sans-serif", color="#F8FAFC")
    )
    return fig
