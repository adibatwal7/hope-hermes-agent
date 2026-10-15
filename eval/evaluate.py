"""Measure ranker quality on hand-labelled jobs vs. a title-only baseline."""
import argparse
import copy
import json
import random
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
    return [job for job, _, _ in kept] + [job for job, _ in excluded]


def precision_at_k(order, k):
    hits = sum(1 for job in order[:k] if job.get("label") == 1)
    return hits / k if k > 0 else 0.0


def recall_at_k(order, k):
    hits = sum(1 for job in order[:k] if job.get("label") == 1)
    total = sum(1 for job in order if job.get("label") == 1)
    return hits / total if total > 0 else 0.0


def average_precision(order):
    hits = 0
    total_prec = 0.0
    for i, job in enumerate(order, start=1):
        if job.get("label") == 1:
            hits += 1
            total_prec += hits / i
    return total_prec / hits if hits > 0 else 0.0


def title_only(weights):
    """Baseline: same ranker, every signal except title switched off."""
    w = copy.deepcopy(weights)
    w["skill"] = 0.0
    w["entry_level"] = 0.0
    w["location"] = 0.0
    w["remote"] = 0.0
    return w


def report(name, order, ks):
    parts = [f"{name:<12}"]
    for k in ks:
        p = precision_at_k(order, k)
        r = recall_at_k(order, k)
        parts.append(f"p@{k} {p:.3f} r@{k} {r:.3f}")
    parts.append(f"AP {average_precision(order):.3f}")
    return " ".join(parts)


def bootstrap_ap_diff(rows, profile, weights, n=1000, seed=0):
    """95% CI for AP(hope) - AP(title-only), resampling jobs with replacement."""
    rng = random.Random(seed)
    diffs = []
    for _ in range(n):
        sample = [rng.choice(rows) for _ in rows]
        positives = sum(r["label"] for r in sample)
        if positives == 0:
            continue
        order_hope = ranked_order(sample, profile, weights)
        order_title = ranked_order(sample, profile, title_only(weights))
        diffs.append(average_precision(order_hope) - average_precision(order_title))
    diffs.sort()
    lo = diffs[int(0.025 * len(diffs))]
    hi = diffs[int(0.975 * len(diffs))]
    return sum(diffs) / len(diffs), lo, hi


def resolve_path(p):
    path = Path(p)
    if not path.is_absolute():
        if path.parent == Path("."):
            return ROOT / "eval" / "data" / path
        return ROOT / path
    return path


def main():
    ap = argparse.ArgumentParser(description="Measure ranker quality on hand-labelled jobs vs. a title-only baseline.")
    ap.add_argument("--k", type=int, nargs="+", default=[5, 10])
    ap.add_argument("--errors", action="store_true", help="show false positives and missed good fits")
    ap.add_argument("--labels", "--input", dest="labels", default="labels.jsonl", help="path to labelled data file (default: labels.jsonl)")
    ap.add_argument("--bootstrap", action="store_true")
    args = ap.parse_args()

    config = json.loads((SKILL / "config.json").read_text())
    labels_path = resolve_path(args.labels)
    rows = load_jsonl(labels_path)
    profile, weights = config["profile"], config["weights"]
    positives = sum(r["label"] for r in rows)
    print(f"{len(rows)} labelled jobs, {positives} good fits "
          f"(random-guess precision ≈ {positives / len(rows):.2f})\n")

    print(report("hope", ranked_order(rows, profile, weights), args.k))
    print(report("title-only", ranked_order(rows, profile, title_only(weights)), args.k))

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

    if args.bootstrap:
        mean, lo, hi = bootstrap_ap_diff(rows, profile, weights)
        print(f"AP diff = {mean:+.3f} (95% CI {lo:+.3f} to {hi:+.3f})")


if __name__ == "__main__":
    main()