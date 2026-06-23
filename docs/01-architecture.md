# 01. Architecture

## 권장 구조

```text
raw/
  source documents
  meeting notes
  exported manuals
  incident summaries
        |
        v
deterministic ingest
  text extraction
  chunking
  source hash
  metadata extraction
        |
        v
search/index layer
  ripgrep
  SQLite FTS5
  optional vector embeddings
        |
        v
candidate layer
  qwen2.5-coder:7b via Ollama
  JSON-only suggestions
        |
        v
curated wiki
  Markdown
  YAML frontmatter
  wikilinks
  review status
        |
        v
human / stronger agent review
```

## 왜 Qwen을 검색 엔진으로 쓰지 않는가

검색은 deterministic해야 한다.

- 어떤 문서가 hit 되었는지 재현 가능해야 한다.
- 같은 query에 같은 후보를 반환해야 한다.
- source path, line, hash, timestamp가 남아야 한다.
- 실패 원인을 debugging할 수 있어야 한다.

SQLite FTS5는 full-text search를 위해 만들어진 SQLite virtual table module이다. 공식 문서는 FTS5가 문서 집합에서 검색어가 포함된 subset을 효율적으로 찾는 기능을 제공한다고 설명한다. 따라서 검색 자체는 FTS5/ripgrep/Python이 더 적합하다.

Reference: https://www.sqlite.org/fts5.html

## Qwen이 들어갈 위치

Qwen은 “정답 생성기”가 아니라 “후보 생성기”다.

```text
search results
  -> Qwen: summarize / classify / suggest links / ask questions
  -> candidate JSON
  -> deterministic validation
  -> human/agent approval
```

좋은 후보 작업:

- 검색어 확장
- 동의어/약어 후보 생성
- wiki page link 후보
- 문서 chunk tag 후보
- 기존 wiki claim과 새 source summary의 충돌 후보
- 부족한 근거 질문

나쁜 후보 작업:

- 원문 없이 최종 답변
- 기존 wiki page 자동 덮어쓰기
- source citation 없는 요약
- code edit
- 업무 판단

## LLM Wiki와 RAG의 차이

Karpathy의 LLM Wiki gist는 일반 RAG가 질문할 때마다 원문 chunk를 다시 검색하고 재조합하는 방식이라고 설명한다. LLM Wiki는 다르다. 새 source가 들어오면 LLM이 읽고, 핵심 정보를 추출하고, 기존 markdown wiki에 통합한다. 이 과정에서 entity page, topic summary, contradiction, cross-reference가 점진적으로 갱신된다.

Reference: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f

실무에서는 둘을 섞는 것이 낫다.

| 계층 | 역할 |
| --- | --- |
| RAG/search | 원문 후보를 빠르게 찾음 |
| LLM Wiki | 시간이 지나도 남는 구조화 지식 |
| Local LLM | wiki 유지 후보를 생성 |
| Human/strong agent | 최종 해석과 변경 승인 |

## Markdown wiki schema

권장 page frontmatter:

```yaml
---
title: API Authentication
type: topic
status: draft
source_refs:
  - docs/api/authentication-v2.md
last_reviewed: 2026-06-24
tags:
  - api
  - security
  - authentication
---
```

권장 본문 구조:

```md
# API Authentication

## Summary

## Source-Backed Claims

## Open Questions

## Related Pages

## Change Log
```

Obsidian은 internal links로 note 간 네트워크를 만들 수 있고, properties에는 `tags`, `aliases` 같은 기본 metadata를 제공한다. 이 구조는 Obsidian이 없어도 Markdown/Git로 유지 가능하고, Obsidian을 쓰면 graph/backlink 탐색이 쉬워진다.

References:

- https://obsidian.md/help/links
- https://obsidian.md/help/properties

## Scaling rule

처음부터 vector DB나 graph DB를 넣지 않는다.

단계별 권장:

1. Markdown + Git + ripgrep
2. SQLite FTS5
3. Optional embeddings via Ollama `/api/embed`
4. Optional graph extraction
5. Optional MCP server

GeekNews의 local RAG 토론에서도 Markdown 문서 기반이면 SQLite FTS5와 간단한 description field만으로도 충분한 경우가 많고, 필요한 경우에만 vector를 보조로 붙이는 접근이 언급된다.

Reference: https://news.hada.io/topic?id=25854
