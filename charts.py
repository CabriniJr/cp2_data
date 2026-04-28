# charts.py
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from data_loader import normalize_columns


def bar_grouped(df: pd.DataFrame, metrics: list) -> go.Figure:
    """Grouped bar chart: pre vs post pandemic average for each metric."""
    records = []
    for metric in metrics:
        for flag, label in [(True, "Pré-pandemia (≤2020)"), (False, "Pós-pandemia (>2020)")]:
            avg = df[df["pre_pandemic"] == flag][metric].mean()
            records.append({"Métrica": metric, "Período": label, "Valor": avg})
    plot_df = pd.DataFrame(records)
    return px.bar(plot_df, x="Métrica", y="Valor", color="Período", barmode="group",
                  title="Média por período (pré vs pós pandemia)")


def radar_chart(df: pd.DataFrame, games: list, axes: list) -> go.Figure:
    """Radar/spider chart comparing games across normalized axes."""
    df_norm = normalize_columns(df, axes)
    df_avg = df_norm.groupby("Game")[axes].mean().reset_index()
    df_sel = df_avg[df_avg["Game"].isin(games)]
    fig = go.Figure()
    for _, row in df_sel.iterrows():
        values = [row[a] for a in axes] + [row[axes[0]]]
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=axes + [axes[0]],
            fill="toself",
            name=row["Game"],
        ))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
                      title="Comparação de perfil entre jogos (normalizado 0–1)")
    return fig


def line_timeline(df: pd.DataFrame, game: str, metric: str) -> go.Figure:
    """Line chart of metric over time for a single game, with pandemic marker."""
    df_game = df[df["Game"] == game].copy()
    df_game["date"] = pd.to_datetime(
        df_game["Year"].astype(str) + "-" + df_game["Month"].astype(str).str.zfill(2) + "-01"
    )
    df_game = df_game.sort_values("date")
    fig = px.line(df_game, x="date", y=metric,
                  title=f"{game} — {metric.replace('_', ' ')} ao longo do tempo")
    pandemic_start = pd.Timestamp("2021-01-01")
    fig.add_shape(
        type="line",
        yref="paper",
        x0=pandemic_start, x1=pandemic_start,
        y0=0, y1=1,
        line=dict(color="red", dash="dash"),
    )
    fig.add_annotation(
        x=pandemic_start, y=1.05,
        yref="paper",
        text="Início pós-pandemia",
        showarrow=False,
        font=dict(color="red"),
    )
    return fig


def scatter_limiar(df: pd.DataFrame, threshold: float) -> go.Figure:
    """Scatter: Streamers vs score, colored by above/below threshold."""
    df = df.copy()
    df["status"] = df["Streamers"].apply(
        lambda x: "Sucesso" if x >= threshold else "Abaixo do limiar"
    )
    fig = px.scatter(
        df, x="Streamers", y="score",
        color="status",
        color_discrete_map={"Sucesso": "orange", "Abaixo do limiar": "steelblue"},
        hover_data=["Game"],
        title="Limiar de Sucesso por número de Streamers",
    )
    fig.add_shape(
        type="line",
        yref="paper",
        x0=threshold, x1=threshold,
        y0=0, y1=1,
        line=dict(color="red", dash="dash"),
    )
    fig.add_annotation(
        x=threshold, y=1.05,
        yref="paper",
        text=f"Limiar: {threshold:,.0f}",
        showarrow=False,
        font=dict(color="red"),
    )
    return fig


def box_pandemic(df: pd.DataFrame, metric: str) -> go.Figure:
    """Box plot da métrica comparando pré vs pós pandemia."""
    df = df.copy()
    df["Período"] = df["pre_pandemic"].map({True: "Pré-pandemia (≤2020)", False: "Pós-pandemia (>2020)"})
    fig = px.box(
        df, x="Período", y=metric,
        color="Período",
        title=f"Distribuição de {metric.replace('_', ' ')} — pré vs pós pandemia",
        points="outliers",
    )
    return fig


def correlation_heatmap(df: pd.DataFrame, cols: list) -> go.Figure:
    """Matriz de correlação de Pearson como heatmap."""
    corr = df[cols].corr().round(2)
    fig = px.imshow(
        corr,
        text_auto=True,
        color_continuous_scale="RdBu_r",
        zmin=-1, zmax=1,
        aspect="auto",
        title="Matriz de Correlação (Pearson)",
    )
    return fig


def scatter_pair(df: pd.DataFrame, x_col: str, y_col: str, r: float) -> go.Figure:
    """Scatter de duas métricas com coeficiente de correlação no título."""
    fig = px.scatter(
        df, x=x_col, y=y_col,
        opacity=0.5,
        hover_data=["Game"],
        title=f"{x_col.replace('_', ' ')} × {y_col.replace('_', ' ')} (r = {r:.2f})",
        trendline="ols" if _has_statsmodels() else None,
    )
    return fig


def _has_statsmodels() -> bool:
    try:
        import statsmodels  # noqa: F401
        return True
    except ImportError:
        return False
