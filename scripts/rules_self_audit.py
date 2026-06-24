from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


CONTEXT_PATTERNS = [
    "AGENTS.md",
    "CLAUDE.md",
    "GEMINI.md",
    ".cursorrules",
    ".github/copilot-instructions.md",
    ".cursor/rules/**/*.md",
    ".cursor/rules/**/*.mdc",
    "skills/*/SKILL.md",
]

SKILL_REFERENCE_PATTERNS = [
    "skills/*/references/*.md",
]

MUST_TERMS = [
    "must",
    "always",
    "required",
    "shall",
    "반드시",
    "항상",
    "필수",
    "해야",
]

FORBID_TERMS = [
    "never",
    "do not",
    "don't",
    "forbid",
    "금지",
    "하지 않는다",
    "하지 말라",
    "하면 안",
]

AUTO_TERMS = [
    "auto",
    "automatic",
    "nightly",
    "scheduled",
    "scheduler",
    "n8n",
    "자동",
    "야간",
]

APPROVAL_TERMS = [
    "approval",
    "approve",
    "human",
    "review",
    "승인",
    "검토",
]

BROAD_CONTEXT_TERMS = [
    "read all",
    "entire repo",
    "whole repo",
    "all files",
    "recursive",
    "모든 파일",
    "전체",
]

TOKEN_TERMS = [
    "token",
    "context",
    "토큰",
    "컨텍스트",
]

PATH_SUFFIXES = (
    ".md",
    ".mdc",
    ".py",
    ".ps1",
    ".yaml",
    ".yml",
    ".json",
    ".toml",
    ".ini",
    ".txt",
    ".c",
    ".h",
    ".cpp",
    ".hpp",
    ".js",
    ".ts",
    ".tsx",
)

BACKTICK_RE = re.compile(r"`([^`\n]+)`")


@dataclass(frozen=True)
class ContextFile:
    path: Path
    rel: str
    text: str
    lines: list[str]


@dataclass(frozen=True)
class LineHit:
    file: str
    line: int
    text: str


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    title: str
    detail: str
    evidence: list[str]
    recommendation: str


def read_text(path: Path) -> str:
    for encoding in ("utf-8", "utf-8-sig", "cp949"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="replace")


def relpath(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def discover_context_files(root: Path, include_skill_references: bool) -> list[ContextFile]:
    patterns = list(CONTEXT_PATTERNS)
    if include_skill_references:
        patterns.extend(SKILL_REFERENCE_PATTERNS)

    paths: list[Path] = []
    seen: set[Path] = set()
    for pattern in patterns:
        for path in root.glob(pattern):
            if not path.is_file():
                continue
            resolved = path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            paths.append(path)

    context_files: list[ContextFile] = []
    for path in sorted(paths, key=lambda item: item.as_posix().lower()):
        text = read_text(path)
        context_files.append(
            ContextFile(
                path=path,
                rel=relpath(root, path),
                text=text,
                lines=text.splitlines(),
            )
        )
    return context_files


def contains_any(line: str, terms: list[str]) -> bool:
    lower = line.lower()
    return any(term.lower() in lower for term in terms)


def collect_line_hits(context_files: list[ContextFile], terms: list[str]) -> list[LineHit]:
    hits: list[LineHit] = []
    for file in context_files:
        for index, line in enumerate(file.lines, start=1):
            if contains_any(line, terms):
                hits.append(LineHit(file=file.rel, line=index, text=line.strip()))
    return hits


def clean_reference_token(token: str) -> str:
    token = token.strip().strip("'\"")
    token = token.rstrip(".,;:)]}")
    token = token.lstrip("([{@")
    return token.strip()


def looks_like_path(token: str) -> bool:
    token = token.replace("\\", "/")
    if not token or token.startswith(("http://", "https://", "#")):
        return False
    if " " in token and not any(token.endswith(suffix) for suffix in PATH_SUFFIXES):
        return False
    return (
        "/" in token
        or "\\" in token
        or "*" in token
        or token.endswith(PATH_SUFFIXES)
    )


def path_exists(root: Path, source_dir: Path, token: str) -> bool:
    normalized = token.replace("\\", "/")
    if re.match(r"^[A-Za-z]:/", normalized):
        return Path(token).exists()
    if normalized.startswith("/"):
        return Path(normalized).exists()
    if any(char in normalized for char in "*?[]"):
        return any(root.glob(normalized)) or any(source_dir.glob(normalized))
    root_candidate = root / normalized
    source_candidate = source_dir / normalized
    if root_candidate.exists() or source_candidate.exists():
        return True
    if "/" not in normalized:
        return any(root.rglob(normalized))
    return False


def extract_references(context_files: list[ContextFile]) -> list[tuple[str, int, str, Path]]:
    references: list[tuple[str, int, str, Path]] = []
    seen: set[tuple[str, int, str]] = set()
    for file in context_files:
        for index, line in enumerate(file.lines, start=1):
            for raw in BACKTICK_RE.findall(line):
                token = clean_reference_token(raw)
                if not looks_like_path(token):
                    continue
                key = (file.rel, index, token)
                if key in seen:
                    continue
                seen.add(key)
                references.append((file.rel, index, token, file.path.parent))
    return references


def short_evidence(hits: list[LineHit], limit: int = 5) -> list[str]:
    return [f"{hit.file}:{hit.line} - {hit.text}" for hit in hits[:limit]]


def build_findings(root: Path, context_files: list[ContextFile]) -> list[Finding]:
    findings: list[Finding] = []

    if not context_files:
        return [
            Finding(
                severity="must_fix",
                code="NO_CONTEXT_FILES",
                title="No agent context files found",
                detail="The repo has no AGENTS.md, CLAUDE.md, Copilot instructions, Cursor rules, or skill entry files.",
                evidence=[],
                recommendation="Add one small entry file that routes agents to the right project rules and verification commands.",
            )
        ]

    missing_refs: list[str] = []
    for source_file, line, token, source_dir in extract_references(context_files):
        if not path_exists(root, source_dir, token):
            missing_refs.append(f"{source_file}:{line} -> `{token}`")
    if missing_refs:
        findings.append(
            Finding(
                severity="must_fix",
                code="BROKEN_REFERENCE",
                title="Referenced files or globs do not resolve",
                detail="Broken references waste context and make the agent follow rules that were never loaded.",
                evidence=missing_refs[:10],
                recommendation="Fix the path, remove stale references, or add the missing routed document.",
            )
        )

    must_hits = collect_line_hits(context_files, MUST_TERMS)
    forbid_hits = collect_line_hits(context_files, FORBID_TERMS)
    auto_hits = collect_line_hits(context_files, AUTO_TERMS)
    approval_hits = collect_line_hits(context_files, APPROVAL_TERMS)
    broad_hits = collect_line_hits(context_files, BROAD_CONTEXT_TERMS)
    token_hits = collect_line_hits(context_files, TOKEN_TERMS)

    for file in context_files:
        hard_rule_count = sum(
            1
            for line in file.lines
            if contains_any(line, MUST_TERMS) or contains_any(line, FORBID_TERMS)
        )
        if hard_rule_count >= 30:
            findings.append(
                Finding(
                    severity="should_check",
                    code="TOO_MANY_HARD_RULES",
                    title="Many hard rules in one context file",
                    detail=f"{file.rel} contains {hard_rule_count} must/never-style lines. Priority can become unclear and token cost rises.",
                    evidence=[file.rel],
                    recommendation="Split rules into a short routing entry file plus focused reference files. Keep the entry file for gates, safety, and routing only.",
                )
            )

        if len(file.text) > 40000:
            findings.append(
                Finding(
                    severity="must_fix",
                    code="LARGE_CONTEXT_FILE",
                    title="Context file is larger than a practical instruction budget",
                    detail=f"{file.rel} has {len(file.text)} characters.",
                    evidence=[file.rel],
                    recommendation="Move detailed domain rules into routed references and keep the top-level file compact.",
                )
            )

    if broad_hits and token_hits:
        findings.append(
            Finding(
                severity="should_check",
                code="BROAD_READ_VS_TOKEN_BUDGET",
                title="Broad read rules may conflict with token/context discipline",
                detail="The repo mentions broad reading and token/context limits. The audit should define when to route instead of reading everything.",
                evidence=short_evidence(broad_hits, 3) + short_evidence(token_hits, 3),
                recommendation="Add an explicit routing policy: read index/registry first, then load only the relevant detailed rule file.",
            )
        )

    if auto_hits and not approval_hits:
        findings.append(
            Finding(
                severity="must_fix",
                code="AUTOMATION_WITHOUT_APPROVAL_BOUNDARY",
                title="Automation terms found without an approval boundary",
                detail="Nightly or automatic maintenance is mentioned, but no human-review/approval wording was detected.",
                evidence=short_evidence(auto_hits),
                recommendation="State that automated jobs produce reports and patch candidates only. Final AGENTS/rules edits require human or primary-agent approval.",
            )
        )

    if auto_hits and forbid_hits:
        findings.append(
            Finding(
                severity="should_check",
                code="AUTO_EDIT_BOUNDARY",
                title="Automation and forbid/never rules coexist",
                detail="This can be correct, but the allowed auto-repair boundary should be written down so future agents do not guess.",
                evidence=short_evidence(auto_hits, 3) + short_evidence(forbid_hits, 3),
                recommendation="Separate safe automatic fixes from report-only findings. For AGENTS.md, prefer report-only by default.",
            )
        )

    if not any("test" in hit.text.lower() or "compile" in hit.text.lower() or "build" in hit.text.lower() for hit in collect_line_hits(context_files, ["test", "compile", "build", "테스트", "컴파일"])):
        findings.append(
            Finding(
                severity="should_check",
                code="NO_VERIFICATION_COMMANDS",
                title="No obvious compile/test/build commands found",
                detail="Agent rules are stronger when they point to concrete verification gates.",
                evidence=[],
                recommendation="Add a short verification section with the fast compile/test command and the expensive full gate.",
            )
        )

    return findings


def grill_questions(findings: list[Finding]) -> list[str]:
    base = [
        "Which rule source wins when AGENTS.md, a skill, and a task-specific handoff disagree?",
        "Which findings may be auto-fixed, and which must stay as report-only patch candidates?",
        "What evidence is required before a new rule is added: repeated user correction, failed review, broken build, or documented defect?",
        "What is the maximum top-level AGENTS.md size before rules must be split into routed files?",
        "Which checks block coding immediately, and which only create a next-day cleanup item?",
        "Can a local LLM propose AGENTS.md edits, or may it only generate questions and findings?",
    ]

    codes = {finding.code for finding in findings}
    if "BROKEN_REFERENCE" in codes:
        base.insert(0, "Are any broken references intentionally optional, or are they stale rule routes that must be removed?")
    if "AUTO_EDIT_BOUNDARY" in codes or "AUTOMATION_WITHOUT_APPROVAL_BOUNDARY" in codes:
        base.insert(0, "What exact files can a nightly job change without approval, if any?")
    if "BROAD_READ_VS_TOKEN_BUDGET" in codes:
        base.insert(0, "When a rule says to read broadly, what routing file should be checked first to avoid token waste?")
    return base


def patch_candidates(findings: list[Finding]) -> list[str]:
    candidates = [
        "Add an `Agent Rules Maintenance` section: nightly jobs generate audit reports and patch candidates only.",
        "Add a `Rule Source Priority` section: user request > task handoff > AGENTS.md > routed skill/reference docs.",
        "Add a `Routing Before Reading` section: inspect registry/index first, then load only relevant detailed docs.",
        "Add a `Verification Gates` section with fast compile/test and full review gates.",
    ]
    codes = {finding.code for finding in findings}
    if "BROKEN_REFERENCE" in codes:
        candidates.append("Repair or delete unresolved backtick file references found in agent context files.")
    if "TOO_MANY_HARD_RULES" in codes or "LARGE_CONTEXT_FILE" in codes:
        candidates.append("Split long instruction files into a short entry point plus focused routed references.")
    return candidates


def report_markdown(root: Path, context_files: list[ContextFile], findings: list[Finding]) -> str:
    generated_at = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    counts = {
        "must_fix": sum(1 for finding in findings if finding.severity == "must_fix"),
        "should_check": sum(1 for finding in findings if finding.severity == "should_check"),
    }
    lines = [
        "# Agent Rules Self-Audit Report",
        "",
        f"Generated: {generated_at}",
        f"Repo: `{root}`",
        "",
        "## Summary",
        "",
        f"- Context files scanned: {len(context_files)}",
        f"- MUST_FIX findings: {counts['must_fix']}",
        f"- SHOULD_CHECK findings: {counts['should_check']}",
        "",
        "## Scanned Files",
        "",
    ]

    if context_files:
        lines.extend(f"- `{file.rel}` ({len(file.text)} chars)" for file in context_files)
    else:
        lines.append("- None")

    lines.extend(["", "## Findings", ""])
    if findings:
        for finding in findings:
            lines.extend(
                [
                    f"### {finding.severity.upper()}: {finding.code}",
                    "",
                    f"**{finding.title}**",
                    "",
                    finding.detail,
                    "",
                    "Evidence:",
                ]
            )
            if finding.evidence:
                lines.extend(f"- {item}" for item in finding.evidence)
            else:
                lines.append("- No direct line evidence; inferred from missing pattern.")
            lines.extend(["", f"Recommendation: {finding.recommendation}", ""])
    else:
        lines.append("No findings. Keep monitoring after structural changes.")

    lines.extend(
        [
            "## Grill-Me Questions",
            "",
        ]
    )
    lines.extend(f"{index}. {question}" for index, question in enumerate(grill_questions(findings), start=1))

    lines.extend(
        [
            "",
            "## Patch Candidates",
            "",
        ]
    )
    lines.extend(f"- {candidate}" for candidate in patch_candidates(findings))

    lines.extend(
        [
            "",
            "## Policy",
            "",
            "- This script is read-only.",
            "- It does not edit AGENTS.md, skills, rule files, source code, or CI.",
            "- Treat this report as a review queue. Apply patches only after human or primary-agent approval.",
            "",
        ]
    )
    return "\n".join(lines)


def report_json(root: Path, context_files: list[ContextFile], findings: list[Finding]) -> str:
    payload = {
        "generated_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "repo": str(root),
        "context_files": [
            {"path": file.rel, "chars": len(file.text), "lines": len(file.lines)}
            for file in context_files
        ],
        "findings": [
            {
                "severity": finding.severity,
                "code": finding.code,
                "title": finding.title,
                "detail": finding.detail,
                "evidence": finding.evidence,
                "recommendation": finding.recommendation,
            }
            for finding in findings
        ],
        "grill_questions": grill_questions(findings),
        "patch_candidates": patch_candidates(findings),
        "policy": "read-only report; patch candidates require approval",
    }
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only AGENTS/rules self-audit report generator")
    parser.add_argument("--repo", default=".", help="Repository root to scan")
    parser.add_argument("--out", help="Write report to this path")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument(
        "--include-skill-references",
        action="store_true",
        help="Also scan skills/*/references/*.md as rule context.",
    )
    parser.add_argument(
        "--fail-on-must-fix",
        action="store_true",
        help="Return exit code 1 when MUST_FIX findings exist. Useful for CI, not nightly reports.",
    )
    args = parser.parse_args()

    root = Path(args.repo).expanduser().resolve()
    if not root.exists():
        raise SystemExit(f"Repo path does not exist: {root}")

    context_files = discover_context_files(root, args.include_skill_references)
    findings = build_findings(root, context_files)
    if args.format == "json":
        output = report_json(root, context_files, findings)
    else:
        output = report_markdown(root, context_files, findings)

    if args.out:
        out_path = Path(args.out).expanduser()
        if not out_path.is_absolute():
            out_path = root / out_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(output, encoding="utf-8")
    else:
        sys.stdout.write(output)

    has_must_fix = any(finding.severity == "must_fix" for finding in findings)
    return 1 if args.fail_on_must_fix and has_must_fix else 0


if __name__ == "__main__":
    raise SystemExit(main())
