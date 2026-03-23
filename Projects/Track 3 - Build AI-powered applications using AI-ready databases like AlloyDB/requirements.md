# Project Plan

Track 3 - Build AI-powered applications using AI-ready databases like AlloyDB

## Track Focus

This project follows the core requirement in the problem statement:

Build a small AI-enabled database feature using AlloyDB for PostgreSQL that lets users query a custom dataset in natural language and get meaningful results.

## Problem Statement

The goal is to prove a practical use case of AlloyDB AI Natural Language outside the default lab setup, with a solution that is low-cost, reproducible, and easy to demo.

For evaluation, this project is presented as a judge-facing reproducible workflow within a single GitHub repository that also contains Track 1 and Track 2.
Reviewers can clone the full repository, open only the corresponding track folder, and execute the runbook commands for that track.

## Final Use Case (One Sentence)

Querying small-business support tickets to detect urgent customer issues using natural language.

## Why This Use Case

- Meets the track objective exactly (NL to SQL over AlloyDB).
- Easier and cheaper than blockchain data while still innovative.
- Real-world value for non-technical support managers.

## Innovation

This solution combines natural language to SQL with a custom urgency scoring model directly in PostgreSQL so non-SQL users can ask business questions like "show unresolved payment issues from this week" and instantly get ranked, actionable results.

## What Must Be Built (Minimum Build Criteria)

The MVP will satisfy all required criteria:

1. Custom dataset stored in AlloyDB (support tickets CSV, not lab default dataset).
2. At least one schema change created by me.
3. AlloyDB AI Natural Language enabled for this dataset.
4. At least one original natural language query.
5. Full pipeline:

- Natural language input
- SQL generation by AlloyDB AI
- SQL execution in AlloyDB
- Relevant result returned in app UI

## Explicit Constraints Checklist

- Not using the default lab dataset.
- Using original queries for this use case.
- One-sentence use case provided.

## Budget-Constrained Plan (Target: about $5 out-of-pocket)

Important: AlloyDB pricing can exceed $5 if left running. To stay within budget, this plan assumes strict runtime control and immediate teardown after demo.

Cost control approach:

1. Use a very small dataset (for example, 2,000 to 10,000 rows).
2. Run AlloyDB only for setup, testing, recording evidence, and final demo window.
3. Use Cloud Run with minimum instances set to 0.
4. Avoid heavy analytics, vector search, and large data ingestion.
5. Stop or delete all billable resources immediately after submission evidence is captured.

## Technical Scope (MVP)

### Dataset

- Real IT support ticket dataset in CSV (`it_support_ticket_sample.csv`).
- Cleaned dataset for MVP uses English-only rows (`it_support_ticket_en.csv`) to keep natural language prompts consistent.
- Imported fields include issue text (`subject`, `body`), support metadata (`type`, `queue`, `priority`, `language`) and tags.

### Schema Design (Custom Work)

- Create table `support_tickets`.
- Add generated column `urgency_score` (0-100) based on priority, sentiment, and unresolved age.
- Optional generated label `urgency_bucket` (low, medium, high).

### AlloyDB AI Natural Language Setup

- Register business terms mapping, for example:
  - "urgent" -> urgency_score > 70
  - "unresolved" -> status != 'closed'
  - "payment issue" -> category = 'billing'

### Application

- Lightweight Python API or Streamlit frontend.
- Input box for natural language query.
- Output panel showing:
  - generated SQL
  - query results table

## Mandatory Submission Deliverables

1. Live Cloud Run URL (mandatory).
1. Snapshot(s) showing working flow:

- natural language input
- generated SQL
- returned results

1. Short repository README with setup and cleanup commands.

## Demo Natural Language Queries (Original)

1. Show high-urgency incident tickets in Technical Support for the last 30 days.
2. Top outage-related tags in English tickets.
3. Which queues have the most urgent open tickets?

## Process Flow

User enters natural language query
-> AlloyDB AI Natural Language generates SQL
-> SQL executes on AlloyDB
-> Results returned to Cloud Run app
-> App displays SQL + results
-> User captures snapshot for submission

## Opportunities

### How this differs from common ideas

- Most ticket dashboards need predefined filters and SQL knowledge.
- This solution supports free-form business questions in plain English.
- It adds database-level urgency intelligence, not only raw listing.

### How it solves the problem

- Reduces time to investigate urgent support issues.
- Enables non-technical users to query operational data directly.
- Makes decision-making faster with ranked urgency output.

### USP

A low-cost, reproducible, natural-language support intelligence app powered by AlloyDB AI and deployable on Cloud Run.

## Reproducibility Plan (Post-Program Friendly)

To ensure the project can be recreated after resources are deleted:

1. Keep a fixed sample CSV in the repository.
2. Keep a data cleaning step that filters to English-only rows for reproducible NL behavior.
3. Provide SQL scripts:
   - `01_schema.sql`
   - `02_seed.sql` (or import command)
   - `03_nl_config.sql`

4. Provide deployment script for Cloud Run.
5. Provide cleanup script to delete resources.
6. Document exact commands in README for one-pass setup and teardown.

Repository execution model:

1. Clone one GitHub repository that contains all tracks.
2. Enter the selected track folder.
3. Run that track's automation scripts without requiring other track files.

## Technologies

### Database and AI

- AlloyDB for PostgreSQL
- AlloyDB AI Natural Language
- PostgreSQL generated columns

### Infra and Hosting

- Google Cloud Run

### App Layer

- Python
- Lightweight Flask/FastAPI UI
- PostgreSQL connector

### Source Control

- GitHub repository

## Risk and Mitigation

1. Risk: Budget overrun.
   Mitigation: strict runtime windows, tiny dataset, immediate cleanup.
2. Risk: Complex schema or UI slows delivery.
   Mitigation: keep single-table MVP and minimum UI.
3. Risk: Reproducibility gaps.
   Mitigation: scripted setup, scripted cleanup, fixed sample dataset.

## Final Statement

This revised plan is aligned to the required problem statement, keeps Cloud Run as a mandatory deliverable, reduces cost risk, preserves innovation, and remains easy to reproduce even after the program resources are shut down.
