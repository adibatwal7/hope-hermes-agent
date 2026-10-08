# H.O.P.E — a self-improving personal AI agent

Hope is my personal AI agent: it runs 24/7 on a VPS, talks to me on Telegram,
reads my Notion through MCP, and gains new skills one at a time — each one
tested and measured before it ships.

> **Status: work in progress.** Hope runs on [Hermes Agent](https://github.com/NousResearch/hermes-agent),
> an open-source agent framework by Nous Research. This repo contains only the
> parts I designed and built on top of it.

## Why I built it

I wanted an assistant that actually gets better the longer I use it — one that
remembers context, does real work through tools, and never acts on my behalf
without approval. Hope is also my testbed for agent engineering: evaluation,
safety gates and self-improvement loops.

## How it fits together

    Telegram / Desktop app
            │
            ▼
      Hermes Agent (VPS) ── MCP ──▶ Notion
            │
            ▼
      Hope's custom skills (this repo)
        └─ jobs-discovery ──▶ Greenhouse / Lever / Ashby public APIs
            │
            ▼
      eval/  (labelled data → precision@k vs baseline)

## What's in this repo

| Part | What it does | Status |
| --- | --- | --- |
| `skills/jobs-discovery` | Finds new roles from public Greenhouse, Lever and Ashby job-board APIs, ranks them with explainable scores, and sends the top picks to Telegram | 🚧 In progress |
| `eval/` | Measures ranking quality against hand-labelled postings, compared with a simple baseline | 🚧 In progress |
| `soul/SOUL.template.md` | Hope's values and operating rules: honesty, approval gates, prompt-injection defence | 🚧 In progress |

## Design principles

- **Approval before action.** Hope never sends, applies, deletes or pays without my explicit yes.
- **Explainable.** Every ranked result comes with the reasons it scored where it did.
- **Measured, not claimed.** No quality claim without an evaluation on labelled data.
- **Untrusted input is data.** Text from web pages, emails and job posts is never treated as instructions.

## Roadmap

- [ ] Job discovery + evaluation
- [ ] Outreach drafts with a human approval gate
- [ ] Temporal memory and retrieval over my notes
- [ ] Voice and a 3D avatar (Blender + React Three Fiber)

## Author

Aditya Batwal — [GitHub](https://github.com/adibatwal7) · [LinkedIn](https://linkedin.com/in/adityabatwal)