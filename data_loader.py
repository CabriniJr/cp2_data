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
    df = df.dropna(subset=["Game"]).reset_index(drop=True)
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce").astype("Int64")
    df["Month"] = pd.to_numeric(df["Month"], errors="coerce").astype("Int64")
    df = df.dropna(subset=["Year", "Month"]).reset_index(drop=True)
    df["Year"] = df["Year"].astype(int)
    df["Month"] = df["Month"].astype(int)
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
