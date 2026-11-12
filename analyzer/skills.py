"""Skill taxonomy and extraction.

Each skill maps to one or more regular expressions. Patterns use custom
boundaries instead of \\b so that names with symbols (C++, Node.js, CI/CD)
match correctly and short names (R) don't match inside other words.
"""

import re


def _word(text):
    """Match `text` (a regex fragment) as a whole token, case-insensitively.

    The boundaries treat + and # as part of a word, so "C" never matches
    inside "C++" and "Java" never matches inside "JavaScript".
    """
    return re.compile(rf"(?<![\w+#])({text})(?![\w+#])", re.IGNORECASE)


TAXONOMY = {
    "Programming languages": {
        "Python": [_word("python")],
        "Java": [_word("java")],  # (?![\w+#]) stops it matching JavaScript
        "JavaScript": [_word("javascript")],
        "TypeScript": [_word("typescript")],
        "C++": [re.compile(r"(?<![\w+#])C\+\+(?![\w+#])")],
        "SQL": [_word("sql")],
        "R": [re.compile(r"(?<![\w&'])R(?![\w&+#'])")],  # case-sensitive on purpose
    },
    "Frameworks and platforms": {
        "React": [_word("react")],
        "Node.js": [_word(r"node\.js")],
        "Next.js": [_word(r"next\.js")],
        "Django": [_word("django")],
        "Google Cloud": [_word("google cloud")],
        "SaaS": [_word("saas")],
    },
    "Engineering practices": {
        "CI/CD": [_word(r"ci/cd"), _word("jenkins")],
        "Agile": [_word("agile"), _word("scrum")],
        "APIs (REST/JSON)": [_word("rest"), _word("json"), _word("apis?")],
        "Code review": [_word("code reviews?"), _word("review code")],
        "Security and auth": [_word("security"), _word("sso"), _word("oauth"), _word("adfs")],
        "Networking": [_word("networking"), _word("dns"), _word(r"tcp/ip"), _word("vpns?")],
    },
    "Data and analytics": {
        "Excel / Google Sheets": [_word("excel"), _word("google sheets"), _word("macros")],
        "BI dashboards": [_word("power bi"), _word("looker"), _word("dashboards?"), _word("visuali[sz]ations?")],
        "ETL and data validation": [_word("etl"), _word("data validation"), _word("data import pipelines?")],
        "Statistics": [_word("statistics"), _word("statistical")],
        "Machine learning": [_word("machine learning")],
    },
    "Support and operations tools": {
        "Ticketing (Zendesk, JIRA, ITSM)": [
            _word("zendesk"), _word("jira"), _word("itsm"), _word("servicenow"),
            _word("freshdesk"), _word("topdesk"), _word("intercom"), _word("support tickets?"),
        ],
        "ITIL": [_word("itil")],
        "Troubleshooting": [_word("troubleshooting"), _word("root cause analysis")],
        "Knowledge base and docs": [_word("knowledge base"), _word("documentation")],
    },
    "Human and domain skills": {
        "Communication": [_word("communication"), _word("explain concepts")],
        "Collaboration": [_word("collaboration")],
        "Attention to detail": [_word("attention to detail")],
        "Judgement and decisions": [_word("judgement"), _word("judgment"), _word("decision-making")],
        "Policy and fraud": [_word("policy enforcement"), _word("fraud detection"), _word("moderation")],
        "User research": [
            _word("user research"), _word("ux research"), _word("human-computer interaction"), _word("hci"),
        ],
    },
    "Degrees named": {
        "Computer Science degree": [_word("computer science")],
        "Psychology degree": [_word("psychology"), _word("cognitive science"), _word("behavioural science")],
    },
}

SKILL_TO_CATEGORY = {skill: cat for cat, skills in TAXONOMY.items() for skill in skills}


_YEARS = re.compile(r"(\d+)\s*(?:\+|-\s*\d+)?\s*\+?\s*years?", re.IGNORECASE)


def extract_min_years(text):
    """Smallest years-of-experience figure in the text ("1-3 years" -> 1, "5+ years" -> 5).

    Returns None when no figure is given. When several are given (for example
    "MS with 3+ years, or BS with 5+ years") the smallest is the lowest bar to entry.
    """
    if not isinstance(text, str):
        return None
    found = [int(m.group(1)) for m in _YEARS.finditer(text)]
    return min(found) if found else None


def extract_skills(text):
    """Return the sorted list of skills mentioned in `text`."""
    if not isinstance(text, str) or not text:
        return []
    found = set()
    for skills in TAXONOMY.values():
        for skill, patterns in skills.items():
            if any(p.search(text) for p in patterns):
                found.add(skill)
    return sorted(found)
