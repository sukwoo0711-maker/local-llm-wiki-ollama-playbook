# 02. Windows + Ollama Setup

## 설치 확인

```powershell
ollama --version
ollama list
```

Ollama는 Windows, macOS, Linux에서 로컬 LLM을 실행할 수 있게 해준다. Qwen 공식 문서는 Ollama에서 Qwen2.5를 한 줄로 실행할 수 있다고 설명한다.

Reference: https://qwen.readthedocs.io/en/latest/run_locally/ollama.html

## 모델 준비

기준 모델:

```powershell
ollama pull qwen2.5-coder:7b
ollama run qwen2.5-coder:7b
```

Ollama의 Qwen2.5-Coder page는 0.5B, 1.5B, 3B, 7B, 14B, 32B 크기를 제공한다고 설명한다. `qwen2.5-coder:7b`는 4.7 GB 모델로 표시된다.

Reference: https://ollama.com/library/qwen2.5-coder:7b

## 64 GB RAM / 8 GB VRAM 기준 모델 선택

| 용도 | 권장 모델 | 이유 |
| --- | --- | --- |
| Wiki scout JSON 후보 | `qwen2.5-coder:7b` | 이미 보유, 8 GB VRAM에서 현실적 |
| 더 빠른 초안/라벨링 | `qwen2.5-coder:3b` 또는 `qwen2.5:3b` | 품질은 낮지만 batch 비용이 적음 |
| embedding | `embeddinggemma`, `qwen3-embedding`, `all-minilm` | Ollama 공식 embedding guide의 recommended models |
| 야간 heavy synthesis | 9B급 보유 모델을 선택적으로 테스트 | 8 GB VRAM에서는 속도/메모리 확인 필요 |
| 14B 이상 | 기본 비추천 | VRAM 초과/CPU spill 가능성이 큼 |

Ollama embedding guide는 embeddings가 semantic search/RAG를 위한 numeric vectors이며, recommended models로 `embeddinggemma`, `qwen3-embedding`, `all-minilm`을 제시한다.

Reference: https://docs.ollama.com/capabilities/embeddings

## Chat API

Ollama chat API는 `POST /api/chat`을 사용한다. body에는 `model`과 `messages`가 필요하고, `format`을 `json`이나 JSON schema로 지정할 수 있다. `stream`은 기본 true이므로 script에서는 false로 두는 것이 다루기 쉽다.

Reference: https://docs.ollama.com/api/chat

PowerShell 예:

```powershell
$body = @{
  model = "qwen2.5-coder:7b"
  messages = @(
    @{ role = "system"; content = "Return JSON only." },
    @{ role = "user"; content = "Generate search terms for API authentication migration." }
  )
  format = "json"
  stream = $false
  options = @{
    temperature = 0.1
    num_ctx = 8192
  }
} | ConvertTo-Json -Depth 10

Invoke-RestMethod `
  -Uri "http://localhost:11434/api/chat" `
  -Method Post `
  -ContentType "application/json" `
  -Body $body
```

## Embed API

Ollama embed API는 `POST /api/embed`를 사용한다.

Reference: https://docs.ollama.com/api/embed

```powershell
$body = @{
  model = "embeddinggemma"
  input = "The quick brown fox jumps over the lazy dog."
} | ConvertTo-Json

Invoke-RestMethod `
  -Uri "http://localhost:11434/api/embed" `
  -Method Post `
  -ContentType "application/json" `
  -Body $body
```

주의:

- `qwen2.5-coder:7b`를 embedding model로 쓰지 않는다.
- embedding model은 별도로 pull한다.
- 처음에는 FTS5/BM25로 충분한지 확인한 뒤 embedding을 추가한다.

## Context 설정

Ollama API에서 `options.num_ctx`를 조절할 수 있다. 하지만 큰 context를 무조건 쓰면 VRAM/RAM과 속도에 부담이 생긴다.

권장:

| 작업 | `num_ctx` |
| --- | ---: |
| query expansion | 2048-4096 |
| link suggestion | 4096-8192 |
| contradiction candidate | 8192 |
| multi-page synthesis | 8192-16384, 야간 batch만 |

작은 모델에게 긴 context를 주는 것보다, 검색으로 필요한 section만 좁혀 넣는 것이 더 안정적이다.
