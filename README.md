# Local LLM Wiki + Ollama Playbook

사내 업무용 PC에서 **LLM Wiki**와 **Ollama local LLM**을 연결할 때 참고하기 위한 공개 playbook이다.

이 저장소의 결론은 단순하다.

> 검색, 색인, 검증은 deterministic script가 맡고, local LLM은 wiki 유지보수를 돕는 후보 생성기로 제한한다.

Local LLM을 억지로 답변자나 코딩 에이전트로 쓰면 품질이 떨어질 수 있다. 이 playbook은 local LLM을 다음 역할로만 권장한다.

- 검색어 확장
- 문서 chunk 라벨 후보 생성
- wiki link 후보 생성
- 모순/누락 질문 후보 생성
- 야간 batch로 stale page, orphan link, thin page 후보 생성
- AGENTS.md / skill rule의 모순, 누락, stale reference 감사 보고서 생성
- cloud AI에 넘길 context pack을 줄이는 사전 필터
- 반복 작업의 recipe와 compact run log를 저장하는 agentic memory

## 대상 환경

이 playbook은 다음 환경을 기준으로 작성했다.

| 항목 | 기준 |
| --- | --- |
| OS | Windows 업무용 PC 우선 |
| RAM | 64 GB |
| VRAM | 8 GB |
| Local LLM runtime | Ollama |
| 보유 모델 | `qwen2.5-coder:7b` |
| 권장 기본 역할 | local wiki scout, JSON 후보 생성기 |

`qwen2.5-coder:7b`는 Ollama library에서 4.7 GB, 32K context window로 제공된다. 8 GB VRAM에서는 “작은 JSON 후보 생성/문서 정리” 용도로 현실적이다. 다만 embedding/search 전용 모델은 아니므로 semantic embedding은 Ollama의 `embeddinggemma`, `qwen3-embedding`, `all-minilm` 같은 embedding 모델을 별도로 쓰는 편이 낫다.

## 핵심 참고 자료

| 주제 | 근거 |
| --- | --- |
| LLM Wiki 개념 | Andrej Karpathy의 LLM Wiki gist: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f |
| LLM Wiki 요약/토론 | GeekNews LLM-Wiki: https://news.hada.io/topic?id=28208 |
| Markdown + Git + BM25/SQLite 사례 | GeekNews WUPHF: https://news.hada.io/topic?id=28910 |
| Local RAG 구현 선택지 | GeekNews Ask HN local RAG: https://news.hada.io/topic?id=25854 |
| Ollama chat API | https://docs.ollama.com/api/chat |
| Ollama embed API | https://docs.ollama.com/api/embed |
| Ollama embeddings guide | https://docs.ollama.com/capabilities/embeddings |
| Qwen2.5 Ollama 실행 | https://qwen.readthedocs.io/en/latest/run_locally/ollama.html |
| Qwen2.5-Coder Ollama | https://ollama.com/library/qwen2.5-coder:7b |
| SQLite FTS5 | https://www.sqlite.org/fts5.html |
| Windows schtasks | https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/schtasks-create |
| PowerShell ScheduledTasks | https://learn.microsoft.com/en-us/powershell/module/scheduledtasks/new-scheduledtaskaction |
| Obsidian links/properties | https://obsidian.md/help/links, https://obsidian.md/help/properties |

## 문서 구조

```text
local-llm-wiki-ollama-playbook/
  README.md
  REPORT.md
  docs/
    01-architecture.md
    02-windows-ollama-setup.md
    03-qwen-role-policy.md
    04-overnight-jobs.md
    05-command-patterns.md
    06-reference-map.md
    07-automation-ideas-research.md
    08-local-llm-use-cases-by-github-stars.md
    09-agents-rule-self-maintenance.md
    10-agentic-memory-operating-model.md
  examples/
    wiki/
      index.md
      api-authentication.md
      incident-response.md
      coding-style.md
    qwen-candidates/
      query-expansion.example.json
      link-candidates.example.json
      gap-questions.example.json
    rules-audit/
      agents-audit.example.md
    memory/
      obsidian-spec-refresh.recipe.json
      obsidian-spec-refresh.run.example.json
  scripts/
    ollama_wiki_scout.py
    agentic_memory.py
    install_nightly_task.ps1
    rules_self_audit.py
    install_agents_audit_task.ps1
```

## 빠른 시작

1. Ollama가 실행 중인지 확인한다.

```powershell
ollama list
ollama run qwen2.5-coder:7b
```

2. Python 예제 스크립트로 JSON 후보 생성을 테스트한다.

```powershell
python .\scripts\ollama_wiki_scout.py expand-query `
  --model qwen2.5-coder:7b `
  --text "How should a team migrate from API key authentication to OAuth?"
```

3. 야간 작업은 먼저 dry-run처럼 수동 실행한다.

```powershell
python .\scripts\ollama_wiki_scout.py gap-questions `
  --model qwen2.5-coder:7b `
  --text "Draft requirement: internal tooling should keep audit logs for administrative actions."
```

4. 충분히 안정화된 뒤에만 Windows Task Scheduler에 등록한다.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\install_nightly_task.ps1
```

5. AGENTS.md / skills / rule 파일의 모순과 누락은 read-only 감사로 먼저 확인한다.

```powershell
python .\scripts\rules_self_audit.py `
  --repo C:\GitRepositories\embedded-ax-devkit `
  --include-skill-references `
  --out reports\agents-audit-manual.md
```

6. 반복 작업 recipe는 agentic memory에 저장한다.

```powershell
python .\scripts\agentic_memory.py init
python .\scripts\agentic_memory.py add-recipe .\examples\memory\obsidian-spec-refresh.recipe.json
python .\scripts\agentic_memory.py search "옵시디언 표준사양 최신화" --kind recipe
```

## 권장 아키텍처

```text
raw documents
  -> deterministic ingest scripts
  -> SQLite FTS5 / file index / optional embeddings
  -> local LLM wiki scout candidate files
  -> agentic memory recipes / compact run logs
  -> human or strong coding agent review
  -> curated markdown wiki
```

중요한 점은 local LLM이 원본 truth를 확정하지 않는 것이다. Qwen은 후보를 만든다. 확정은 사람이 하거나 더 강한 coding/review agent가 원문 근거를 확인한 뒤 한다.

## 금지 원칙

- `qwen2.5-coder:7b`에게 최종 업무 판단을 맡기지 않는다.
- 검색/색인을 local LLM에게 맡기지 않는다. SQLite FTS5, ripgrep, Python script를 우선한다.
- local LLM 출력으로 wiki 본문을 자동 덮어쓰지 않는다.
- 전체 대화 transcript나 원본 사양 전문을 agentic memory에 저장하지 않는다.
- 야간 AGENTS/rule 감사 결과로 규칙 파일을 자동 덮어쓰지 않는다. 보고서와 patch 후보까지만 자동화한다.
- 모순 후보를 발견했다고 기존 지식을 자동 삭제하지 않는다.
- 사내 원문을 public repo, cloud AI, 외부 API에 올리지 않는다.
- 답변 품질이 떨어지는 workflow라면 local LLM 도입을 중단한다.

## 적용 판단 기준

Local LLM을 도입할 가치가 있는 경우:

- 문서가 많아 사람이 매일 라벨링하기 어렵다.
- cloud AI에 원문을 올릴 수 없다.
- JSON 후보 생성이 조금 틀려도 후속 검증이 가능하다.
- 야간에 저부하 작업을 돌릴 수 있다.
- wiki 링크/질문/검색어 확장처럼 정답보다 후보가 필요한 작업이다.

도입하지 않는 편이 나은 경우:

- 이미 Python script가 완벽히 규칙 기반으로 처리한다.
- local LLM 출력 때문에 사람이 더 많이 검토해야 한다.
- 작은 모델이 같은 실수를 반복한다.
- 답변자가 필요하지 후보 생성기가 필요한 것이 아니다.
