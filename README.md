# ClauseCheck

**An invoice-review agent that reads the fine print.**

ClauseCheck automates accounts-payable review using agentic RAG. When an
invoice arrives, the agent decides what evidence it needs (vendor contract,
amendments, approval policy, dispute history), retrieves it iteratively,
grades whether the evidence is sufficient, and verifies each claim on the
invoice. Every finding cites the exact contract clause behind it. When
evidence is missing or conflicting, the agent escalates to a human instead
of guessing.

## Why it matters
Invoice errors hide in unstructured documents: a rate cut by an amendment
three months ago, a payment term that differs from the contract, a new bank
account. Rules alone can't catch these, and single-shot RAG misses the
amendment. ClauseCheck's agent finds them and proves it with citations.

## Key features
- Query decomposition into checkable invoice claims
- Hybrid retrieval (pgvector + Postgres full-text) with reranking
- Amendment-aware chunking that respects effective dates
- Evidence grading with query rewrite and retry (corrective RAG)
- Citation enforcement: no cited chunk, no finding
- Human-in-the-loop approval and auto-drafted vendor emails
- Live agent trace streamed to the UI
- Built-in eval harness: single-shot RAG vs. agent accuracy

## Architecture (all on Vultr)
Cloud Compute (Docker Compose: FastAPI, worker, Next.js) ·
Managed PostgreSQL + pgvector · Object Storage · Serverless Inference

## Repo layout
/infra  /data  /retrieval  /agent  /backend  /frontend  /evals

## Quick start
cp .env.example .env
docker compose up --build
make eval   # baseline vs. agent comparison

## Hackathon
Vultr Hackathon, Track 02: Future of Work (Finance & Accounting)