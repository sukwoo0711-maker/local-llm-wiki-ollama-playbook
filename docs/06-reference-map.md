# 06. Reference Map

모든 주요 아이디어와 근거 URL을 연결한다.

| Idea | Recommendation | Reference |
| --- | --- | --- |
| LLM Wiki is persistent, not query-time only | Build a durable markdown wiki between raw sources and answers | https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f |
| RAG re-derives knowledge on every query | Use RAG/search for retrieval, but compile stable knowledge into wiki pages | https://news.hada.io/topic?id=28208 |
| Markdown + Git can be enough early | Start with markdown/git before heavier graph/vector infra | https://news.hada.io/topic?id=28910 |
| SQLite FTS5 is suitable for local full-text search | Use deterministic search before LLM reasoning | https://www.sqlite.org/fts5.html |
| Local RAG can start without vector DB | For markdown documents, FTS5/BM25 may be enough; add vectors later | https://news.hada.io/topic?id=25854 |
| Ollama chat API supports JSON mode | Use JSON-only candidate generation | https://docs.ollama.com/api/chat |
| Ollama embed API exists | Use `/api/embed` with embedding models for optional semantic search | https://docs.ollama.com/api/embed |
| Embedding models are separate | Use `embeddinggemma`, `qwen3-embedding`, or `all-minilm`, not coder model | https://docs.ollama.com/capabilities/embeddings |
| Qwen2.5 runs in Ollama | Use `ollama run qwen2.5` or specific tags | https://qwen.readthedocs.io/en/latest/run_locally/ollama.html |
| Qwen2.5-Coder model sizes | Use `qwen2.5-coder:7b` as baseline for 8 GB VRAM candidate generation | https://ollama.com/library/qwen2.5-coder:7b |
| Obsidian links create knowledge network | Wikilinks can make the markdown wiki navigable | https://obsidian.md/help/links |
| Obsidian properties support metadata | Use `tags`, `aliases`, and custom properties in frontmatter | https://obsidian.md/help/properties |
| Windows nightly automation | Use Task Scheduler/schtasks after manual dry-run | https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/schtasks-create |
| PowerShell scheduled task actions | Use ScheduledTasks cmdlets for maintainable task registration | https://learn.microsoft.com/en-us/powershell/module/scheduledtasks/new-scheduledtaskaction |
| AGENTS.md context files can drift | Audit agent context files for stale references, conflicts, weak guidance, and missing maintenance rules | https://github.com/samilozturk/agentlint |
| Agent harness can be linted | Score AGENTS/CLAUDE/rules/CI/hooks with deterministic checks before agent work | https://github.com/marketplace/actions/agentlint |
| Self-audit + verification + adversarial review | Use layered verification reports for AI-generated or AI-maintained outputs | https://github.com/github/awesome-copilot/blob/main/docs/README.agents.md |
| AGENTS.md is a shared open format | Keep top-level AGENTS.md as a concise routing surface for coding agents | https://github.com/agentsmd/agents.md |
| Rule collections use routing | Split large instruction files into targeted rule files instead of loading everything | https://github.com/PatrickJS/awesome-cursorrules |
| agents.md needs operational discipline | Treat agents.md as maintained project infrastructure, not a one-off prompt dump | https://github.blog/ai-and-ml/github-copilot/how-to-write-a-great-agents-md-lessons-from-over-2500-repositories/ |
| LLM Wiki MCP pattern | Use CLI/MCP around a local Markdown wiki, SQLite index, context packs, lint and repair | https://github.com/Electro-resonance/LLM-WIKI-MCP |
| Draft/review/publish workflow | Generate drafts first, review/approve, then publish to curated wiki | https://github.com/kytmanov/obsidian-llm-wiki-local |
| Hybrid search and save-back | Use BM25/vector/rerank for query and save useful answers as synthesis pages | https://github.com/NiharShrotri/llm-wiki |
| Knowledge compiler | Compile raw sources into citation-traceable interlinked Markdown pages | https://github.com/atomicstrata/llm-wiki-compiler |
| Agent-maintained team wiki | Use per-agent notebooks, shared wiki promotion, fact logs, BM25/SQLite | https://news.hada.io/topic?id=28910 |
