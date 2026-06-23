# Result Report

이 보고서는 LLM Wiki와 Ollama local LLM을 사내 업무용 PC에 참고 적용하기 위한 조사 결과다.

## 결론

`qwen2.5-coder:7b`는 64 GB RAM / 8 GB VRAM 업무용 PC에서 **local wiki scout**로 쓰는 것이 가장 안전하다.

권장 역할:

- query expansion
- wiki link suggestion
- gap question generation
- contradiction candidate detection
- context pack selection
- nightly stale page review

비권장 역할:

- 최종 업무 답변자
- 코드 수정자
- 사양 해석자
- root cause 판단자
- 검색 엔진 대체재

## 근거 요약

1. Karpathy의 LLM Wiki pattern은 raw documents를 매번 RAG로 재검색하는 대신 LLM이 persistent markdown wiki를 점진적으로 유지하는 구조를 제안한다.
2. GeekNews 요약과 토론에서도 LLM Wiki의 가치는 영속적 축적, cross-reference, contradiction/gap 관리에 있다.
3. Local RAG 토론에서는 Markdown 기반 소규모 지식에는 SQLite FTS5/BM25가 충분히 효과적일 수 있다는 사례가 제시된다.
4. Ollama는 chat API와 embed API를 제공하지만, embedding은 전용 embedding model을 쓰는 것이 맞다.
5. Qwen2.5-Coder는 coding/code reasoning/fixing에 특화되어 있지만, 7B local model은 강한 cloud coding agent를 대체하기보다 구조화 JSON 후보 생성에 적합하다.

## 산출물

| 파일 | 목적 |
| --- | --- |
| `README.md` | 전체 playbook |
| `docs/01-architecture.md` | 권장 아키텍처 |
| `docs/02-windows-ollama-setup.md` | Windows/Ollama setup |
| `docs/03-qwen-role-policy.md` | Qwen 역할 제한 정책 |
| `docs/04-overnight-jobs.md` | 퇴근 후 batch 작업 |
| `docs/05-command-patterns.md` | 실제 명령 prompt/API pattern |
| `docs/06-reference-map.md` | 아이디어별 근거 URL |
| `scripts/ollama_wiki_scout.py` | Ollama chat API 예제 |
| `scripts/install_nightly_task.ps1` | Windows Task Scheduler 예제 |

## 운영 원칙

```text
Python deterministic scripts first.
Local LLM candidate generation second.
Human or strong agent verification last.
```

Local LLM 도입으로 답변 품질이 떨어지면 해당 단계는 끈다. 이 repo는 local LLM을 무조건 적용하는 절차서가 아니라, 사내 PC에서 필요한 부분만 선택해 보완하기 위한 근거 기반 guide다.
