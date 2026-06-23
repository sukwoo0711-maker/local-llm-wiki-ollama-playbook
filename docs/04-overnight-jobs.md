# 04. Overnight Jobs

퇴근 후 local LLM이 의미 있는 일을 하게 하려면, 위험한 자동 수정보다 **후보 생성 + 리포트 생성**에 집중해야 한다.

## 야간 작업 원칙

1. 원본 파일은 읽기 전용으로 취급한다.
2. curated wiki를 직접 덮어쓰지 않는다.
3. 후보는 `qwen-candidates/` 아래에 쌓는다.
4. 다음 날 사람이 review할 수 있는 `nightly-report.md`를 만든다.
5. 실패해도 업무 pipeline이 깨지지 않아야 한다.

## 추천 작업 목록

| 작업 | 빈도 | Local LLM 필요 | 설명 |
| --- | --- | --- | --- |
| source hash scan | 매일 | 없음 | 변경된 source 탐지 |
| FTS index rebuild | 매일 | 없음 | SQLite/ripgrep index 갱신 |
| orphan link scan | 매일 | 없음 | 존재하지 않는 wikilink 탐지 |
| thin page detection | 매일 | 선택 | 내용이 너무 얕은 page 후보 |
| query expansion cache | 매일 | 있음 | 자주 쓰는 검색 intent별 query set 생성 |
| gap question generation | 매일 | 있음 | draft 문서별 누락 질문 생성 |
| contradiction scout | 주 1-2회 | 있음 | 변경 source와 관련 page만 비교 |
| summary refresh | 주 1회 | 있음 | stale summary 후보 생성 |

## 피해야 할 작업

- 전체 wiki를 매일 LLM에 넣고 재작성
- 전체 문서쌍 contradiction 비교
- source citation 없는 summary 자동 반영
- 오래 걸리는 14B/32B 모델을 업무 PC에서 무제한 실행
- 업무 시간에 CPU/GPU를 점유하는 batch

Karpathy gist 토론에서도 full wiki contradiction check는 context 비용이 크므로, 새 source가 실제로 건드린 page나 1-2 degree local subgraph로 좁히는 접근이 제안된다.

Reference: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f

## Windows Task Scheduler

Microsoft `schtasks /create`는 명령이나 프로그램을 지정 시간에 실행하도록 schedule할 수 있다.

Reference: https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/schtasks-create

예:

```powershell
schtasks /Create `
  /TN "LocalLlmWikiNightly" `
  /SC DAILY `
  /ST 22:30 `
  /TR "powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\Work\wiki\nightly.ps1"
```

PowerShell ScheduledTasks module을 쓰면 action/trigger/settings를 object로 정의할 수 있다. `New-ScheduledTaskAction`은 task가 실행할 command definition을 만든다.

Reference: https://learn.microsoft.com/en-us/powershell/module/scheduledtasks/new-scheduledtaskaction

## Nightly report template

```md
# Nightly Wiki Report

Date: 2026-06-24
Model: qwen2.5-coder:7b

## Changed Sources

## Rebuilt Index

## Candidate Query Expansions

## Candidate Links

## Possible Contradictions

## Gap Questions

## Failures

## Human Review Checklist
```

## Safety gate

야간 작업은 다음 파일만 생성해야 한다.

```text
knowledge/qwen-candidates/*.jsonl
knowledge/reports/nightly-YYYY-MM-DD.md
logs/nightly-YYYY-MM-DD.log
```

다음은 금지한다.

```text
wiki/*.md 직접 수정
raw/* 수정
git commit 자동 실행
사내 자료 외부 전송
```
