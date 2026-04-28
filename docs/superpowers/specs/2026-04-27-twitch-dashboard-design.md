# Twitch Game Data — Dashboard Design

**Date:** 2026-04-27
**Stack:** Python 3.14, Streamlit, Plotly, Pandas
**Data source:** `Twitch_game_data.csv` (21 000 linhas, 2016–2024, encoding latin-1)

---

## Objetivo

Dashboard interativo para responder três perguntas analíticas sobre dados de jogos na Twitch:

1. O perfil de interação mudou a partir da pandemia?
2. Tem algum jogo que se destacou mais?
3. A partir de qual número de streamers um jogo faz sucesso?

---

## Coluna Derivada

Criada no carregamento do CSV:

```python
df["pre_pandemic"] = df["Year"] <= 2020  # True = antes/durante 2020, False = 2021+
```

---

## Estrutura do Dashboard

### Layout

- **`st.tabs`** com 4 abas na área principal
- **Sidebar** com filtros globais que afetam todas as abas:
  - Multiselect de jogos (padrão: top 10 por Hours_watched)
  - Seletor de métrica principal (`Hours_watched`, `Peak_viewers`, `Avg_viewers`, `Streamers`, `Avg_viewer_ratio`, `Hours_streamed`)

---

### Aba 1 — Pandemia

**Pergunta:** O perfil de interação mudou a partir da pandemia?

- **3 KPIs** no topo: variação percentual de `Hours_watched`, `Avg_viewers` e `Peak_viewers` entre pré (≤2020) e pós (>2020)
- **Gráfico de barras agrupadas** (Plotly): médias das métricas numéricas principais, agrupadas por `pre_pandemic`
- Cor diferente para pré vs pós

---

### Aba 2 — Radar

**Objetivo:** Comparar perfis de jogos visualmente.

- **Multiselect de eixos:** usuário escolhe quais colunas numéricas compõem o radar (padrão: `Hours_watched`, `Peak_viewers`, `Avg_viewers`, `Streamers`, `Avg_viewer_ratio`)
- **Multiselect de jogos** para comparar (até 5; usa filtro da sidebar como ponto de partida)
- **Radar chart normalizado** min-max (0–1) via Plotly `go.Scatterpolar`
- Cada jogo = uma linha/polígono colorido

---

### Aba 3 — Jogos em Destaque

**Pergunta:** Tem algum jogo que se destacou mais?

- **Top 10 ranking** por métrica selecionada na sidebar (barras horizontais)
- **Linha do tempo** do jogo #1: `Avg_viewers` ao longo dos meses, com linha vertical em jan/2021 marcando pós-pandemia
- Destaque visual (fundo cinza) para o período pré-pandemia no gráfico de linha

---

### Aba 4 — Limiar de Sucesso

**Pergunta:** A partir de qual número de streamers um jogo faz sucesso?

**Métrica combinada de sucesso:**

```
score = w1*Hours_watched_norm + w2*Peak_viewers_norm + w3*Avg_viewers_norm + w4*Avg_viewer_ratio_norm
```

- Pesos `w1..w4` definidos por sliders (padrão: 25% cada; soma forçada = 100%)
- Cada coluna normalizada min-max antes da combinação

**Visualização:**

- **Scatter plot**: eixo X = `Streamers`, eixo Y = `score`
- **Limiar automático** = percentil 75 de `Streamers` (calculado sobre os dados filtrados)
- **Slider manual** para ajustar o limiar (range: min–max de `Streamers`)
- Pontos acima do limiar destacados em laranja, abaixo em azul
- Tooltip com nome do jogo, score, Streamers, Year

---

### Aba 5 — Perguntas & Respostas

**Objetivo:** Slide de apresentação com as respostas diretas às três perguntas.

- Layout em cards estilizados (`st.container` com `st.markdown`)
- Cada card contém:
  - A pergunta em destaque (negrito/título)
  - A resposta gerada a partir dos dados reais (calculada no carregamento)
  - O número-chave ou insight principal (ex: "Hours watched cresceu 47% pós-pandemia")
- Sem interatividade — conteúdo fixo para apresentação
- Botão "Regenerar insights" recalcula as respostas com os filtros da sidebar ativos

**Respostas geradas automaticamente:**

| Pergunta | Fonte do dado |
|---|---|
| Mudou o perfil pós-pandemia? | Variação % das médias pré vs pós |
| Qual jogo se destacou mais? | Jogo com maior `Hours_watched` total |
| Limiar de sucesso de streamers? | Percentil 75 de `Streamers` dos jogos acima da mediana de score |

---

## Dados e Pré-processamento

- Encoding: `latin-1`
- Coluna `pre_pandemic`: `Year <= 2020`
- Normalização min-max aplicada por coluna apenas onde necessário (Aba 2 e Aba 4)
- Cache com `@st.cache_data` no carregamento do CSV

---

## Arquivos

```
cp2_data/
├── Twitch_game_data.csv
├── dashboard.py          # arquivo principal Streamlit
└── docs/
    └── superpowers/
        └── specs/
            └── 2026-04-27-twitch-dashboard-design.md
```

---

## Fora de Escopo

- Autenticação ou login
- Dados em tempo real
- Export de relatórios
- Mobile responsiveness
