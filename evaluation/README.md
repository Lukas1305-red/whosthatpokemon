# Retrieval evaluation

## Decision

Use a two-stage retrieval path in production:

```text
recruiter query → Cohere embedding → Chroma top 25 → Cohere rerank → top 5 Pokémon
```

The candidate pool is **25**. It is the current quality/latency knee: it
captures most of the reranking benefit without the diminishing returns and
additional cost of pools 50 and 100. If reranking fails or is rate-limited,
return the original Chroma ranking rather than failing the user request.

## What was evaluated

The gold set in `cases.json` has 50 recruiter-style queries. Each query has
graded, source-grounded relevance labels from `data/pokemon_enriched.json`:

* `3`: strong match
* `2`: plausible alternate
* `1`: partial match

The suite reports Recall@5 (a query-level hit rate), nDCG@5, MRR, and logical
request latency. Logical latency includes query formatting, embedding/vector
retrieval, and reranking where relevant. It excludes evaluation-only Cohere
rate-limit waits and retry sleeps.

## Results

On the 50-case set, raw vector retrieval versus reranking 25 candidates:

```text
                         Raw       Rerank 25
Recall@5                0.76       0.90
nDCG@5                  0.46       0.62
MRR                      0.64       0.89
Typical latency (p50)    0.32 s     0.74 s
```

An LLM query formatter was tested and did not improve the raw baseline
consistently, so it was removed. The cross-encoder reranker improves both
top-five coverage and ordering.

Candidate-pool experiments showed increasing quality with larger pools. The
largest jump was from 10 to 25; 25 to 50 and 50 to 100 were incremental. Use
median latency for the current pool-size decision. Single-run p95 values had
provider/network outliers, so repeat and interleave pool experiments before
using tail latency to make a tighter production SLO.

## Run the suite

Run the raw, LLM, or reranking comparison:

```bash
make evaluate EVAL_ARGS="--strategies raw,rerank"
```

Run the Matplotlib candidate-pool sweep (defaults to 10, 25, 50, 100):

```bash
make evaluate EVAL_SUITE=candidate_pools
```

For a low-cost smoke run:

```bash
make evaluate EVAL_SUITE=candidate_pools EVAL_ARGS="--case-limit 3"
```

Reports and charts are written under `evaluation/results/` and ignored by git.

## Layout

```text
evaluation/
├── cases.json                 # tracked gold set
├── run_retrieval.py           # strategy comparison runner
├── run_candidate_pools.py     # pool sweep and Matplotlib chart
├── metrics.py                 # ranking and latency metrics
├── rerankers.py               # Cohere reranker adapter
├── cohere_requests.py         # pacing and 429 retry handling
├── tests/                     # evaluation-specific tests
└── results/                   # ignored JSON reports and PNG charts
```
