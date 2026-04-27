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
