from pathlib import Path
import pandas as pd


def load_results(path: str | Path = "data/processed/results.csv") -> pd.DataFrame:
    return pd.read_csv(Path(path))
