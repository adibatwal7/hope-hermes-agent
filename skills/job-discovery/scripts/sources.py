import html
import json
import re
import urllib.request

def to_text(raw):
    """Turn Greenhouse's HTML description into plain text."""
    if not raw:
        return ""
    # TODO 1: unescape it twice (Greenhouse escapes HTML twice) -> html.unescape
    text = html.unescape(raw)
    text = html.unescape(text)
    # TODO 2: remove tags like <p> with a regex -> re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"<[^>]+>", " ", text)
    # TODO 3: collapse repeated spaces -> re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\s+", " ", text).strip()
    return text

def fetch_greenhouse(company):
    url = f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs?content=true"
    # TODO 4: download the URL and parse the JSON
    #         hint: urllib.request.urlopen(url) and json.load(...)
    with urllib.request.urlopen(url, timeout=20) as resp:
        data = json.load(resp)
    # TODO 5: loop over data["jobs"] and build a list of dicts with:
    #         id, company, title, location, url, description
    #         hint: location is nested -> job["location"]["name"]
    #               url is job["absolute_url"], description is to_text(job["content"])
    jobs = []
    for job in data["jobs"]:
        jobs.append({
            "id": f"greenhouse:{company}:{job['id']}",
            "company": company,
            "title": job["title"],
            "location": job["location"]["name"],
            "url": job["absolute_url"],
            "description": to_text(job["content"]),
        })
    return jobs

if __name__ == "__main__":
    jobs = fetch_greenhouse("anthropic")
    print(len(jobs), "jobs")
    for j in jobs[:3]:
        print("-", j["title"], "|", j["location"])