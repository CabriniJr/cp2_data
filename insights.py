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
