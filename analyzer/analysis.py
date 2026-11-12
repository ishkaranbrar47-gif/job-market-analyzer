"""Load postings, extract skills, and compute the numbers the report uses."""

import pandas as pd

from .skills import SKILL_TO_CATEGORY, extract_min_years, extract_skills

HOURS_PER_YEAR = 2080  # 40 hours x 52 weeks, the usual full-time conversion


def load_postings(path):
    df = pd.read_csv(path)
    required = {"title", "company", "track", "requirements"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"CSV is missing columns: {', '.join(sorted(missing))}")
    df["requirements"] = df["requirements"].fillna("")
    df["skills"] = (df["title"].fillna("") + "; " + df["requirements"]).map(extract_skills)
    df["min_years"] = df["requirements"].map(extract_min_years).astype("Int64")
    df["annual_pay_mid"] = df.apply(annual_pay_midpoint, axis=1)
    return df


def annual_pay_midpoint(row):
    """Midpoint of the posted range, converted to a yearly figure. None if no pay given."""
    lo, hi = row.get("pay_min"), row.get("pay_max")
    if pd.isna(lo) and pd.isna(hi):
        return None
    lo = hi if pd.isna(lo) else lo
    hi = lo if pd.isna(hi) else hi
    mid = (float(lo) + float(hi)) / 2
    if str(row.get("pay_unit", "")).lower() == "hour":
        mid *= HOURS_PER_YEAR
    return round(mid)


def skill_counts(df):
    """How many postings mention each skill, with share of all postings."""
    exploded = df[["track", "skills"]].explode("skills").dropna(subset=["skills"])
    counts = exploded["skills"].value_counts().rename_axis("skill").reset_index(name="postings")
    counts["share"] = (counts["postings"] / len(df)).round(3)
    counts["category"] = counts["skill"].map(SKILL_TO_CATEGORY)
    return counts


def skills_by_track(df):
    """Matrix of track x skill, each cell = share of that track's postings."""
    exploded = df[["track", "skills"]].explode("skills").dropna(subset=["skills"]).reset_index(drop=True)
    table = pd.crosstab(exploded["skills"], exploded["track"]).rename_axis(index="skill")
    track_sizes = df["track"].value_counts()
    return (table / track_sizes).round(2)


def match_postings(df, profile_skills):
    """Score each posting by the share of its detected skills the candidate has."""
    have = set(profile_skills)

    def score(skills):
        if not skills:
            return None
        return round(len(have & set(skills)) / len(skills), 2)

    out = df[["title", "company", "location", "track", "skills", "min_years"]].copy()
    out["match"] = df["skills"].map(score)
    out["missing"] = df["skills"].map(lambda s: sorted(set(s) - have))
    # Rank by skill match first; among equal matches, lower experience bars first.
    out["_years_sort"] = out["min_years"].fillna(0)
    out = out.sort_values(["match", "_years_sort"], ascending=[False, True], na_position="last")
    return out.drop(columns="_years_sort").reset_index(drop=True)


def skill_gaps(df, profile_skills):
    """Skills the candidate lacks, ranked by how many postings ask for them."""
    counts = skill_counts(df)
    return counts[~counts["skill"].isin(set(profile_skills))].reset_index(drop=True)


def pay_summary(df):
    """Median yearly pay midpoint per track and currency (no currency conversion)."""
    paid = df.dropna(subset=["annual_pay_mid"])
    if paid.empty:
        return pd.DataFrame(columns=["track", "currency", "postings", "median_annual"])
    return (
        paid.groupby(["track", "currency"])["annual_pay_mid"]
        .agg(postings="count", median_annual="median")
        .reset_index()
        .sort_values(["currency", "median_annual"], ascending=[True, False])
    )
