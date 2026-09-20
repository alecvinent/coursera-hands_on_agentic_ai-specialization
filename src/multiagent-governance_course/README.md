# Multi-Agent Design & Governance

Workbook for the Multi-Agent Design & Governance course on Coursera. Learn to classify agent types, build multi-agent content pipelines, and design governance frameworks for agentic AI systems.

## Modules

| Module | Topic | Key Files |
|--------|-------|-----------|
| 1 | Agent Classification & Foundations | `classification/graph.py`, `analysis/tradeoffs.py`, `scenarios/`, `interaction_map/mapper.py` |
| 2 | Sequential Agent Content Pipeline | `agents/researcher.py`, `agents/writer.py`, `agents/seo.py`, `workflow.py` |
| 3 | Course-End Governance Project | Governance documentation and exercises (PDFs) |

## Prerequisites

- Python 3.10+
- [Poetry](https://python-poetry.org/)
- API key for an LLM provider

## Setup

```bash
poetry install
cp .env.example .env
# Edit .env with your API key
```

## Running

```bash
# Module 1 — Agent Classification
poetry run python -m src.multiagent-governance_course.module_1_foundations.app

# Module 2 — Sequential Content Pipeline (Researcher → Writer → SEO)
poetry run python -m src.multiagent-governance_course.module_2_multiagents
```

## Tests

```bash
python -m unittest discover -s tests/multiagent-governance_course -t . -v
```

## Additional Resources

- Module 1 covers agent classification, interaction maps, and trade-off analysis
- Module 2 implements a sequential Researcher → Writer → SEO blog pipeline
- Module 3 is the course-end project on multi-agent design and governance (see PDFs in `module_3_governance/`)
