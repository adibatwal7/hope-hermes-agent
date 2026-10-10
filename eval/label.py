"""Hand-label sampled jobs: would I actually apply to this today? (y/n)"""
import json
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IN = ROOT / "eval" / "data" / "to_label.jsonl"
OUT = ROOT / "eval" / "data" / "labels.jsonl"


def load_jsonl(path):
    # TODO 1: if path doesn't exist, return []
    #         else return [json.loads(line) for each non-empty line]
    if not path.exists():
        return []
    with path.open("r") as f:
        return [json.loads(line) for line in f if line.strip()]


def main():
    jobs = load_jsonl(IN)
    # TODO 2: done_ids = a SET of row["id"] for rows already in OUT
    done_ids = {job["id"] for job in load_jsonl(OUT)}
    todo = [j for j in jobs if j["id"] not in done_ids]
    print(f"{len(done_ids)} done, {len(todo)} to go. Keys: y = apply, n = no, s = skip, q = quit\n")

    with OUT.open("a") as f:
        for i, job in enumerate(todo, 1):
            # TODO 3: print a header: f"[{i}/{len(todo)}] {title} @ {company} ({location})"
            #         then job["url"]
            #         then the first ~600 chars of description, wrapped:
            #         textwrap.fill(job["description"][:600], width=90)
            #         DO NOT print score or bucket (blind labelling)
            print(f"[{i}/{len(todo)}] {job['title']} @ {job['company']} ({job['location']})")
            print(job["url"])
            print(textwrap.fill(job["description"][:600], width=90))
            
            # TODO 4: loop until the answer is one of y/n/s/q:
            #         ans = input("Apply? [y/n/s/q] ").strip().lower()
            while True:
                ans = input("Apply? [y/n/s/q] ").strip().lower()
                if ans in "ynsq":
                    break
                print("Please answer y, n, s, or q.")
            # TODO 5: q -> break
            #         s -> continue (skipped jobs stay unlabelled; you'll see them next run)
            #         y/n -> row = {**job, "label": 1 if ans == "y" else 0}
            #                f.write(json.dumps(row) + "\n")
            #                f.flush()   # saved immediately, even if you Ctrl+C
            if ans == "q":
                break
            if ans == "s":
                continue
            row = {**job, "label": 1 if ans == "y" else 0}
            f.write(json.dumps(row) + "\n")
            f.flush()
            ...

    # TODO 6: reload OUT and print: total labelled, how many 1s, how many 0s
    labels = load_jsonl(OUT)
    print(f"\nTotal labelled: {len(labels)}")
    print(f"Apply: {sum(1 for j in labels if j['label'] == 1)}")
    print(f"No: {sum(1 for j in labels if j['label'] == 0)}")


if __name__ == "__main__":
    main()