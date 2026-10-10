"""Measure ranker quality on hand-labelled jobs vs. a title-only baseline."""
import argparse
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "skills" / "job-discovery"
sys.path.insert(0, str(SKILL / "scripts"))
sys.path.insert(0, str(ROOT / "eval"))

# pyrefly: ignore [missing-import]
from rank import rank
# pyrefly: ignore [missing-import]
from label import load_jsonl      # reuse your loader instead of rewriting it

LABELS = ROOT / "eval" / "data" / "labels.jsonl"


def ranked_order(rows, profile, weights):
    """All rows, best first. Excluded rows go at the very end."""
    kept, excluded = rank(rows, profile, weights)
    # TODO 1: return [job for job, score, reasons in kept] + [job for job, why in excluded]
    return [job for job, _, _ in kept] + [job for job, _ in excluded]


def precision_at_k(order, k):
    # TODO 2: hits = number of label == 1 in order[:k]; return hits / k
    hits = sum(1 for job in order[:k] if job.get("label") == 1)
    return hits / k if k > 0 else 0.0


def recall_at_k(order, k):
    # TODO 3: total = number of label == 1 in the whole order
    #         return hits in order[:k] / total   (return 0.0 if total == 0)
    hits = sum(1 for job in order[:k] if job.get("label") == 1)
    total = sum(1 for job in order if job.get("label") == 1)
    return hits / total if total > 0 else 0.0


def average_precision(order):
    # TODO 4: hits = 0, total = 0.0
    #         for i, job in enumerate(order, start=1):
    #             if job["label"] == 1:
    #                 hits += 1
    #                 total += hits / i        # precision at this position
    #         return total / hits  (0.0 if hits == 0)
    hits = 0
    total_prec = 0.0
    for i, job in enumerate(order, start=1):
        if job.get("label") == 1:
            hits += 1
            total_prec += hits / i
    return total_prec / hits if hits > 0 else 0.0


def title_only(weights):
    """Baseline: same ranker, every signal except title switched off."""
    # TODO 5: w = copy.deepcopy(weights); set skill, entry_level, location, remote to 0.0; return w
    w = copy.deepcopy(weights)
    w["skill"] = 0.0
    w["entry_level"] = 0.0
    w["location"] = 0.0
    w["remote"] = 0.0
    return w


def report(name, order, ks):
    # TODO 6: build one row of the table, e.g.
    #   f"{name:<12}" + p@k and r@k for each k in ks + f"AP {average_precision(order):.2f}"
    parts = [f"{name:<12}"]
    for k in ks:
        p = precision_at_k(order, k)
        r = recall_at_k(order, k)
        parts.append(f"p@{k} {p:.3f} r@{k} {r:.3f}")
    parts.append(f"AP {average_precision(order):.3f}")
    return " ".join(parts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, nargs="+", default=[5, 10])
    ap.add_argument("--errors", action="store_true")
    args = ap.parse_args()

    config = json.loads((SKILL / "config.json").read_text())
    rows = load_jsonl(LABELS)
    profile, weights = config["profile"], config["weights"]
    positives = sum(r["label"] for r in rows)
    print(f"{len(rows)} labelled jobs, {positives} good fits "
          f"(random-guess precision ≈ {positives / len(rows):.2f})\n")

    # TODO 7: print report("hope", ranked_order(rows, profile, weights), args.k)
    #         print report("title-only", ranked_order(rows, profile, title_only(weights)), args.k)
    print(report("hope", ranked_order(rows, profile, weights), args.k))
    print(report("title-only", ranked_order(rows, profile, title_only(weights)), args.k))

    # TODO 8: list good fits removed by hard filters:
    #   _, excluded = rank(rows, profile, weights)
    #   for job, why in excluded: if job["label"] == 1 -> print title, company, why
    _, excluded = rank(rows, profile, weights)
    for job, why in excluded:
        if job.get("label") == 1:
            print(job["title"], "|", job["company"], "|", why)

    if args.errors:
        kept, _ = rank(rows, profile, weights)
        print("\nFalse positives:")
        for job, score, reasons in kept[:10]:
            if job.get("label") == 0:
                print(f"{score:>5}  {job['title']} ({job['company']})")
                print(f"       {'; '.join(reasons)}")

        print("\nMissed good fits:")
        for job, score, reasons in kept[10:]:
            if job.get("label") == 1:
                print(f"{score:>5}  {job['title']} ({job['company']})")
                print(f"       {'; '.join(reasons)}")


if __name__ == "__main__":
    main()