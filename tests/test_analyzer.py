import json

import pandas as pd
import pytest

import analyze
from analyzer.analysis import annual_pay_midpoint, load_postings, match_postings, pay_summary, skill_counts
from analyzer.skills import extract_min_years, extract_skills

# --- skill extraction edge cases ---------------------------------------------


def test_java_does_not_match_javascript():
    assert extract_skills("Strong JavaScript skills") == ["JavaScript"]


def test_cpp_matches_with_symbols():
    assert "C++" in extract_skills("Experience in C++ and Python")


def test_r_only_matches_as_a_standalone_capital():
    assert "R" in extract_skills("SQL, Python, R, Excel")
    assert "R" not in extract_skills("Research and R&D roles; React")


def test_nodejs_and_cicd():
    skills = extract_skills("Node.js services deployed with CI/CD")
    assert {"Node.js", "CI/CD"} <= set(skills)


def test_synonyms_map_to_one_skill():
    assert extract_skills("We use Jenkins") == ["CI/CD"]
    assert extract_skills("Tickets live in Zendesk and JIRA") == ["Ticketing (Zendesk, JIRA, ITSM)"]


@pytest.mark.parametrize(
    "text, years",
    [
        ("1-3 years technical support", 1),
        ("Minimum 5+ years experience", 5),
        ("MS with 3+ years, or BS with 5+ years", 3),
        ("0-2 years moderation", 0),
        ("No experience required", None),
    ],
)
def test_extract_min_years(text, years):
    assert extract_min_years(text) == years


def test_empty_text():
    assert extract_skills("") == []
    assert extract_skills(None) == []


# --- pay normalisation -------------------------------------------------------


def test_hourly_pay_is_annualised():
    row = pd.Series({"pay_min": 25.0, "pay_max": 35.0, "pay_unit": "hour"})
    assert annual_pay_midpoint(row) == 62400  # 30 x 2080


def test_single_ended_range():
    row = pd.Series({"pay_min": float("nan"), "pay_max": 50000.0, "pay_unit": "year"})
    assert annual_pay_midpoint(row) == 50000


def test_no_pay_returns_none():
    row = pd.Series({"pay_min": float("nan"), "pay_max": float("nan"), "pay_unit": ""})
    assert annual_pay_midpoint(row) is None


# --- analysis on a small CSV --------------------------------------------------


@pytest.fixture
def postings(tmp_path):
    path = tmp_path / "p.csv"
    pd.DataFrame(
        [
            {"title": "Dev", "company": "A", "location": "x", "track": "software", "pay_min": 60000,
             "pay_max": 80000, "currency": "CAD", "pay_unit": "year", "requirements": "Python; SQL; React"},
            {"title": "Analyst", "company": "B", "location": "x", "track": "data", "pay_min": 30,
             "pay_max": 30, "currency": "CAD", "pay_unit": "hour", "requirements": "SQL; Excel"},
            {"title": "Support", "company": "C", "location": "x", "track": "support", "pay_min": None,
             "pay_max": None, "currency": None, "pay_unit": None, "requirements": "Zendesk; SQL"},
        ]
    ).to_csv(path, index=False)
    return path


def test_skill_counts(postings):
    counts = skill_counts(load_postings(postings)).set_index("skill")
    assert counts.loc["SQL", "postings"] == 3
    assert counts.loc["SQL", "share"] == 1.0
    assert counts.loc["Python", "postings"] == 1


def test_match_scores_and_missing(postings):
    m = match_postings(load_postings(postings), {"Python", "SQL"})
    top = m.iloc[0]
    assert top["company"] == "A"
    assert top["match"] == pytest.approx(0.67, abs=0.01)
    assert top["missing"] == ["React"]


def test_pay_summary_skips_unpaid(postings):
    pay = pay_summary(load_postings(postings))
    assert set(pay["track"]) == {"software", "data"}
    assert pay.set_index("track").loc["data", "median_annual"] == 62400


def test_missing_columns_rejected(tmp_path):
    path = tmp_path / "bad.csv"
    path.write_text("title,company\nDev,A\n")
    with pytest.raises(ValueError, match="missing columns"):
        load_postings(path)


# --- end to end ---------------------------------------------------------------


def test_cli_writes_report_and_charts(postings, tmp_path, capsys):
    profile = tmp_path / "profile.json"
    profile.write_text(json.dumps({"name": "Test", "skills": ["Python", "SQL"]}))
    out = tmp_path / "out"
    analyze.main(["--data", str(postings), "--profile", str(profile), "--out", str(out)])
    for name in ("report.md", "top_skills.png", "skills_by_track.png", "skill_counts.csv", "matches.csv"):
        assert (out / name).exists(), name
    assert "Analyzed 3 postings" in capsys.readouterr().out
