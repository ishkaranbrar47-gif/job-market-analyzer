"""Charts and a Markdown report."""

from pathlib import Path

import matplotlib
import pandas as pd

matplotlib.use("Agg")  # render to files, no display needed
import matplotlib.pyplot as plt  # noqa: E402

TRACK_LABELS = {
    "software": "Software dev",
    "support": "Tech support",
    "data": "Data analysis",
    "ai_training": "AI training",
    "trust_safety": "Trust & safety",
    "ux_research": "UX research",
}


def chart_top_skills(counts, have, path, top_n=15):
    top = counts.head(top_n).iloc[::-1]
    colors = ["#0E7C66" if s in have else "#B8C2CC" for s in top["skill"]]
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.barh(top["skill"], top["postings"], color=colors)
    ax.set_xlabel("Number of postings that mention it")
    ax.set_title("Most requested skills across remote entry-level postings")
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.xaxis.grid(True, color="#E5E8EB")
    ax.set_axisbelow(True)
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in ("#0E7C66", "#B8C2CC")]
    ax.legend(handles, ["Have it", "Gap"], loc="lower right", frameon=False)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def chart_track_heatmap(matrix, path, top_n=15):
    top = matrix.loc[matrix.sum(axis=1).sort_values(ascending=False).index[:top_n]]
    top = top.rename(columns=TRACK_LABELS)
    fig, ax = plt.subplots(figsize=(9, 7))
    im = ax.imshow(top.values, cmap="Greens", vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(len(top.columns)), top.columns, rotation=30, ha="right")
    ax.set_yticks(range(len(top.index)), top.index)
    for i in range(top.shape[0]):
        for j in range(top.shape[1]):
            v = top.values[i, j]
            if v > 0:
                ax.text(j, i, f"{v:.0%}", ha="center", va="center", fontsize=8,
                        color="white" if v > 0.6 else "#16202B")
    ax.set_title("Share of each track's postings that mention a skill")
    fig.colorbar(im, ax=ax, fraction=0.03, format=lambda x, _: f"{x:.0%}")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def _md_table(df, columns):
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    for _, row in df.iterrows():
        lines.append("| " + " | ".join(str(row[c]) for c in columns) + " |")
    return "\n".join(lines)


def write_report(out_dir, df, counts, matches, gaps, pay, profile_name):
    out = Path(out_dir)
    m = matches.dropna(subset=["match"]).copy()
    m["match"] = (m["match"] * 100).round().astype(int).astype(str) + "%"
    m["missing"] = m["missing"].map(lambda s: ", ".join(s) or "none")
    m["years asked"] = m["min_years"].map(lambda y: "not stated" if pd.isna(y) else f"{int(y)}+")
    g = gaps.head(10).copy()
    g["share"] = (g["share"] * 100).round().astype(int).astype(str) + "%"
    p = pay.copy()
    p["track"] = p["track"].map(lambda t: TRACK_LABELS.get(t, t))
    p["median_annual"] = p["median_annual"].map(lambda v: f"{v:,.0f}")

    text = f"""# Remote Job Market Report

{len(df)} postings across {df['track'].nunique()} tracks. Profile: **{profile_name}**.

![Top skills](top_skills.png)

## Best-matching postings

Match = share of the skills a posting names that this profile has. "Years asked" is the lowest
experience figure the posting states; check it before applying.

{_md_table(m.head(10), ["title", "company", "track", "match", "years asked", "missing"])}

## Biggest skill gaps

Skills this profile doesn't list yet, ranked by how many postings ask for them.

{_md_table(g, ["skill", "category", "postings", "share"])}

## Pay by track

Yearly midpoint of posted ranges; hourly rates x 2,080 hours. Currencies are not converted.
Most AI-training work is part-time contract work, so those yearly figures show the full-time
equivalent, not typical earnings.

{_md_table(p, ["track", "currency", "postings", "median_annual"])}

![Skills by track](skills_by_track.png)
"""
    (out / "report.md").write_text(text)
