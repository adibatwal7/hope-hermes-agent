"""Daily job discovery: fetch -> skip already-seen -> rank -> print top N -> remember."""
import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from rank import rank
from sources import fetch_all

SKILL_DIR = Path(__file__).parent.parent          # skills/job-discovery/


def open_db(path):
    """Open (or create) the database and make sure the table exists."""
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    # TODO 1: run a CREATE TABLE IF NOT EXISTS statement for a table called
    #         `seen` with columns: id TEXT PRIMARY KEY, first_seen TEXT,
    #         title TEXT, company TEXT, url TEXT
    #         hint: db.execute("""CREATE TABLE IF NOT EXISTS seen (...)""")
    db.execute("""CREATE TABLE IF NOT EXISTS seen (
        id TEXT PRIMARY KEY,
        first_seen TEXT,
        title TEXT,
        company TEXT,
        url TEXT
    )""")
    db.commit()
    return db


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
    # TODO 2: load all already-seen ids into a Python set
    #         hint: {row[0] for row in db.execute("SELECT id FROM seen")}
    seen_ids = {row[0] for row in db.execute("SELECT id FROM seen")}

    # TODO 3: keep only jobs whose id is NOT in seen_ids
    new_jobs = [job for job in jobs if job["id"] not in seen_ids]

    kept, excluded = rank(new_jobs, config["profile"], config["weights"])
    # TODO 4: keep only jobs scoring at least config["min_score"], then take the top_n
    picks = [(job, score, reasons) for job, score, reasons in kept
         if score >= config["min_score"]][:top_n]

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

    # TODO 5: unless --dry-run, remember ALL ranked new jobs (not just picks)
    #         so tomorrow only truly new ones appear.
    #         hint: db.executemany("INSERT OR IGNORE INTO seen VALUES (?,?,?,?,?)", rows)
    #               rows = [(job["id"], now, job["title"], job["company"], job["url"]) for ...]
    #         now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    #         then db.commit()  <- without this, nothing is saved!

    if not args.dry_run:
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        rows = [
            (job["id"], now, job["title"], job["company"], job["url"])
            for job, _, _ in kept
        ]
        db.executemany("INSERT OR IGNORE INTO seen VALUES (?,?,?,?,?)", rows)
        db.commit()
    db.close()


if __name__ == "__main__":
    main()