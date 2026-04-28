import streamlit as st
import pandas as pd
import plotly.express as px

from data_loader import load_data, normalize_columns, NUMERIC_COLS
from insights import (
    pandemic_delta, top_game, streamers_threshold,
    descriptive_stats, top_correlated_pairs,
)
from charts import (
    bar_grouped, radar_chart, line_timeline, scatter_limiar,
    box_pandemic, correlation_heatmap, scatter_pair,
)

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
    st.markdown("---")
    st.caption(
        "Os filtros acima afetam todas as abas. "
        "A história começa pela aba **Pandemia** e termina em **Conclusão**."
    )

df_filtered = df[df["Game"].isin(selected_games)] if selected_games else df


def _qa_pandemic(df: pd.DataFrame, m: str) -> str:
    delta = pandemic_delta(df, m)
    verbo = "cresceu" if delta["delta_pct"] > 0 else "caiu"
    abs_pct = abs(delta["delta_pct"])
    if abs_pct > 20:
        confirmacao = "Sim, de forma expressiva"
    elif abs_pct > 5:
        confirmacao = "Sim"
    else:
        confirmacao = "Marginalmente"
    return (
        f"{confirmacao}. A média mensal de **{m.replace('_', ' ')}** "
        f"{verbo} **{abs_pct:.1f}%** "
        f"no período pós-pandemia (2021+) em relação a antes (≤2020)."
    )


# ── Tabs ──────────────────────────────────────────────────────────────────────
tabs = st.tabs([
    "🦠 Pandemia",
    "📈 Estatísticas",
    "🕸️ Radar",
    "🏆 Destaque",
    "🔗 Correlação",
    "📊 Limiar",
    "🎯 Conclusão",
])
tab_pandemia, tab_stats, tab_radar, tab_destaque, tab_corr, tab_limiar, tab_conclusao = tabs

# ── Aba 1: Pandemia ───────────────────────────────────────────────────────────
with tab_pandemia:
    st.header("1. O perfil de interação mudou a partir da pandemia?")
    st.markdown(
        "> Em 2020, a Twitch cresceu em um único ano. Mas o número mais relevante "
        "não é o **tamanho** do crescimento — é **o que mudou dentro dele**. "
        "Pela primeira vez em 4 anos, **Just Chatting** derrubou **League of Legends** do #1. "
        "As pessoas não queriam só ver jogos. Queriam **companhia**."
    )

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

    delta_hw = pandemic_delta(df_filtered, "Hours_watched")
    delta_st = pandemic_delta(df_filtered, "Streamers")
    st.info(
        f"**Interpretação:** Horas assistidas variaram **{delta_hw['delta_pct']:+.1f}%** "
        f"e o número de streamers únicos **{delta_st['delta_pct']:+.1f}%**. "
        "O crescimento de **criadores** superou o de **audiência** — sinal de que "
        "a porta de entrada da Twitch se abriu, e muita gente passou a streamar. "
        "A plataforma deixou de ser só um lugar para *assistir* e virou um lugar para *participar*."
    )

# ── Aba 2: Estatísticas Descritivas ───────────────────────────────────────────
with tab_stats:
    st.header("2. Por trás da média: a dispersão")
    st.markdown(
        "Médias contam metade da história. **Mediana, moda, desvio padrão, "
        "variância e quartis** revelam o resto: onde os dados realmente se "
        "concentram e o quanto variam. A pista que vamos seguir aqui é: "
        "*a Twitch ficou maior — mas também ficou mais desigual?*"
    )

    stats_df = descriptive_stats(df_filtered, NUMERIC_COLS)
    st.dataframe(
        stats_df.style.format({
            c: "{:,.2f}" for c in stats_df.columns if c != "Métrica"
        }),
        use_container_width=True,
        hide_index=True,
    )

    chosen = st.selectbox(
        "Escolha uma métrica para ver a distribuição pré vs pós pandemia",
        NUMERIC_COLS,
        index=NUMERIC_COLS.index("Hours_watched"),
    )
    st.plotly_chart(box_pandemic(df_filtered, chosen), use_container_width=True)

    pre_std = float(df_filtered[df_filtered["pre_pandemic"]][chosen].std() or 0)
    post_std = float(df_filtered[~df_filtered["pre_pandemic"]][chosen].std() or 0)
    post_median = float(df_filtered[~df_filtered["pre_pandemic"]][chosen].median() or 0)
    post_mean = float(df_filtered[~df_filtered["pre_pandemic"]][chosen].mean() or 0)
    if pre_std > 0:
        var_change = (post_std - pre_std) / pre_std * 100
        comp = "aumentou" if var_change > 0 else "diminuiu"
        skew_ratio = post_mean / post_median if post_median > 0 else 0
        st.info(
            f"**Interpretação:** O desvio padrão de *{chosen.replace('_', ' ')}* "
            f"{comp} **{abs(var_change):.1f}%** no pós-pandemia "
            f"(de {pre_std:,.0f} para {post_std:,.0f}). "
            f"A **média ({post_mean:,.0f}) é {skew_ratio:.1f}× maior que a mediana "
            f"({post_median:,.0f})** — distribuição extremamente assimétrica: "
            "**poucos jogos concentram a maior parte da audiência**, a maioria fica na cauda."
        )

# ── Aba 3: Radar ──────────────────────────────────────────────────────────────
with tab_radar:
    st.header("3. Três identidades coexistindo na mesma plataforma")
    st.markdown(
        "Nem todo jogo cresce do mesmo jeito. O radar revela três perfis distintos:\n"
        "- 🎮 **Comunidade consolidada** (League of Legends): *Avg_viewer_ratio* alto, audiência fiel\n"
        "- 🎯 **Audiência de evento** (Fortnite): picos de *Peak_viewers* enormes, mas ratio baixo\n"
        "- 💬 **Social** (Just Chatting): muitos *Streamers*, conteúdo conversacional\n\n"
        "Compare os três para ver que a Twitch não é uma plataforma só — são várias dentro da mesma."
    )

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
        st.info(
            "**Como ler:** Polígonos grandes = jogos dominantes em várias métricas. "
            "Polígonos com picos isolados = jogos especializados em uma dimensão "
            "(ex.: alto *Avg_viewer_ratio* = poucos canais mas muita audiência por canal)."
        )
    else:
        st.info("Selecione pelo menos 1 eixo e 1 jogo.")

# ── Aba 4: Destaque ───────────────────────────────────────────────────────────
with tab_destaque:
    st.header("4. Quem se destacou — e por quê?")
    st.markdown(
        "**Just Chatting não existia antes de 2018.** Em 2020, virou o jogo mais "
        "assistido da plataforma — e nunca mais saiu do #1. "
        "**GTA V** cresceu fortemente pós-pandemia, impulsionado pelos servidores de "
        "*roleplay*. **VALORANT** lançou em 2020 e já acumulou mais horas que **Dota 2**, "
        "um jogo com 4 anos de vantagem. Os top 3 concentram cerca de **27% de todo o mercado**."
    )

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
        st.info(
            f"**Interpretação:** *{best}* lidera o ranking acumulado. "
            "Observe se a curva tem inflexão clara após jan/2021 — isso indica que o "
            "jogo se beneficiou (ou foi prejudicado) pelo cenário pós-pandemia."
        )
    else:
        st.info("Jogo não encontrado nos dados filtrados.")

# ── Aba 5: Correlação ─────────────────────────────────────────────────────────
with tab_corr:
    st.header("5. Quais métricas andam juntas?")
    st.markdown(
        "A **correlação de Pearson** mede o quanto duas métricas variam em conjunto: "
        "**+1** sobem juntas, **−1** uma sobe quando a outra desce, **0** independentes. "
        "Algumas métricas aqui são praticamente redundantes (r ≈ 1) — outras totalmente "
        "independentes (r ≈ 0). Saber qual é qual evita análises enganosas: "
        "*fidelidade de audiência* (Avg_viewer_ratio), por exemplo, **não depende de volume**."
    )

    st.plotly_chart(correlation_heatmap(df_filtered, NUMERIC_COLS), use_container_width=True)

    pairs = top_correlated_pairs(df_filtered, NUMERIC_COLS, n=3)
    if pairs:
        bullets = "\n".join(
            f"- **{a.replace('_', ' ')}** × **{b.replace('_', ' ')}** → r = {r:+.2f}"
            for a, b, r in pairs
        )
        st.markdown(f"**Pares mais correlacionados:**\n{bullets}")

        a, b, r = pairs[0]
        st.plotly_chart(scatter_pair(df_filtered, a, b, r), use_container_width=True)

        forca = "muito forte" if abs(r) > 0.8 else ("forte" if abs(r) > 0.5 else "moderada")
        st.info(
            f"**Interpretação:** A correlação entre *{a.replace('_', ' ')}* e "
            f"*{b.replace('_', ' ')}* é **{forca}** (r = {r:+.2f}). "
            "Quando duas métricas têm correlação alta, uma pode ser usada para prever a outra."
        )

# ── Aba 6: Limiar de Sucesso ──────────────────────────────────────────────────
with tab_limiar:
    st.header("6. A partir de qual nº de streamers um jogo faz sucesso?")
    st.markdown(
        "Construímos um **score composto de sucesso** combinando 4 métricas (com pesos ajustáveis) "
        "e cruzamos com o número de streamers. A linha vermelha marca o limiar — "
        "padrão = **percentil 75** (jogos no top 25% em volume de streamers)."
    )

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
            pct_above = n_above / len(df_agg) * 100
            st.caption(f"{n_above} jogos acima do limiar ({pct_above:.1f}%)")

            st.plotly_chart(scatter_limiar(df_agg, threshold), use_container_width=True)

            r_streamers_score = float(df_agg[["Streamers", "score"]].corr().iloc[0, 1])
            above_games = df_agg[df_agg["Streamers"] >= threshold]["Game"].tolist()
            below_games = df_agg[df_agg["Streamers"] < threshold]["Game"].tolist()
            avg_above = float(df_filtered[df_filtered["Game"].isin(above_games)]["Avg_viewers"].mean() or 0)
            avg_below = float(df_filtered[df_filtered["Game"].isin(below_games)]["Avg_viewers"].mean() or 0)
            ratio = avg_above / avg_below if avg_below > 0 else 0
            st.info(
                f"**Interpretação:** Acima de **{threshold:,} streamers**, os jogos têm "
                f"audiência média **{ratio:.1f}× maior** que abaixo do limiar "
                f"({avg_above:,.0f} vs {avg_below:,.0f} viewers em média). "
                f"A correlação entre nº de streamers e o score composto é **r = {r_streamers_score:+.2f}**. "
                "Existe uma **massa crítica de criadores** que precisa ser atingida antes "
                "da audiência escalar — não é só popularidade, é fundação."
            )

# ── Aba 7: Conclusão ──────────────────────────────────────────────────────────
with tab_conclusao:
    st.header("🎯 Conclusão — Síntese das descobertas")

    delta_full = pandemic_delta(df_filtered, metric)
    best_full = top_game(df_filtered, metric)
    threshold_full = streamers_threshold(df_filtered)
    pairs = top_correlated_pairs(df_filtered, NUMERIC_COLS, n=1)
    top_pair = pairs[0] if pairs else (None, None, 0)

    qa_items = [
        {
            "pergunta": "1) O perfil de interação mudou a partir da pandemia?",
            "resposta": _qa_pandemic(df_filtered, metric),
            "destaque": f"{delta_full['delta_pct']:+.1f}%",
        },
        {
            "pergunta": "2) Tem algum jogo que se destacou mais?",
            "resposta": (
                f"**{best_full}** lidera com o maior total acumulado de "
                f"*{metric.replace('_', ' ')}* no período selecionado. "
                "É o jogo de referência para análises comparativas."
            ),
            "destaque": best_full,
        },
        {
            "pergunta": "3) A partir de qual nº de streamers um jogo faz sucesso?",
            "resposta": (
                f"O limiar automático (percentil 75 da distribuição de Streamers) é "
                f"**{threshold_full:,.0f} streamers**. "
                "Jogos acima desse patamar concentram a maior parte da audiência."
            ),
            "destaque": f"{threshold_full:,.0f}",
        },
    ]

    for item in qa_items:
        with st.container(border=True):
            st.markdown(f"### {item['pergunta']}")
            st.markdown(f"> **Insight-chave:** {item['destaque']}")
            st.markdown(item["resposta"])

    if top_pair[0]:
        a, b, r = top_pair
        st.markdown("---")
        st.markdown(
            f"**Bônus estatístico:** A maior correlação observada é entre "
            f"*{a.replace('_', ' ')}* e *{b.replace('_', ' ')}* "
            f"(**r = {r:+.2f}**), o que indica que essas métricas são praticamente "
            "redundantes para classificar o sucesso de um jogo."
        )

    st.markdown("---")
    st.success(
        "### A história em uma frase\n"
        "**Os números voltaram depois da pandemia. O comportamento não voltou.** "
        "A Twitch deixou de ser uma plataforma sobre jogos e virou uma plataforma sobre **pessoas que jogam**."
    )

    st.caption(
        "Limitações: amostra restrita aos jogos rankeados mensalmente na Twitch; "
        "correlação não implica causalidade; o pico pandêmico (2020) pode mascarar tendências de longo prazo."
    )
