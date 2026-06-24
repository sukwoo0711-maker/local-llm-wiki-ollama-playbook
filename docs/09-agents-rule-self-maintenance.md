# 09. AGENTS Rule Self-Maintenance

조사일: 2026-06-25
목표: `grill-me`식 질문으로 `AGENTS.md`, skill, Cursor/Copilot rule의 모순과 누락을 찾아내고, 사내 PC에서 야간 보고서로 돌릴 수 있게 정리한다.

## 결론

GitHub에는 이미 비슷한 흐름이 있다. 다만 좋은 사례들은 공통적으로 **자동 수정/자동 push**가 아니라 **감사, 점수화, 보고서, 수정 후보 생성**에 머문다.

사내 PC에 이식할 때도 같은 경계가 맞다.

```text
nightly schedule
  -> read AGENTS.md / skills / rule files
  -> deterministic checks
  -> grill-me question candidates
  -> patch candidates
  -> reports/agents-audit-YYYY-MM-DD.md
  -> human or primary coding agent approval
  -> manual patch / review / commit
```

`qwen2.5-coder:7b`는 여기서 “판정자”가 아니라 질문 후보 생성기다. 깨진 경로, 큰 파일, 과한 hard rule 수, 승인 경계 누락 같은 것은 deterministic script가 먼저 잡고, Qwen이나 `grill-me`는 왜 그 규칙이 필요한지 캐묻는 데 쓴다.

## 실제 GitHub 사례

| Project | 확인한 패턴 | 사내 적용 포인트 |
| --- | --- | --- |
| `samilozturk/agentlint` | `AGENTS.md` / `CLAUDE.md` / skills / rules / workflows를 codebase-aware하게 유지하는 CLI/MCP. scan, prompt, score, quick check 개념이 있다. | 우리도 read-only scan과 maintenance prompt를 만든다. |
| GitHub Marketplace `AgentLint` | repo가 AI coding agent를 얼마나 잘 지원하는지 deterministic checks로 점수화한다. AGENTS, CLAUDE, CI, hooks, `.gitignore`까지 harness로 본다. | AGENTS만 보지 말고 compile/test gate, 보안 파일, hook까지 점검 범위를 넓힐 수 있다. |
| `github/awesome-copilot`의 Doublecheck agent | self-audit, source verification, adversarial review 3단계 보고서 패턴. | `grill-me` 질문을 adversarial review 단계로 둔다. |
| `agentsmd/agents.md` | AGENTS.md를 coding agent 안내용 open format으로 정리한다. | 사내 repo도 top-level AGENTS를 짧은 router로 쓰고 상세 규칙은 reference로 뺀다. |
| Cursor rules 생태계 | `.cursor/rules/*.mdc`처럼 task별 rule routing을 쓴다. | 큰 단일 markdown보다 작은 rule file을 라우팅하는 방식이 토큰 면에서 낫다. |
| GitHub Blog agents.md 글 | 여러 repo의 agents.md 운용에서 얻은 작성 원칙을 정리한다. | “한 번 쓰고 방치”가 아니라 운영 artifact로 다룬다. |

GitHub REST API로 본 관련 repo 신호(2026-06-25):

| Repo | Stars | 의미 |
| --- | ---: | --- |
| `PatrickJS/awesome-cursorrules` | 40,085 | rule collection/routing 생태계가 이미 크다. |
| `github/awesome-copilot` | 35,653 | instructions, agents, skills, prompt 생태계가 크다. |
| `agentsmd/agents.md` | 22,461 | AGENTS.md 표준화 수요가 크다. |
| `ciembor/agent-rules-books` | 1,951 | AGENTS/skills rule library 수요가 있다. |
| `matank001/cursor-security-rules` | 372 | 보안 rule set도 별도 관리된다. |
| `samilozturk/agentlint` | 28 | 아직 작지만, 문제 정의가 우리 요구와 가장 직접적으로 맞는다. |

## AS-IS / TO-BE

### 1. 규칙 모순 찾기

AS-IS:

```text
AGENTS.md:
  - 작업 전 관련 문서를 충분히 읽어라.
  - 토큰을 아껴라.
  - skill reference를 따라가라.

실제 동작:
  agent가 큰 md 파일을 통째로 읽고 토큰을 많이 쓴다.
```

TO-BE:

```text
nightly audit:
  SHOULD_CHECK BROAD_READ_VS_TOKEN_BUDGET
  Evidence:
    AGENTS.md: read all relevant docs
    AGENTS.md: keep context lean

Grill question:
  "넓게 읽어야 할 때, 먼저 어떤 index/registry를 보고 라우팅할 것인가?"

Patch candidate:
  "Routing Before Reading 섹션 추가"
```

효과: 규칙을 삭제하지 않고도 우선순위와 라우팅을 명확히 한다.

### 2. 승인 경계 누락 찾기

AS-IS:

```text
AGENTS.md:
  - 야간 자동화로 규칙을 갱신한다.

문제:
  어느 파일까지 자동 수정 가능한지 없다.
```

TO-BE:

```text
nightly audit:
  MUST_FIX AUTOMATION_WITHOUT_APPROVAL_BOUNDARY

Patch candidate:
  "자동화는 reports/ 에 감사 리포트와 patch 후보만 생성한다.
   AGENTS.md, skills, source code는 승인 전 자동 수정하지 않는다."
```

효과: 자동화가 편해지면서도 규칙 파일이 임의로 바뀌는 위험을 막는다.

### 3. 오래된 경로 찾기

AS-IS:

```text
AGENTS.md:
  - `docs/old-review-flow.md`를 읽어라.

실제 repo:
  docs/old-review-flow.md 삭제됨
```

TO-BE:

```text
nightly audit:
  MUST_FIX BROKEN_REFERENCE
  Evidence:
    AGENTS.md:42 -> `docs/old-review-flow.md`
```

효과: agent가 없는 문서를 찾느라 시간을 쓰거나 잘못된 가정을 세우는 일을 줄인다.

### 4. hard rule 과다 찾기

AS-IS:

```text
AGENTS.md:
  반드시 A
  반드시 B
  반드시 C
  ...
```

문제: 모든 것이 중요하면 아무 것도 중요하지 않다. 토큰도 많이 든다.

TO-BE:

```text
nightly audit:
  SHOULD_CHECK TOO_MANY_HARD_RULES

Patch candidate:
  AGENTS.md는 entry/router로 줄이고,
  compile gate, review gate, skill routing을 별도 reference로 분리한다.
```

효과: Codex가 매번 읽는 상위 규칙은 작아지고, 필요한 상세 규칙만 로드한다.

## 사내 PC 이식 절차

1. playbook repo를 사내 PC에 clone한다.

```powershell
git clone https://github.com/sukwoo0711-maker/local-llm-wiki-ollama-playbook.git
cd .\local-llm-wiki-ollama-playbook
```

2. 대상 repo를 수동으로 한 번 감사한다.

```powershell
python .\scripts\rules_self_audit.py `
  --repo C:\GitRepositories\embedded-ax-devkit `
  --include-skill-references `
  --out reports\agents-audit-manual.md
```

기본 실행은 report-only라서 `MUST_FIX`가 있어도 exit code 0을 반환한다. CI gate로 쓰고 싶을 때만 `--fail-on-must-fix`를 추가한다.

3. 생성된 report를 보고 세 가지로 분류한다.

| 분류 | 처리 |
| --- | --- |
| `MUST_FIX` | 깨진 경로, 승인 경계 누락처럼 실제 위험이 높은 항목. 바로 수정 후보 작성. |
| `SHOULD_CHECK` | 토큰 낭비, rule 과다, 라우팅 모호성. 다음 정리 작업으로 보냄. |
| Grill-Me Questions | 사용자나 primary agent에게 물어야 하는 설계 질문. 답이 나오면 규칙으로 승격. |

4. 야간 작업으로 등록한다.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass `
  -File .\scripts\install_agents_audit_task.ps1 `
  -TargetRepo C:\GitRepositories\embedded-ax-devkit `
  -StartTime 22:45
```

5. 아침에 `reports/agents-audit-YYYY-MM-DD.md`만 확인한다.

## n8n으로 옮길 때

Task Scheduler가 충분하면 n8n은 필요 없다. 그래도 n8n을 쓰면 다음 흐름이 깔끔하다.

```text
Cron 22:45
  -> Execute Command: python scripts/rules_self_audit.py ...
  -> Read Binary/Text File: reports/agents-audit-YYYY-MM-DD.md
  -> IF: MUST_FIX count > 0
  -> Send notification: Teams/Slack/Email/local file
  -> optional: create GitHub issue in private repo
```

n8n의 장점은 조건 분기와 알림이다. 실제 규칙 판정은 Python script가 맡는 편이 디버깅이 쉽다.

## 권장 AGENTS.md 유지보수 규칙

다음 문구를 AGENTS.md 또는 routed reference에 추가하는 것이 좋다.

```md
## Agent Rules Maintenance

- Nightly jobs may generate rule audit reports and patch candidates under `reports/`.
- Nightly jobs must not edit `AGENTS.md`, skills, rule files, source code, or CI without approval.
- When rules conflict, newest user instruction wins, then task handoff, then `AGENTS.md`, then routed skill/reference docs.
- Prefer routing over bulk reading: inspect index/registry files first, then load only relevant detailed references.
- New durable rules need evidence: repeated user correction, failed review, broken build/test, or documented defect.
```

## Qwen / Grill-Me 역할 분담

| Stage | Tool | Role |
| --- | --- | --- |
| deterministic audit | Python | 깨진 경로, 큰 파일, hard rule 과다, 승인 경계 누락을 잡는다. |
| local question draft | `qwen2.5-coder:7b` | 사내 내용을 외부로 보내지 않고 누락 질문 후보를 만든다. |
| adversarial interrogation | `grill-me` | 사용자의 정책 결정을 하나씩 물고 늘어진다. |
| final edit/review | Codex or human | 실제 AGENTS.md 수정, compile gate, review, commit을 수행한다. |

## References

- Agent Lint: https://github.com/samilozturk/agentlint
- AgentLint GitHub Action: https://github.com/marketplace/actions/agentlint
- GitHub awesome-copilot agents: https://github.com/github/awesome-copilot/blob/main/docs/README.agents.md
- AGENTS.md open format: https://github.com/agentsmd/agents.md
- GitHub Blog, agents.md lessons: https://github.blog/ai-and-ml/github-copilot/how-to-write-a-great-agents-md-lessons-from-over-2500-repositories/
- Cursor rules collection: https://github.com/PatrickJS/awesome-cursorrules
