"""Score jobs against a profile with simple, explainable signals."""
import re

PROFILE = {
    "target_titles": ["machine learning engineer", "ml engineer", "ai engineer",
                      "applied scientist", "research engineer", "data scientist"],
    "skills": ["python", "pytorch", "cuda", "tensorflow", "xgboost", "mlflow",
               "airflow", "docker", "kubernetes", "fastapi", "sql", "llm", "rag"],
    "entry_level_terms": ["new grad", "new graduate", "entry level", "early career", "junior"],
    "preferred_locations": ["new york", "boston", "san francisco", "seattle"],
    "exclude_title_terms": ["senior", "sr", "staff", "principal", "director",
                            "manager", "head of", "lead", "intern", "internship"],
}   

def normalize(text):
    """Lowercase, replace punctuation with spaces, and pad with spaces."""
    return " " + re.sub(r"[^a-z0-9+#]+", " ", (text or "").lower()) + " "


def has(text, phrase):
    """True if `phrase` appears as whole words in normalized `text`."""
    return f" {phrase} " in text


def score_job(job, profile=PROFILE):
    """Return (score, reasons, excluded_reason_or_None)."""
    title = normalize(job["title"])
    body = normalize(job["description"])
    location = normalize(job["location"])
    reasons = []

    # TODO 1: hard filter. If any exclude term is in the title,
    #         return (0, [], f"title contains '{term}'")
    for term in profile["exclude_title_terms"]:
        if has(title, term):
            return 0.0, [], f"title contains '{term}'"

    score = 0.0

    # TODO 2: title match. If any target title is in the title,
    #         add 3 points and a reason like "title matches 'ml engineer'"
    for target in profile["target_titles"]:
        if has(title, target):
            score += 3.0
            reasons.append(f"title matches '{target}'")
            break  # stop after first match (no double counting)

    # TODO 3: skills. Build a list of the skills found in title OR body.
    #         add 0.4 per skill, but count at most 8 skills
    #         reason: "5 skills: python, pytorch, docker..."
    found_skills = []
    for skill in profile["skills"]:
        if has(title, skill) or has(body, skill):
            found_skills.append(skill)

    # cap at 8 skills, but always show at least 1 if found
    if len(found_skills) > 8:
        found_skills = found_skills[:8]

    if found_skills:
        score += 0.4 * len(found_skills)
        reasons.append(f"{len(found_skills)} skills: {', '.join(found_skills)}")

    # TODO 4: entry-level wording in title or body -> +1 and a reason
    for term in profile["entry_level_terms"]:
        if has(title, term) or has(body, term):
            score += 1.0
            reasons.append(f"entry-level ({term})")
            break  # one point only

    # TODO 5: location. "remote" in location -> +0.5,
    #         otherwise a preferred location -> +0.8, each with a reason
    if has(location, "remote"):
        score += 0.5
        reasons.append("remote")
    else:
        for preferred in profile["preferred_locations"]:
            if has(location, preferred):
                score += 0.8
                reasons.append(f"preferred location: {preferred}")
                break

    return round(score, 2), reasons, None


def rank(jobs, profile=PROFILE):
    """Return (kept_sorted_best_first, excluded)."""
    kept, excluded = [], []
    for job in jobs:
        score, reasons, why_out = score_job(job, profile)
        # TODO 6: put (job, score, reasons) into `kept`,
        #         or (job, why_out) into `excluded`
        if why_out:
            excluded.append((job, why_out))
        else:
            kept.append((job, score, reasons))
            
    # TODO 7: sort `kept` by score, highest first
    #         hint: kept.sort(key=lambda item: item[1], reverse=True)
    kept.sort(key=lambda item: item[1], reverse=True)


    return kept, excluded


if __name__ == "__main__":
    from sources import fetch_all
    jobs, errors = fetch_all({"greenhouse": ["anthropic"], "lever": ["palantir"], "ashby": ["openai"]})
    kept, excluded = rank(jobs)
    print(f"{len(jobs)} fetched, {len(excluded)} filtered out, {len(kept)} ranked\n")
    for job, score, reasons in kept[:5]:
        print(f"{score:>5}  {job['title']} ({job['company']})")
        print(f"       {'; '.join(reasons)}")