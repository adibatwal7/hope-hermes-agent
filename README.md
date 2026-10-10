<img width="1672" height="941" alt="hermes-agent-thumb" src="https://github.com/user-attachments/assets/2bf2a3e0-1aeb-4d81-9849-5dc65c3e36a4" />

# H.O.P.E — a personal AI agent

Hope is my personal AI agent. It runs 24/7 on a VPS, talks to me on Telegram,
reads my Notion through MCP, and gains new skills one at a time — each one
evaluated before I trust it.

> Hope runs on [Hermes Agent](https://github.com/NousResearch/hermes-agent), an
> open-source agent framework by Nous Research. **This repo contains only the
> parts I designed and built on top of it:** custom skills, the evaluation
> harness, and Hope's operating rules.

## What works today

**Job discovery skill.** Every weekday at 8:30 AM ET, Hope fetches new postings
from 30 companies' public job boards, ranks them against my profile, and sends
me the top picks on Telegram — each with the reasons it scored where it did.

    ✨ 5 new roles (of 41 new · 6,632 fetched)

    1. Software Engineer, New Grad — scaleai (7.0)
       title matches 'new grad'; 4 skills: python, typescript, react, rag;
       entry-level (new grad)
       https://...

## How it works

    Hermes cron (weekdays 8:30 ET)
            │
            ▼
    sources.py ──▶ Greenhouse · Lever · Ashby public APIs
            │        one normalized Job shape; a failing board never stops the run
            ▼
    discover.py ─▶ SQLite "seen" table → only postings I haven't seen before
            │
            ▼
    rank.py ─────▶ hard filters (seniority, clearance, internships)
            │      + weighted signals: title, skills (capped), entry-level, location
            ▼
    Telegram report, with a reason for every point

**Design choices**

- **Explainable over clever.** A weighted-signal ranker is the baseline any
  embedding or LLM ranker has to beat on the same labels.
- **Config, not code.** Titles, skills, companies and weights live in
  `config.json` (private); `config.example.json` shows the shape.
- **Whole-word matching.** Text is normalized and padded, so `rag` matches
  "RAG" but not "storage".
- **Untrusted input.** Job descriptions are treated as data, never as
  instructions to the agent.

## Evaluation

I hand-labelled real postings with one question — *would I apply to this
today?* — and measured how well the ranker puts good fits at the top,
compared with a baseline that uses only title matching.

- **Sampling:** stratified (ranker's top 25, a random 25 from the rest, 10
  filtered-out jobs), shuffled, and labelled blind to score.
- **Metrics:** precision@k, recall@k, average precision (AP).
- **Protocol:** tuned on a dev set, then evaluated once on a frozen held-out
  set with no overlapping postings.

| Set | Postings | Good fits | Ranker AP | Title-only AP | AP diff (95% bootstrap CI) |
| --- | --- | --- | --- | --- | --- |
| Dev (used for tuning) | 94 | 29 | 0.74 | 0.62 | +0.12 (+0.01 to +0.31) |
| Held-out (frozen) | 60 | 30 | 0.95 | 0.91 | +0.05 (−0.01 to +0.24) |

**What error analysis found and fixed**

- **Feature leakage:** "stripe" was in my skills list, so every Stripe posting
  scored a free skill match on the company name.
- **Skill stuffing:** long descriptions listing every buzzword outranked
  better-fitting roles; capping the skill bonus fixed most of it.
- **Under-weighted seniority fit:** new-grad roles sat below the top 10;
  entry-level wording now carries more weight.

**Honest limits:** one labeller; small samples; the held-out gain is
positive but its confidence interval crosses zero at n = 60; scores tie near
the top-10 cut-off. Full history: [docs/results.md](docs/results.md).

## Run it

Python 3.10+, standard library only.

    cp skills/job-discovery/config.example.json skills/job-discovery/config.json
    python3 skills/job-discovery/scripts/discover.py --dry-run --top 10

    # Evaluation
    python3 eval/export_sample.py                 # sample postings to label
    python3 eval/label.py                         # y / n / skip / quit, resumable
    python3 eval/evaluate.py --errors --bootstrap

## Repo layout

    skills/job-discovery/   SKILL.md, config example, scripts (fetch, rank, discover)
    eval/                   sampling, labelling and evaluation tools
    docs/results.md         every evaluation run, including what didn't help
    soul/SOUL.template.md   Hope's values: honesty, approval gates, injection defence

## Principles

- **Approval before action.** Hope never sends, applies, deletes or pays
  without my explicit yes.
- **Measured, not claimed.** No quality claim without an evaluation on
  labelled data.

## Roadmap

- [x] Job discovery skill, running daily
- [x] Evaluation harness with held-out test and bootstrap CIs
- [ ] Collapse duplicate postings across locations
- [ ] Unit tests
- [ ] Embedding-based ranker, evaluated against the same labels
- [ ] Outreach drafts with a human approval gate
- [ ] Temporal memory and retrieval over my notes
- [ ] Voice and a 3D avatar (Blender + React Three Fiber)

## Author

Aditya Batwal — [GitHub](https://github.com/adibatwal7) · [LinkedIn](https://linkedin.com/in/adityabatwal)