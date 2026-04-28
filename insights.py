import math
import pandas as pd


def pandemic_delta(df: pd.DataFrame, metric: str) -> dict:
    monthly = df.groupby(["Year", "Month", "pre_pandemic"])[metric].sum().reset_index()
    pre_series = monthly[monthly["pre_pandemic"]][metric]
    post_series = monthly[~monthly["pre_pandemic"]][metric]
    pre = float(pre_series.mean()) if not pre_series.empty else 0.0
    post = float(post_series.mean()) if not post_series.empty else 0.0
    if math.isnan(pre):
        pre = 0.0
    if math.isnan(post):
        post = 0.0
    delta_pct = ((post - pre) / pre) * 100.0 if pre != 0 else 0.0
    return {"pre": pre, "post": post, "delta_pct": delta_pct}


def top_game(df: pd.DataFrame, metric: str = "Hours_watched") -> str:
    df_clean = df.dropna(subset=["Game", metric])
    if df_clean.empty:
        return "—"
    grouped = df_clean.groupby("Game")[metric].sum()
    if grouped.empty:
        return "—"
    return str(grouped.idxmax())


def streamers_threshold(df: pd.DataFrame, pct: int = 75) -> float:
    series = df["Streamers"].dropna()
    if series.empty:
        return 0.0
    return float(series.quantile(pct / 100))


def descriptive_stats(df: pd.DataFrame, cols: list) -> pd.DataFrame:
    rows = []
    for col in cols:
        s = df[col].dropna()
        if s.empty:
            continue
        mode_vals = s.mode()
        mode_val = float(mode_vals.iloc[0]) if not mode_vals.empty else float("nan")
        q1 = float(s.quantile(0.25))
        q3 = float(s.quantile(0.75))
        rows.append({
            "Métrica": col,
            "Média": float(s.mean()),
            "Mediana": float(s.median()),
            "Moda": mode_val,
            "Desvio Padrão": float(s.std()),
            "Variância": float(s.var()),
            "Mín": float(s.min()),
            "Q1": q1,
            "Q3": q3,
            "Máx": float(s.max()),
            "IQR": q3 - q1,
        })
    return pd.DataFrame(rows)


def top_correlated_pairs(df: pd.DataFrame, cols: list, n: int = 3) -> list:
    corr = df[cols].corr().abs()
    pairs = []
    for i, a in enumerate(cols):
        for b in cols[i + 1:]:
            r = float(df[[a, b]].corr().iloc[0, 1])
            pairs.append((a, b, r))
    pairs.sort(key=lambda x: abs(x[2]), reverse=True)
    return pairs[:n]
