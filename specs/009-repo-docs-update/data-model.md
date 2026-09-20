# Data Model: Course README & General README Update

**Date**: 2026-09-20
**Feature**: 009-repo-docs-update

## Entities

### Course

A Coursera course represented as a directory under `src/`.

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Course directory name (e.g., `langgraph_course`) |
| `title` | string | Human-readable course title |
| `description` | string | 1-3 sentence summary of what the course teaches |
| `modules` | list[Module] | Ordered list of modules in the course |
| `has_code` | boolean | Whether the course contains runnable Python code |
| `has_tests` | boolean | Whether the course has associated test files |
| `has_readme` | boolean | Whether a README already exists (only MCP course) |

### Module

A module within a course.

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Module directory name (e.g., `module_1`) |
| `topic` | string | What the module covers |
| `key_files` | list[string] | Notable files in the module |

### README

A markdown documentation file.

| Field | Type | Description |
|-------|------|-------------|
| `path` | string | File path relative to repo root |
| `scope` | enum | `root` \| `course` \| `task` |
| `sections` | list[string] | Ordered section headings |

## Document Structure Schema

All per-course READMEs follow this consistent structure:

```markdown
# [Course Title]

[1-3 sentence description]

## Modules

| Module | Topic | Key Files |
|--------|-------|-----------|
| 1 | [topic] | [files] |
| 2 | [topic] | [files] |
| 3 | [topic] | [files] |

## Prerequisites

[Course-specific prerequisites, if different from shared setup]

## Setup

[Course-specific setup instructions]

## Running

[Commands to run the course exercises]

## Tests

[Commands to run tests, if applicable]

## Additional Resources

[Links to sub-project READMEs, PDFs, or external references]
```

## Root README Structure (Post-Update)

```markdown
# Coursera Agentic AI Specialization

[One-paragraph description]

## LinkedIn Summary
[Preserved verbatim]

## Courses

| Course | Topic | Link |
|--------|-------|------|
| LangGraph Framework | [description] | [link] |
| Multi-Agent Design & Governance | [description] | [link] |
| ... | ... | ... |

## Shared Setup

### Prerequisites
### Installation
### API Keys

## Project Structure

[High-level tree]

## Flowise Course-end Project

[Link to existing guide]

## AGENTS.md

[Reference to existing conventions file]
```

## Relationships

```
Root README ──links to──> Course README (×7)
Course README ──links to──> Task README (MCP course only, ×2)
Course README ──describes──> Module (×3 per course)
Root README ──moved from──> LangGraph Course README (pattern docs)
```
