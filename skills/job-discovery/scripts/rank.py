"""Score jobs against a profile with simple, explainable signals."""
import re


def normalize(text):
    """Lowercase, replace punctuation with spaces, and pad with spaces."""
    if text is None:
        return ""
    text = text.lower()
    text = re.sub(r"[^a-z0-9+#]+", " ", text).strip()
    return f" {text} "


def has(text, phrase):
    """True if `phrase` appears as whole words in normalized `text`."""
    if text is None or phrase is None:
        return False
    return normalize(phrase) in text


def score_job(job, profile, weights):
    """Return (score, reasons, excluded_reason_or_None)."""
    title = normalize(job["title"])
    body = normalize(job["description"])
    location = normalize(job["location"])
    reasons = []

    for term in profile["exclude_title_terms"]:
        if has(title, term):
            return 0.0, [], f"title contains '{term}'"

    score = 0.0

    for target in profile["target_titles"]:
        if has(title, target):
            score += weights["title"]
            reasons.append(f"title matches '{target}'")
            break  # stop after first match (no double counting)

    found_skills = []
    for skill in profile["skills"]:
        if has(title, skill) or has(body, skill):
            found_skills.append(skill)

    # cap at skills_cap
    if len(found_skills) > weights["skills_cap"]:
        found_skills = found_skills[:weights["skills_cap"]]

    if found_skills:
        score += weights["skill"] * len(found_skills)
        reasons.append(f"{len(found_skills)} skills: {', '.join(found_skills)}")

    for term in profile["entry_level_terms"]:
        if has(title, term) or has(body, term):
            score += weights["entry_level"]
            reasons.append(f"entry-level ({term})")
            break  # one point only

    if has(location, "remote"):
        score += weights["remote"]
        reasons.append("remote")
    else:
        for preferred in profile["preferred_locations"]:
            if has(location, preferred):
                score += weights["location"]
                reasons.append(f"preferred location: {preferred}")
                break

    return round(score, 2), reasons, None


def rank(jobs, profile, weights):
    """Return (kept_sorted_best_first, excluded)."""
    kept, excluded = [], []
    for job in jobs:
        score, reasons, why_out = score_job(job, profile, weights)
        if why_out:
            excluded.append((job, why_out))
        else:
            kept.append((job, score, reasons))

    kept.sort(key=lambda item: item[1], reverse=True)
    return kept, excluded


if __name__ == "__main__":
    import json
    from pathlib import Path
    from sources import fetch_all

    config_path = Path(__file__).parent.parent / "config.json"
    config = json.loads(config_path.read_text())

    jobs, errors = fetch_all(config["companies"])
    kept, excluded = rank(jobs, config["profile"], config["weights"])
    print(f"{len(jobs)} fetched, {len(excluded)} filtered out, {len(kept)} ranked\n")
    for job, score, reasons in kept[:5]:
        print(f"{score:>5}  {job['title']} ({job['company']})")
        print(f"       {'; '.join(reasons)}")