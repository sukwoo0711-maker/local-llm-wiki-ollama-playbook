# 08. Local LLM Use Cases by GitHub Stars

조사일: 2026-06-25  
기준: GitHub REST API로 확인한 star 수, 현재 PC의 Ollama 모델, RTX 3070 Ti 8 GB VRAM, 사내 업무 PC 적용 가능성

## 결론

`qwen2.5-coder:7b`를 단순 wiki scout로만 쓰면 아깝다. 하지만 강한 cloud coding agent를 대체하려고 하면 실망할 가능성이 높다.

가장 현실적인 역할은 다음이다.

```text
Qwen local LLM = private preflight assistant
```

즉, 사내 원문/코드/로그를 외부로 보내기 전에 로컬에서 1차로 훑는 역할이다.

권장 활용:

- compile error triage
- test failure 요약
- 코드 변경 전 영향 범위 후보
- 작은 함수 단위 리팩토링 계획 초안
- private code/document Q&A
- 문서/회의록/action item 정리
- LLM-Wiki 후보 생성
- nightly preflight report

비권장 활용:

- 최종 코드 리뷰
- 사양/규격 최종 판단
- 자동 코드 수정/자동 merge
- 긴 agent loop
- 전체 repo를 통째로 이해시키는 작업
- 검색엔진 대체

## Local Environment

현재 확인:

```text
GPU: NVIDIA GeForce RTX 3070 Ti, 8192 MiB
Installed Ollama models:
  qwen2.5-coder:7b      4.7 GB
  qwen3.5-9b-64k        6.6 GB
  qwen3.5:9b            6.6 GB
  hermes3:3b            2.0 GB
```

주의: 현재 명령에서 Windows WMI는 RAM을 약 16 GB로 보고했다. 사용자가 제시한 사내 PC 목표 환경은 64 GB RAM / 8 GB VRAM이다. 모델 추천은 8 GB VRAM 제약을 우선 반영한다.

## GitHub Star Sorted Landscape

| Rank | Repo | Stars | What it is | 사내 PC 적합도 |
| ---: | --- | ---: | --- | --- |
| 1 | `n8n-io/n8n` | 193,888 | workflow automation with AI integrations | 높음, 야간 자동화/보고서에 좋음 |
| 2 | `Significant-Gravitas/AutoGPT` | 185,149 | autonomous agent platform | 낮음, 사내 업무에는 과자율 위험 |
| 3 | `ollama/ollama` | 174,843 | local model runtime | 매우 높음, 이미 사용 중 |
| 4 | `huggingface/transformers` | 161,866 | model framework | 중간, 운영보다 실험/모델 확인용 |
| 5 | `langflow-ai/langflow` | 150,027 | visual agent/workflow builder | 중간, PoC용 |
| 6 | `langgenius/dify` | 146,434 | agent/workflow app platform | 중간, 내부 app화할 때 |
| 7 | `open-webui/open-webui` | 142,856 | Ollama/OpenAI compatible chat UI | 매우 높음, 사내 로컬 LLM 포털 |
| 8 | `langchain-ai/langchain` | 140,096 | agent/RAG framework | 중간, 직접 구현 시 |
| 9 | `ggml-org/llama.cpp` | 117,952 | efficient local inference | 중간, Ollama 아래 기술 이해/특수 실행 |
| 10 | `openai/codex` | 93,357 | terminal coding agent | 이미 사용 중, 강한 작업은 Codex |
| 11 | `vllm-project/vllm` | 83,740 | high-throughput serving | 낮음, 8 GB 단일 GPU에는 과함 |
| 12 | `lobehub/lobehub` | 79,038 | agent operations/chat platform | 중간, UI/agent management 관심 시 |
| 13 | `OpenHands/OpenHands` | 78,218 | AI software development agent | 낮음-중간, local 7B만으로는 품질 불안 |
| 14 | `openinterpreter/openinterpreter` | 64,115 | local/open model code interpreter | 중간, read-only/sandbox 작업에 한정 |
| 15 | `Mintplex-Labs/anything-llm` | 62,020 | local-first document/agent workspace | 매우 높음, 사내문서 Q&A 후보 |
| 16 | `mem0ai/mem0` | 59,346 | AI memory layer | 중간, 장기 memory 실험 |
| 17 | `microsoft/autogen` | 59,208 | agentic AI framework | 중간-낮음, 로컬 7B에는 과함 |
| 18 | `crewAIInc/crewAI` | 54,290 | multi-agent orchestration | 중간-낮음, 명확한 workflow 있을 때만 |
| 19 | `FlowiseAI/Flowise` | 53,982 | visual AI agent builder | 중간, RAG PoC용 |
| 20 | `run-llama/llama_index` | 50,352 | document agent/RAG framework | 높음, 문서 파이프라인 구현 시 |
| 21 | `oobabooga/textgen` | 47,370 | local LLM desktop/API app | 중간, 모델 실험용 |
| 22 | `janhq/jan` | 43,170 | offline ChatGPT-like desktop app | 높음, 단순 local chat UI |
| 23 | `QuivrHQ/quivr` | 39,175 | opinionated RAG app | 중간, 문서 Q&A app |
| 24 | `khoj-ai/khoj` | 35,282 | self-hosted second brain and automations | 높음, local docs + scheduled research |
| 25 | `continuedev/continue` | 34,415 | open-source coding agent/IDE assistant | 매우 높음, 로컬 코드 보조 |
| 26 | `QwenLM/Qwen3` | 27,329 | Qwen model family | 모델 검토 근거 |
| 27 | `deepset-ai/haystack` | 25,678 | RAG/search/agent pipelines | 중간, production pipeline용 |
| 28 | `Cinnamon/kotaemon` | 25,487 | document chat/RAG UI | 높음, 사내문서 QA 후보 |

Source: GitHub REST API, 2026-06-25.

## Best-Fit Stack for the Office PC

### Tier 1: 바로 쓸 만한 조합

| Purpose | Tool | Model | Why |
| --- | --- | --- | --- |
| Local chat portal | Open WebUI or Jan | `qwen2.5-coder:7b`, `qwen3.5:9b` | 사내 PC에서 private chat UI |
| Document Q&A | AnythingLLM or Kotaemon | `qwen3.5-9b-64k` for synthesis, embedding model for retrieval | scout보다 실용적 |
| IDE/code preflight | Continue | `qwen2.5-coder:7b` | 코드 설명/compile error/test failure triage |
| Nightly workflow | n8n or Windows Task Scheduler | `qwen2.5-coder:7b` | 보고서 자동화 |
| LLM-Wiki maintenance | current playbook scripts | `qwen2.5-coder:7b` + FTS5 | 안전한 후보 생성 |

### Tier 2: PoC 후 결정

| Purpose | Tool | Reason |
| --- | --- | --- |
| Visual RAG builder | Flowise/Langflow | 만들기는 쉽지만 운영 복잡도 증가 |
| Custom document pipeline | LlamaIndex/Haystack | 직접 구현할 때 강력하지만 boilerplate 필요 |
| Long-term memory | mem0/Khoj | 유용하지만 privacy/정합성 정책 필요 |
| Local code interpreter | Open Interpreter | read-only, temp workspace에서만 |

### Tier 3: 현재는 비추천

| Tool | Why |
| --- | --- |
| AutoGPT | 자율 loop가 과하고 작은 local model과 궁합이 나쁨 |
| vLLM | 단일 8 GB GPU 업무 PC에는 serving 목적이 과함 |
| Multi-agent frameworks only | local 7B/9B 모델 여러 개를 돌리는 것보다 하나를 잘 제한하는 편이 낫다 |

## Better Than Scout: Practical Use Cases

### 1. Compile Error Triage

`qwen2.5-coder:7b`에 compile log와 관련 snippet만 넣고 원인 후보와 다음 check를 JSON으로 받는다.

테스트 결과:

```json
{
  "likely_causes": [
    "The function 'init_uart' is not declared or defined in any of the included files.",
    "The macro 'UART_BAUD_115200' is not defined or misspelled."
  ],
  "next_checks": [
    "Check the board.h and spi.h files to ensure that the 'init_uart' function is declared and that the 'UART_BAUD_115200' macro is defined.",
    "Verify if there is a typo or if the correct header file needs to be included."
  ],
  "risk": "low"
}
```

평가:

- error 2개는 잘 잡았다.
- `const` qualifier warning은 놓쳤다.
- 따라서 “사람 대신 리뷰”는 아니고 “compile log preflight”가 맞다.

추천 명령 패턴:

```text
You are a local compile-error triage assistant.
Return JSON only.
Do not edit code.
Identify likely cause, exact evidence, next local checks, and warnings not explained.
```

### 2. Test Failure Summarizer

입력:

- failing test name
- assertion diff
- recent changed files

출력:

```json
{
  "failure_type": "contract mismatch|timing|format|logic|test stale",
  "likely_files": [],
  "evidence": [],
  "next_checks": []
}
```

가치:

- 긴 pytest/unittest 로그를 Codex에 넘기기 전에 압축
- 사내 code/log를 cloud로 보내지 않아도 됨

### 3. Private Codebase Explainer

입력:

- 한 파일 또는 함수
- 주변 README/contract 일부

출력:

- 함수 역할 요약
- 숨은 side effect 후보
- 리팩토링 전 확인할 질문
- call graph 후보

주의:

- qwen이 call graph를 확정하면 안 된다.
- `rg`, compiler, ctags, clangd, static analysis가 근거여야 한다.

### 4. Small Refactor Planner

좋은 용도:

- 50-200줄 함수 분해 후보
- naming 개선
- duplicate branch 감지
- guard clause 제안
- test case 후보

나쁜 용도:

- 직접 patch 생성 후 적용
- scheduler/interrupt/register/protocol 변경
- 사양 기반 behavior 변경

### 5. Local Document Q&A

AnythingLLM, Kotaemon, Khoj, Open WebUI를 붙이면 scout보다 가치가 커진다.

추천:

```text
Open WebUI = 범용 로컬 챗 포털
AnythingLLM/Kotaemon = 사내문서 Q&A workspace
Khoj = second brain + scheduled automation
```

검색은 embedding/FTS가 맡고 Qwen은 answer synthesis만 맡긴다.

### 6. Nightly Preflight Report

퇴근 후 실행:

- changed source summary
- new document gap questions
- broken wiki links
- stale page candidates
- compile/test log summary
- tomorrow's review queue

출력:

```text
reports/nightly-YYYY-MM-DD.md
```

이건 scout보다 훨씬 실용적이다. 아침에 “어제 무엇이 바뀌었고 무엇을 봐야 하는지”만 보면 된다.

### 7. Local Red-Team for Requirements

grill-me 전에 Qwen으로 질문 후보를 만든다.

```text
Qwen -> broad missing questions
grill-me -> aggressive requirement interrogation
Codex -> implementation/review
```

이때 Qwen은 질문 다양성 생성기로 쓰기 좋다.

## Model Recommendation

### Keep

| Model | Use |
| --- | --- |
| `qwen2.5-coder:7b` | compile/test/code preflight, small refactor planning, JSON candidates |
| `qwen3.5-9b-64k` | long-context document synthesis experiments, context pack review |
| `qwen3.5:9b` | general reasoning/document QA if latency acceptable |
| `hermes3:3b` | very fast routing/classification if quality is acceptable |

### Add

| Model | Use | Why |
| --- | --- | --- |
| `embeddinggemma` | embeddings | Ollama recommended embedding model |
| `qwen3-embedding` | embeddings | Qwen ecosystem embedding model |
| `all-minilm` | lightweight embeddings | fast baseline |

Reference: https://docs.ollama.com/capabilities/embeddings

### Avoid for now

| Model class | Why |
| --- | --- |
| 14B+ interactive models | 8 GB VRAM에서는 CPU spill/latency가 커질 수 있음 |
| huge context by default | 작은 모델에 긴 context를 넣으면 느리고 산만해짐 |
| local model as final reviewer | 놓치는 warning/edge case가 있음 |

## Recommended Rollout

### Week 1: Local Preflight

1. Keep Ollama + `qwen2.5-coder:7b`.
2. Add compile/test failure triage command.
3. Add nightly report for changed files/logs.
4. Do not let Qwen edit files.

### Week 2: Local UI

1. Install Open WebUI or Jan.
2. Add a workspace for private docs.
3. Test AnythingLLM or Kotaemon on a small neutral document set.
4. Measure whether answers reduce time or create review burden.

### Week 3: IDE Integration

1. Try Continue with Ollama.
2. Allow read-only code explanation and test suggestion.
3. For code edit, require Codex/human approval.

### Week 4: Automation

1. Use n8n or Task Scheduler for nightly queue.
2. Generate morning report.
3. Add context-pack generation for Codex.
4. Track false-positive rate.

## Decision

Local LLM is not useless, but its value is not “being a smaller Codex.”

Best role:

```text
Private preflight assistant + local UI + document Q&A + nightly automation
```

For this PC, the highest-value path is:

1. Open WebUI or Jan for local chat.
2. Continue for local code explanation/preflight.
3. AnythingLLM/Kotaemon/Khoj for document Q&A.
4. n8n or Task Scheduler for nightly reports.
5. Keep `qwen2.5-coder:7b`; add an embedding model.

This is materially more useful than scout-only, while still respecting the limits of an 8 GB VRAM local model.
