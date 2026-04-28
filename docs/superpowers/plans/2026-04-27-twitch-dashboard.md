# Twitch Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Criar um dashboard Streamlit com 5 abas para responder 3 perguntas analíticas sobre dados de jogos na Twitch (2016–2024).

**Architecture:** Um único arquivo `dashboard.py` orquestra as abas e a sidebar; lógica de dados em `data_loader.py` e `insights.py`; funções de gráfico em `charts.py`. Cada módulo tem responsabilidade única e é testável de forma independente.

**Tech Stack:** Python 3.14, Streamlit ≥1.32, Plotly ≥5.18, Pandas ≥2.0, Pytest ≥8.0

---

## File Map

| Arquivo | Responsabilidade |
|---|---|
| `requirements.txt` | Dependências do projeto |
| `data_loader.py` | Carregamento, derivação de `pre_pandemic`, normalização min-max |
| `insights.py` | Funções de insight: delta pandemia, top jogo, limiar de streamers |
| `charts.py` | Funções que retornam figuras Plotly |
| `dashboard.py` | App Streamlit: sidebar, tabs, composição das 5 abas |
| `tests/__init__.py` | Marca diretório como pacote de testes |
| `tests/test_data_loader.py` | Testes de `data_loader.py` |
| `tests/test_insights.py` | Testes de `insights.py` |

---

## Task 1: Requirements e Setup

**Files:**
- Create: `requirements.txt`
- Create: `tests/__init__.py`

- [ ] **Step 1: Criar requirements.txt**

```
streamlit>=1.32.0
plotly>=5.18.0
pandas>=2.0.0
pytest>=8.0.0
```

- [ ] **Step 2: Instalar dependências**

```bash
python3 -m pip install -r requirements.txt
```

Saída esperada: `Successfully installed streamlit plotly pandas pytest ...`

- [ ] **Step 3: Criar tests/__init__.py vazio**

```bash
mkdir -p tests && touch tests/__init__.py
```

- [ ] **Step 4: Commit**

```bash
git init
git add requirements.txt tests/__init__.py
git commit -m "chore: setup project dependencies"
```

---

## Task 2: data_loader.py (TDD)

**Files:**
- Create: `data_loader.py`
- Create: `tests/test_data_loader.py`

- [ ] **Step 1: Escrever os testes**

```python
# tests/test_data_loader.py
import pandas as pd
import pytest
from data_loader import _build_dataframe, normalize_columns, NUMERIC_COLS
import os

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "Twitch_game_data.csv")


def test_pre_pandemic_column_true_for_2020_and_before():
    df = _build_dataframe(DATA_PATH)
    assert df[df["Year"] <= 2020]["pre_pandemic"].all()


def test_pre_pandemic_column_false_for_2021_and_after():
    df = _build_dataframe(DATA_PATH)
    assert not df[df["Year"] > 2020]["pre_pandemic"].any()


def test_dataframe_has_13_columns():
    df = _build_dataframe(DATA_PATH)
    assert df.shape[1] == 13


def test_dataframe_has_21000_rows():
    df = _build_dataframe(DATA_PATH)
    assert df.shape[0] == 21000


def test_normalize_columns_range_zero_to_one():
    df = _build_dataframe(DATA_PATH)
    norm = normalize_columns(df.copy(), ["Hours_watched"])
    assert norm["Hours_watched"].min() >= 0.0
    assert norm["Hours_watched"].max() <= 1.0


def test_normalize_columns_does_not_modify_other_columns():
    df = _build_dataframe(DATA_PATH)
    original_peak = df["Peak_viewers"].copy()
    normalize_columns(df, ["Hours_watched"])
    pd.testing.assert_series_equal(df["Peak_viewers"], original_peak)


def test_numeric_cols_constant_is_list_of_strings():
    assert isinstance(NUMERIC_COLS, list)
    assert all(isinstance(c, str) for c in NUMERIC_COLS)
```

- [ ] **Step 2: Rodar testes e confirmar falha**

```bash
cd /home/guaxinim/Documents/Projects/cp2_data && python3 -m pytest tests/test_data_loader.py -v
```

Saída esperada: `ERROR` ou `ImportError` — `data_loader` não existe ainda.

- [ ] **Step 3: Implementar data_loader.py**

```python
# data_loader.py
import os
import pandas as pd

try:
    import streamlit as st
    _cache = st.cache_data
except Exception:
    def _cache(fn):
        return fn

NUMERIC_COLS = [
    "Hours_watched", "Hours_streamed", "Peak_viewers", "Peak_channels",
    "Streamers", "Avg_viewers", "Avg_channels", "Avg_viewer_ratio",
]

_DEFAULT_PATH = os.path.join(os.path.dirname(__file__), "Twitch_game_data.csv")


def _build_dataframe(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, encoding="latin-1")
    df["pre_pandemic"] = df["Year"] <= 2020
    return df


@_cache
def load_data(path: str = _DEFAULT_PATH) -> pd.DataFrame:
    return _build_dataframe(path)


def normalize_columns(df: pd.DataFrame, cols: list) -> pd.DataFrame:
    result = df.copy()
    for col in cols:
        col_min = result[col].min()
        col_max = result[col].max()
        if col_max > col_min:
            result[col] = (result[col] - col_min) / (col_max - col_min)
        else:
            result[col] = 0.0
    return result
```

- [ ] **Step 4: Rodar testes e confirmar passa**

```bash
python3 -m pytest tests/test_data_loader.py -v
```

Saída esperada: `7 passed`

- [ ] **Step 5: Commit**

```bash
git add data_loader.py tests/test_data_loader.py
git commit -m "feat: add data_loader with pre_pandemic column and normalization"
```

---

## Task 3: insights.py (TDD)

**Files:**
- Create: `insights.py`
- Create: `tests/test_insights.py`

- [ ] **Step 1: Escrever os testes**

```python
# tests/test_insights.py
import os
import pandas as pd
from data_loader import _build_dataframe
from insights import pandemic_delta, top_game, streamers_threshold

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "Twitch_game_data.csv")


def _df():
    return _build_dataframe(DATA_PATH)


def test_pandemic_delta_returns_required_keys():
    result = pandemic_delta(_df(), "Hours_watched")
    assert set(result.keys()) == {"pre", "post", "delta_pct"}


def test_pandemic_delta_pct_is_float():
    result = pandemic_delta(_df(), "Hours_watched")
    assert isinstance(result["delta_pct"], float)


def test_pandemic_delta_pre_is_positive():
    result = pandemic_delta(_df(), "Hours_watched")
    assert result["pre"] > 0


def test_top_game_returns_string():
    result = top_game(_df(), "Hours_watched")
    assert isinstance(result, str) and len(result) > 0


def test_top_game_is_in_dataset():
    df = _df()
    result = top_game(df, "Hours_watched")
    assert result in df["Game"].values


def test_streamers_threshold_within_range():
    df = _df()
    t = streamers_threshold(df)
    assert df["Streamers"].min() <= t <= df["Streamers"].max()


def test_streamers_threshold_default_is_p75():
    df = _df()
    assert streamers_threshold(df) == df["Streamers"].quantile(0.75)
```

- [ ] **Step 2: Rodar testes e confirmar falha**

```bash
python3 -m pytest tests/test_insights.py -v
```

Saída esperada: `ImportError` — `insights` não existe.

- [ ] **Step 3: Implementar insights.py**

```python
# insights.py
import pandas as pd


def pandemic_delta(df: pd.DataFrame, metric: str) -> dict:
    monthly = df.groupby(["Year", "Month", "pre_pandemic"])[metric].sum().reset_index()
    pre = float(monthly[monthly["pre_pandemic"]][metric].mean())
    post = float(monthly[~monthly["pre_pandemic"]][metric].mean())
    delta_pct = ((post - pre) / pre) * 100.0 if pre != 0 else 0.0
    return {"pre": pre, "post": post, "delta_pct": delta_pct}


def top_game(df: pd.DataFrame, metric: str = "Hours_watched") -> str:
    return str(df.groupby("Game")[metric].sum().idxmax())


def streamers_threshold(df: pd.DataFrame, pct: int = 75) -> float:
    return float(df["Streamers"].quantile(pct / 100))
```

- [ ] **Step 4: Rodar testes e confirmar passa**

```bash
python3 -m pytest tests/test_insights.py -v
```

Saída esperada: `7 passed`

- [ ] **Step 5: Rodar suite completa**

```bash
python3 -m pytest tests/ -v
```

Saída esperada: `14 passed`

- [ ] **Step 6: Commit**

```bash
git add insights.py tests/test_insights.py
git commit -m "feat: add insights module with pandemic delta, top game, and streamer threshold"
```

---

## Task 4: charts.py

**Files:**
- Create: `charts.py`

*(Funções Plotly não são testadas com TDD — verificação via dashboard manual na Task 11)*

- [ ] **Step 1: Criar charts.py**

```python
# charts.py
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from data_loader import normalize_columns


def bar_grouped(df: pd.DataFrame, metrics: list) -> go.Figure:
    records = []
    for metric in metrics:
        for flag, label in [(True, "Pré-pandemia (≤2020)"), (False, "Pós-pandemia (>2020)")]:
            avg = df[df["pre_pandemic"] == flag][metric].mean()
            records.append({"Métrica": metric, "Período": label, "Valor": avg})
    plot_df = pd.DataFrame(records)
    return px.bar(plot_df, x="Métrica", y="Valor", color="Período", barmode="group",
                  title="Média por período")


def radar_chart(df: pd.DataFrame, games: list, axes: list) -> go.Figure:
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
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1])))
    return fig


def line_timeline(df: pd.DataFrame, game: str, metric: str) -> go.Figure:
    df_game = df[df["Game"] == game].copy()
    df_game["date"] = pd.to_datetime(
        df_game["Year"].astype(str) + "-" + df_game["Month"].astype(str).str.zfill(2) + "-01"
    )
    df_game = df_game.sort_values("date")
    fig = px.line(df_game, x="date", y=metric, title=f"{game} — {metric} ao longo do tempo")
    fig.add_vline(x="2021-01-01", line_dash="dash", line_color="red",
                  annotation_text="Início pós-pandemia")
    return fig


def scatter_limiar(df: pd.DataFrame, threshold: float) -> go.Figure:
    df = df.copy()
    df["status"] = df["Streamers"].apply(
        lambda x: "Sucesso" if x >= threshold else "Abaixo do limiar"
    )
    fig = px.scatter(
        df, x="Streamers", y="score",
        color="status",
        color_discrete_map={"Sucesso": "orange", "Abaixo do limiar": "steelblue"},
        hover_data=["Game"],
        title="Limiar de Sucesso por Streamers",
    )
    fig.add_vline(x=threshold, line_dash="dash", line_color="red",
                  annotation_text=f"Limiar: {threshold:,.0f}")
    return fig
```

- [ ] **Step 2: Verificar sintaxe**

```bash
python3 -c "import charts; print('OK')"
```

Saída esperada: `OK`

- [ ] **Step 3: Commit**

```bash
git add charts.py
git commit -m "feat: add charts module with bar, radar, line, and scatter functions"
```

---

## Task 5: dashboard.py — skeleton, sidebar, e estrutura de abas

**Files:**
- Create: `dashboard.py`

- [ ] **Step 1: Criar dashboard.py com skeleton**

```python
# dashboard.py
import streamlit as st
import pandas as pd
import plotly.express as px

from data_loader import load_data, normalize_columns, NUMERIC_COLS
from insights import pandemic_delta, top_game, streamers_threshold
from charts import bar_grouped, radar_chart, line_timeline, scatter_limiar

st.set_page_config(page_title="Twitch Analytics", layout="wide")

df = load_data()

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("Filtros Globais")
    top10_default = (
        df.groupby("Game")["Hours_watched"].sum().nlargest(10).index.tolist()
    )
    selected_games = st.multiselect(
        "Jogos",
        options=sorted(df["Game"].unique()),
        default=top10_default,
    )
    metric = st.selectbox("Métrica principal", NUMERIC_COLS, index=0)

df_filtered = df[df["Game"].isin(selected_games)] if selected_games else df

# ── Tabs ─────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["Pandemia", "Radar", "Destaque", "Limiar de Sucesso", "Q&A"]
)

# placeholders — implementados nas tasks seguintes
with tab1:
    st.write("Tab 1")
with tab2:
    st.write("Tab 2")
with tab3:
    st.write("Tab 3")
with tab4:
    st.write("Tab 4")
with tab5:
    st.write("Tab 5")
```

- [ ] **Step 2: Rodar o dashboard e verificar skeleton**

```bash
cd /home/guaxinim/Documents/Projects/cp2_data && python3 -m streamlit run dashboard.py
```

Abrir `http://localhost:8501`. Verificar: sidebar com filtros, 5 abas visíveis, sem erros no terminal.

- [ ] **Step 3: Commit**

```bash
git add dashboard.py
git commit -m "feat: add dashboard skeleton with sidebar and tab structure"
```

---

## Task 6: Aba 1 — Pandemia

**Files:**
- Modify: `dashboard.py` (bloco `with tab1`)

- [ ] **Step 1: Substituir placeholder da tab1**

Substituir `with tab1: st.write("Tab 1")` por:

```python
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
```

- [ ] **Step 2: Verificar no browser**

Recarregar `http://localhost:8501`. Verificar: 3 KPIs com delta colorido (verde/vermelho), gráfico de barras agrupadas pré/pós.

- [ ] **Step 3: Commit**

```bash
git add dashboard.py
git commit -m "feat: implement pandemia tab with KPIs and grouped bar chart"
```

---

## Task 7: Aba 2 — Radar

**Files:**
- Modify: `dashboard.py` (bloco `with tab2`)

- [ ] **Step 1: Substituir placeholder da tab2**

Substituir `with tab2: st.write("Tab 2")` por:

```python
with tab2:
    st.header("Perfil de Jogos — Radar")

    axes = st.multiselect(
        "Eixos do radar",
        options=NUMERIC_COLS,
        default=["Hours_watched", "Peak_viewers", "Avg_viewers", "Streamers", "Avg_viewer_ratio"],
    )
    available_games = sorted(df_filtered["Game"].unique())
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
        st.plotly_chart(
            radar_chart(df_filtered, games_radar, axes),
            use_container_width=True,
        )
    else:
        st.info("Selecione pelo menos 1 eixo e 1 jogo.")
```

- [ ] **Step 2: Verificar no browser**

Selecionar 2-3 jogos e 4 eixos. Verificar: polígonos coloridos no radar, normalização 0–1 visível.

- [ ] **Step 3: Commit**

```bash
git add dashboard.py
git commit -m "feat: implement radar tab with selectable axes and games"
```

---

## Task 8: Aba 3 — Destaque

**Files:**
- Modify: `dashboard.py` (bloco `with tab3`)

- [ ] **Step 1: Substituir placeholder da tab3**

Substituir `with tab3: st.write("Tab 3")` por:

```python
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
        title=f"Top 10 jogos por {metric}",
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
```

- [ ] **Step 2: Verificar no browser**

Verificar: barras horizontais top 10 ordenadas, linha do tempo com marcador vermelho em jan/2021.

- [ ] **Step 3: Commit**

```bash
git add dashboard.py
git commit -m "feat: implement destaque tab with top 10 ranking and timeline"
```

---

## Task 9: Aba 4 — Limiar de Sucesso

**Files:**
- Modify: `dashboard.py` (bloco `with tab4`)

- [ ] **Step 1: Substituir placeholder da tab4**

Substituir `with tab4: st.write("Tab 4")` por:

```python
with tab4:
    st.header("Limiar de Sucesso de Streamers")
    st.markdown("Defina os pesos para compor o score de sucesso (total deve somar 100%).")

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
        ).reset_index()

        auto_threshold = streamers_threshold(df_agg)
        threshold = st.slider(
            "Limiar de Streamers",
            min_value=int(df_agg["Streamers"].min()),
            max_value=int(df_agg["Streamers"].max()),
            value=int(auto_threshold),
            step=100,
        )
        n_above = int((df_agg["Streamers"] >= threshold).sum())
        st.caption(f"{n_above} jogos acima do limiar ({n_above/len(df_agg)*100:.1f}%)")

        st.plotly_chart(scatter_limiar(df_agg, threshold), use_container_width=True)
```

- [ ] **Step 2: Verificar no browser**

Ajustar sliders de peso. Verificar: scatter com pontos laranjas/azuis, linha de limiar ajustável, contagem de jogos acima.

- [ ] **Step 3: Commit**

```bash
git add dashboard.py
git commit -m "feat: implement limiar tab with weighted score and streamer threshold"
```

---

## Task 10: Aba 5 — Q&A

**Files:**
- Modify: `dashboard.py` (bloco `with tab5` + helper `_qa_pandemic`)

- [ ] **Step 1: Adicionar helper _qa_pandemic antes das tabs**

Adicionar logo após a linha `df_filtered = ...` e antes de `tab1, tab2, ... = st.tabs(...)`:

```python
def _qa_pandemic(df: pd.DataFrame, m: str = "Hours_watched") -> str:
    delta = pandemic_delta(df, m)
    direction = "cresceu" if delta["delta_pct"] > 0 else "caiu"
    return (
        f"Sim. A média mensal de **{m.replace('_', ' ')}** "
        f"{direction} **{abs(delta['delta_pct']):.1f}%** "
        f"no período pós-pandemia (2021+) em relação a antes (≤2020)."
    )
```

- [ ] **Step 2: Substituir placeholder da tab5**

Substituir `with tab5: st.write("Tab 5")` por:

```python
with tab5:
    st.header("Perguntas & Respostas")
    st.caption("Respostas geradas automaticamente com base nos filtros ativos.")

    if st.button("Regenerar insights"):
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
```

- [ ] **Step 3: Verificar no browser**

Verificar: 3 cards com borda, pergunta em título, insight destacado, resposta textual baseada nos dados reais. Testar botão "Regenerar insights".

- [ ] **Step 4: Commit**

```bash
git add dashboard.py
git commit -m "feat: implement Q&A tab with auto-generated data-driven answers"
```

---

## Task 11: Smoke Test e Integração Final

**Files:**
- No changes — verificação manual e execução da suite de testes

- [ ] **Step 1: Rodar suite completa de testes**

```bash
cd /home/guaxinim/Documents/Projects/cp2_data && python3 -m pytest tests/ -v
```

Saída esperada: `14 passed`

- [ ] **Step 2: Iniciar o dashboard**

```bash
python3 -m streamlit run dashboard.py
```

- [ ] **Step 3: Verificar golden path em cada aba**

| Aba | O que verificar |
|---|---|
| Pandemia | 3 KPIs com delta, barras agrupadas pré/pós |
| Radar | Radar normalizado com 3 jogos padrão |
| Destaque | Top 10 barras horizontais + linha do tempo |
| Limiar | Scatter laranja/azul com slider funcional |
| Q&A | 3 cards com respostas baseadas nos dados |

- [ ] **Step 4: Testar edge case — sidebar sem jogos selecionados**

Limpar o multiselect de jogos na sidebar. Verificar: dashboard continua funcionando (usa `df` completo pelo `if selected_games else df`).

- [ ] **Step 5: Commit final**

```bash
git add .
git commit -m "chore: final integration verified — all tabs and tests passing"
```
