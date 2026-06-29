# 10. Agentic Memory Operating Model

검토일: 2026-06-30

## 조사 범위

`sukwoo0711-maker` GitHub 계정과 로컬 clone에서 LLM Wiki, relation graph, agent memory 관련 내용을 확인했다.

확인한 repo:

| Repo | 확인한 내용 | 판단 |
| --- | --- | --- |
| `local-llm-wiki-ollama-playbook` | LLM Wiki 구조, Ollama scout, SQLite FTS5, draft/review/publish, save-back synthesis, AGENTS rule audit가 있다. | 원칙은 좋지만 agentic memory 저장소와 자동 recipe/run-log schema가 없다. |
| `local-relation-graph-viewer-v2` | JSONL record graph, evidence, review status, privacy scan, local HTML viewer가 있다. | LLM Wiki 결과나 사양 관계를 사람이 검토하는 UI로 좋다. memory 자체의 source of truth는 아니다. |
| `embedded-ax-devkit` | context graph/agent memory evaluation 문서가 있다. Neo4j/Graphiti는 보류하고 YAML/Markdown/Mermaid decision trace를 우선하자는 결론이다. | 현재 판단과 일치한다. 무거운 graph DB보다 SQLite/Markdown 기반 memory가 먼저다. |
| `repo-parser` | repo metadata/heading/symbol map을 만든다. | context map에는 좋지만 반복 작업 recipe 저장소는 아니다. |

주요 근거:

- `README.md`: local LLM은 candidate generator로 제한한다.
- `docs/01-architecture.md`: deterministic search/index, Qwen candidate layer, human/strong agent review를 분리한다.
- `docs/07-automation-ideas-research.md`: source ledger, draft-approve-publish, save-back synthesis, nightly review queue를 제안한다.
- `docs/09-agents-rule-self-maintenance.md`: AGENTS/rule 자동화는 report-only와 patch candidate 경계가 맞다고 정리한다.
- `embedded-ax-devkit/docs/12-context-graph-agent-memory-evaluation.md`: graph DB는 보류하고 decision trace/provenance를 기존 workflow에 가볍게 흡수하라고 판단한다.

## 비판적 리뷰

### 잘 된 부분

- raw source와 curated wiki를 분리한다.
- 검색/색인/검증을 deterministic script에 맡긴다.
- local LLM은 JSON 후보 생성기로 제한한다.
- draft/review/publish 경계가 있다.
- 근거 링크와 source hash를 남기려는 방향이 있다.
- relation graph viewer는 evidence와 review 상태를 표시한다.

### 빠진 부분

반복 작업에서 토큰을 줄이려면 다음 기억이 필요하다.

| Memory | 필요성 | 현재 상태 |
| --- | --- | --- |
| procedural memory | "옵시디언 표준사양 최신화" 같은 반복 작업 절차를 재사용한다. | 문서에는 아이디어가 있지만 machine-readable recipe가 없다. |
| episodic memory | 지난 실행의 결과, 경고, 실패를 압축 저장한다. | run log schema가 없다. |
| decision memory | SQLite를 source of truth로 둔 이유 같은 설계 결정을 재사용한다. | 문서에 흩어져 있고 query 가능한 저장소가 없다. |
| pitfall memory | `section_path`를 링크로 만들지 않는 규칙 같은 실수를 방지한다. | 대화에는 있었지만 repo에 durable하게 없다. |
| retrieval interface | agent가 필요한 memory만 찾는다. | MCP/SQLite memory query가 없다. |

### 위험

자동 memory를 "대화 전체 저장"으로 만들면 실패한다.

- 토큰이 줄지 않고 오히려 늘어난다.
- 미검증 LLM 추론이 다음 작업을 오염시킨다.
- 원본 사양/민감정보가 memory에 남을 수 있다.
- 오래된 run log가 최신 recipe보다 우선될 수 있다.

따라서 저장 단위는 transcript가 아니라 `recipe`, `decision`, `pitfall`, `compact run_log`여야 한다.

## To-Be

```text
user request
  -> search agentic memory
  -> load matching recipe/checklist
  -> inspect current repo/source state
  -> execute deterministic tools
  -> write compact run log
  -> update recipe only after repeated success or explicit review
```

## Memory categories

| Kind | 저장할 것 | 저장하지 말 것 |
| --- | --- | --- |
| `recipe` | 반복 작업 절차, 입력/출력, validation checklist, 금지 규칙 | 원본 사양 전문 |
| `run_log` | 실행 결과 요약, count, hash, warning, result | 전체 stdout, 전체 대화 |
| `decision` | 설계 결정과 근거 | 미검증 추측 |
| `pitfall` | 반복 실수와 회피 규칙 | 개인/사내 민감 문자열 |

## 구현 보완

이 repo에 `scripts/agentic_memory.py`를 추가했다.

특징:

- Python standard library만 사용한다.
- SQLite + FTS5로 compact memory를 저장/검색한다.
- memory DB는 `memory/agentic_memory.sqlite`에 생성한다.
- 저장 대상은 recipe/run_log부터 시작한다.
- generated DB는 public Git에 넣지 않는다.

초기화:

```powershell
python .\scripts\agentic_memory.py init
```

Obsidian spec refresh recipe 저장:

```powershell
python .\scripts\agentic_memory.py add-recipe .\examples\memory\obsidian-spec-refresh.recipe.json
```

예시 run log 저장:

```powershell
python .\scripts\agentic_memory.py add-run-log .\examples\memory\obsidian-spec-refresh.run.example.json
```

다음 작업에서 recipe 검색:

```powershell
python .\scripts\agentic_memory.py search "옵시디언 표준사양 최신화" --kind recipe
```

ID로 recipe 로드:

```powershell
python .\scripts\agentic_memory.py get task.obsidian_spec_refresh
```

## Obsidian spec refresh memory example

`examples/memory/obsidian-spec-refresh.recipe.json`에는 다음 규칙을 넣었다.

- SQLite `specs` table is the local normalized source of truth.
- Obsidian generated notes are read-only views.
- Human comments go to `reviews/*.review.md`.
- `section_path` values such as `3.1.1` must not become Obsidian links or graph nodes.
- Do not store raw original specs in agentic memory.

이 recipe는 다음 사용자 요청에 매칭된다.

- "옵시디언에 표준사양 문서를 최신화해줘"
- "사양 md 다시 생성해줘"
- "SQLite 기준으로 Obsidian vault export 갱신"

## 운영 규칙

1. 자동 저장은 run log까지 허용한다.
2. recipe 변경은 반복 성공, 사용자 승인, 또는 실패 분석 근거가 있을 때만 한다.
3. agentic memory에 원본 사양 전문을 저장하지 않는다.
4. `source_refs`를 항상 남긴다.
5. memory 검색 결과는 실행 전 현재 repo 상태로 검증한다.
6. 오래된 memory는 삭제보다 `status=stale`로 전환한다.

## 다음 단계

1. `decision`과 `pitfall` JSON 예시를 추가한다.
2. MCP server wrapper를 추가해서 Codex/Claude/Cursor가 같은 SQLite memory를 검색하게 한다.
3. `rules_self_audit.py` 결과 중 반복되는 warning을 `pitfall` 후보로 저장한다.
4. Obsidian export pipeline이 생기면 실행 후 compact run log를 자동 저장한다.
