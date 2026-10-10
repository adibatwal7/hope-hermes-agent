"""Export a fair, mixed sample of jobs for hand-labelling."""
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "skills" / "job-discovery"
sys.path.insert(0, str(SKILL / "scripts"))

# pyrefly: ignore [missing-import]
from rank import rank
# pyrefly: ignore [missing-import]
from sources import fetch_all

random.seed(42)   # same "random" sample every run -> reproducible


def main():
    config = json.loads((SKILL / "config.json").read_text())
    jobs, errors = fetch_all(config["companies"])      # NOTE: ignores seen.db on purpose
    kept, excluded = rank(jobs, config["profile"], config["weights"])

    # TODO 1: top = the first 25 items of `kept`
    top_n = 25
    top_jobs = kept[:top_n] 
    # TODO 2: rest = everything in `kept` after the first 25
    #         middle = random.sample(rest, 25)
    rest = kept[top_n:]
    middle_n = 25
    middle_jobs = random.sample(rest, middle_n)
    # TODO 3: low = random.sample(excluded, 10)
    #         careful: `excluded` holds (job, reason) pairs, not (job, score, reasons)
    low_n = 10
    low_jobs = random.sample(excluded, low_n)

    # TODO 4: for each item, append a dict with:
    #   id, company, title, location, url, description,
    #   "score" (0 for excluded jobs), "bucket" ("top" / "middle" / "excluded"),
    #   "label": None   <- you'll fill this in during 10b
    sample = []
    for job, score, reasons in top_jobs:
        sample.append({
            "id": job["id"],
            "company": job["company"],
            "title": job["title"],
            "location": job["location"],
            "url": job["url"],
            "description": job["description"],
            "score": score,
            "bucket": "top",
            "label": None,
        })
    for job, score, reasons in middle_jobs:
        sample.append({
            "id": job["id"],
            "company": job["company"],
            "title": job["title"],
            "location": job["location"],
            "url": job["url"],
            "description": job["description"],
            "score": score,
            "bucket": "middle",
            "label": None,
        })
    for job, reason in low_jobs:      # excluded items don't have a computed score
        sample.append({
            "id": job["id"],
            "company": job["company"],
            "title": job["title"],
            "location": job["location"],
            "url": job["url"],
            "description": job["description"],
            "score": 0,
            "bucket": "excluded",
            "label": None,
        })

    # TODO 5: random.shuffle(sample) so you can't see which bucket a job is from
    #         while labelling (this prevents bias!)
    random.shuffle(sample)
    out = ROOT / "eval" / "data" / "to_label.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w") as f:
        for row in sample:
            f.write(json.dumps(row) + "\n")      # one JSON object per line = "JSONL"
    print(f"Wrote {len(sample)} jobs to {out}")


if __name__ == "__main__":
    main()