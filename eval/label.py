import argparse
import json
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IN = ROOT / "eval" / "data" / "to_label.jsonl"
OUT = ROOT / "eval" / "data" / "labels.jsonl"


def load_jsonl(path):
    if not path.exists():
        return []
    with path.open("r") as f:
        return [json.loads(line) for line in f if line.strip()]


def resolve_path(p):
    path = Path(p)
    if not path.is_absolute():
        if path.parent == Path("."):
            return ROOT / "eval" / "data" / path
        return ROOT / path
    return path


def main():
    ap = argparse.ArgumentParser(description="Hand-label sampled jobs: would I actually apply to this today?")
    ap.add_argument("--input", default="to_label.jsonl", help="input file with sampled jobs (default: to_label.jsonl)")
    ap.add_argument("--labels", default="labels.jsonl", help="output file for saved labels (default: labels.jsonl)")
    args = ap.parse_args()

    in_path = resolve_path(args.input)
    out_path = resolve_path(args.labels)

    jobs = load_jsonl(in_path)
    done_ids = {job["id"] for job in load_jsonl(out_path)}
    todo = [j for j in jobs if j["id"] not in done_ids]
    print(f"{len(done_ids)} done, {len(todo)} to go. Keys: y = apply, n = no, s = skip, q = quit\n")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("a") as f:
        for i, job in enumerate(todo, 1):
            print(f"[{i}/{len(todo)}] {job['title']} @ {job['company']} ({job['location']})")
            print(job["url"])
            print(textwrap.fill(job["description"][:600], width=90))

            while True:
                ans = input("Apply? [y/n/s/q] ").strip().lower()
                if ans in ("y","n","s","q"):
                    break
                print("Please answer y, n, s, or q.")
            if ans == "q":
                break
            if ans == "s":
                continue
            row = {**job, "label": 1 if ans == "y" else 0}
            f.write(json.dumps(row) + "\n")
            f.flush()

    labels = load_jsonl(out_path)
    print(f"\nTotal labelled: {len(labels)}")
    print(f"Apply: {sum(1 for j in labels if j['label'] == 1)}")
    print(f"No: {sum(1 for j in labels if j['label'] == 0)}")


if __name__ == "__main__":
    main()