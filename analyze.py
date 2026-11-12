"""Command-line entry point.

Example:
    python analyze.py --data data/postings.csv --profile profile.json --out reports
"""

import argparse
import json
from pathlib import Path

from analyzer.analysis import load_postings, match_postings, pay_summary, skill_counts, skill_gaps, skills_by_track
from analyzer.report import chart_top_skills, chart_track_heatmap, write_report


def main(argv=None):
    parser = argparse.ArgumentParser(description="Find which skills remote job postings ask for.")
    parser.add_argument("--data", default="data/postings.csv", help="CSV of job postings")
    parser.add_argument("--profile", default="profile.json", help="JSON with name and skills")
    parser.add_argument("--out", default="reports", help="folder for the report and charts")
    args = parser.parse_args(argv)

    profile = json.loads(Path(args.profile).read_text())
    have = set(profile["skills"])
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    df = load_postings(args.data)
    counts = skill_counts(df)
    matches = match_postings(df, have)
    gaps = skill_gaps(df, have)
    pay = pay_summary(df)

    chart_top_skills(counts, have, out / "top_skills.png")
    chart_track_heatmap(skills_by_track(df), out / "skills_by_track.png")
    counts.to_csv(out / "skill_counts.csv", index=False)
    matches.assign(skills=matches["skills"].map("; ".join), missing=matches["missing"].map("; ".join)).to_csv(
        out / "matches.csv", index=False
    )
    write_report(out, df, counts, matches, gaps, pay, profile.get("name", "candidate"))

    print(f"Analyzed {len(df)} postings. Top skills:")
    for _, row in counts.head(5).iterrows():
        print(f"  {row['skill']:<32} {row['postings']:>2} postings ({row['share']:.0%})")
    print(f"Report written to {out / 'report.md'}")


if __name__ == "__main__":
    main()
