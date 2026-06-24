# 07. LLM-Wiki Automation Ideas Research

조사일: 2026-06-25  
목표: GitHub, GeekNews, YouTube, 공식 문서에서 LLM-Wiki 자동화 아이디어를 수집하고, 사내 업무용 PC에 적용 가능한 패턴으로 정리한다.

## 결론

LLM-Wiki 자동화는 “local LLM이 모든 것을 알아서 쓰는 시스템”이 아니라, **raw source를 보존하고, deterministic index를 유지하며, LLM은 draft/candidate를 만들고, 사람 또는 강한 agent가 승인하는 pipeline**으로 설계해야 한다.

가장 안전한 구조:

```text
raw sources
  -> deterministic ingest and search
  -> local LLM candidate generation
  -> draft wiki pages
  -> lint / review / approve
  -> curated markdown wiki
  -> query / synthesis / save-back
```

`qwen2.5-coder:7b`는 이 구조에서 final answer model이 아니라 `fast scout / candidate generator`로 쓰는 것이 맞다.

## Source Channels

### GitHub

| Project | Useful idea | Reference |
| --- | --- | --- |
| LLM-WIKI-MCP | Markdown source of truth, SQLite local index, Ollama-compatible model, CLI + MCP server, graph/lint/repair/context pack | https://github.com/Electro-resonance/LLM-WIKI-MCP |
| obsidian-llm-wiki-local | 3-stage pipeline: ingest with fast model, compile with heavier model, review/approve drafts, then publish to Obsidian wiki | https://github.com/kytmanov/obsidian-llm-wiki-local |
| NiharShrotri/llm-wiki | Ollama + Qwen + QMD; hybrid BM25/vector/rerank; save good answers back into synthesis pages; lint/fix wiki | https://github.com/NiharShrotri/llm-wiki |
| llm-wiki-compiler | Raw sources in, citation-traceable interlinked markdown wiki out; durable pages with provenance, review state, retrieval metadata | https://github.com/atomicstrata/llm-wiki-compiler |
| WUPHF | Markdown + Git + BM25/SQLite, per-entity fact logs, promotion from agent notebooks to shared team wiki | https://github.com/nex-crm/wuphf |
| Hypomnema | LLM-native personal/team wiki inside coding-agent workflow | https://github.com/sk-lim19f/Hypomnema |
| mcp-local-rag | Local-first RAG exposed through MCP; useful pattern when wiki/search should become agent tools | https://github.com/shinpr/mcp-local-rag |

### GeekNews

| Topic | Useful idea | Reference |
| --- | --- | --- |
| LLM-Wiki | persistent wiki, raw sources as immutable truth, index.md/log.md, lint operations, Obsidian as IDE for wiki | https://news.hada.io/topic?id=28208 |
| WUPHF | markdown + git, BM25/SQLite before vector DB, per-agent notebook and shared team wiki, append-only fact logs | https://news.hada.io/topic?id=28910 |
| Ask HN local RAG | small markdown knowledge bases can start with FTS/BM25; vector DB is optional, not mandatory | https://news.hada.io/topic?id=25854 |

### YouTube

YouTube 검색 메타데이터에서 local RAG/Ollama/Markdown 관련 실습 영상을 확인했다. 영상은 구현 세부를 검증하는 1차 근거라기보다 “실제 사용자들이 어떤 pipeline을 실습하는지” 보는 보조 채널로 사용한다.

| Video | Useful idea | URL |
| --- | --- | --- |
| Build your Private AI Agent with RAG using Langchain & Ollama \| RAG on Markdown Files | Markdown files + local Ollama RAG agent 실습 흐름 | https://www.youtube.com/watch?v=ohKbhu_9USA |
| Turn ANY File into LLM Knowledge in SECONDS | file-to-knowledge ingestion workflow idea | https://www.youtube.com/watch?v=fg0_0M8kZ8g |
| Local RAG using Ollama: Korean Performance of the Ollama Embedding Model, Semantic Chunking | Korean retrieval/embedding/chunking 평가 아이디어 | https://www.youtube.com/watch?v=GsZ9w04smVE |
| How to Build a Local AI Agent With Python (Ollama, LangChain & RAG) | Python local agent + RAG implementation pattern | https://www.youtube.com/watch?v=E4l91XKQSgw |
| Finally a Local RAG That WORKS!! (+ FULL RAG Pipeline) | end-to-end local RAG pipeline checklist | https://www.youtube.com/watch?v=c5jHhMXmXyo |
| Easy 100% Local RAG Tutorial (Ollama) + Full Code | simple full-code local RAG baseline | https://www.youtube.com/watch?v=Oe-7dGDyzPM |

### Official Docs

| Source | Useful idea | Reference |
| --- | --- | --- |
| Ollama chat API | JSON mode, local `/api/chat`, model options, non-streaming automation | https://docs.ollama.com/api/chat |
| Ollama embed API | separate embedding endpoint for semantic search | https://docs.ollama.com/api/embed |
| Ollama embeddings guide | use embedding-specific models such as `embeddinggemma`, `qwen3-embedding`, `all-minilm` | https://docs.ollama.com/capabilities/embeddings |
| SQLite FTS5 | deterministic local full-text search, BM25-style ranking | https://www.sqlite.org/fts5.html |
| Windows schtasks | after-hours automation on Windows | https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/schtasks-create |

## Automation Patterns

### 1. Source Ledger

Maintain a machine-readable ledger of every raw source.

```json
{
  "source_id": "src-2026-001",
  "path": "raw/policy/security-review.md",
  "sha256": "...",
  "type": "markdown",
  "status": "new|ingested|needs-review|archived",
  "last_ingested_at": "2026-06-25T22:30:00+09:00"
}
```

Automation:

- scan raw folder
- calculate hash
- detect new/changed/deleted sources
- queue only changed sources for LLM review

Why:

- prevents reprocessing everything nightly
- gives provenance
- avoids LLM rewriting pages without source changes

References:

- LLM-WIKI-MCP supports provenance-aware re-ingestion and local indexed vaults: https://github.com/Electro-resonance/LLM-WIKI-MCP
- LLM-Wiki GeekNews emphasizes raw sources as immutable truth: https://news.hada.io/topic?id=28208

### 2. Two-Speed Model Pipeline

Use a fast model for extraction and a heavier model for synthesis.

```text
fast model
  -> title/concept/tag candidates
  -> source summary
  -> quality score

heavier model or stronger agent
  -> draft article
  -> contradiction check
  -> synthesis page
```

For the current PC:

| Role | Model |
| --- | --- |
| fast scout | `qwen2.5-coder:7b` |
| cheaper fallback | `hermes3:3b` or smaller Qwen |
| heavier local experiment | installed `qwen3.5:9b` / `qwen3.5-9b-64k`, only if latency is acceptable |
| cloud/strong review | optional, only with sanitized context |

References:

- `obsidian-llm-wiki-local` uses fast 3B-8B ingest and heavier 7B-14B compile: https://github.com/kytmanov/obsidian-llm-wiki-local
- Qwen role policy in this repo: `docs/03-qwen-role-policy.md`

### 3. Draft-Approve-Publish

Never let local LLM directly overwrite curated wiki pages.

```text
wiki/.drafts/topic.md
  -> lint
  -> diff
  -> approve / reject / edit
  -> wiki/topic.md
```

Automation:

- write drafts under `.drafts/`
- store rejection feedback
- inject rejection feedback into next compile
- strip low-confidence annotations only when approved

References:

- `obsidian-llm-wiki-local` review stage approves/rejects/diffs/edits drafts and publishes after approval: https://github.com/kytmanov/obsidian-llm-wiki-local

### 4. Index as Router

Keep `wiki/index.md` as the first navigation file.

```md
# Wiki Index

## Security

- [[api-authentication]] - OAuth/API key migration notes

## Operations

- [[incident-response]] - incident ownership and follow-up process
```

Automation:

- update index when pages are approved
- include one-line summary per page
- include metadata such as status, last source, source count

References:

- GeekNews LLM-Wiki notes `index.md` as a content-centered catalog and routing layer: https://news.hada.io/topic?id=28208
- `obsidian-llm-wiki-local` uses `wiki/index.md` as routing layer instead of embeddings for small vaults: https://github.com/kytmanov/obsidian-llm-wiki-local

### 5. Append-Only Fact Log

For entity-like pages, store facts as append-only JSONL before synthesis.

```jsonl
{"fact_id":"api-auth-0001","entity":"api-authentication","claim":"OAuth clients support scoped access.","source_id":"src-2026-001","offset":412}
{"fact_id":"api-auth-0002","entity":"api-authentication","claim":"API keys require manual rotation.","source_id":"src-2026-002","offset":94}
```

Automation:

- extract fact candidates only when evidence phrase appears in source
- assign deterministic IDs
- rebuild entity brief after N new facts
- do not delete old facts; supersede them

References:

- WUPHF uses per-entity fact logs and deterministic IDs including sentence offsets: https://news.hada.io/topic?id=28910

### 6. Promotion Flow

Separate personal/agent notebooks from shared wiki.

```text
agents/qwen-scout/notebook/*.md
  -> reviewed candidates
  -> team/wiki/*.md
```

Automation:

- notebook entries expire unless promoted
- promoted entries require source evidence
- backlinks are generated during promotion

References:

- WUPHF describes per-agent notebooks and promotion into shared team wiki: https://news.hada.io/topic?id=28910

### 7. Lint and Repair

Run wiki lint nightly and write a human review report.

Lint checks:

- orphan pages
- broken wikilinks
- missing source refs
- stale source hash
- thin pages
- duplicate titles
- pages with too many low-confidence claims
- contradictions between source summary and page claim

Repair policy:

- safe repairs can update index/dangling metadata
- risky repairs produce candidate patches only
- never auto-delete pages

References:

- GeekNews LLM-Wiki lists lint items including contradictions, stale claims, orphan pages, missing cross-references: https://news.hada.io/topic?id=28208
- LLM-WIKI-MCP supports linting and repair commands: https://github.com/Electro-resonance/LLM-WIKI-MCP
- NiharShrotri/llm-wiki includes `wiki lint --fix`: https://github.com/NiharShrotri/llm-wiki

### 8. Hybrid Search Optionality

Start simple, add vector search only when FTS/BM25 fails.

```text
Phase 1: ripgrep + index.md
Phase 2: SQLite FTS5
Phase 3: BM25 + vector + reranker
Phase 4: MCP tool interface
```

References:

- SQLite FTS5 official docs: https://www.sqlite.org/fts5.html
- GeekNews WUPHF notes markdown + git + BM25/SQLite before vector DB: https://news.hada.io/topic?id=28910
- NiharShrotri/llm-wiki uses QMD hybrid BM25 + vector + LLM reranker: https://github.com/NiharShrotri/llm-wiki

### 9. Context Pack Generation

Generate compact evidence packs for stronger agents.

```json
{
  "task": "review authentication migration plan",
  "selected_pages": [
    {
      "path": "wiki/api-authentication.md",
      "reason": "defines credential migration concerns"
    }
  ],
  "excluded_pages": [
    {
      "path": "wiki/coding-style.md",
      "reason": "low relevance"
    }
  ]
}
```

Automation:

- retrieve top pages
- hydrate full pages only for top few hits
- summarize why each context item matters
- let strong agent verify from source-backed pages

References:

- LLM-WIKI-MCP supports context-pack generation: https://github.com/Electro-resonance/LLM-WIKI-MCP
- NiharShrotri/llm-wiki hydrates top 5-8 search hits before synthesis: https://github.com/NiharShrotri/llm-wiki

### 10. Save-Back Synthesis

When a query produces a useful synthesis, save it as a new reviewed page rather than losing it in chat history.

```text
query
  -> cited answer
  -> save as wiki/synthesis/topic-comparison.md
  -> link from index
```

References:

- NiharShrotri/llm-wiki supports `wiki query ... --save-as ...`: https://github.com/NiharShrotri/llm-wiki
- GeekNews LLM-Wiki notes that good answers can be stored back as pages: https://news.hada.io/topic?id=28208

### 11. Nightly Review Queue

Good overnight jobs:

- source hash scan
- FTS rebuild
- stale page detection
- orphan link report
- link candidate generation
- thin page candidate generation
- contradiction candidate generation for changed sources only
- context-pack cache generation for frequent tasks

Bad overnight jobs:

- rewrite entire wiki
- delete old pages
- publish drafts automatically
- run all-pairs contradiction checks
- send raw private sources to cloud APIs

References:

- Windows Task Scheduler: https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/schtasks-create
- `docs/04-overnight-jobs.md`

## Local LLM Test

Test command:

```powershell
python .\scripts\ollama_wiki_scout.py gap-questions `
  --model qwen2.5-coder:7b `
  --text "Draft: automate an LLM-maintained markdown wiki from local source documents..."
```

Observed output:

```json
{
  "must_ask": [
    "Who will own the LLM-maintained markdown wiki system?",
    "What is the expected frequency of updates to the pages based on local source documents?",
    "How should the review reports be structured and who will use them?"
  ],
  "should_ask": [
    "What are the criteria for determining when a page needs an update?",
    "Should there be a rollback mechanism in case of errors during automated updates?",
    "How will security measures be implemented to protect sensitive information in the wiki?"
  ]
}
```

Assessment:

- Good enough for gap-question generation.
- Too slow for large all-page overnight synthesis if repeated many times.
- Should remain a candidate generator, not a publisher.

## Practical Recommendation

For this PC and workflow, implement automation in this order:

1. `source-ledger.jsonl`
2. `wiki/index.md` and `wiki/log.md`
3. SQLite FTS5 index
4. `qwen2.5-coder:7b` query expansion and gap-question candidate generation
5. draft-approve-publish workflow
6. nightly lint report
7. context-pack generation
8. optional embeddings/reranker only after FTS misses real queries

This keeps the local LLM useful without letting it reduce answer quality.
