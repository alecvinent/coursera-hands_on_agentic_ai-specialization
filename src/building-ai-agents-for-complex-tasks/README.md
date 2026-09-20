# Building AI Agents for Complex Tasks

Workbook for the Building AI Agents for Complex Tasks course on Coursera. Learn to classify agent types, build multi-step agents, and diagnose agent behavior using logs and edge cases.

## Modules

| Module | Topic | Key Files |
|--------|-------|-----------|
| 1 | Agent Type Classification | `classifications.txt`, task text files |
| 2 | Build Multi-Step Agents | `task1/agent.py`, `task2/agent.py` |
| 3 | Diagnose & Improve Agent Behavior | `task1/`, `task2/agent.py`, `task3/agent.py` |

## Prerequisites

- Python 3.10+
- [Poetry](https://python-poetry.org/)

## Setup

```bash
poetry install
```

## Running

```bash
# Module 2 — Multi-Step Agents
cd src/building-ai-agents-for-complex-tasks/module_2/task1 && python agent.py
cd src/building-ai-agents-for-complex-tasks/module_2/task2 && python agent.py

# Module 3 — Behavior Diagnosis
cd src/building-ai-agents-for-complex-tasks/module_3/task2 && python agent.py
cd src/building-ai-agents-for-complex-tasks/module_3/task3 && python agent.py
```

## Tests

No automated test suite. Exercises are validated through Coursera submission.

## Additional Resources

- Module 1 is text-based (classifying agent types in real-world use cases)
- Module 2 builds agents using LangChain or Rasa
- Module 3 focuses on diagnosing behavior via logs and deploying real-world agents
