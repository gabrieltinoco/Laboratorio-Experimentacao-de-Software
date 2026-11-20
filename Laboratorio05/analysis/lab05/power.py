import numpy as np
from scipy.stats import mannwhitneyu


def simulate_power(x, y, n: int, n_sim: int = 2000, alpha: float = 0.05, seed: int = 20262) -> float:
    rng = np.random.default_rng(seed)
    x = np.asarray(x)
    y = np.asarray(y)
    significant = 0
    for _ in range(n_sim):
        sample_x = rng.choice(x, size=n, replace=True)
        sample_y = rng.choice(y, size=n, replace=True)
        pvalue = mannwhitneyu(sample_x, sample_y, alternative="two-sided").pvalue
        if pvalue < alpha:
            significant += 1
    return significant / n_sim
