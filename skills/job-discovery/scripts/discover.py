"""Daily job discovery: fetch -> skip already-seen -> rank -> print top N -> remember."""
import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from rank import rank, normalize
from sources import fetch_all

SKILL_DIR = Path(__file__).parent.parent          # skills/job-discovery/


def open_db(path):
    """Open (or create) the database and make sure the table exists."""
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.execute("""CREATE TABLE IF NOT EXISTS seen (
        id TEXT PRIMARY KEY,
        first_seen TEXT,
        title TEXT,
        company TEXT,
        url TEXT
    )""")
    db.commit()
    return db


def collapse_duplicates(picks):
    """Merge the same role posted in several cities into one entry."""
    groups = {}
    for job, score, reasons in picks:
        key = (job["company"], normalize(job["title"]))
        loc = job["location"] or "n/a"
        if key not in groups:
            # picks is already sorted by score descending, so the first
            # posting encountered for each role already has the highest score.
            groups[key] = [job, score, reasons, [loc]]
        else:
            if loc not in groups[key][3]:
                groups[key][3].append(loc)

    return [
        ({**job, "location": " · ".join(locations)}, score, reasons)
        for job, score, reasons, locations in groups.values()
    ]


def main():
    parser = argparse.ArgumentParser(description="Find new jobs that fit my profile.")
    parser.add_argument("--top", type=int, help="how many jobs to show")
    parser.add_argument("--dry-run", action="store_true",
                        help="show results but don't mark them as seen")
    args = parser.parse_args()

    config = json.loads((SKILL_DIR / "config.json").read_text())
    top_n = args.top or config.get("top_n", 5)

    jobs, errors = fetch_all(config["companies"])

    db = open_db(SKILL_DIR / "data" / "seen.db")
    seen_ids = {row[0] for row in db.execute("SELECT id FROM seen")}

    new_jobs = [job for job in jobs if job["id"] not in seen_ids]

    kept, excluded = rank(new_jobs, config["profile"], config["weights"])
    good = [(j, s, r) for j, s, r in kept if s >= config["min_score"]]
    picks = collapse_duplicates(good)[:top_n]

    # Print a short, Telegram-friendly report
    print(f"{len(jobs)} fetched · {len(new_jobs)} new · {len(excluded)} filtered out")
    if not picks:
        print("No new matching roles today.")
    for i, (job, score, reasons) in enumerate(picks, 1):
        print(f"\n{i}. {job['title']} — {job['company']} ({job['location'] or 'n/a'})")
        print(f"   score {score}: {'; '.join(reasons)}")
        print(f"   {job['url']}")
    if errors:
        print(f"\n⚠ {len(errors)} board(s) failed: {'; '.join(errors[:3])}")

    # Remember every new job (not just picks) so tomorrow shows only truly new ones.
    # A failed save must not hide today's report, so warn instead of crashing.
    if not args.dry_run:
        try:
            now = datetime.now(timezone.utc).isoformat(timespec="seconds")
            rows = [
                (job["id"], now, job["title"], job["company"], job["url"])
                for job in new_jobs
            ]
            db.executemany("INSERT OR IGNORE INTO seen VALUES (?,?,?,?,?)", rows)
            db.commit()
        except sqlite3.Error as e:
            print(f"\n⚠ Couldn't save seen jobs ({e}). Tomorrow may repeat today's roles.")
    db.close()


if __name__ == "__main__":
    main()