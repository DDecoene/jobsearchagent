# Career Discovery Agent — agents.md (v2)

## 1. Purpose

This system is a personal AI agent that scans job listings and identifies roles aligned with a **systems ownership + internal process improvement mindset**.

It does not function as a static job filter. It operates as a **time-aware discovery engine** that surfaces both:

* immediate high-fit roles
* and non-obvious adjacent opportunities

---

## 2. Core Principle

The agent does NOT answer:

* “Is this a perfect match?”

It answers:

* “Does this role signal system ownership potential or adjacency?”
* “Could this evolve into meaningful operational control work?”
* “Is there hidden structural alignment beyond the job title?”

---

## 3. Operating Modes

### 3.1 Day 1 — Backfill Mode (Historical Intake)

On initial run, the system processes a bounded historical window.

#### Rule:

Only ingest job listings where:

```
published_date >= now - 14 days
```

If no published date exists:

* The job is excluded OR heavily deprioritized

#### Purpose:

* Avoid historical noise explosion
* Capture only recent market signal
* Establish baseline dataset

---

### 3.2 Day 2+ — Incremental Mode (Streaming Intake)

After initial run, the system switches to delta processing.

#### Rule:

Only process jobs that have NOT been seen before.

A job is considered “seen” if its fingerprint exists in the database.

---

## 4. Job Identity (Deduplication Model)

Each job is uniquely identified by:

```json id="job_fingerprint"
{
  "fingerprint": "hash(normalize(title) + normalize(company) + normalize(location))"
}
```

### Notes:

* Description is NOT part of fingerprint (too volatile)
* This ensures stable deduplication across sources

---

## 5. Input Data Model

All job listings are normalized into:

```json id="job_input"
{
  "title": "",
  "company": "",
  "location": "",
  "description": "",
  "url": "",
  "source": "",
  "published_date": null
}
```

---

## 6. Output Format

Each job produces structured analysis:

```json id="job_output"
{
  "title": "",
  "company": "",
  "score_primary_match": 0-100,
  "score_hidden_potential": 0-100,
  "score_friction_risk": 0-100,
  "summary": "",
  "why_it_matters": [],
  "why_it_might_not_fit": [],
  "tags": [],
  "discovery_signal": ""
}
```

---

## 7. Scoring Model

### 7.1 Primary Match Score

Direct alignment with:

* ERP / business systems ownership
* internal application ownership
* operations systems responsibility
* process improvement authority
* workflow optimization mandate

Signals:

* ERP / WMS / CRM mention (+)
* “process improvement” (+)
* “systems ownership” (+)
* “operations + IT hybrid” (+)

---

### 7.2 Hidden Potential Score (Critical)

Measures whether the role can evolve into meaningful system ownership.

High score when:

* SME environment (50–300 employees)
* vague or flexible role scope
* end-to-end responsibility implied
* hybrid IT/operations structure
* undefined but systems-heavy environment

---

### 7.3 Friction Risk Score

Measures bureaucratic or low-autonomy environments.

High risk signals:

* ticket-only support work
* rigid escalation structures
* pure execution roles
* heavy corporate hierarchy
* “assist/support” framing

---

## 8. Classification Tags

Examples:

* ERP
* WMS
* Business Systems
* Operations IT
* Process Improvement
* SME Environment
* Enterprise Bureaucracy
* High Potential
* Low Autonomy
* Data/Systems Hybrid

---

## 9. Agent Behavior Rules

### Rule 1 — Do not over-filter

Moderate matches must still be surfaced if hidden potential is high.

---

### Rule 2 — Title is not truth

Job titles are weak signals. Description content is primary.

---

### Rule 3 — Prioritize emergent opportunity

The agent must highlight roles that could evolve into system ownership.

---

### Rule 4 — Reject static execution roles

Jobs that are purely task-based should be deprioritized.

---

## 10. Ranking Logic

```id="ranking"
final_score =
  (0.45 * score_primary_match) +
  (0.35 * score_hidden_potential) -
  (0.20 * score_friction_risk)
```

Jobs are sorted by final_score but not strictly filtered.

---

## 11. LLM Processing Strategy

### Step 1 — Cheap Pre-Classifier (optional but recommended)

Before full scoring:

Return:

```json id="precheck"
{
  "keep": true/false,
  "reason": ""
}
```

Purpose:

* reduce LLM cost
* eliminate irrelevant jobs early

---

### Step 2 — Full Analysis (only if keep = true)

Apply full scoring model and structured output.

---

## 12. System Architecture Assumptions

### Ingestion behavior:

* multiple job sources (VDAB, Indeed, company sites, etc.)
* normalized into single schema
* deduplicated via fingerprint

---

### Time-awareness rules:

#### Day 1 (Backfill Mode):

* only jobs from last 14 days
* excludes unknown-date listings by default

#### Day 2+ (Incremental Mode):

* only unseen jobs processed
* system becomes event-stream based

---

## 13. Discovery Signal (Key Concept)

Each job must include a short “discovery signal”:

Examples:

* “hidden ERP ownership potential in SME logistics environment”
* “underdefined systems role with high autonomy potential”
* “low match now, high structural growth opportunity”

This is the system’s core value output.

---

## 14. Philosophy

This system assumes:

* Job titles are unreliable
* Career value lies in system-level control, not role labels
* Adjacent opportunities are often more valuable than direct matches
* Time-aware processing is essential for signal clarity

The goal is not job search automation.

It is:

> **structured discovery of overlooked system ownership opportunities over time**

---
