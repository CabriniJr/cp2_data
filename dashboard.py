import streamlit as st
import pandas as pd
import plotly.express as px

from data_loader import load_data, normalize_columns, NUMERIC_COLS
from insights import pandemic_delta, top_game, streamers_threshold
from charts import bar_grouped, radar_chart, line_timeline, scatter_limiar

st.set_page_config(page_title="Twitch Analytics", layout="wide")

df = load_data()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("Filtros Globais")
    top10_default = (
        df.groupby("Game")["Hours_watched"].sum().nlargest(10).index.tolist()
    )
    selected_games = st.multiselect(
        "Jogos",
        options=sorted(df["Game"].dropna().unique()),
        default=top10_default,
    )
    metric = st.selectbox("Métrica principal", NUMERIC_COLS, index=0)

df_filtered = df[df["Game"].isin(selected_games)] if selected_games else df

# ── Helper para Q&A ───────────────────────────────────────────────────────────
def _qa_pandemic(df: pd.DataFrame, m: str) -> str:
    delta = pandemic_delta(df, m)
    direction = "cresceu" if delta["delta_pct"] > 0 else "caiu"
    return (
        f"Sim. A média mensal de **{m.replace('_', ' ')}** "
        f"{direction} **{abs(delta['delta_pct']):.1f}%** "
        f"no período pós-pandemia (2021+) em relação a antes (≤2020)."
    )

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["🦠 Pandemia", "🕸️ Radar", "🏆 Destaque", "📊 Limiar de Sucesso", "❓ Q&A"]
)

# ── Aba 1: Pandemia ───────────────────────────────────────────────────────────
with tab1:
    st.header("O perfil de interação mudou a partir da pandemia?")

    kpi_metrics = ["Hours_watched", "Avg_viewers", "Peak_viewers"]
    kpi_cols = st.columns(len(kpi_metrics))
    for col, m in zip(kpi_cols, kpi_metrics):
        delta = pandemic_delta(df_filtered, m)
        col.metric(
            label=m.replace("_", " "),
            value=f"{delta['post']:,.0f}",
            delta=f"{delta['delta_pct']:+.1f}% vs pré-pandemia",
        )

    st.plotly_chart(bar_grouped(df_filtered, kpi_metrics), use_container_width=True)

# ── Aba 2: Radar ──────────────────────────────────────────────────────────────
with tab2:
    st.header("Perfil de Jogos — Radar")

    axes = st.multiselect(
        "Eixos do radar",
        options=NUMERIC_COLS,
        default=["Hours_watched", "Peak_viewers", "Avg_viewers", "Streamers", "Avg_viewer_ratio"],
    )
    available_games = sorted(df_filtered["Game"].dropna().unique())
    default_games = available_games[:3] if len(available_games) >= 3 else available_games
    games_radar = st.multiselect(
        "Jogos para comparar (máx. 5)",
        options=available_games,
        default=default_games,
    )
    if len(games_radar) > 5:
        st.warning("Selecione no máximo 5 jogos para o radar.")
        games_radar = games_radar[:5]

    if axes and games_radar:
        st.plotly_chart(radar_chart(df_filtered, games_radar, axes), use_container_width=True)
    else:
        st.info("Selecione pelo menos 1 eixo e 1 jogo.")

# ── Aba 3: Destaque ───────────────────────────────────────────────────────────
with tab3:
    st.header("Qual jogo se destacou mais?")

    top_n = (
        df_filtered.groupby("Game")[metric].sum()
        .nlargest(10)
        .reset_index()
    )
    top_n.columns = ["Game", metric]
    fig_top = px.bar(
        top_n, x=metric, y="Game", orientation="h",
        title=f"Top 10 jogos por {metric.replace('_', ' ')}",
    )
    fig_top.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig_top, use_container_width=True)

    best = top_game(df_filtered, metric)
    st.subheader(f"Evolução de: {best}")
    if best in df_filtered["Game"].values:
        st.plotly_chart(
            line_timeline(df_filtered, best, metric),
            use_container_width=True,
        )
    else:
        st.info("Jogo não encontrado nos dados filtrados.")

# ── Aba 4: Limiar de Sucesso ──────────────────────────────────────────────────
with tab4:
    st.header("Limiar de Sucesso de Streamers")
    st.markdown("Defina os pesos para compor o score de sucesso (total normalizado internamente).")

    score_metrics = ["Hours_watched", "Peak_viewers", "Avg_viewers", "Avg_viewer_ratio"]
    w_cols = st.columns(len(score_metrics))
    weights = [
        col.slider(m.replace("_", " "), 0, 100, 25, step=5, key=f"w_{m}")
        for col, m in zip(w_cols, score_metrics)
    ]
    total_w = sum(weights)

    if total_w == 0:
        st.warning("Ajuste os pesos — todos estão em 0.")
    else:
        if total_w != 100:
            st.caption(f"Soma dos pesos: {total_w}% (normalizado internamente para 100%)")

        df_score = normalize_columns(df_filtered, score_metrics)
        df_score["score"] = sum(
            df_score[m] * (w / total_w)
            for m, w in zip(score_metrics, weights)
        )
        df_agg = df_score.groupby("Game").agg(
            Streamers=("Streamers", "mean"),
            score=("score", "mean"),
        ).reset_index().dropna(subset=["Streamers", "score"])

        if df_agg.empty:
            st.info("Sem dados suficientes para calcular o limiar.")
        else:
            s_min = int(df_agg["Streamers"].min())
            s_max = int(df_agg["Streamers"].max())
            auto_threshold = int(streamers_threshold(df_agg))

            if s_max <= s_min:
                threshold = s_min
                st.caption(f"Apenas um valor de Streamers presente ({s_min:,}). Limiar fixo.")
            else:
                step = max(1, (s_max - s_min) // 100)
                threshold = st.slider(
                    "Limiar de Streamers",
                    min_value=s_min,
                    max_value=s_max,
                    value=min(max(auto_threshold, s_min), s_max),
                    step=step,
                )

            n_above = int((df_agg["Streamers"] >= threshold).sum())
            st.caption(f"{n_above} jogos acima do limiar ({n_above / len(df_agg) * 100:.1f}%)")

            st.plotly_chart(scatter_limiar(df_agg, threshold), use_container_width=True)

# ── Aba 5: Q&A ────────────────────────────────────────────────────────────────
with tab5:
    st.header("Perguntas & Respostas")
    st.caption("Respostas geradas automaticamente com base nos filtros ativos.")

    if st.button("🔄 Regenerar insights"):
        st.cache_data.clear()
        st.rerun()

    qa_items = [
        {
            "pergunta": "O perfil de interação mudou a partir da pandemia?",
            "resposta": _qa_pandemic(df_filtered, metric),
            "destaque": f"{pandemic_delta(df_filtered, metric)['delta_pct']:+.1f}%",
        },
        {
            "pergunta": "Tem algum jogo que se destacou mais?",
            "resposta": (
                f"**{top_game(df_filtered, metric)}** lidera com o maior total acumulado "
                f"de *{metric.replace('_', ' ')}* no período selecionado."
            ),
            "destaque": top_game(df_filtered, metric),
        },
        {
            "pergunta": "A partir de qual número de streamers um jogo faz sucesso?",
            "resposta": (
                f"O limiar automático (percentil 75 de Streamers) é "
                f"**{streamers_threshold(df_filtered):,.0f} streamers**. "
                f"Jogos acima desse patamar tendem a ter maior audiência e engajamento."
            ),
            "destaque": f"{streamers_threshold(df_filtered):,.0f} streamers",
        },
    ]

    for item in qa_items:
        with st.container(border=True):
            st.markdown(f"### {item['pergunta']}")
            st.markdown(f"> **Insight-chave:** {item['destaque']}")
            st.markdown(item["resposta"])
