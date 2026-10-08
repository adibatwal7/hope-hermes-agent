"""Fetch job postings from Greenhouse, Lever, and Ashby public job-board APIs.

Every fetcher returns a list of dicts with the same keys:
    id, company, title, location, url, description
"""
import html
import json
import re
import urllib.request

TIMEOUT = 20
HEADERS = {"User-Agent": "hermes-job-fetcher/1.0"}


def get_json(url):
    """Download a URL and parse it as JSON."""
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.load(resp)


def to_text(raw):
    """Turn Greenhouse's HTML description into plain text."""
    if not raw:
        return ""
    text = html.unescape(html.unescape(raw))   # Greenhouse escapes HTML twice
    text = re.sub(r"<[^>]+>", " ", text)       # drop tags like <p>
    return re.sub(r"\s+", " ", text).strip()   # collapse whitespace


def fetch_greenhouse(company):
    data = get_json(f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs?content=true")
    jobs = []
    for job in data.get("jobs", []):
        jobs.append({
            "id": f"greenhouse:{company}:{job['id']}",
            "company": company,
            "title": job.get("title", ""),
            "location": (job.get("location") or {}).get("name", ""),
            "url": job.get("absolute_url", ""),
            "description": to_text(job.get("content")),
        })
    return jobs


def fetch_lever(company):
    data = get_json(f"https://api.lever.co/v0/postings/{company}?mode=json")
    # Lever returns a LIST. A bad company name returns {"ok": false, ...} instead.
    if isinstance(data, dict):
        raise ValueError(data.get("error", "unexpected Lever response"))
    jobs = []
    for job in data:
        categories = job.get("categories") or {}
        jobs.append({
            "id": f"lever:{company}:{job['id']}",
            "company": company,
            "title": job.get("text", ""),             # Lever calls the title "text"
            "location": categories.get("location", ""),
            "url": job.get("hostedUrl", ""),
            "description": job.get("descriptionPlain", ""),
        })
    return jobs


def fetch_ashby(company):
    # Real endpoint: returns {"jobs": [...]} with title / location / jobUrl / descriptionPlain
    data = get_json(f"https://api.ashbyhq.com/posting-api/job-board/{company}")
    jobs = []
    for job in data.get("jobs", []):
        if job.get("isListed") is False:              # unlisted = direct-link only
            continue
        jobs.append({
            "id": f"ashby:{company}:{job['id']}",
            "company": company,
            "title": job.get("title", ""),
            "location": job.get("location", ""),
            "url": job.get("jobUrl", ""),
            "description": job.get("descriptionPlain", ""),
        })
    return jobs


FETCHERS = {"greenhouse": fetch_greenhouse, "lever": fetch_lever, "ashby": fetch_ashby}


def fetch_all(companies):
    """companies = {"greenhouse": [...], "lever": [...], "ashby": [...]}"""
    all_jobs, errors = [], []
    for source, names in companies.items():
        fetch = FETCHERS[source]
        for name in names:
            try:
                all_jobs.extend(fetch(name))
            except Exception as exc:
                errors.append(f"{source}:{name}: {exc}")
    return all_jobs, errors


if __name__ == "__main__":
    companies = {
        "greenhouse": ["anthropic", "nope123"],   # nope123 is fake on purpose
        "lever": ["palantir"],
        "ashby": ["openai"],
    }
    jobs, errors = fetch_all(companies)
    print(len(jobs), "jobs total")
    for source in FETCHERS:
        count = sum(1 for j in jobs if j["id"].startswith(source + ":"))
        print(f"  {source}: {count}")
    for j in jobs[:3]:
        print("-", j["company"], "|", j["title"], "|", j["location"])
    if errors:
        print("Errors:\n " + "\n ".join(errors))