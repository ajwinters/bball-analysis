"""One plot style for every analysis, and a save helper that files figures in place.

    from bball import style
    style.use()
    fig, ax = plt.subplots()
    ...
    style.save(fig, "deflections-by-season", mo.notebook_dir())
"""

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt


def use() -> None:
    mpl.rcParams.update(
        {
            "figure.figsize": (8, 4.5),
            "figure.dpi": 110,
            "savefig.dpi": 150,
            "savefig.bbox": "tight",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.alpha": 0.3,
            "axes.titlesize": 13,
            "axes.titleweight": "bold",
            "axes.titlelocation": "left",
            "font.size": 10,
            "legend.frameon": False,
        }
    )


def save(fig: plt.Figure, name: str, folder: Path | str, fmt: str = "png") -> Path:
    """Save to <folder>/_figures/<name>.<fmt> and return the path."""
    out = Path(folder) / "_figures" / f"{name}.{fmt}"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out)
    return out


def save_table(df, name: str, folder: Path | str) -> Path:
    """Save a small result table to <folder>/_tables/<name>.csv (committed; keep it small)."""
    out = Path(folder) / "_tables" / f"{name}.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    return out
