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
    fig.add_vline(x="2021-01-01", line_dash="dash", line_color="red",
                  annotation_text="Início pós-pandemia")
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
    fig.add_vline(x=threshold, line_dash="dash", line_color="red",
                  annotation_text=f"Limiar: {threshold:,.0f}")
    return fig
